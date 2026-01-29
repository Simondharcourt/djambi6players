import pygame

from .constants import *


def draw_player_turn(
    screen, players, current_player_index, next_player_index=None, t=None
):
    """Displays the player order with colored tokens and an animated arrow for the current player."""
    jeton_radius = 15
    spacing = 10
    start_x = 20
    start_y = 300
    arrow_size = 20
    font = pygame.font.Font(None, 36)  # Make sure to initialize the font

    for i, player in enumerate(players):
        # Token position
        x = start_x
        y = start_y + i * (jeton_radius * 2 + spacing)

        # Draw the token
        pygame.draw.circle(screen, player.color, (x, y), jeton_radius)

        # Display the score next to the token
        score_text = font.render(str(player.relative_score), True, WHITE)
        screen.blit(
            score_text, (x + jeton_radius + spacing, y - score_text.get_height() // 2)
        )

    # Draw the animated arrow
    if next_player_index is not None and t is not None:
        current_y = start_y + current_player_index * (jeton_radius * 2 + spacing)
        next_y = start_y + next_player_index * (jeton_radius * 2 + spacing)
        arrow_y = current_y + (next_y - current_y) * t
        draw_arrow(screen, start_x, arrow_y, arrow_size, jeton_radius, spacing)
    else:
        arrow_y = start_y + current_player_index * (jeton_radius * 2 + spacing)
        draw_arrow(screen, start_x, arrow_y, arrow_size, jeton_radius, spacing)


def draw_arrow(screen, x, y, arrow_size, jeton_radius, spacing):
    """Draws an arrow at the specified position."""
    offset = 60  # Offset to the right in pixels
    arrow_points = [
        (x + jeton_radius + spacing + offset, y),
        (x + jeton_radius + spacing + arrow_size + offset, y - arrow_size // 2),
        (x + jeton_radius + spacing + arrow_size + offset, y + arrow_size // 2),
    ]
    pygame.draw.polygon(screen, WHITE, arrow_points)


def draw_legend(screen):
    font = pygame.font.Font(None, FONT_SIZE)
    legend_items = [
        ("Space", "Play"),
        ("<-", "Undo"),
        ("->", "Redo"),
        ("Return", "Auto play"),
    ]

    total_width = sum(
        font.size(f"{key}: {value}")[0] for key, value in legend_items
    ) + 20 * (len(legend_items) - 1)
    start_x = (WINDOW_WIDTH - total_width) // 2
    y = WINDOW_HEIGHT - 100

    for key, value in legend_items:
        text = font.render(f"{key}: {value}", True, WHITE)
        screen.blit(text, (start_x, y))
        start_x += text.get_width() + 20  # Space between elements


def animate_player_elimination(screen, players, eliminated_player_index, board):
    jeton_radius = 15
    spacing = 10
    start_x = 20
    start_y = 300
    fall_duration = 60  # Number of frames for fall animation

    for frame in range(fall_duration):
        screen.fill(BLACK)  # Clear the screen

        # Redraw the board
        board.draw(screen)

        for i, player in enumerate(players):
            x = start_x
            y = start_y + i * (jeton_radius * 2 + spacing)

            if i == eliminated_player_index:
                # Animate the fall of the eliminated token
                fall_distance = (
                    frame / fall_duration
                ) ** 2 * WINDOW_HEIGHT  # Fall acceleration
                y = int(y + fall_distance)

            if y < WINDOW_HEIGHT:  # Only draw the token if it's still visible
                pygame.draw.circle(screen, player.color, (int(x), int(y)), jeton_radius)

        # Draw the arrow for the current player
        current_player_index = board.current_player_index % len(players)
        arrow_y = start_y + current_player_index * (jeton_radius * 2 + spacing)
        draw_arrow(screen, start_x, arrow_y, 20, jeton_radius, spacing)

        pygame.display.flip()
        pygame.time.wait(16)  # About 60 FPS


def draw_button(screen, text, x, y, width, height, color, text_color):
    pygame.draw.rect(screen, color, (x, y, width, height))
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)
