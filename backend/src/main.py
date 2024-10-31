import pygame
import sys
import logging
from constants import *
from board import Board
from animation import draw_player_turn, draw_legend, draw_button

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
                    board.next_player()
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

