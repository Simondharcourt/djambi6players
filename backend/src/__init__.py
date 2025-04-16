"""
Djambi backend package for game logic and AI.
"""

from .board import Board
from .constants import BOARD_SIZE, COLORS, START_POSITIONS, NB_PLAYER_MODE, NAMES
from .pieces import create_piece, hex_to_pixel, is_within_board
from .player import Player
from .minmax_player import MinMaxPlayer

__all__ = [
    'Board',
    'BOARD_SIZE', 'COLORS', 'START_POSITIONS', 'NB_PLAYER_MODE', 'NAMES',
    'create_piece', 'hex_to_pixel', 'is_within_board',
    'Player',
    'MinMaxPlayer',
]
