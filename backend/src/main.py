import logging
import sys

import pygame

from .animation import draw_button, draw_legend, draw_player_turn
from .board import Board
from .constants import *

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Add function to process arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Choose game parameters.")
    parser.add_argument(
        "--nb_player_mode",
        type=int,
        choices=[3, 4, 6],
        default=3,
        help="Number of players (3, 4 or 6)",
    )
    return parser.parse_args()


def main():
    # Getting the arguments
    args = parse_arguments()
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Djambi")
    clock = pygame.time.Clock()
    current_player_index = 0
    board = Board(args.nb_player_mode, current_player_index)

    # Initialize the font for text
    pygame.font.init()
    font = pygame.font.Font(None, FONT_SIZE)

    # Main game loop
    running = True
    game_over = False
    winner = None
    selected_piece = None
    possible_moves: list[tuple[int, int]] = []
    auto_play = False

    # Define the button dimensions and position
    button_width, button_height = 200, 50
    button_x = (WINDOW_WIDTH - button_width) // 2
    button_y = WINDOW_HEIGHT // 2 + 50

    while running:
        screen.fill(BLACK)

        # Check events (close the window or press 'Esc' key)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Clear possible moves on each key press
                selected_piece = None
                possible_moves = []
                board.piece_to_place = None
                board.available_cells = []

                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and not game_over and not auto_play:
                    board.players[board.current_player_index].play_turn(board)
                    board.next_player()
                elif event.key == pygame.K_LSHIFT and not game_over and not auto_play:
                    board.players[board.current_player_index].think_and_play_turn(board)
                    board.next_player()
                elif event.key == pygame.K_RETURN:
                    auto_play = not auto_play  # Toggle auto_play state
                elif event.key == pygame.K_LEFT:  # Left arrow to undo
                    new_index = board.undo()
                    if new_index is not None:
                        board.current_player_index = new_index
                elif event.key == pygame.K_RIGHT:  # Right arrow to redo
                    new_index = board.redo()
                    if new_index is not None:
                        board.current_player_index = new_index
            elif (
                event.type == pygame.MOUSEBUTTONDOWN and not game_over and not auto_play
            ):
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

        # Check if only one player remains
        if len(board.players) == 1 and not game_over:
            game_over = True
            winner = board.players[0]
            auto_play = False

        if not game_over:
            if auto_play:
                board.players[board.current_player_index].play_turn(board)
                board.next_player()  # Use the new method here as well

            # Get the current player
            current_player = board.players[board.current_player_index]
            draw_player_turn(screen, board.players, board.current_player_index)

            # Draw the board and pieces
            board.draw(screen, selected_piece, board.piece_to_place)
            if selected_piece and not auto_play:
                board.draw_possible_moves(screen, possible_moves)
            if board.piece_to_place and not auto_play:
                board.draw_available_cells(screen)

            # Add the legend
            draw_legend(screen)
        else:
            # Display the victory message
            if winner is not None:
                win_text = font.render(f"Player {winner.color} has won!", True, WHITE)
                win_rect = win_text.get_rect(
                    center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3)
                )
                screen.blit(win_text, win_rect)

            # Draw the "Play Again" button
            draw_button(
                screen,
                "Play Again",
                button_x,
                button_y,
                button_width,
                button_height,
                WHITE,
                BLACK,
            )

            # Check if the "Play Again" button is clicked
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if (
                    button_x <= mouse_x <= button_x + button_width
                    and button_y <= mouse_y <= button_y + button_height
                ):
                    # Reset the game
                    current_player_index = 4
                    board = Board(current_player_index)
                    game_over = False
                    winner = None
                    selected_piece = None
                    possible_moves = []
                    auto_play = False

        # Display "Player's turn" with the current player's token or victory message
        pygame.display.flip()
        clock.tick(30)

    # Quit properly
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
