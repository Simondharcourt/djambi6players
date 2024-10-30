


from constants import *
import logging
import pygame
import cairosvg
from io import BytesIO
import random
import math


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


class Piece:
    necromobile_image = None

    def __init__(self, q, r, color, piece_class, svg_path=None):
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
        if IS_PRODUCTION:
            return None
        with open(svg_path, 'rb') as f:
            svg_data = f.read()
        png_data = cairosvg.svg2png(bytestring=svg_data, output_width=target_size[0], output_height=target_size[1])
        image = pygame.image.load(BytesIO(png_data))
        return image  # Retourner directement l'image sans redimensionnement

    def load_image(self):
        # Charger l'image seulement quand nécessaire
        self.class_image = self.load_svg_as_surface(self.svg_path)

    @classmethod
    def load_necromobile_image(cls):
        if cls.necromobile_image is None:
            cls.necromobile_image = pygame.transform.scale(
                cls.load_svg_as_surface(ASSET_PATH + 'necromobile.svg'),
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
                if not is_within_board(new_q, new_r) or board.is_occupied(new_q, new_r):
                    break
                if not (new_q == 0 and new_r == 0 and not isinstance(self, ChiefPiece)):
                    possible_moves.append((new_q, new_r))
                step += 1  # Continuer dans la même direction

        return possible_moves

    def move(self, new_q, new_r, board):
        if (new_q, new_r) not in self.all_possible_moves(board):
            return False # new_q, new_r is not a valid move.
        self.q = new_q
        self.r = new_r
        return True

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
                
    
    def move(self, new_q, new_r, board, moved_piece_position=None):
        original_q, original_r = self.q, self.r
        if (new_q, new_r) not in self.all_possible_moves(board):
            return False # new_q, new_r is not a valid move.
        target_piece = board.get_piece_at(new_q, new_r)
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        if target_piece and target_piece.color != self.color and not target_piece.is_dead:
            if isinstance(target_piece, ChiefPiece):
                board.chief_killed(target_piece, board.get_chief_of_color(self.color))
            target_piece.die()
            unoccupied_cells = board.get_unoccupied_cells()
            if not moved_piece_position:
                new_position = random.choice(unoccupied_cells)
            elif moved_piece_position in unoccupied_cells:
                new_position = moved_piece_position
            else:
                return False # moved_piece_position is not a valid position.
            target_piece.q, target_piece.r = new_position
            logging.info(f"Le militant a tué la pièce en {new_q}, {new_r} et l'a déplacée en {target_piece.q,}, {target_piece.r}")

        self.q, self.r = new_q, new_r
        logging.info(f"Le militant s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
        return True

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
        if (new_q, new_r) not in self.all_possible_moves(board):
            return False # new_q, new_r is not a valid move.
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
        return True
    
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

    def move(self, new_q, new_r, board, moved_piece_position=None):
        original_q, original_r = self.q, self.r
        if (new_q, new_r) not in self.all_possible_moves(board):
            return False # new_q, new_r is not a valid move.
        target_piece = board.get_piece_at(new_q, new_r)

        # Ajouter l'animation du mouvement
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and target_piece.color != self.color and not target_piece.is_dead:
            if isinstance(target_piece, ChiefPiece):
                board.chief_killed(target_piece, board.get_chief_of_color(self.color))
            target_piece.die()
            unoccupied_cells = board.get_unoccupied_cells()
            if not moved_piece_position:
                new_position = random.choice(unoccupied_cells)
            elif moved_piece_position in unoccupied_cells:
                new_position = moved_piece_position
            else:
                return False # moved_piece_position is not a valid position.
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
        return True

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

    def move(self, new_q, new_r, board, moved_piece_position=None):
        original_q, original_r = self.q, self.r
        if (new_q, new_r) not in self.all_possible_moves(board):
            return False # new_q, new_r is not a valid move.
        target_piece = board.get_piece_at(new_q, new_r)
        
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and not target_piece.is_dead:
            # Trouver une case libre aléatoire
            unoccupied_cells = board.get_unoccupied_cells()
            if not moved_piece_position:
                new_position = random.choice(unoccupied_cells)
            elif moved_piece_position in unoccupied_cells:
                new_position = moved_piece_position
            else:
                return False # moved_piece_position is not a valid position.
            # Déplacer la pièce rencontrée vers la nouvelle position
            target_piece.q, target_piece.r = new_position
            logging.info(f"Le diplomate {self.name} a déplacé le {target_piece.piece_class} {target_piece.name} de {new_q}, {new_r} vers {new_position}")
            
            if isinstance(target_piece, ChiefPiece) and target_piece.on_central_cell:
                target_piece.leave_central_cell(board)
                
        # Déplacer le diplomate
        self.q, self.r = new_q, new_r
        logging.info(f"Le diplomate s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
        return True
        
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
    

    def move(self, new_q, new_r, board,  moved_piece_position=None):
        original_q, original_r = self.q, self.r
        if (new_q, new_r) not in self.all_possible_moves(board):
            return False # new_q, new_r is not a valid move.
        
        target_piece = board.get_piece_at(new_q, new_r)
        board.animate_move(pygame.display.get_surface(), self, original_q, original_r, new_q, new_r)
        
        if target_piece and target_piece.is_dead:
            # Trouver une case libre aléatoire
            unoccupied_cells = board.get_unoccupied_cells()
            if not moved_piece_position:
                new_position = random.choice(unoccupied_cells)
            elif moved_piece_position in unoccupied_cells:
                new_position = moved_piece_position
            else:
                return False # moved_piece_position is not a valid position.
            # Déplacer la pièce rencontrée vers la nouvelle position
            target_piece.q, target_piece.r = new_position
            logging.info(f"Le necromobile a déplacé la pièce de {new_q}, {new_r} vers {new_position}")
        # Déplacer le necromobile
        self.q, self.r = new_q, new_r
        logging.info(f"Le necromobile s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
        return True

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
    if not IS_PRODUCTION:  # Only load image if not in production
        piece.load_image()  # Charger l'image immédiatement après la création
    return piece

