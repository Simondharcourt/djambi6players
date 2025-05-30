from .constants import *
import math
import pygame
import logging
from .pieces import *
from .minmax_player import MinMaxPlayer
from .animation import animate_player_elimination, draw_player_turn
from .utils import get_directions, get_colors, get_start_positions

class Board:
    def __init__(self, nb_players, current_player_index=0, one_player_mode=False):
        self.hexagons = []
        self.pieces = []
        self.nb_players = nb_players
        self.eliminated_players = []
        self.current_player_index = current_player_index
        self.one_player_mode = one_player_mode
        logging.debug("Initialisation du plateau")

        if self.nb_players in [3, 4]:
            self.board_size = 5
            self.advanced_rules = False
        elif self.nb_players == 6:
            self.board_size = 7
            self.advanced_rules = True
        else:
            raise ValueError("Nombre de joueurs invalide. Veuillez choisir 3, 4 ou 6.")

        self.directions = get_directions(self.nb_players)
        self.colors, self.color_reverse, self.names = get_colors(self.nb_players)
        self.start_positions = get_start_positions(self.nb_players)

        # Initialisation des hexagones du plateau
        for q in range(-self.board_size + 1, self.board_size):
            for r in range(-self.board_size + 1, self.board_size):
                if -q - r in range(-self.board_size + 1, self.board_size) or self.nb_players == 4:
                    self.hexagons.append((q, r))

        # Ajouter des pièces aux positions de départ
        self.initialize_pieces()
        self.rl = False
        self.history = []
        self.future = []
        self.piece_to_place = None  # Pièce tuée à placer manuellement
        self.available_cells = []  # Cellules disponibles pour placer la pièce tuée
        self.board_surface = self.create_board_surface()
        self.hex_pixel_positions = self.calculate_hex_pixel_positions()
        self.save_state(self.current_player_index)

    def create_board_surface(self):
        board_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        board_surface.fill(BLACK)
        for hex_coord in self.hexagons:
            q, r = hex_coord
            x, y = self.hex_to_pixel(q, r)
            pygame.draw.polygon(board_surface, WHITE, self.hex_corners(x, y), 1)
            if q == 0 and r == 0:
                pygame.draw.polygon(
                    board_surface, CENTRAL_WHITE, self.hex_corners(x, y), 0
                )
            else:
                pygame.draw.polygon(board_surface, WHITE, self.hex_corners(x, y), 1)
        return board_surface

    def calculate_hex_pixel_positions(self):
        positions = {}
        for q, r in self.hexagons:
            x, y = self.hex_to_pixel(q, r)
            positions[(q, r)] = (x, y)
        return positions

    def is_within_board(self, q, r):
        """Vérifie si les coordonnées q, r sont dans les limites du plateau."""
        if self.nb_players in [3, 6]:
            s = -q - r  # Coordonnée s dans un système hexagonal
            return abs(q) < self.board_size and abs(r) < self.board_size and abs(s) < self.board_size
        elif self.nb_players == 4:
            return abs(q) < self.board_size and abs(r) < self.board_size

    def hex_to_pixel(self, q, r):
        if self.nb_players in [3, 6]:
            x = HEX_RADIUS * 3 / 2 * q
            y = HEX_RADIUS * math.sqrt(3) * (r + q / 2)
        elif self.nb_players == 4:
            x = math.sqrt(3) * HEX_RADIUS * q  # Ajustement pour le mode 4 joueurs
            y = math.sqrt(3) * HEX_RADIUS * r  # Ajustement pour le mode 4 joueurs
        # Décalage vertical pour centrer le plateau plus haut
        pixel_coords = (
            int(x + WINDOW_WIDTH // 2),
            int(y + (WINDOW_HEIGHT // 2) - VERTICAL_OFFSET),
        )
        return pixel_coords

    def find_adjacent_vectors(self, dq, dr):
        for v1 in self.directions["adjacent"]:
            for v2 in self.directions["adjacent"]:
                if v1 != v2:  # Vérifie que v1 et v2 sont différents
                    if (v1[0] + v2[0] == dq) and (v1[1] + v2[1] == dr):
                        return v1, v2  # Retourne les vecteurs trouvés
        return None

    def initialize_pieces(self):
        # Position de départ des pièces (exemple arbitraire)
        logging.debug("Initialisation des pièces")

        class_svg_paths = {
            "assassin": ASSET_PATH + "assassin.svg",
            "chief": ASSET_PATH + "chief.svg",
            "diplomat": ASSET_PATH + "diplomat.svg",
            "militant": ASSET_PATH + "militant.svg",
            "necromobile": ASSET_PATH + "necromobile.svg",
            "reporter": ASSET_PATH + "reporter.svg",
        }
        self.players = []
        for color in self.colors.keys():
            pieces = [
                create_piece(q, r, self.colors[color], cl, class_svg_paths[cl])
                for q, r, c, cl in self.start_positions
                if c == color
            ]
            self.players.append(MinMaxPlayer(self.colors[color], pieces))
            self.pieces.extend(pieces)
        self.update_all_scores()
        self.update_all_opportunity_scores()

    def save_state(self, current_player_index):
        state = {
            "pieces": [
                (p.q, p.r, p.color, p.piece_class, p.svg_path, p.is_dead)
                for p in self.pieces
            ],
            "players": [
                {"color": p.color, "pieces": [piece.piece_class for piece in p.pieces]}
                for p in self.players
                if p is not None
            ],
            "current_player_index": current_player_index,
            "players_colors_order": [
                p.color for p in self.players
            ],  # probably something to do with this.
        }
        self.history.append(state)
        self.future.clear()

    def load_state(self, state):
        self.pieces = [
            create_piece(q, r, color, piece_class, svg_path)
            for q, r, color, piece_class, svg_path, is_dead in state["pieces"]
        ]
        for piece, (_, _, _, _, _, is_dead) in zip(self.pieces, state["pieces"]):
            piece.is_dead = is_dead
            if piece.q == 0 and piece.r == 0:
                piece.on_central_cell = True
            else:
                piece.on_central_cell = False
        self.players = []
        for player_data in state["players"]:
            player_pieces = [
                piece for piece in self.pieces if piece.color == player_data["color"]
            ]
            self.players.append(MinMaxPlayer(player_data["color"], player_pieces))
        self.update_all_scores()
        return state["current_player_index"]

    def undo(self):
        if (
            len(self.history) > 1
        ):  # Assurez-vous qu'il reste au moins un état après l'annulation
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
        for q in range(-self.board_size + 1, self.board_size):
            for r in range(-self.board_size + 1, self.board_size):
                # Vérifier si la case est sur le plateau
                if self.is_within_board(q, r):
                    # Exclure la case centrale et les cases occupées
                    if (q != 0 or r != 0) and not self.is_occupied(q, r):
                        unoccupied_cells.append((q, r))
        return unoccupied_cells

    def get_chief_of_color(self, color):
        for piece in self.pieces:
            if isinstance(piece, ChiefPiece) and piece.color == color:
                return piece
        return None

    def chief_killed(self, killed_chief, killer_chief):
        killed_player = next(
            (player for player in self.players if player.color == killed_chief.color),
            None,
        )
        killer_player = (
            next(
                (
                    player
                    for player in self.players
                    if player.color == killer_chief.color
                ),
                None,
            )
            if killer_chief
            else None
        )

        if killed_player is None:
            logging.error(
                f"Erreur : Impossible de trouver le joueur tué. Killed chief color: {killed_chief.color}"
            )
            return

        self.eliminated_players.append(killed_player)
        # Changer la couleur de toutes les pièces du joueur tué
        for piece in killed_player.pieces:
            if killer_player:
                piece.color = killer_player.color
                piece.name = self.names[killer_player.color]
                piece.load_image()
            else:
                piece.die()  # Si pas de tueur spécifique, les pièces meurent simplement

        # Transférer toutes les pièces au joueur qui a tué le chef, s'il y en a un
        if killer_player:
            killer_player.pieces.extend(killed_player.pieces)

        # Supprimer toutes les occurrences du joueur tué
        while killed_player in self.players:
            killed_player_index = self.players.index(killed_player)
            if not self.rl:
                animate_player_elimination(
                    pygame.display.get_surface(),
                    self.players,
                    killed_player_index,
                    self,
                )
            self.players.pop(killed_player_index)

        logging.debug(
            f"Le chef {killed_chief.name} a été tué{'.' if not killer_chief else f' par le chef {killer_chief.name}.'} Toutes ses pièces sont maintenant {'mortes' if not killer_chief else f'contrôlées par {killer_chief.name}'}."
        )

        # Mettre à jour l'index du joueur courant si nécessaire
        if self.current_player_index >= len(self.players):
            self.current_player_index = -1

    def draw(self, screen, selected_piece=None, piece_to_place=None):
        if self.rl:
            return
        for hex_coord in self.hexagons:
            x, y = self.hex_pixel_positions[hex_coord]
            q, r = hex_coord
            pygame.draw.polygon(screen, WHITE, self.hex_corners(x, y), 1)

            if q == 0 and r == 0:
                pygame.draw.polygon(
                    screen, CENTRAL_WHITE, self.hex_corners(x, y), 0
                )  # Remplissage complet
            else:
                pygame.draw.polygon(
                    screen, WHITE, self.hex_corners(x, y), 1
                )  # Seulement le contour

        self.current_player_color = self.players[self.current_player_index].color
        for piece in self.pieces:
            is_current_player = (
                piece.color == self.current_player_color
                and selected_piece is None
                and piece_to_place is None
            )
            piece.draw(self, screen, is_current_player)

    def hex_corners(self, x, y):
        """Retourne les coins de l'hexagone en fonction de sa position pixel."""
        corners = []
        if self.nb_players in [3, 6]:
            for i in range(6):
                angle_deg = 60 * i
                angle_rad = math.radians(angle_deg)
                corner_x = x + HEX_RADIUS * math.cos(angle_rad)
                corner_y = y + HEX_RADIUS * math.sin(angle_rad)
                corners.append((corner_x, corner_y))
        elif self.nb_players == 4:
            # Créer un carré en utilisant des offsets directs
            half_size = (
                HEX_RADIUS * math.sqrt(3) / 2
            )  # Ajusté pour avoir la même taille approximative que l'hexagone
            corners = [
                (x - half_size, y - half_size),  # Coin supérieur gauche
                (x + half_size, y - half_size),  # Coin supérieur droit
                (x + half_size, y + half_size),  # Coin inférieur droit
                (x - half_size, y + half_size),  # Coin inférieur gauche
            ]
        return corners

    def update_all_opportunity_scores(self):
        for p in self.pieces:
            p.update_threat_and_protections(self)
        for p in self.pieces:
            p.update_piece_best_moves(self)
            p.evaluate_threat_score(self)

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
        self.update_all_scores()
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.save_state(self.current_player_index)

    def move_piece(self, piece, new_q, new_r):
        """Déplace une pièce vers une nouvelle position."""
        if (new_q, new_r) in self.get_possible_moves(piece):
            target_piece = self.get_piece_at(new_q, new_r)
            original_q, original_r = piece.q, piece.r
            logging.debug(
                f"Le {piece.piece_class} {piece.name} se déplace de {piece.q},{piece.r} à {new_q},{new_r}"
            )
            if target_piece and isinstance(
                piece, (MilitantPiece, ChiefPiece, DiplomatPiece, NecromobilePiece)
            ):
                # Tuer la pièce ennemie
                if isinstance(piece, (MilitantPiece, ChiefPiece)):
                    if isinstance(target_piece, ChiefPiece):
                        self.chief_killed(
                            target_piece, self.get_chief_of_color(piece.color)
                        )
                        logging.debug(
                            f"Le chef {target_piece.name} a été tué par le {piece.piece_class} {piece.name}."
                        )

                    if target_piece.on_central_cell and isinstance(piece, ChiefPiece):
                        piece.enter_central_cell(self)
                        logging.debug(
                            f"Le chef {piece.name} entre sur la case centrale."
                        )

                    target_piece.die()
                    logging.debug(
                        f"Le {target_piece.piece_class} {target_piece.name} a té tué par le {piece.piece_class} {piece.name}."
                    )

                if (
                    isinstance(piece, DiplomatPiece)
                    and isinstance(target_piece, ChiefPiece)
                    and target_piece.on_central_cell
                    and not target_piece.is_dead
                ):
                    logging.debug(
                        f"Le diplomate {piece.name} fait quitter le chef {target_piece.name} de la case centrale."
                    )
                    target_piece.leave_central_cell(self)

                self.piece_to_place = (
                    target_piece  # Stocker la pièce tuée pour un placement manuel
                )
                self.available_cells = self.get_unoccupied_cells() + [
                    (original_q, original_r)
                ]  # Obtenir les cellules disponibles
                # Déplacer la pièce qui a tué à la position de la cible
                self.animate_move(
                    pygame.display.get_surface(),
                    piece,
                    original_q,
                    original_r,
                    new_q,
                    new_r,
                )
                piece.q, piece.r = new_q, new_r
            else:
                piece.move(new_q, new_r, self)
                self.next_player()
            return True
        return False

    def check_surrounded_chiefs(self):
        for player in self.players:
            chief = next(
                (piece for piece in player.pieces if isinstance(piece, ChiefPiece)),
                None,
            )
            if chief and not chief.on_central_cell:
                if chief.is_surrounded(self):
                    logging.debug(
                        f"Le chef {chief.name} a été éliminé car il était encerclé!"
                    )
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
        if self.rl:
            return
        for q, r in self.available_cells:
            x, y = self.hex_to_pixel(q, r)
            pygame.draw.circle(screen, GREY, (int(x), int(y)), 10)

    def pixel_to_hex(self, x, y):
        """Convertit les coordonnées pixel en coordonnées hexagonales."""

        if self.nb_players in [3, 6]:
            x = (x - WINDOW_WIDTH // 2) / (HEX_RADIUS * 3 / 2)
            y = (y - (WINDOW_HEIGHT // 2 - VERTICAL_OFFSET)) / (
                HEX_RADIUS * math.sqrt(3)
            )
            q = x
            r = y - x / 2
            return round(q), round(r)
        elif self.nb_players == 4:
            # Ajustement pour le mode 4 joueurs (carrés)
            x = (x - WINDOW_WIDTH // 2) / (
                HEX_RADIUS * math.sqrt(3)
            )  # Ajusté pour les carrés
            y = (y - (WINDOW_HEIGHT // 2 - VERTICAL_OFFSET)) / (
                HEX_RADIUS * math.sqrt(3)
            )  # Ajusté pour les carrés
            q = x
            r = y
            return round(q), round(r)

    def draw_possible_moves(self, screen, possible_moves):
        """Dessine les mouvements possibles sur l'écran."""
        if self.rl:
            return
        for q, r in possible_moves:
            x, y = self.hex_to_pixel(q, r)
            pygame.draw.circle(screen, (100, 100, 100), (int(x), int(y)), 10)

    def get_player_of_color(self, color):
        """Retourne le joueur correspondant à la couleur donnée."""
        for player in self.players:
            if player.color == color:
                return player
        return None  # Retourne None si aucun joueur ne correspond à la couleur

    def animate_move(self, screen, piece, start_q, start_r, end_q, end_r):
        if self.rl:
            return
        frames = 30  # Nombre de frames pour l'animation
        logging.debug(
            f"Animation de déplacement de {piece.piece_class} {piece.name} de {start_q},{start_r} à {end_q},{end_r}"
        )

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
            x, y = self.hex_to_pixel(current_q, current_r)
            pygame.draw.circle(screen, piece.color, (int(x), int(y)), PIECE_RADIUS)
            if piece.class_image:
                class_image_rect = piece.class_image.get_rect(center=(int(x), int(y)))
                screen.blit(piece.class_image, class_image_rect)

            # Dessiner l'ordre des joueurs avec l'animation de la flèche
            draw_player_turn(
                screen, self.players, current_player_index, next_player_index, t
            )

            pygame.display.flip()
            pygame.time.wait(5)  # Attendre 5ms entre chaque frame

        # Remettre la pièce à sa position finale
        piece.q, piece.r = end_q, end_r

        # Redessiner une dernière fois pour s'assurer que tout est à jour
        screen.fill(BLACK)
        self.draw(screen)
        draw_player_turn(screen, self.players, next_player_index)
        pygame.display.flip()

    def update_all_scores(self):
        for player in self.players:
            player.compute_score(self)
        for player in self.players:
            player.compute_relative_score(self)

    def handle_client_move(
        self, player_color, selected_pos, destination_pos, captured_piece_pos=None
    ):
        """
        Gère le mouvement d'un client.

        :param player_color: La couleur du joueur qui fait le mouvement
        :param selected_pos: Tuple (q, r) de la position de la pièce sélectionnée
        :param destination_pos: Tuple (q, r) de la destination de la pièce
        :param captured_piece_pos: Tuple (q, r) optionnel pour la position de la pièce capturée
        :return: Boolean indiquant si le mouvement a été effectué avec succès
        """
        # Vérifier si c'est le tour du joueur
        current_player = self.players[self.current_player_index]
        if tuple(current_player.color) != tuple(self.colors[player_color]):
            logging.debug(
                f"Ce n'est pas le tour du joueur {tuple(self.colors[player_color])} mais du joueur {tuple(current_player.color)}"
            )
            return False

        # Sélectionner la pièce
        selected_piece = self.get_piece_at(*selected_pos)
        if not selected_piece or tuple(selected_piece.color) != tuple(
            self.colors[player_color]
        ):
            logging.debug(f"Pièce invalide sélectionnée à {selected_pos}")
            return False

        # Vérifier si le mouvement est valide
        if destination_pos not in self.get_possible_moves(selected_piece):
            logging.debug(f"Mouvement invalide de {selected_pos} à {destination_pos}")
            return False

        # Effectuer le mouvement
        success = self.move_piece(selected_piece, *destination_pos)
        if not success:
            logging.debug(f"Échec du déplacement de {selected_pos} à {destination_pos}")
            return False

        # Gérer la pièce capturée si nécessaire
        if self.piece_to_place and captured_piece_pos:
            if not self.place_dead_piece(*captured_piece_pos):
                logging.debug(
                    f"Échec du placement de la pièce capturée à {captured_piece_pos}"
                )
                return False

        # Si tout s'est bien passé, passer au joueur suivant
        # self.next_player() // there is probably another next player somewhere else, idk where
        return True

    def send_state(self):
        """
        Prépare et renvoie l'état actuel du plateau sous forme de chaîne JSON.
        """
        return {
            "pieces": [
                {
                    "q": piece.q,
                    "r": piece.r,
                    "color": self.color_reverse[piece.color],
                    "piece_class": piece.piece_class,
                    "is_dead": piece.is_dead,
                }
                for piece in self.pieces
            ],
            "current_player_index": self.current_player_index,  # not adapted to chief in the center
            "current_player_color": self.color_reverse[
                self.players[self.current_player_index].color
            ],
            "players": [
                {
                    "color": self.color_reverse[player.color],
                    "name": " ",
                    "score": player.score,
                    "relative_score": player.relative_score,
                }
                for player in self.players
            ],
            "piece_to_place": {
                "q": self.piece_to_place.q,
                "r": self.piece_to_place.r,
                "color": self.color_reverse[self.piece_to_place.color],
                "piece_class": self.piece_to_place.piece_class,
                "is_dead": self.piece_to_place.is_dead,
            }
            if self.piece_to_place
            else None,
            "available_cells": self.available_cells,
        }
