import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Tuple, Dict, List, Optional
import random
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.src import (
    Board,
    BOARD_SIZE, COLORS, START_POSITIONS, NB_PLAYER_MODE, NAMES,
    create_piece, hex_to_pixel, is_within_board,
    Player,
    MinMaxPlayer
)

class DjambiEnv(gym.Env):
    """
    Environnement Djambi pour 3 joueurs avec reinforcement learning.
    Utilise le backend existant pour la logique du jeu.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialisation du plateau
        self.board = Board(current_player_index=0)
        self.board.rl = True  # Mode reinforcement learning
        
        # Définition des espaces d'observation et d'action
        self.observation_space = spaces.Dict({
            "board": spaces.Box(low=0, high=3, shape=(BOARD_SIZE*2-1, BOARD_SIZE*2-1), dtype=np.int8),
            "player_status": spaces.Box(low=0, high=1, shape=(3,), dtype=np.int8),
            "current_player": spaces.Discrete(3)
        })
        
        # Action : (piece_q, piece_r, move_q, move_r)
        self.action_space = spaces.MultiDiscrete([
            BOARD_SIZE*2-1,  # piece_q
            BOARD_SIZE*2-1,  # piece_r
            BOARD_SIZE*2-1,  # move_q
            BOARD_SIZE*2-1   # move_r
        ])
        
        # Initialisation
        self.reset()
    
    def reset(self, seed: Optional[int] = None) -> Tuple[Dict, Dict]:
        """
        Réinitialise l'environnement pour une nouvelle partie.
        """
        super().reset(seed=seed)
        
        # Réinitialiser le plateau
        self.board = Board(current_player_index=0)
        self.board.rl = True
        
        # Garder seulement 3 joueurs
        self.board.players = self.board.players[:3]
        self.board.pieces = [p for p in self.board.pieces if p.color in [p.color for p in self.board.players]]
        
        # Joueur actuel (commence aléatoirement)
        self.board.current_player_index = random.randint(0, 2)
        
        return self._get_observation(), self._get_info()
    
    def _get_observation(self) -> Dict:
        """
        Retourne l'observation actuelle.
        """
        # Créer une représentation du plateau
        board_state = np.zeros((BOARD_SIZE*2-1, BOARD_SIZE*2-1), dtype=np.int8)
        for piece in self.board.pieces:
            if not piece.is_dead:
                q, r = piece.q + BOARD_SIZE - 1, piece.r + BOARD_SIZE - 1
                # Utiliser l'index de la couleur dans la liste des couleurs
                color_name = NAMES[piece.color]
                color_index = list(NAMES.keys()).index(piece.color) + 1
                board_state[q, r] = color_index
        
        # État des joueurs
        player_status = np.ones(3, dtype=np.int8)
        for i, player in enumerate(self.board.players):
            if not any(not p.is_dead for p in player.pieces):
                player_status[i] = 0
        
        return {
            "board": board_state,
            "player_status": player_status,
            "current_player": self.board.current_player_index
        }
    
    def _get_info(self) -> Dict:
        """
        Retourne les informations supplémentaires.
        """
        return {
            "current_player": self.board.current_player_index,
            "player_status": [1 if any(not p.is_dead for p in player.pieces) else 0 for player in self.board.players]
        }
    
    def _is_valid_move(self, piece_q: int, piece_r: int, move_q: int, move_r: int) -> bool:
        """
        Vérifie si un mouvement est valide.
        """
        # Convertir les coordonnées
        piece_q = piece_q - (BOARD_SIZE - 1)
        piece_r = piece_r - (BOARD_SIZE - 1)
        move_q = move_q - (BOARD_SIZE - 1)
        move_r = move_r - (BOARD_SIZE - 1)
        
        # Vérifier si la pièce existe et appartient au joueur actuel
        piece = self.board.get_piece_at(piece_q, piece_r)
        if not piece or piece.color != self.board.players[self.board.current_player_index].color:
            return False
        
        # Vérifier si le mouvement est possible
        possible_moves = self.board.get_possible_moves(piece)
        return (move_q, move_r) in possible_moves
    
    def step(self, action: np.ndarray) -> Tuple[Dict, float, bool, bool, Dict]:
        """
        Exécute une action et retourne (observation, reward, terminated, truncated, info)
        """
        piece_q, piece_r, move_q, move_r = action
        
        # Vérifie si l'action est valide
        if not self._is_valid_move(piece_q, piece_r, move_q, move_r):
            return self._get_observation(), -0.1, False, False, self._get_info()
        
        # Convertir les coordonnées
        piece_q = piece_q - (BOARD_SIZE - 1)
        piece_r = piece_r - (BOARD_SIZE - 1)
        move_q = move_q - (BOARD_SIZE - 1)
        move_r = move_r - (BOARD_SIZE - 1)
        
        # Exécuter le mouvement
        piece = self.board.get_piece_at(piece_q, piece_r)
        success = self.board.move_piece(piece, move_q, move_r)
        
        if not success:
            return self._get_observation(), -0.1, False, False, self._get_info()
        
        # Vérifier les éliminations
        reward = 0.0
        terminated = False
        
        # Vérifier si un joueur a été éliminé
        for i, player in enumerate(self.board.players):
            if not any(not p.is_dead for p in player.pieces):
                if i == self.board.current_player_index:
                    reward = -1.0  # Le joueur actuel a été éliminé
                else:
                    reward = 1.0   # Le joueur actuel a éliminé un autre joueur
                terminated = True
                break
        
        # Passer au joueur suivant
        self.board.next_player()
        
        return self._get_observation(), reward, terminated, False, self._get_info()
    
    def render(self):
        """
        Affiche l'état actuel du plateau.
        """
        print("\nPlateau actuel:")
        board_state = self._get_observation()["board"]
        print(board_state)
        print(f"Joueur actuel: {self.board.current_player_index + 1}")
        print(f"Statut des joueurs: {self._get_info()['player_status']}") 