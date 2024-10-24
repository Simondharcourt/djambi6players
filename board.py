import pygame
import sys
import math
import logging
import random
import cairosvg
from io import BytesIO
# Paramètres du jeu
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
COLORS = {
    'purple': (128, 0, 128),
    'blue': (0, 0, 255),
    'red': (255, 0, 0),
    'pink': (255, 105, 180),
    'yellow': (255, 255, 0),
    'green': (0, 255, 0),
}
NAMES = {
    (128, 0, 128): 'Violet',
    (0, 0, 255): 'Bleu',
    (255, 0, 0): 'Rouge',
    (255, 105, 180): 'Rose',
    (255, 255, 0): 'Jaune',
    (0, 255, 0): 'Vert',
    DARKER_GREY: 'Mort',
}
ORDER_PLAYERS = list(COLORS)
ADJACENT_DIRECTIONS = [
    (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1),  # Directions existantes
]
DIAG_DIRECTIONS = [
    (2, -1), (1, -2), (-1, -1), (-2, 1), (-1, 2), (1, 1)  # Nouvelles directions diagonales
]
ALL_DIRECTIONS = ADJACENT_DIRECTIONS + DIAG_DIRECTIONS

HIGHLIGHT_WIDTH = 3  # Épaisseur du cercle de surbrillance

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class Piece:
    necromobile_image = None

    def __init__(self, q, r, color, piece_class, svg_path):
        self.q = q  # Coordonnée hexagonale q
        self.r = r  # Coordonnée hexagonale r
        self.color = color  # Couleur de la pièce
        self.is_dead = False  # Indique si la pièce est morte ou non
        self.piece_class = piece_class  # Classe de la pièce (e.g., 'assassin', 'chief')
        self.svg_path = svg_path  # Ajout de cet attribut
        self.class_image = None  # Ne pas stocker l'image ici
        self.name = NAMES[color]
        self.on_central_cell = False  # Nouvel attribut pour suivre si le chef est sur la case centrale

    def die(self):
        """Marque la pièce comme morte et change sa couleur en grise."""
        self.is_dead = True
        self.color = DARKER_GREY  # Couleur grise pour les pièces mortes
        logging.info(f"Pièce en {self.q}, {self.r} est morte")

    @staticmethod
    def load_svg_as_surface(svg_path, target_size=(SIZE_IMAGE, SIZE_IMAGE)):
        """Charge le fichier SVG et le convertit directement à la taille désirée."""
        # Lire le fichier SVG et convertir en PNG avec CairoSVG à la taille souhaitée
        with open(svg_path, 'rb') as f:
            svg_data = f.read()

        # Convertir le SVG en PNG avec la taille exacte demandée
        png_data = cairosvg.svg2png(bytestring=svg_data, output_width=target_size[0], output_height=target_size[1])

        # Charger les données PNG dans Pygame directement sans redimensionner
        image = pygame.image.load(BytesIO(png_data))

        return image  # Retourner directement l'image sans redimensionnement

    def load_image(self):
        # Charger l'image seulement quand nécessaire
        self.class_image = self.load_svg_as_surface(self.svg_path)

    @classmethod
    def load_necromobile_image(cls):
        if cls.necromobile_image is None:
            cls.necromobile_image = pygame.transform.scale(
                cls.load_svg_as_surface('assets/necromobile.svg'),
                (SIZE_IMAGE // 2, SIZE_IMAGE // 2)
            )

    def draw(self, screen, is_current_player):
        x, y = hex_to_pixel(self.q, self.r)
        
        if not self.is_dead:
            pygame.draw.circle(screen, self.color, (x, y), PIECE_RADIUS)
            class_image_rect = self.class_image.get_rect(center=(x, y))
            screen.blit(self.class_image, class_image_rect)
            
            # Dessiner le cercle de surbrillance si c'est le tour du joueur
            if is_current_player:
                pygame.draw.circle(screen, GREY, (x, y), PIECE_RADIUS + 2, HIGHLIGHT_WIDTH)
        else:
            pygame.draw.circle(screen, GREY, (x, y), PIECE_RADIUS)
            
            if Piece.necromobile_image is None:
                Piece.load_necromobile_image()
            necromobile_rect = Piece.necromobile_image.get_rect(center=(x, y))
            screen.blit(Piece.necromobile_image, necromobile_rect)

    def all_possible_moves(self, board):
        """Retourne une liste de toutes les cases possibles où la pièce peut aller."""
        if self.is_dead:
            return [] # ne peut se déplacer.
        
        possible_moves = []
        # Pour chaque direction, explorer les cases jusqu'à rencontrer un obstacle ou le bord du plateau
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            while True:
                new_q = self.q + dq * step
                new_r = self.r + dr * step

                # Si le mouvement est en dehors du plateau ou bloque par une autre pièce, arrêter
                if not is_within_board(new_q, new_r) or board.is_occupied(new_q, new_r):
                    break

                # Ajouter les coordonnées du mouvement possible
                if not (new_q == 0 and new_r == 0 and not isinstance(self, ChiefPiece)):
                    possible_moves.append((new_q, new_r))
                step += 1  # Continuer dans la même direction

        return possible_moves

    def move(self, new_q, new_r, board):
        # Effectuer le déplacement
        self.q = new_q
        self.r = new_r

    def is_surrounded(self, board, visited=None):
        if visited is None:
            visited = set()

        if (self.q, self.r) in visited:
            return True
        visited.add((self.q, self.r))

        for dq, dr in ALL_DIRECTIONS:
            new_q = self.q + dq
            new_r = self.r + dr

            if not is_within_board(new_q, new_r):
                continue  # Case hors du plateau, considérée comme non-encerclement
            piece_at_position = board.get_piece_at(new_q, new_r)

            if piece_at_position is None:
                return False  # Il y a une case vide, donc pas encerclé

            if piece_at_position.is_dead:
                continue  # Continue d'examiner les autres directions

            # Pour une pièce alliée, vérifie si elle est encerclée
            if piece_at_position.color == self.color:
                if not piece_at_position.is_surrounded(board, visited):
                    return False  # Trouvé une pièce alliée qui n'est pas encerclée

        return True  # Toutes les directions sont bloquées ou conduisent à des pièces mortes/alliées encerclées

        

class MilitantPiece(Piece):
    def __init__(self, q, r, color, piece_class, svg_path):
        super().__init__(q, r, color, piece_class, svg_path)

    def all_possible_moves(self, board):
        if self.is_dead:
            return [] # ne peut se déplacer.
        possible_moves = []
        directions = ADJACENT_DIRECTIONS + DIAG_DIRECTIONS
        max_steps = {
            'adjacent': 2,
            'diagonal': 1
        }

        for dq, dr in directions:
            is_diagonal = (dq, dr) in DIAG_DIRECTIONS
            for step in range(1, max_steps['diagonal' if is_diagonal else 'adjacent'] + 1):
                new_q = self.q + dq * step
                new_r = self.r + dr * step
                
                if not is_within_board(new_q, new_r):
                    break
                
                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if piece_at_position.color != self.color and not piece_at_position.is_dead:
                        possible_moves.append((new_q, new_r))
                    break
                elif not (new_q == 0 and new_r == 0) or (board.is_occupied(0, 0) and not isinstance(piece_at_position, ChiefPiece) and not piece_at_position.is_dead): # possibilité d'enlever cette dernière condition selon les règles.
                    possible_moves.append((new_q, new_r))
        return possible_moves
                
    
    def move(self, new_q, new_r, board):
        original_q, original_r = self.q, self.r
        target_piece = board.get_piece_at(new_q, new_r)

        # Supprimer l'appel à animate_move ici
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and target_piece.color != self.color and not target_piece.is_dead:
            # Tuer la pièce ennemie
            if isinstance(target_piece, ChiefPiece):
                board.chief_killed(target_piece, board.get_chief_of_color(self.color))
            target_piece.die()
            unoccupied_cells = board.get_unoccupied_cells()
            new_position = random.choice(unoccupied_cells)
            # Déplacer la pièce rencontrée vers la nouvelle position
            target_piece.q, target_piece.r = new_position
            # Déplacer la pièce tuée à la position d'origine de l'assassin
            logging.info(f"Le militant a tué la pièce en {new_q}, {new_r} et l'a déplacée en {target_piece.q,}, {target_piece.r}")


        # Déplacer le militant
        self.q, self.r = new_q, new_r
        logging.info(f"Le militant s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")

class AssassinPiece(Piece):
    def __init__(self, q, r, color, piece_class, svg_path):
        super().__init__(q, r, color, piece_class, svg_path)

    def all_possible_moves(self, board):
        """Retourne tous les mouvements possibles pour l'assassin, y compris les cases occupées par des ennemis,
        et en traversant les pièces alliées."""
        if self.is_dead:
            return [] # ne peut se dplacer.
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            while True:
                new_q = self.q + dq * step
                new_r = self.r + dr * step

                if not is_within_board(new_q, new_r):
                    break

                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if piece_at_position.color != self.color:
                        if not piece_at_position.is_dead:
                            possible_moves.append((new_q, new_r))  # L'assassin peut se déplacer sur une pièce ennemie
                        break  # Arrêter après avoir rencontré une pièce ennemie
                    # Si c'est une pièce alliée, on continue sans l'ajouter aux mouvements possibles
                elif not (new_q == 0 and new_r == 0) or (board.is_occupied(0, 0) and not isinstance(piece_at_position, ChiefPiece) and not piece_at_position.is_dead):
                    possible_moves.append((new_q, new_r))
                step += 1
        return possible_moves

    def move(self, new_q, new_r, board):
        """Déplace l'assassin et tue la pièce ennemie si présente."""
        original_q, original_r = self.q, self.r
        target_piece = board.get_piece_at(new_q, new_r)

        # Ajouter l'animation du mouvement
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and target_piece.color != self.color and not target_piece.is_dead:
            if isinstance(target_piece, ChiefPiece):
                board.chief_killed(target_piece, board.get_chief_of_color(self.color))
            target_piece.die()
            target_piece.q, target_piece.r = original_q, original_r
            logging.info(f"L'assassin a tué la pièce en {new_q}, {new_r} et l'a déplacée en {original_q}, {original_r}")


        # Déplacer l'assassin
        self.q, self.r = new_q, new_r
        logging.info(f"L'assassin s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")

class ChiefPiece(Piece):
    def __init__(self, q, r, color, piece_class, svg_path):
        super().__init__(q, r, color, piece_class, svg_path)

    def all_possible_moves(self, board):
        if self.is_dead:
            return []  # ne peut se déplacer. # Le chef ne bouge plus s'il est sur la case centrale
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            while True:
                new_q = self.q + dq * step
                new_r = self.r + dr * step

                if not is_within_board(new_q, new_r):
                    break

                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if piece_at_position.color != self.color:
                        if not piece_at_position.is_dead:
                            possible_moves.append((new_q, new_r))
                    break
                else:
                    possible_moves.append((new_q, new_r))
                step += 1
        return possible_moves

    def move(self, new_q, new_r, board):
        original_q, original_r = self.q, self.r
        target_piece = board.get_piece_at(new_q, new_r)

        # Ajouter l'animation du mouvement
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and target_piece.color != self.color and not target_piece.is_dead:
            if isinstance(target_piece, ChiefPiece):
                board.chief_killed(target_piece, board.get_chief_of_color(self.color))
            target_piece.die()
            unoccupied_cells = board.get_unoccupied_cells()
            new_position = random.choice(unoccupied_cells)
            target_piece.q, target_piece.r = new_position
            logging.info(f"Le chef a tué la pièce en {new_q}, {new_r} et l'a déplacée en {target_piece.q,}, {target_piece.r}")

        # Déplacer le chef
        self.q, self.r = new_q, new_r
        logging.info(f"Le chef s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")

        # Vérifier si le chef est sur la case centrale
        if not self.on_central_cell and self.q == 0 and self.r == 0:
            self.enter_central_cell(board)
        elif self.on_central_cell and (self.q != 0 or self.r != 0):
            self.leave_central_cell(board)

    def enter_central_cell(self, board):
        self.on_central_cell = True
        logging.info(f"Le chef {self.name} est arrivé sur la case centrale!")
        new_order = []
        for player_index in range(board.current_player_index + 1, len(board.players) + board.current_player_index):
            new_order.append(board.players[player_index%len(board.players)])
            new_order.append(board.get_player_of_color(self.color))
        board.players = new_order
        board.current_player_index = -1

    def leave_central_cell(self, board):
        self.on_central_cell = False
        logging.info(f"Le chef {self.name} n'est plus sur la case centrale.")
        new_order = []
        for player_index in range(board.current_player_index + 1, len(board.players) + board.current_player_index):
            player = board.players[player_index%len(board.players)]
            if player and player.color != self.color:
                new_order.append(player)
        new_order.append(board.get_player_of_color(self.color))
        board.players = new_order
        board.current_player_index = -1

    def is_surrounded(self, board, visited=None):
        if self.on_central_cell:
            return False  # Le chef n'est jamais considéré comme encerclé s'il est sur la case centrale
        return super().is_surrounded(board, visited)

class DiplomatPiece(Piece):
    """Ajoute un comportement spécifique pour les diplomates."""
    def __init__(self, q, r, color, piece_class, svg_path):
        super().__init__(q, r, color, piece_class, svg_path)

    def all_possible_moves(self, board):
        if self.is_dead:
            return [] # ne peut se déplacer.
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            while True:
                new_q = self.q + dq * step
                new_r = self.r + dr * step

                if not is_within_board(new_q, new_r):
                    break

                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if not piece_at_position.is_dead: # toutes les pièces sont accessibles
                        possible_moves.append((new_q, new_r))  # L'assassin peut se déplacer sur une pièce ennemie
                    break  # Arrêter dans cette direction aprs avoir rencontré une pièce
                elif not (new_q == 0 and new_r == 0) or (board.is_occupied(0, 0) and not isinstance(piece_at_position, ChiefPiece) and not piece_at_position.is_dead):
                    possible_moves.append((new_q, new_r))
                step += 1
        return possible_moves

    def move(self, new_q, new_r, board):
        original_q, original_r = self.q, self.r
        target_piece = board.get_piece_at(new_q, new_r)

        # Ajouter l'animation du mouvement
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and not target_piece.is_dead:
            # Trouver une case libre aléatoire
            unoccupied_cells = board.get_unoccupied_cells()
            new_position = random.choice(unoccupied_cells)
            # Déplacer la pièce rencontrée vers la nouvelle position
            target_piece.q, target_piece.r = new_position
            logging.info(f"Le diplomate {self.name} a déplacé le {target_piece.piece_class} {target_piece.name} de {new_q}, {new_r} vers {new_position}")
            
            if isinstance(target_piece, ChiefPiece) and target_piece.on_central_cell:
                target_piece.leave_central_cell(board)
                
        # Déplacer le diplomate
        self.q, self.r = new_q, new_r
        logging.info(f"Le diplomate s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")

class NecromobilePiece(Piece):
    """Ajoute un comportement spécifique pour les necromobiles."""
    
    def __init__(self, q, r, color, piece_class, svg_path):
        super().__init__(q, r, color, piece_class, svg_path)

    def all_possible_moves(self, board):
        if self.is_dead:
            return [] # ne peut se dplacer.
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            while True:
                new_q = self.q + dq * step
                new_r = self.r + dr * step
                if not is_within_board(new_q, new_r):
                    break
                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if piece_at_position.is_dead: # toutes les pièces sont accessibles
                        possible_moves.append((new_q, new_r))  # L'assassin peut se déplacer sur une pièce ennemie
                    break  # Arrêter dans cette direction après avoir rencontré une pièce
                elif not (new_q == 0 and new_r == 0) or (board.is_occupied(0, 0) and piece_at_position.is_dead):
                    possible_moves.append((new_q, new_r))
                step += 1
        return possible_moves
    

    def move(self, new_q, new_r, board):
        original_q, original_r = self.q, self.r
        target_piece = board.get_piece_at(new_q, new_r)

        # Ajouter l'animation du mouvement
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and target_piece.is_dead:
            # Trouver une case libre aléatoire
            unoccupied_cells = board.get_unoccupied_cells()
            new_position = random.choice(unoccupied_cells)
            # Déplacer la pièce rencontrée vers la nouvelle position
            target_piece.q, target_piece.r = new_position
            logging.info(f"Le necromobile a déplacé la pièce de {new_q}, {new_r} vers {new_position}")
        # Déplacer le necromobile
        self.q, self.r = new_q, new_r
        logging.info(f"Le necromobile s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
    
class ReporterPiece(Piece):
    def __init__(self, q, r, color, piece_class, svg_path):
        super().__init__(q, r, color, piece_class, svg_path)

    def all_possible_moves(self, board):
        """Le reporter peut se déplacer normalement."""
        return super().all_possible_moves(board)

    def move(self, new_q, new_r, board):
        """Déplace le reporter et tue les pièces adverses autour de sa nouvelle position."""
        # Effectuer le déplacement
        original_q, original_r = self.q, self.r
        self.q = new_q
        self.r = new_r
        
        # Ajouter l'animation du mouvement
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        # Tuer les ennemis adjacents après le déplacement
        for dq, dr in ADJACENT_DIRECTIONS:
            adjacent_q = self.q + dq
            adjacent_r = self.r + dr
            piece = board.get_piece_at(adjacent_q, adjacent_r)
            if piece and piece.color != self.color and not piece.is_dead:
                logging.info(f"Le reporter tue la pièce ennemie en {adjacent_q}, {adjacent_r}")
                if isinstance(piece, ChiefPiece):
                    board.chief_killed(piece, board.get_chief_of_color(self.color))
                piece.die()

def create_piece(q, r, color, piece_class, svg_path):
    """Crée une pièce de la classe appropriée."""
    class_mapping = {
        'militant': MilitantPiece,
        'assassin': AssassinPiece,
        'chief': ChiefPiece,
        'diplomat': DiplomatPiece,
        'necromobile': NecromobilePiece,
        'reporter': ReporterPiece,
    }
    
    piece_class_constructor = class_mapping.get(piece_class, Piece)
    piece = piece_class_constructor(q, r, color, piece_class, svg_path)
    piece.load_image()  # Charger l'image immédiatement après la création
    return piece


class Player:
    def __init__(self, color, pieces):
        self.color = color
        self.pieces = pieces
        self.name = NAMES[color]

    def play_turn(self, board):
        """Joue un tour : déplace une de ses pièces aléatoirement parmi les mouvements possibles."""
        all_moves = []

        # Récupérer tous les mouvements possibles pour toutes les pièces du joueur
        for piece in self.pieces:
            moves = piece.all_possible_moves(board)
            if moves:
                # Associer chaque mouvement possible avec la pièce correspondante
                all_moves.append((piece, moves))

        # Si aucun mouvement n'est possible, passer le tour
        if not all_moves:
            logging.debug(f"Joueur {self.name}: aucun mouvement possible, tour passé.")
            return

        # Choisir une pièce et un mouvement aléatoire
        piece, moves = random.choice(all_moves)  # Choisir une pièce avec des mouvements possibles
        move = random.choice(moves)  # Choisir un mouvement aléatoire pour cette pièce

        # Appliquer le mouvement à la pièce
        new_q, new_r = move
        logging.debug(f"Joueur {self.name} déplace la pièce de {piece.q},{piece.r} vers {new_q},{new_r}")
        piece.move(new_q, new_r, board)
        
    def change_color(self, new_color):
        self.color = new_color
        for piece in self.pieces:
            piece.color = new_color

    def remove_piece(self, piece):
        self.pieces.remove(piece)

    def add_piece(self, piece):
        self.pieces.append(piece)
        piece.color = self.color


def is_within_board(q, r):
    """Vérifie si les coordonnées q, r sont dans les limites du plateau."""
    s = -q - r  # Coordonnée s dans un système hexagonal
    return abs(q) < BOARD_SIZE and abs(r) < BOARD_SIZE and abs(s) < BOARD_SIZE


def hex_to_pixel(q, r):
    x = HEX_RADIUS * 3/2 * q
    y = HEX_RADIUS * math.sqrt(3) * (r + q/2)
    
    # Décalage vertical pour centrer le plateau plus haut
    
    pixel_coords = (
        int(x + WINDOW_WIDTH // 2),
        int(y + (WINDOW_HEIGHT // 2) - VERTICAL_OFFSET)
    )
    return pixel_coords

class Board:
    def __init__(self, current_player_index):
        self.hexagons = []
        self.pieces = []
        self.current_player_index = current_player_index
        logging.info("Initialisation du plateau")
        
        # Initialisation des hexagones du plateau
        for q in range(-BOARD_SIZE + 1, BOARD_SIZE):
            for r in range(-BOARD_SIZE + 1, BOARD_SIZE):
                if -q - r in range(-BOARD_SIZE + 1, BOARD_SIZE):
                    self.hexagons.append((q, r))

        # Ajouter des pièces aux positions de départ
        self.initialize_pieces()
        self.history = []
        self.future = []
        self.piece_to_place = None  # Pièce tuée à placer manuellement
        self.available_cells = []  # Cellules disponibles pour placer la pièce tuée
        self.board_surface = self.create_board_surface()
        self.hex_pixel_positions = self.calculate_hex_pixel_positions()

    def create_board_surface(self):
        board_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        board_surface.fill(BLACK)
        for hex_coord in self.hexagons:
            q, r = hex_coord
            x, y = hex_to_pixel(q, r)
            pygame.draw.polygon(board_surface, WHITE, self.hex_corners(x, y), 1)
            if q == 0 and r == 0:
                pygame.draw.polygon(board_surface, CENTRAL_WHITE, self.hex_corners(x, y), 0)
            else:
                pygame.draw.polygon(board_surface, WHITE, self.hex_corners(x, y), 1)
        return board_surface

    def calculate_hex_pixel_positions(self):
        positions = {}
        for q, r in self.hexagons:
            x, y = hex_to_pixel(q, r)
            positions[(q, r)] = (x, y)
        return positions


    def initialize_pieces(self):
        # Position de départ des pièces (exemple arbitraire)
        logging.info("Initialisation des pièces")
        start_positions = [
            # Pièces violettes (en bas à gauche)
            (-5, -1, 'purple', 'assassin'), (-4, -2, 'purple', 'militant'), (-6, 0, 'purple', 'chief'),
            (-4, -1, 'purple', 'militant'), (-5, 0, 'purple', 'diplomat'), (-4, 0, 'purple', 'necromobile'), 
            (-5, 1, 'purple', 'militant'), (-6, 1, 'purple', 'reporter'), (-6, 2, 'purple', 'militant'),
            
            # Pièces bleues (en haut)
            (0, -6, 'blue', 'chief'), (1, -6, 'blue', 'reporter'), (2, -6, 'blue', 'militant'),
            (0, -5, 'blue', 'diplomat'), (-1, -4, 'blue', 'militant'), (-2, -4, 'blue', 'militant'),
            (0, -4, 'blue', 'necromobile'), (1, -5, 'blue', 'militant'), (-1, -5, 'blue', 'assassin'),
            
            # # Pièces rouges (en bas à droite)
            (6, -4, 'red', 'militant'), (6, -5, 'red', 'assassin'), (6, -6, 'red', 'chief'),
            (5, -6, 'red', 'reporter'), (4, -6, 'red', 'militant'), (5, -5, 'red', 'diplomat'),
            (4, -4, 'red', 'necromobile'), (4, -5, 'red', 'militant'), (5, -4, 'red', 'militant'),

            # Pièces roses (en haut à droite)
            (6, -2, 'pink', 'militant'), (5, -1, 'pink', 'militant'), (6, -1, 'pink', 'assassin'),(4, 2, 'pink', 'militant'),
            (5, 0, 'pink', 'diplomat'), (4, 0, 'pink', 'necromobile'), (6, 0, 'pink', 'chief'),
            (5, 1, 'pink', 'reporter'), (4, 1, 'pink', 'militant'),

            # Pièces jaunes (en bas)
            (0, 5, 'yellow', 'diplomat'), (-1, 5, 'yellow', 'militant'), (-2, 6, 'yellow', 'militant'),
            (-1, 6, 'yellow', 'assassin'), (1, 5, 'yellow', 'reporter'), (0, 6, 'yellow', 'chief'),
            (0, 4, 'yellow', 'necromobile'), (2, 4, 'yellow', 'militant'), (1, 4, 'yellow', 'militant'),
            
            # Pièces vertes (en haut à gauche)
            (-5, 6, 'green', 'assassin'), (-4, 6, 'green', 'militant'), (-6, 6, 'green', 'chief'),
            (-6, 5, 'green', 'reporter'), (-6, 4, 'green', 'militant'), (-5, 5, 'green', 'diplomat'),
            (-4, 5, 'green', 'militant'), (-5, 4, 'green', 'militant'), (-4, 4, 'green', 'necromobile'),
        ]
        
        class_svg_paths = {
            'assassin': 'assets/assassin.svg',
            'chief': 'assets/chief.svg',
            'diplomat': 'assets/diplomat.svg',
            'militant': 'assets/militant.svg',
            'necromobile': 'assets/necromobile.svg',
            'reporter': 'assets/reporter.svg'
        }
        
        self.players = []
        for color in COLORS.keys():
            pieces = [create_piece(q, r, COLORS[color], cl, class_svg_paths[cl]) for q, r, c, cl in start_positions if c == color]
            self.players.append(Player(COLORS[color], pieces))
            self.pieces.extend(pieces)

    def save_state(self, current_player_index):
        state = {
            'pieces': [(p.q, p.r, p.color, p.piece_class, p.svg_path, p.is_dead) for p in self.pieces],
            'players': [{'color': p.color, 'pieces': [piece.piece_class for piece in p.pieces]} for p in self.players if p is not None],
            'current_player_index': current_player_index
        }
        self.history.append(state)
        self.future.clear()

    def load_state(self, state):
        self.pieces = [create_piece(q, r, color, piece_class, svg_path) for q, r, color, piece_class, svg_path, is_dead in state['pieces']]
        for piece, (_, _, _, _, _, is_dead) in zip(self.pieces, state['pieces']):
            piece.is_dead = is_dead
        self.players = []
        for player_data in state['players']:
            player_pieces = [piece for piece in self.pieces if piece.color == player_data['color']]
            self.players.append(Player(player_data['color'], player_pieces))
        return state['current_player_index']

    def undo(self):
        if len(self.history) > 1:  # Assurez-vous qu'il reste au moins un état après l'annulation
            self.future.append(self.history.pop())
            previous_state = self.history[-1]
            return self.load_state(previous_state)
        return None

    def redo(self):
        if self.future:
            next_state = self.future.pop()
            self.history.append(next_state)
            return self.load_state(next_state)
        return None

    def get_piece_at(self, q, r):
        """Retourne la pièce à la position (q, r) si elle existe, sinon None."""
        for piece in self.pieces:
            if piece.q == q and piece.r == r:
                return piece
        return None

    def is_occupied(self, q, r):
        """Vérifie si une case est déjà occupée par une pièce."""
        for piece in self.pieces:
            if piece.q == q and piece.r == r:
                return True
        return False

    def get_unoccupied_cells(self):
        """Renvoie toutes les cases inoccupées qui ne sont pas la case centrale."""
        unoccupied_cells = []
        for q in range(-BOARD_SIZE + 1, BOARD_SIZE):
            for r in range(-BOARD_SIZE + 1, BOARD_SIZE):
                # Vérifier si la case est sur le plateau
                if is_within_board(q, r):
                    # Exclure la case centrale et les cases occupées
                    if (q != 0 or r != 0) and not self.is_occupied(q, r):
                        unoccupied_cells.append((q, r))
        return unoccupied_cells

    def chief_on_central_cell(self):
        for player in self.players:
            for piece in player.pieces:
                if isinstance(piece, ChiefPiece) and piece.q == 0 and piece.r == 0 and piece.on_central_cell:
                    return player
        return None

    def get_chief_of_color(self, color):
        for piece in self.pieces:
            if isinstance(piece, ChiefPiece) and piece.color == color:
                return piece
        return None

    def chief_killed(self, killed_chief, killer_chief):
        killed_player = next((player for player in self.players if player.color == killed_chief.color), None)
        killer_player = next((player for player in self.players if player.color == killer_chief.color), None) if killer_chief else None

        if killed_player is None:
            logging.error(f"Erreur : Impossible de trouver le joueur tué. Killed chief color: {killed_chief.color}")
            return

        # Changer la couleur de toutes les pièces du joueur tué
        for piece in killed_player.pieces:
            if killer_player:
                piece.color = killer_player.color
                piece.name = NAMES[killer_player.color]
                piece.load_image()
            else:
                piece.die()  # Si pas de tueur spécifique, les pièces meurent simplement

        # Transférer toutes les pièces au joueur qui a tué le chef, s'il y en a un
        if killer_player:
            killer_player.pieces.extend(killed_player.pieces)

        # Supprimer toutes les occurrences du joueur tué
        while killed_player in self.players:
            killed_player_index = self.players.index(killed_player)
            animate_player_elimination(pygame.display.get_surface(), self.players, killed_player_index, self)
            self.players.pop(killed_player_index)

        logging.info(f"Le chef {killed_chief.name} a été tué{'.' if not killer_chief else f' par le chef {killer_chief.name}.'} Toutes ses pièces sont maintenant {'mortes' if not killer_chief else f'contrôlées par {killer_chief.name}'}.")

        # Mettre à jour l'index du joueur courant si nécessaire
        if self.current_player_index >= len(self.players):
            self.current_player_index = 0


    def draw(self, screen, selected_piece=None, piece_to_place=None):
        # Utiliser les positions pré-calculées
        for hex_coord in self.hexagons:
            x, y = self.hex_pixel_positions[hex_coord]
            q, r = hex_coord
            pygame.draw.polygon(screen, WHITE, self.hex_corners(x, y), 1)

            # Si la case est la case centrale, la dessiner en blanc
            if q == 0 and r == 0:
                pygame.draw.polygon(screen, CENTRAL_WHITE, self.hex_corners(x, y), 0)  # Remplissage complet
            else:
                pygame.draw.polygon(screen, WHITE, self.hex_corners(x, y), 1)  # Seulement le contour

        # Dessiner les pièces
        current_player_color = self.players[self.current_player_index].color
        for piece in self.pieces:
            is_current_player = (piece.color == current_player_color and selected_piece is None and piece_to_place is None)
            piece.draw(screen, is_current_player)


    def hex_corners(self, x, y):
        """Retourne les coins de l'hexagone en fonction de sa position pixel."""
        corners = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.radians(angle_deg)
            corner_x = x + HEX_RADIUS * math.cos(angle_rad)
            corner_y = y + HEX_RADIUS * math.sin(angle_rad)
            corners.append((corner_x, corner_y))
        return corners

    def select_piece(self, q, r):
        """Sélectionne une pièce à la position (q, r)."""
        piece = self.get_piece_at(q, r)
        if piece and piece.color == self.players[self.current_player_index].color:
            return piece
        return None

    def get_possible_moves(self, piece):
        """Retourne les mouvements possibles pour une pièce."""
        return piece.all_possible_moves(self)

    def next_player(self):
        """Passe au joueur suivant et effectue les vérifications nécessaires."""
        self.check_surrounded_chiefs()
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.save_state(self.current_player_index)

    def move_piece(self, piece, new_q, new_r):
        """Déplace une pièce vers une nouvelle position."""
        if (new_q, new_r) in self.get_possible_moves(piece):
            target_piece = self.get_piece_at(new_q, new_r)
            original_q, original_r = piece.q, piece.r
            logging.info(f"Le {piece.piece_class} {piece.name} se déplace de {piece.q},{piece.r} à {new_q},{new_r}")
            if target_piece and isinstance(piece, (MilitantPiece, ChiefPiece, DiplomatPiece, NecromobilePiece)):
                # Tuer la pièce ennemie
                if isinstance(piece, (MilitantPiece, ChiefPiece)):
                    if isinstance(target_piece, ChiefPiece):
                        self.chief_killed(target_piece, self.get_chief_of_color(piece.color))
                        logging.info(f"Le chef {target_piece.name} a été tué par le {piece.piece_class} {piece.name}.")
                            
                    if target_piece.on_central_cell and isinstance(piece, ChiefPiece):
                        piece.enter_central_cell(self)
                        logging.info(f"Le chef {piece.name} entre sur la case centrale.")
                        
                    target_piece.die()
                    logging.info(f"Le {target_piece.piece_class} {target_piece.name} a té tué par le {piece.piece_class} {piece.name}.") 
                        
                if isinstance(piece, DiplomatPiece) and isinstance(target_piece, ChiefPiece) and target_piece.on_central_cell and not target_piece.is_dead:
                    logging.info(f"Le diplomate {piece.name} fait quitter le chef {target_piece.name} de la case centrale.")
                    target_piece.leave_central_cell(self)
                    
                self.piece_to_place = target_piece  # Stocker la pièce tuée pour un placement manuel
                self.available_cells = self.get_unoccupied_cells() + [(original_q, original_r)]  # Obtenir les cellules disponibles
                # Déplacer la pièce qui a tué à la position de la cible
                self.animate_move(pygame.display.get_surface(), piece, original_q, original_r, new_q, new_r)
                piece.q, piece.r = new_q, new_r
            else:
                piece.move(new_q, new_r, self)
                self.next_player()
            return True
        return False

    def check_surrounded_chiefs(self):
        for player in self.players:
            chief = next((piece for piece in player.pieces if isinstance(piece, ChiefPiece)), None)
            if chief and not chief.on_central_cell:
                if chief.is_surrounded(self):
                    logging.info(f"Le chef {chief.name} a été éliminé car il était encerclé!")
                    self.chief_killed(chief, None)

    def place_dead_piece(self, new_q, new_r):
        """Place une pièce morte à une nouvelle position."""
        if self.piece_to_place and (new_q, new_r) in self.available_cells:
            self.piece_to_place.q = new_q
            self.piece_to_place.r = new_r
            self.piece_to_place = None
            self.available_cells = []
            self.next_player()
            return True
        return False

    def draw_available_cells(self, screen):
        """Dessine les cellules disponibles pour placer la pièce tuée."""
        for q, r in self.available_cells:
            x, y = hex_to_pixel(q, r)
            pygame.draw.circle(screen, GREY, (int(x), int(y)), 10)

    def pixel_to_hex(self, x, y):
        """Convertit les coordonnées pixel en coordonnées hexagonales."""
        x = (x - WINDOW_WIDTH // 2) / (HEX_RADIUS * 3/2)
        y = (y - (WINDOW_HEIGHT // 2 - VERTICAL_OFFSET)) / (HEX_RADIUS * math.sqrt(3))
        q = x
        r = y - x/2
        return round(q), round(r)

    def draw_possible_moves(self, screen, possible_moves):
        """Dessine les mouvements possibles sur l'écran."""
        for q, r in possible_moves:
            x, y = hex_to_pixel(q, r)
            pygame.draw.circle(screen, (100, 100, 100), (int(x), int(y)), 10)

    def get_player_of_color(self, color):
        """Retourne le joueur correspondant à la couleur donnée."""
        for player in self.players:
            if player.color == color:
                return player
        return None  # Retourne None si aucun joueur ne correspond à la couleur

    def to_json(self):
        return {
            'pieces': [
                {
                    'q': piece.q,
                    'r': piece.r,
                    'color': piece.color,
                    'piece_class': piece.piece_class,
                    'is_dead': piece.is_dead
                } for piece in self.pieces
            ],
            'current_player_index': self.current_player_index
        }

    def animate_move(self, screen, piece, start_q, start_r, end_q, end_r):
        frames = 30  # Nombre de frames pour l'animation
        logging.info(f"Animation de déplacement de {piece.piece_class} {piece.name} de {start_q},{start_r} à {end_q},{end_r}")
        
        original_q, original_r = piece.q, piece.r  # Sauvegarder la position originale
        current_player_index = self.current_player_index
        next_player_index = (current_player_index + 1) % len(self.players)
        
        for i in range(frames + 1):
            t = i / frames
            current_q = start_q + (end_q - start_q) * t
            current_r = start_r + (end_r - start_r) * t
            
            # Mettre à jour temporairement la position de la pièce
            piece.q, piece.r = current_q, current_r
            
            # Redessiner le plateau complet
            screen.fill(BLACK)
            self.draw(screen)
            
            # Dessiner la pièce en mouvement par-dessus
            x, y = hex_to_pixel(current_q, current_r)
            pygame.draw.circle(screen, piece.color, (int(x), int(y)), PIECE_RADIUS)
            if piece.class_image:
                class_image_rect = piece.class_image.get_rect(center=(int(x), int(y)))
                screen.blit(piece.class_image, class_image_rect)
            
            # Dessiner l'ordre des joueurs avec l'animation de la flèche
            draw_player_turn(screen, self.players, current_player_index, next_player_index, t)
            
            pygame.display.flip()
            pygame.time.wait(5)  # Attendre 5ms entre chaque frame
        
        # Remettre la pièce à sa position finale
        piece.q, piece.r = end_q, end_r
        
        # Redessiner une dernière fois pour s'assurer que tout est à jour
        screen.fill(BLACK)
        self.draw(screen)
        draw_player_turn(screen, self.players, next_player_index)
        pygame.display.flip()

def draw_player_turn(screen, players, current_player_index, next_player_index=None, t=None):
    """Affiche l'ordre des joueurs avec des jetons colorés et une flèche animée pour le joueur actuel."""
    jeton_radius = 15
    spacing = 10
    start_x = 20
    start_y = 300
    arrow_size = 20

    for i, player in enumerate(players):
        # Position du jeton
        x = start_x
        y = start_y + i * (jeton_radius * 2 + spacing)
        
        # Dessiner le jeton
        pygame.draw.circle(screen, player.color, (x, y), jeton_radius)

    # Dessiner la flèche animée
    if next_player_index is not None and t is not None:
        current_y = start_y + current_player_index * (jeton_radius * 2 + spacing)
        next_y = start_y + next_player_index * (jeton_radius * 2 + spacing)
        arrow_y = current_y + (next_y - current_y) * t
        draw_arrow(screen, start_x, arrow_y, arrow_size, jeton_radius, spacing)
    else:
        arrow_y = start_y + current_player_index * (jeton_radius * 2 + spacing)
        draw_arrow(screen, start_x, arrow_y, arrow_size, jeton_radius, spacing)

def draw_arrow(screen, x, y, arrow_size, jeton_radius, spacing):
    """Dessine une flèche à la position spécifiée."""
    arrow_points = [
        (x + jeton_radius + spacing, y),
        (x + jeton_radius + spacing + arrow_size, y - arrow_size // 2),
        (x + jeton_radius + spacing + arrow_size, y + arrow_size // 2)
    ]
    pygame.draw.polygon(screen, WHITE, arrow_points)

def draw_legend(screen):
    font = pygame.font.Font(None, FONT_SIZE)
    legend_items = [
        ("Space", "Play"),
        ("<-", "Undo"),
        ("->", "Redo"),
        ("Return", "Auto play")
    ]
    
    total_width = sum(font.size(f"{key}: {value}")[0] for key, value in legend_items) + 20 * (len(legend_items) - 1)
    start_x = (WINDOW_WIDTH - total_width) // 2
    y = WINDOW_HEIGHT - 100
    
    for key, value in legend_items:
        text = font.render(f"{key}: {value}", True, WHITE)
        screen.blit(text, (start_x, y))
        start_x += text.get_width() + 20  # Espace entre les éléments

def animate_player_elimination(screen, players, eliminated_player_index, board):
    jeton_radius = 15
    spacing = 10
    start_x = 20
    start_y = 300
    fall_duration = 60  # Nombre de frames pour l'animation de chute
    
    for frame in range(fall_duration):
        screen.fill(BLACK)  # Effacer l'écran
        
        # Redessiner le plateau
        board.draw(screen)
        
        for i, player in enumerate(players):
            x = start_x
            y = start_y + i * (jeton_radius * 2 + spacing)
            
            if i == eliminated_player_index:
                # Animer la chute du jeton éliminé
                fall_distance = (frame / fall_duration) ** 2 * WINDOW_HEIGHT  # Accélération de la chute
                y += fall_distance
            
            if y < WINDOW_HEIGHT:  # Ne dessiner le jeton que s'il est encore visible
                pygame.draw.circle(screen, player.color, (int(x), int(y)), jeton_radius)
        
        # Dessiner la flèche pour le joueur actuel
        current_player_index = board.current_player_index % len(players)
        arrow_y = start_y + current_player_index * (jeton_radius * 2 + spacing)
        draw_arrow(screen, start_x, arrow_y, 20, jeton_radius, spacing)
        
        pygame.display.flip()
        pygame.time.wait(16)  # Environ 60 FPS


def draw_button(screen, text, x, y, width, height, color, text_color):
    pygame.draw.rect(screen, color, (x, y, width, height))
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Djambi")
    clock = pygame.time.Clock()
    current_player_index = 4
    board = Board(current_player_index)

    # Initialiser la police pour le texte
    pygame.font.init()
    font = pygame.font.Font(None, FONT_SIZE)

    # Sauvegarder l'état initial explicitement
    board.save_state(current_player_index)

    # Boucle principale du jeu
    running = True
    game_over = False
    winner = None
    selected_piece = None
    possible_moves = []
    auto_play = False

    # Définir les dimensions et la position du bouton
    button_width, button_height = 200, 50
    button_x = (WINDOW_WIDTH - button_width) // 2
    button_y = WINDOW_HEIGHT // 2 + 50

    while running:
        screen.fill(BLACK)

        # Vérifier les événements (fermer la fenêtre ou appuyer sur la touche 'Esc')
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Effacer les mouvements possibles à chaque pression de touche
                selected_piece = None
                possible_moves = []
                board.piece_to_place = None
                board.available_cells = []
                
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and not game_over and not auto_play:
                    board.players[board.current_player_index].play_turn(board)
                    board.current_player_index = (board.current_player_index + 1) % len(board.players)
                    board.save_state(board.current_player_index)
                elif event.key == pygame.K_RETURN:
                    auto_play = not auto_play  # Basculer l'état de auto_play
                elif event.key == pygame.K_LEFT:  # Flèche gauche pour annuler
                    new_index = board.undo()
                    if new_index is not None:
                        board.current_player_index = new_index
                elif event.key == pygame.K_RIGHT:  # Flèche droite pour rétablir
                    new_index = board.redo()
                    if new_index is not None:
                        board.current_player_index = new_index
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over and not auto_play:
                x, y = pygame.mouse.get_pos()
                q, r = board.pixel_to_hex(x, y)
                
                if board.piece_to_place:
                    if board.place_dead_piece(q, r):
                        selected_piece = None
                        possible_moves = []
                elif selected_piece:
                    if (q, r) == (selected_piece.q, selected_piece.r):
                        selected_piece = None
                        possible_moves = []
                    elif board.move_piece(selected_piece, q, r):
                        selected_piece = None
                        possible_moves = []
                    else:
                        new_piece = board.select_piece(q, r)
                        if new_piece:
                            selected_piece = new_piece
                            possible_moves = board.get_possible_moves(selected_piece)
                else:
                    selected_piece = board.select_piece(q, r)
                    if selected_piece:
                        possible_moves = board.get_possible_moves(selected_piece)

        # Vérifier s'il ne reste qu'un seul joueur
        if len(board.players) == 1 and not game_over:
            game_over = True
            winner = board.players[0]
            auto_play = False

        if not game_over:
            if auto_play:
                board.players[board.current_player_index].play_turn(board)
                board.next_player()  # Utiliser la nouvelle méthode ici aussi
            
            # Récupérer le joueur actuel
            current_player = board.players[board.current_player_index]
            draw_player_turn(screen, board.players, board.current_player_index)

            # Dessiner le plateau et les pièces
            board.draw(screen, selected_piece, board.piece_to_place)
            if selected_piece and not auto_play:
                board.draw_possible_moves(screen, possible_moves)
            if board.piece_to_place and not auto_play:
                board.draw_available_cells(screen)
            
            # Ajouter la légende
            draw_legend(screen)
        else:
            # Afficher le message de victoire
            win_text = font.render(f"Le joueur {winner.name} a gagné !", True, WHITE)
            win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
            screen.blit(win_text, win_rect)

            # Dessiner le bouton "Rejouer"
            draw_button(screen, "Rejouer", button_x, button_y, button_width, button_height, WHITE, BLACK)

            # Vérifier si le bouton "Rejouer" est cliqué
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
                    # Réinitialiser le jeu
                    current_player_index = 4
                    board = Board(current_player_index)
                    board.save_state(current_player_index)
                    game_over = False
                    winner = None
                    selected_piece = None
                    possible_moves = []
                    auto_play = False

        # Afficher "Player's turn" avec le jeton du joueur actuel ou le message de victoire
        pygame.display.flip()

        # Limiter la vitesse à 30 FPS
        clock.tick(30)

    # Quitter proprement
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

