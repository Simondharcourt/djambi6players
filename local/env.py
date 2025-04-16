import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Tuple, Dict, List, Optional
import random

class DjambiEnv(gym.Env):
    """
    Environnement Djambi pour 3 joueurs avec reinforcement learning.
    Un joueur gagne s'il élimine un autre joueur (+1).
    Un joueur perd s'il est éliminé (-1).
    La partie se termine dès qu'un joueur est éliminé.
    """
    
    def __init__(self):
        super().__init__()
        
        # Dimensions du plateau
        self.board_size = 6
        self.num_players = 3
        
        # Définition des espaces d'observation et d'action
        # Observation : plateau (6x6) + état des joueurs
        self.observation_space = spaces.Dict({
            "board": spaces.Box(low=0, high=3, shape=(self.board_size, self.board_size), dtype=np.int8),
            "player_status": spaces.Box(low=0, high=1, shape=(self.num_players,), dtype=np.int8),
            "current_player": spaces.Discrete(self.num_players)
        })
        
        # Action : (piece_x, piece_y, move_x, move_y)
        self.action_space = spaces.MultiDiscrete([
            self.board_size,  # piece_x
            self.board_size,  # piece_y
            self.board_size,  # move_x
            self.board_size   # move_y
        ])
        
        # Initialisation
        self.reset()
    
    def reset(self, seed: Optional[int] = None) -> Tuple[Dict, Dict]:
        """
        Réinitialise l'environnement pour une nouvelle partie.
        """
        super().reset(seed=seed)
        
        # Initialisation du plateau
        self.board = np.zeros((self.board_size, self.board_size), dtype=np.int8)
        
        # Placement initial des pièces pour chaque joueur
        # Joueur 1 (1) : coins supérieurs
        self.board[0, 0] = 1
        self.board[0, self.board_size-1] = 1
        
        # Joueur 2 (2) : coins inférieurs
        self.board[self.board_size-1, 0] = 2
        self.board[self.board_size-1, self.board_size-1] = 2
        
        # Joueur 3 (3) : milieu
        self.board[self.board_size//2, 0] = 3
        self.board[self.board_size//2, self.board_size-1] = 3
        
        # État des joueurs (1 = vivant, 0 = éliminé)
        self.player_status = np.ones(self.num_players, dtype=np.int8)
        
        # Joueur actuel (commence aléatoirement)
        self.current_player = random.randint(0, self.num_players-1)
        
        return self._get_observation(), self._get_info()
    
    def _get_observation(self) -> Dict:
        """
        Retourne l'observation actuelle.
        """
        return {
            "board": self.board.copy(),
            "player_status": self.player_status.copy(),
            "current_player": self.current_player
        }
    
    def _get_info(self) -> Dict:
        """
        Retourne les informations supplémentaires.
        """
        return {
            "current_player": self.current_player,
            "player_status": self.player_status.copy()
        }
    
    def _is_valid_move(self, piece_pos: Tuple[int, int], move_pos: Tuple[int, int]) -> bool:
        """
        Vérifie si un mouvement est valide.
        """
        piece_x, piece_y = piece_pos
        move_x, move_y = move_pos
        
        # Vérifie les limites du plateau
        if not (0 <= move_x < self.board_size and 0 <= move_y < self.board_size):
            return False
        
        # Vérifie si la case de destination est vide
        if self.board[move_x, move_y] != 0:
            return False
        
        # Vérifie si le mouvement est en diagonale
        dx = abs(move_x - piece_x)
        dy = abs(move_y - piece_y)
        if dx != dy or dx == 0:
            return False
        
        return True
    
    def _check_elimination(self) -> Optional[int]:
        """
        Vérifie si un joueur a été éliminé.
        Retourne l'index du joueur éliminé ou None.
        """
        for player in range(self.num_players):
            if self.player_status[player] == 1:  # Si le joueur est encore en vie
                player_pieces = np.where(self.board == player + 1)
                if len(player_pieces[0]) == 0:  # Plus de pièces
                    return player
        return None
    
    def step(self, action: np.ndarray) -> Tuple[Dict, float, bool, bool, Dict]:
        """
        Exécute une action et retourne (observation, reward, terminated, truncated, info)
        """
        piece_x, piece_y, move_x, move_y = action
        
        # Vérifie si l'action est valide
        if not self._is_valid_move((piece_x, piece_y), (move_x, move_y)):
            return self._get_observation(), -0.1, False, False, self._get_info()
        
        # Exécute le mouvement
        player = self.board[piece_x, piece_y]
        self.board[piece_x, piece_y] = 0
        self.board[move_x, move_y] = player
        
        # Vérifie les éliminations
        eliminated_player = self._check_elimination()
        
        # Calcule la récompense
        reward = 0.0
        terminated = False
        
        if eliminated_player is not None:
            self.player_status[eliminated_player] = 0
            if eliminated_player == self.current_player:
                reward = -1.0  # Le joueur actuel a été éliminé
            else:
                reward = 1.0   # Le joueur actuel a éliminé un autre joueur
            terminated = True
        
        # Passe au joueur suivant
        self.current_player = (self.current_player + 1) % self.num_players
        while self.player_status[self.current_player] == 0:
            self.current_player = (self.current_player + 1) % self.num_players
        
        return self._get_observation(), reward, terminated, False, self._get_info()
    
    def render(self):
        """
        Affiche l'état actuel du plateau.
        """
        print("\nPlateau actuel:")
        print(self.board)
        print(f"Joueur actuel: {self.current_player + 1}")
        print(f"Statut des joueurs: {self.player_status}")