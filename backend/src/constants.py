import os
import argparse


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
ASSET_PATH = os.path.join(os.path.dirname(CURRENT_DIR), "assets/")
IS_PRODUCTION = os.environ.get("ENVIRONMENT") == "production"
HIGHLIGHT_WIDTH = 3  # Épaisseur du cercle de surbrillance
