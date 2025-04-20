import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Tuple, Dict, List, Optional
import random
import sys
import os
import logging
import pygame
from backend.src.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_SIZE


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

from backend.src import (
    Board,
    create_piece,
    Player,
    MinMaxPlayer,
)


class DjambiEnv(gym.Env):
    """
    Environnement Djambi pour 3 joueurs avec reinforcement learning.
    Utilise le backend existant pour la logique du jeu.
    """

    def __init__(self, nb_players: int = 3, render_mode: Optional[str] = "human"):
        super().__init__()
        logger.info("Initializing Djambi environment")

        self.render_mode = render_mode
        self.nb_players = nb_players
        self.paused = False  # État de pause

        if True:
            pygame.init()
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("Djambi")
            self.clock = pygame.time.Clock()
            pygame.font.init()
            self.font = pygame.font.Font(None, FONT_SIZE)

        # Initialisation du plateau
        self.board = Board(self.nb_players, current_player_index=0)
        self.board.rl = (
            render_mode != "human"
        )  # Set rl to False when rendering is enabled

        # Définition des espaces d'observation et d'action
        self.observation_space = spaces.Dict(
            {
                "board": spaces.Box(
                    low=0,
                    high=self.nb_players,
                    shape=(self.board.board_size * 2 - 1, self.board.board_size * 2 - 1),
                    dtype=np.int8,
                ),
                "player_status": spaces.Box(low=0, high=1, shape=(self.nb_players,), dtype=np.int8),
                "current_player": spaces.Discrete(self.nb_players),
            }
        )

        # Action : (piece_q, piece_r, move_q, move_r)
        self.action_space = spaces.MultiDiscrete(
            [
                self.board.board_size * 2 - 1,  # piece_q
                self.board.board_size * 2 - 1,  # piece_r
                self.board.board_size * 2 - 1,  # move_q
                self.board.board_size * 2 - 1,  # move_r
            ]
        )

        # Initialisation
        self.reset()

    def get_valid_actions(self) -> List[np.ndarray]:
        """
        Retourne la liste des actions valides pour le joueur actuel.
        """
        valid_actions = []
        current_player = self.board.players[self.board.current_player_index]

        # Pour chaque pièce du joueur actuel
        for piece in current_player.pieces:
            if piece.is_dead:
                continue

            # Obtenir les mouvements possibles pour cette pièce
            possible_moves = self.board.get_possible_moves(piece)

            # Convertir les coordonnées hexagonales en coordonnées de l'espace d'action
            piece_q = piece.q + (self.board.board_size - 1)
            piece_r = piece.r + (self.board.board_size - 1)

            for move_q, move_r in possible_moves:
                move_q = move_q + (self.board.board_size - 1)
                move_r = move_r + (self.board.board_size - 1)

                # Créer l'action
                action = np.array([piece_q, piece_r, move_q, move_r])
                valid_actions.append(action)

        return valid_actions

    def sample_action(self) -> np.ndarray:
        """
        Échantillonne une action valide aléatoire.
        """
        valid_actions = self.get_valid_actions()
        if not valid_actions:
            # Si aucune action valide, retourner une action invalide (sera rejetée par step)
            return self.action_space.sample()
        return random.choice(valid_actions)

    def reset(self, seed: Optional[int] = None) -> Tuple[Dict, Dict]:
        """
        Réinitialise l'environnement pour une nouvelle partie.
        """
        logger.info("Resetting environment")
        super().reset(seed=seed)

        # Réinitialiser le plateau
        self.board = Board(self.nb_players, current_player_index=0)
        self.board.rl = (
            self.render_mode != "human"
        )  # Use self.render_mode instead of render_mode

        self.board.pieces = [
            p
            for p in self.board.pieces
            if p.color in [p.color for p in self.board.players]
        ]

        # Joueur actuel (commence aléatoirement)
        self.board.current_player_index = random.randint(0, self.nb_players - 1)
        logger.info(f"Game started with player {self.board.current_player_index + 1}")

        if self.render_mode == "human":
            self.render()

        return self._get_observation(), self._get_info()

    def _get_observation(self) -> Dict:
        """
        Retourne l'observation actuelle.
        """
        # Créer une représentation du plateau
        board_state = np.zeros((self.board.board_size * 2 - 1, self.board.board_size * 2 - 1), dtype=np.int8)
        for piece in self.board.pieces:
            if not piece.is_dead:
                q, r = piece.q + self.board.board_size - 1, piece.r + self.board.board_size - 1
                # Utiliser l'index de la couleur dans la liste des couleurs
                color_name = self.board.names[piece.color]
                color_index = list(self.board.names.keys()).index(piece.color) + 1
                board_state[q, r] = color_index

        # État des joueurs
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
        Retourne les informations supplémentaires.
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
        Vérifie si un mouvement est valide.
        """
        # Convertir les coordonnées
        piece_q = piece_q - (self.board.board_size - 1)
        piece_r = piece_r - (self.board.board_size - 1)
        move_q = move_q - (self.board.board_size - 1)
        move_r = move_r - (self.board.board_size - 1)

        # Vérifier si la pièce existe et appartient au joueur actuel
        piece = self.board.get_piece_at(piece_q, piece_r)
        if (
            not piece
            or piece.color != self.board.players[self.board.current_player_index].color
        ):
            logger.warning(
                f"Invalid move: Piece at ({piece_q}, {piece_r}) doesn't exist or doesn't belong to current player"
            )
            return False

        # Vérifier si le mouvement est possible
        possible_moves = self.board.get_possible_moves(piece)
        is_valid = (move_q, move_r) in possible_moves
        if not is_valid:
            logger.warning(
                f"Invalid move: Move to ({move_q}, {move_r}) not in possible moves {possible_moves}"
            )
        return is_valid

    def step(self, action: np.ndarray) -> Tuple[Dict, float, bool, bool, Dict]:
        """
        Exécute une action et retourne (observation, reward, terminated, truncated, info)
        """
        piece_q, piece_r, move_q, move_r = action
        logger.info(
            f"Player {self.board.current_player_index + 1} attempting move: piece at ({piece_q}, {piece_r}) to ({move_q}, {move_r})"
        )

        # Vérifie si l'action est valide
        if not self._is_valid_move(piece_q, piece_r, move_q, move_r):
            logger.warning("Invalid move attempted")
            return self._get_observation(), -0.1, False, False, self._get_info()

        # Convertir les coordonnées
        piece_q = piece_q - (self.board.board_size - 1)
        piece_r = piece_r - (self.board.board_size - 1)
        move_q = move_q - (self.board.board_size - 1)
        move_r = move_r - (self.board.board_size - 1)

        # Exécuter le mouvement
        piece = self.board.get_piece_at(piece_q, piece_r)
        success = self.board.move_piece(piece, move_q, move_r)

        if not success:
            logger.warning("Move execution failed")
            return self._get_observation(), -0.1, False, False, self._get_info()

        logger.info(
            f"Move executed successfully: {piece.__class__.__name__} moved to ({move_q}, {move_r})"
        )

        # Vérifier les éliminations
        reward = 0.0
        terminated = False

        # Vérifier si le joueur actuel a éliminé quelqu'un
        if self.board.eliminated_players:
            reward = 1.0  # Le joueur actuel a éliminé un autre joueur
            logger.info(f"Current player has eliminated another player")
            terminated = True

        # Si une pièce a été tuée et doit être placée
        if self.board.piece_to_place is not None:
            # Choisir une position aléatoire valide pour placer la pièce morte
            if self.board.available_cells:
                placement_q, placement_r = random.choice(self.board.available_cells)
                placement_success = self.board.place_dead_piece(placement_q, placement_r)
                if not placement_success:
                    logger.warning("Failed to place dead piece")
                    return self._get_observation(), -0.1, False, False, self._get_info()
            else:
                logger.warning("No available cells for dead piece placement")
                return self._get_observation(), -0.1, False, False, self._get_info()

        # Le next_player() est déjà appelé dans board.move_piece() et board.place_dead_piece()
        logger.info(f"Next player: {self.board.current_player_index + 1}")

        if self.render_mode == "human":
            self.render()

        return self._get_observation(), reward, terminated, False, self._get_info()

    def render(self):
        """
        Affiche l'état actuel du plateau.
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
                        logger.info(
                            f"Training {'paused' if self.paused else 'resumed'}"
                        )

            self.screen.fill((0, 0, 0))  # BLACK
            self.board.draw(self.screen)

            # Afficher l'état de pause
            if self.paused:
                pause_text = self.font.render(
                    "PAUSED - Press SPACE to resume", True, (255, 255, 255)
                )
                text_rect = pause_text.get_rect(center=(WINDOW_WIDTH / 2, 20))
                self.screen.blit(pause_text, text_rect)

            pygame.display.flip()
            self.clock.tick(60)
        else:
            logger.info("Rendering current board state")
            print("\nPlateau actuel:")
            board_state = self._get_observation()["board"]
            print(board_state)
            print(f"Joueur actuel: {self.board.current_player_index + 1}")
            print(f"Statut des joueurs: {self._get_info()['player_status']}")

    def close(self):
        """
        Ferme l'environnement et libère les ressources.
        """
        if self.render_mode == "human":
            pygame.quit()
