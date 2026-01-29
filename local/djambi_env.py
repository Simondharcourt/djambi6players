import logging
import os
import random
import sys
from typing import Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
import pygame
from gymnasium import spaces

from backend.src.constants import FONT_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("djambi_rl.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.src import Board, MinMaxPlayer, Player, create_piece


class DjambiEnv(gym.Env):
    """
    Djambi environment for 3 players with reinforcement learning.
    Uses the existing backend for game logic.
    """

    def __init__(self, nb_players: int = 3, render: bool = False):
        super().__init__()
        logger.debug("Initializing Djambi environment")

        self.render_mode = "human" if render else None
        self.nb_players = nb_players
        self.paused = False  # Pause state

        if self.render_mode == "human":
            pygame.init()
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("Djambi")
            self.clock = pygame.time.Clock()
            pygame.font.init()
            self.font = pygame.font.Font(None, FONT_SIZE)

        # Initialize the board
        self.board = Board(self.nb_players, current_player_index=0)
        self.board.rl = (
            self.render_mode != "human"
        )  # Set rl to False when rendering is enabled

        # Define observation and action spaces
        self.observation_space = spaces.Dict(
            {
                "board": spaces.Box(
                    low=0,
                    high=self.nb_players,
                    shape=(
                        self.board.board_size * 2 - 1,
                        self.board.board_size * 2 - 1,
                    ),
                    dtype=np.int8,
                ),
                "player_status": spaces.Box(
                    low=0, high=1, shape=(self.nb_players,), dtype=np.int8
                ),
                "current_player": spaces.Discrete(self.nb_players),
            }
        )

        # Action: (piece_q, piece_r, move_q, move_r)
        self.action_space = spaces.MultiDiscrete(
            [
                self.board.board_size * 2 - 1,  # piece_q
                self.board.board_size * 2 - 1,  # piece_r
                self.board.board_size * 2 - 1,  # move_q
                self.board.board_size * 2 - 1,  # move_r
            ]
        )

        # Initialization
        self.reset()

    def get_valid_actions(self) -> List[np.ndarray]:
        """
        Returns the list of valid actions for the current player.
        """
        valid_actions = []
        current_player = self.board.players[self.board.current_player_index]

        # For each piece of the current player
        for piece in current_player.pieces:
            if piece.is_dead:
                continue

            # Get possible moves for this piece
            possible_moves = self.board.get_possible_moves(piece)

            # Convert hexagonal coordinates to action space coordinates
            piece_q = piece.q + (self.board.board_size - 1)
            piece_r = piece.r + (self.board.board_size - 1)

            for move_q, move_r in possible_moves:
                move_q = move_q + (self.board.board_size - 1)
                move_r = move_r + (self.board.board_size - 1)

                # Create the action
                action = np.array([piece_q, piece_r, move_q, move_r])
                valid_actions.append(action)

        return valid_actions

    def sample_action(self) -> np.ndarray:
        """
        Samples a random valid action.
        """
        valid_actions = self.get_valid_actions()
        if not valid_actions:
            # If no valid action, return an invalid action (will be rejected by step)
            sampled: np.ndarray = self.action_space.sample()
            return sampled
        return random.choice(valid_actions)

    def reset(
        self, seed: Optional[int] = None, options: Optional[dict] = None
    ) -> Tuple[Dict, Dict]:
        """
        Resets the environment for a new game.
        """
        logger.debug("Resetting environment")
        super().reset(seed=seed, options=options)

        # Reset the board
        self.board = Board(self.nb_players, current_player_index=0)
        self.board.rl = (
            self.render_mode != "human"
        )  # Use self.render_mode instead of render_mode

        self.board.pieces = [
            p
            for p in self.board.pieces
            if p.color in [p.color for p in self.board.players]
        ]

        # Current player (starts randomly)
        self.board.current_player_index = random.randint(0, self.nb_players - 1)
        logger.debug(f"Game started with player {self.board.current_player_index + 1}")

        if self.render_mode == "human":
            self.render()

        return self._get_observation(), self._get_info()

    def _get_observation(self) -> Dict[str, np.ndarray]:
        """
        Returns the current observation.
        """
        # Create a board representation
        board_state: np.ndarray = np.zeros(
            (self.board.board_size * 2 - 1, self.board.board_size * 2 - 1),
            dtype=np.int8,
        )
        for piece in self.board.pieces:
            if not piece.is_dead:
                q, r = (
                    piece.q + self.board.board_size - 1,
                    piece.r + self.board.board_size - 1,
                )
                # Use the color index in the color list
                color_name = self.board.names[piece.color]
                color_index = list(self.board.names.keys()).index(piece.color) + 1
                board_state[q, r] = color_index

        # Player status
        player_status = np.ones(self.nb_players, dtype=np.int8)
        for i, player in enumerate(self.board.players):
            if not any(not p.is_dead for p in player.pieces):
                player_status[i] = 0

        return {
            "board": board_state,
            "player_status": player_status,
            "current_player": self.board.current_player_index,
        }

    def _get_info(self) -> Dict:
        """
        Returns additional information.
        """
        return {
            "current_player": self.board.current_player_index,
            "player_status": [
                1 if any(not p.is_dead for p in player.pieces) else 0
                for player in self.board.players
            ],
        }

    def _is_valid_move(
        self, piece_q: int, piece_r: int, move_q: int, move_r: int
    ) -> bool:
        """
        Checks if a move is valid.
        """
        # Convert coordinates
        piece_q = piece_q - (self.board.board_size - 1)
        piece_r = piece_r - (self.board.board_size - 1)
        move_q = move_q - (self.board.board_size - 1)
        move_r = move_r - (self.board.board_size - 1)

        # Check if the piece exists and belongs to the current player
        piece = self.board.get_piece_at(piece_q, piece_r)
        if (
            not piece
            or piece.color != self.board.players[self.board.current_player_index].color
        ):
            logger.warning(
                f"Invalid move: Piece at ({piece_q}, {piece_r}) doesn't exist or doesn't belong to current player"
            )
            return False

        # Check if the move is possible
        possible_moves = self.board.get_possible_moves(piece)
        is_valid = (move_q, move_r) in possible_moves
        if not is_valid:
            logger.warning(
                f"Invalid move: Move to ({move_q}, {move_r}) not in possible moves {possible_moves}"
            )
        return is_valid

    def step(self, action: np.ndarray) -> Tuple[Dict, float, bool, bool, Dict]:
        """
        Executes an action and returns (observation, reward, terminated, truncated, info)
        """
        piece_q, piece_r, move_q, move_r = action
        # logger.debug(
        #     f"Player {self.board.current_player_index + 1} attempting move: piece at ({piece_q}, {piece_r}) to ({move_q}, {move_r})"
        # )

        # Check if the action is valid
        if not self._is_valid_move(piece_q, piece_r, move_q, move_r):
            logger.debug("Invalid move attempted")
            return self._get_observation(), -10.0, False, False, self._get_info()

        current_player = self.board.players[self.board.current_player_index]
        score_initial = current_player.compute_relative_score(self.board)

        # Convert coordinates
        piece_q = piece_q - (self.board.board_size - 1)
        piece_r = piece_r - (self.board.board_size - 1)
        move_q = move_q - (self.board.board_size - 1)
        move_r = move_r - (self.board.board_size - 1)

        # Execute the move
        piece = self.board.get_piece_at(piece_q, piece_r)
        success = self.board.move_piece(piece, move_q, move_r)

        if not success:
            logger.debug("Move execution failed")
            return self._get_observation(), -10.0, False, False, self._get_info()

        logger.debug(
            f"Move executed successfully: {piece.__class__.__name__} {current_player.name} moved from ({piece_q}, {piece_r}) to ({move_q}, {move_r})"
        )

        # Check eliminations
        terminated = False

        # Calculate the current player's relative score
        reward = current_player.compute_relative_score(self.board) - score_initial

        if reward > 0:
            logger.debug(
                f"Player {current_player.name} has improved his score by {reward}"
            )
        elif reward < 0:
            logger.debug(f"Player {current_player.name} has lost {reward} points")

        if self.board.eliminated_players:
            terminated = True

        # If a piece has been killed and must be placed
        if self.board.piece_to_place is not None:
            # Choose a random valid position to place the dead piece
            if self.board.available_cells:
                placement_q, placement_r = random.choice(self.board.available_cells)
                logger.debug(
                    f"Placing dead piece {self.board.piece_to_place.__class__.__name__} at ({placement_q}, {placement_r})"
                )
                placement_success = self.board.place_dead_piece(
                    placement_q, placement_r
                )
                if not placement_success:
                    logger.debug("Failed to place dead piece")
                    return (
                        self._get_observation(),
                        -10.0,
                        False,
                        False,
                        self._get_info(),
                    )
            else:
                logger.debug("No available cells for dead piece placement")
                return self._get_observation(), -10.0, False, False, self._get_info()

        # next_player() is already called in board.move_piece() and board.place_dead_piece()
        logger.debug(
            f"Next player: {self.board.players[self.board.current_player_index].name}"
        )

        if self.render_mode == "human":
            self.render()

        return self._get_observation(), reward, terminated, False, self._get_info()

    def render(self):
        """
        Displays the current board state.
        """
        if self.render_mode == "human":
            # Handle pygame events to keep window responsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                        logger.debug(
                            f"Training {'paused' if self.paused else 'resumed'}"
                        )

            self.screen.fill((0, 0, 0))  # BLACK
            self.board.draw(self.screen)

            # Display pause state
            if self.paused:
                pause_text = self.font.render(
                    "PAUSED - Press SPACE to resume", True, (255, 255, 255)
                )
                text_rect = pause_text.get_rect(center=(WINDOW_WIDTH / 2, 20))
                self.screen.blit(pause_text, text_rect)

            pygame.display.flip()
            self.clock.tick(60)
        else:
            logger.debug("Rendering current board state")
            print("\nCurrent board:")
            board_state = self._get_observation()["board"]
            print(board_state)
            print(f"Current player: {self.board.current_player_index + 1}")
            print(f"Player status: {self._get_info()['player_status']}")

    def close(self):
        """
        Closes the environment and releases resources.
        """
        if self.render_mode == "human":
            pygame.quit()
