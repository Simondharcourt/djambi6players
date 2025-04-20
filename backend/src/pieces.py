from .constants import *
import logging
import pygame
import cairosvg
from io import BytesIO
import random
import math


def is_within_board(q, r):
    """Vérifie si les coordonnées q, r sont dans les limites du plateau."""
    if NB_PLAYER_MODE in [3, 6]:
        s = -q - r  # Coordonnée s dans un système hexagonal
        return abs(q) < BOARD_SIZE and abs(r) < BOARD_SIZE and abs(s) < BOARD_SIZE
    elif NB_PLAYER_MODE == 4:
        return abs(q) < BOARD_SIZE and abs(r) < BOARD_SIZE


def hex_to_pixel(q, r):
    if NB_PLAYER_MODE in [3, 6]:
        x = HEX_RADIUS * 3/2 * q
        y = HEX_RADIUS * math.sqrt(3) * (r + q/2)
    elif NB_PLAYER_MODE == 4:
        x = math.sqrt(3) * HEX_RADIUS * q  # Ajustement pour le mode 4 joueurs
        y = math.sqrt(3) * HEX_RADIUS * r  # Ajustement pour le mode 4 joueurs
    # Décalage vertical pour centrer le plateau plus haut
    pixel_coords = (
        int(x + WINDOW_WIDTH // 2),
        int(y + (WINDOW_HEIGHT // 2) - VERTICAL_OFFSET)
    )
    return pixel_coords


def find_adjacent_vectors(dq, dr):
    for v1 in ADJACENT_DIRECTIONS:
        for v2 in ADJACENT_DIRECTIONS:
            if v1 != v2:  # Vérifie que v1 et v2 sont différents
                if (v1[0] + v2[0] == dq) and (v1[1] + v2[1] == dr):
                    return v1, v2  # Retourne les vecteurs trouvés
    return None  


class Piece:
    necromobile_image = None

    def __init__(self, q, r, color, piece_class, svg_path=None, menace_score=0, opportunity_score=0, std_value=1):
        self.q = q  # Coordonnée hexagonale q
        self.r = r  # Coordonnée hexagonale r
        self.color = color  # Couleur de la pièce
        self.is_dead = False  # Indique si la pièce est morte ou non
        self.piece_class = piece_class  # Classe de la pièce (e.g., 'assassin', 'chief')
        self.svg_path = svg_path  # Ajout de cet attribut
        self.class_image = None  # Ne pas stocker l'image ici
        self.name = NAMES[color]
        self.on_central_cell = False  # Nouvel attribut pour suivre si le chef est sur la case centrale

        # self.menace_score = menace_score
        # self.opportunity_score = opportunity_score
        self.opportunity_moves = {}
        self.threaten = []
        self.protect = []
        self.is_threatened_by = []
        self.is_protected_by = []
        self.std_value = std_value
        
        self.possible_moves = []
        self.best_moves = {}

        self.threat_score = 0

    def remove_threat_and_protections_after_move(self):
        for piece in self.threaten:
            piece.is_threatened_by.remove(self)
        for piece in self.protect:
            piece.is_protected_by.remove(self)
        self.threaten = []
        self.protect = []


    def update_threat_and_protections(self, board):
        self.remove_threat_and_protections_after_move()
        
        possible_moves = self.all_possible_moves(board)
        pieces = [board.get_piece_at(q, r) for q, r in possible_moves]
        pieces = [p for p in pieces if p]  # Filtrer les cases vides
        self.threaten = [p for p in pieces if p.color != self.color]
        self.protect = [p for p in pieces if p.color == self.color]
        for piece in pieces:
            if piece in self.threaten:
                piece.is_threatened_by.append(self)
                                
            elif piece in self.protect:
                piece.is_protected_by.append(self)
        
    def evaluate_threat_score(self, board):
        threat_score = 0
        threatened_score = 0

        is_protected = 1 if len(self.is_protected_by)>0 else 0
        for threat in self.is_threatened_by:
            threatened_score += max(0, self.std_value - threat.std_value * is_protected)

        if isinstance(self, ChiefPiece) and (0,0) in self.possible_moves:
            threat_score += 2 * self.std_value * (len(board.players)-2)
            
        for target in self.threaten:
            is_protected = 1 if len(target.is_protected_by)>0 else 0
            threat_score += max(0, target.std_value - self.std_value * is_protected)
            
        self.threat_score = threat_score - threatened_score * self.std_value * (len(board.players) - 1)
        return self.threat_score

    def update_piece_best_moves(self, board):
        # self.opportunity_moves = {(self, (p.q, p.r)): {'victim_value': p.std_value, 'protected_value': len(p.is_protected_by)} for p in self.threaten}
        is_protected = 1 if len(self.is_protected_by)>0 else 0
        
        get_out_score = 0
        for threat in self.is_threatened_by:
            get_out_score += max(0, self.std_value - threat.std_value * is_protected) * (len(board.players)-1)
        
        best_moves = {}
        possible_moves = self.all_possible_moves(board)
        
        if isinstance(self, ChiefPiece) and (0,0) in possible_moves:
            best_moves[(self, possible_moves)] = 2 * self.std_value * (len(board.players)-2)
        
        if get_out_score>0:
            for move in possible_moves:
                best_moves[(self, move)] = get_out_score
        
        for target in self.threaten:
            is_protected = 1 if len(target.is_protected_by)>0 else 0
            best_moves[(self, (target.q, target.r))] = target.std_value - self.std_value * is_protected * (len(board.players)-1) + get_out_score
        
        self.best_moves = best_moves
        return best_moves


    def die(self):
        """Marque la pièce comme morte et change sa couleur en grise."""
        self.is_dead = True
        self.color = DARKER_GREY  # Couleur grise pour les pièces mortes
        logging.debug(f"Pièce en {self.q}, {self.r} est morte")

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
            if (dq, dr) in DIAG_DIRECTIONS:
                v1, v2 = find_adjacent_vectors(dq, dr)
            new_q, new_r = self.q, self.r
            while True:
                if (dq, dr) in DIAG_DIRECTIONS and board.is_occupied(new_q + v1[0], new_r + v1[1]) and board.is_occupied(new_q + v2[0], new_r + v2[1]):
                    break
                new_q = self.q + dq * step
                new_r = self.r + dr * step
                if not is_within_board(new_q, new_r) or board.is_occupied(new_q, new_r):
                    break
                
                
                if not (new_q == 0 and new_r == 0 and not isinstance(self, ChiefPiece)):
                    possible_moves.append((new_q, new_r))
                step += 1  # Continuer dans la même direction

        self.possible_moves = possible_moves
        return possible_moves

    def move(self, new_q, new_r, board):
        if (new_q, new_r) not in self.all_possible_moves(board):
            return False # new_q, new_r is not a valid move.
        self.q = new_q
        self.r = new_r
        self.update_threat_and_protections(board)
        return True

    def is_surrounded(self, board, visited=None):
        if visited is None:
            visited = set()
        if (self.q, self.r) in visited:
            return True
        visited.add((self.q, self.r))

        for dq, dr in ADJACENT_DIRECTIONS:
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
    def __init__(self, q, r, color, piece_class, svg_path, menace_score=0, opportunity_score=0, std_value=1):
        super().__init__(q, r, color, piece_class, svg_path, menace_score, opportunity_score, std_value)

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
                
                
                if (dq, dr) in DIAG_DIRECTIONS:
                    v1, v2 = find_adjacent_vectors(dq, dr)
                    if board.is_occupied(self.q + v1[0], self.r + v1[1]) and board.is_occupied(self.q + v2[0], self.r + v2[1]):
                        break
                
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
            logging.debug(f"Le militant a tué la pièce en {new_q}, {new_r} et l'a déplacée en {target_piece.q,}, {target_piece.r}")

        self.q, self.r = new_q, new_r
        logging.debug(f"Le militant s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
        self.update_threat_and_protections(board)
        return True

class AssassinPiece(Piece):
    def __init__(self, q, r, color, piece_class, svg_path, menace_score=0, opportunity_score=0, std_value=2):
        super().__init__(q, r, color, piece_class, svg_path, menace_score, opportunity_score, std_value)

    def all_possible_moves(self, board):
        """Retourne tous les mouvements possibles pour l'assassin, y compris les cases occupées par des ennemis,
        et en traversant les pièces alliées."""
        if self.is_dead:
            return [] # ne peut se dplacer.
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            new_q, new_r = self.q, self.r
            if (dq, dr) in DIAG_DIRECTIONS:
                v1, v2 = find_adjacent_vectors(dq, dr)
            while True:
                if (dq, dr) in DIAG_DIRECTIONS and board.is_occupied(new_q + v1[0], new_r + v1[1]) and board.is_occupied(new_q + v2[0], new_r + v2[1]):
                    if not ADVANCED_RULES:
                        break
                    piece1 = board.get_piece_at(new_q + v1[0], new_r + v1[1])
                    piece2 = board.get_piece_at(new_q + v2[0], new_r + v2[1])
                    if (piece1.color != self.color or piece1.is_dead) and (piece2.color != self.color or piece2.is_dead):
                        break
                new_q = self.q + dq * step
                new_r = self.r + dr * step

                if not is_within_board(new_q, new_r):
                    break

                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if piece_at_position.is_dead:
                        break
                    elif piece_at_position.color != self.color:
                        possible_moves.append((new_q, new_r))  # L'assassin peut se déplacer sur une pièce ennemie
                        break
                    elif not ADVANCED_RULES:
                        break
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
            logging.debug(f"L'assassin a tué la pièce en {new_q}, {new_r} et l'a déplacée en {original_q}, {original_r}")


        # Déplacer l'assassin
        self.q, self.r = new_q, new_r
        logging.debug(f"L'assassin s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
        self.update_threat_and_protections(board)
        return True
    
class ChiefPiece(Piece):
    def __init__(self, q, r, color, piece_class, svg_path, menace_score=0, opportunity_score=0, std_value=5):
        super().__init__(q, r, color, piece_class, svg_path, menace_score, opportunity_score, std_value)

    def all_possible_moves(self, board):
        if self.is_dead:
            return []  # ne peut se déplacer. # Le chef ne bouge plus s'il est sur la case centrale
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            new_q, new_r = self.q, self.r
            if (dq, dr) in DIAG_DIRECTIONS:
                v1, v2 = find_adjacent_vectors(dq, dr)
            while True:
                if (dq, dr) in DIAG_DIRECTIONS and board.is_occupied(new_q + v1[0], new_r + v1[1]) and board.is_occupied(new_q + v2[0], new_r + v2[1]):
                    break
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
            logging.debug(f"Le chef a tué la pièce en {new_q}, {new_r} et l'a déplacée en {target_piece.q,}, {target_piece.r}")

        # Déplacer le chef
        self.q, self.r = new_q, new_r
        logging.debug(f"Le chef s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")

        self.update_threat_and_protections(board)
        
        # Vérifier si le chef est sur la case centrale
        if not self.on_central_cell and self.q == 0 and self.r == 0:
            self.enter_central_cell(board)
        elif self.on_central_cell and (self.q != 0 or self.r != 0):
            self.leave_central_cell(board)
        return True

    def enter_central_cell(self, board):
        self.on_central_cell = True
        self.std_value += 5
        logging.debug(f"Le chef {self.name} est arrivé sur la case centrale!")
        new_order = []
        for player_index in range(board.current_player_index + 1, len(board.players) + board.current_player_index):
            new_order.append(board.players[player_index%len(board.players)])
            new_order.append(board.get_player_of_color(self.color))
        board.players = new_order
        board.current_player_index = -1

    def leave_central_cell(self, board):
        self.on_central_cell = False
        self.std_value -= 5
        logging.debug(f"Le chef {self.name} n'est plus sur la case centrale.")
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
    def __init__(self, q, r, color, piece_class, svg_path, menace_score=0, opportunity_score=0, std_value=2):
        super().__init__(q, r, color, piece_class, svg_path, menace_score, opportunity_score, std_value)

    def all_possible_moves(self, board):
        if self.is_dead:
            return [] # ne peut se déplacer.
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            new_q, new_r = self.q, self.r
            if (dq, dr) in DIAG_DIRECTIONS:
                v1, v2 = find_adjacent_vectors(dq, dr)
            while True:
                
                if (dq, dr) in DIAG_DIRECTIONS and board.is_occupied(new_q + v1[0], new_r + v1[1]) and board.is_occupied(new_q + v2[0], new_r + v2[1]):
                    break
                new_q = self.q + dq * step
                new_r = self.r + dr * step



                if not is_within_board(new_q, new_r):
                    break

                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if not piece_at_position.is_dead and (ADVANCED_RULES or piece_at_position.color != self.color): # toutes les pièces sont accessibles
                        possible_moves.append((new_q, new_r))
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
            logging.debug(f"Le diplomate {self.name} a déplacé le {target_piece.piece_class} {target_piece.name} de {new_q}, {new_r} vers {new_position}")
            
            if isinstance(target_piece, ChiefPiece) and target_piece.on_central_cell:
                target_piece.leave_central_cell(board)
                
        # Déplacer le diplomate
        self.q, self.r = new_q, new_r
        logging.debug(f"Le diplomate s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
        self.update_threat_and_protections(board)
        return True
        
class NecromobilePiece(Piece):
    """Ajoute un comportement spécifique pour les necromobiles."""
    
    def __init__(self, q, r, color, piece_class, svg_path, menace_score=0, opportunity_score=0, std_value=3):
        super().__init__(q, r, color, piece_class, svg_path, menace_score, opportunity_score, std_value)

    def all_possible_moves(self, board):
        if self.is_dead:
            return [] # ne peut se dplacer.
        possible_moves = []
        for dq, dr in ALL_DIRECTIONS:
            step = 1
            new_q, new_r = self.q, self.r
            if (dq, dr) in DIAG_DIRECTIONS:
                v1, v2 = find_adjacent_vectors(dq, dr)
            while True:
                if (dq, dr) in DIAG_DIRECTIONS and board.is_occupied(new_q + v1[0], new_r + v1[1]) and board.is_occupied(new_q + v2[0], new_r + v2[1]):
                    break
                new_q = self.q + dq * step
                new_r = self.r + dr * step
                if not is_within_board(new_q, new_r):
                    break

                piece_at_position = board.get_piece_at(new_q, new_r)
                if piece_at_position:
                    if piece_at_position.is_dead:
                        possible_moves.append((new_q, new_r)) 
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
            logging.debug(f"Le necromobile a déplacé la pièce de {new_q}, {new_r} vers {new_position}")
        # Déplacer le necromobile
        self.q, self.r = new_q, new_r
        logging.debug(f"Le necromobile s'est déplacé de {original_q}, {original_r} à {new_q}, {new_r}")
        self.update_threat_and_protections(board)
        return True

class ReporterPiece(Piece):
    def __init__(self, q, r, color, piece_class, svg_path, menace_score=0, opportunity_score=0, std_value=2):
        super().__init__(q, r, color, piece_class, svg_path, menace_score, opportunity_score, std_value)

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
        if ADVANCED_RULES:
            for dq, dr in ADJACENT_DIRECTIONS:
                adjacent_q = self.q + dq
                adjacent_r = self.r + dr
                piece = board.get_piece_at(adjacent_q, adjacent_r)
                if piece and piece.color != self.color and not piece.is_dead:
                    logging.debug(f"Le reporter tue la pièce ennemie en {adjacent_q}, {adjacent_r}")
                    if isinstance(piece, ChiefPiece):
                        board.chief_killed(piece, board.get_chief_of_color(self.color))
                    piece.die()
        else:
            # implement only one kill from the reporter.
            adjacent_enemies = []
            for dq, dr in ADJACENT_DIRECTIONS:
                adjacent_q = self.q + dq
                adjacent_r = self.r + dr
                piece = board.get_piece_at(adjacent_q, adjacent_r)
                if piece and piece.color != self.color and not piece.is_dead:
                    adjacent_enemies.append(piece)
            
            # Si des ennemis sont adjacents, en choisir un au hasard à éliminer
            if adjacent_enemies:
                target_piece = max(adjacent_enemies, key=lambda p: p.std_value)
                logging.debug(f"Le reporter tue la pièce ennemie en {target_piece.q}, {target_piece.r} (valeur: {target_piece.std_value})")
                if isinstance(target_piece, ChiefPiece):
                    board.chief_killed(target_piece, board.get_chief_of_color(self.color))
                target_piece.die()

        self.update_threat_and_protections(board)
        return True

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

