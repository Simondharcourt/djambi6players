
import os

BOARD_SIZE = 7  # Nombre de cases par ligne/colonne sur le plateau
HEX_RADIUS = 35  # Rayon des hexagones
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 1000
PIECE_RADIUS = 25
SIZE_IMAGE = 50
VERTICAL_OFFSET = 100  # Ajustez cette valeur selon vos préférences
WHITE = (255, 255, 255)
CENTRAL_WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
DARKER_GREY = (100, 100, 100)
FONT_SIZE = 36
# Obtenir le chemin absolu du répertoire contenant board.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Remonter d'un niveau et accéder au dossier assets
ASSET_PATH = os.path.join(os.path.dirname(CURRENT_DIR), 'assets/')
IS_PRODUCTION = os.environ.get('ENVIRONMENT') == 'production'

COLORS = {
    'purple': (128, 0, 128),
    'blue': (0, 0, 255),
    'red': (255, 0, 0),
    'pink': (255, 105, 180),
    'yellow': (255, 255, 0),
    'green': (0, 255, 0),
}
ALL_COLORS = {**COLORS, 'white': (255, 255, 255), 'grey': (100, 100, 100)}
COLORS_REVERSE = {v: k for k, v in ALL_COLORS.items()}
NAMES = {
    (128, 0, 128): 'Violet',
    (0, 0, 255): 'Bleu',
    (255, 0, 0): 'Rouge',
    (255, 105, 180): 'Rose',
    (255, 255, 0): 'Jaune',
    (0, 255, 0): 'Vert',
    (100, 100, 100): 'Mort',
}
ADJACENT_DIRECTIONS = [
    (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1),  # Directions existantes
]
DIAG_DIRECTIONS = [
    (2, -1), (1, -2), (-1, -1), (-2, 1), (-1, 2), (1, 1)  # Nouvelles directions diagonales
]
ALL_DIRECTIONS = ADJACENT_DIRECTIONS + DIAG_DIRECTIONS
HIGHLIGHT_WIDTH = 3  # Épaisseur du cercle de surbrillance