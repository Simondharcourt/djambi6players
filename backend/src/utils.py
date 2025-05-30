





def get_colors(nb_players):
    if nb_players == 6:
        colors = {
        "yellow": (255, 255, 0),
        "pink": (255, 105, 180),
        "red": (255, 0, 0),
        "blue": (0, 0, 255),
        "purple": (128, 0, 128),
        "green": (0, 255, 0),
        }
        names = {
            (128, 0, 128): "Violet",
            (0, 0, 255): "Bleu",
            (255, 0, 0): "Rouge",
            (255, 105, 180): "Rose",
            (255, 255, 0): "Jaune",
            (0, 255, 0): "Vert",
            (100, 100, 100): "Mort",
        }
    elif nb_players == 3:
        colors = {
            "yellow": (255, 255, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
        }
        names = {
            (255, 0, 0): "Rouge",
            (255, 255, 0): "Jaune",
            (0, 255, 0): "Vert",
            (100, 100, 100): "Mort",
        }
    elif nb_players == 4:
        colors = {
            "yellow": (255, 255, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "red": (255, 0, 0),
        }

        names = {
            (0, 0, 255): "Bleu",
            (255, 0, 0): "Rouge",
            (255, 255, 0): "Jaune",
            (0, 255, 0): "Vert",
            (100, 100, 100): "Mort",
        }
    all_colors = {**colors, "white": (255, 255, 255), "grey": (100, 100, 100)}
    color_reverse = {v: k for k, v in all_colors.items()}
    return colors, color_reverse, names


def get_start_positions(nb_players):
    if nb_players == 6:
        return [
            # Pièces violettes (en bas à gauche)
            (-5, -1, "purple", "assassin"),
            (-4, -2, "purple", "militant"),
            (-6, 0, "purple", "chief"),
            (-4, -1, "purple", "militant"),
            (-5, 0, "purple", "diplomat"),
            (-4, 0, "purple", "necromobile"),
            (-5, 1, "purple", "militant"),
            (-6, 1, "purple", "reporter"),
            (-6, 2, "purple", "militant"),
            # Pièces bleues (en haut)
            (0, -6, "blue", "chief"),
            (1, -6, "blue", "reporter"),
            (2, -6, "blue", "militant"),
            (0, -5, "blue", "diplomat"),
            (-1, -4, "blue", "militant"),
            (-2, -4, "blue", "militant"),
            (0, -4, "blue", "necromobile"),
            (1, -5, "blue", "militant"),
            (-1, -5, "blue", "assassin"),
            # # Pièces rouges (en bas à droite)
            (6, -4, "red", "militant"),
            (6, -5, "red", "assassin"),
            (6, -6, "red", "chief"),
            (5, -6, "red", "reporter"),
            (4, -6, "red", "militant"),
            (5, -5, "red", "diplomat"),
            (4, -4, "red", "necromobile"),
            (4, -5, "red", "militant"),
            (5, -4, "red", "militant"),
            # Pièces roses (en haut à droite)
            (6, -2, "pink", "militant"),
            (5, -1, "pink", "militant"),
            (6, -1, "pink", "assassin"),
            (4, 2, "pink", "militant"),
            (5, 0, "pink", "diplomat"),
            (4, 0, "pink", "necromobile"),
            (6, 0, "pink", "chief"),
            (5, 1, "pink", "reporter"),
            (4, 1, "pink", "militant"),
            # Pièces jaunes (en bas)
            (0, 5, "yellow", "diplomat"),
            (-1, 5, "yellow", "militant"),
            (-2, 6, "yellow", "militant"),
            (-1, 6, "yellow", "assassin"),
            (1, 5, "yellow", "reporter"),
            (0, 6, "yellow", "chief"),
            (0, 4, "yellow", "necromobile"),
            (2, 4, "yellow", "militant"),
            (1, 4, "yellow", "militant"),
            # Pièces vertes (en haut à gauche)
            (-5, 6, "green", "assassin"),
            (-4, 6, "green", "militant"),
            (-6, 6, "green", "chief"),
            (-6, 5, "green", "reporter"),
            (-6, 4, "green", "militant"),
            (-5, 5, "green", "diplomat"),
            (-4, 5, "green", "militant"),
            (-5, 4, "green", "militant"),
            (-4, 4, "green", "necromobile"),
        ]
    elif nb_players == 3:
        return [
            # Pièces violettes (en bas à gauche)
            (-3, -1, "green", "assassin"),
            (-2, -2, "green", "militant"),
            (-4, 0, "green", "chief"),
            (-2, -1, "green", "militant"),
            (-3, 0, "green", "diplomat"),
            (-2, 0, "green", "necromobile"),
            (-3, 1, "green", "militant"),
            (-4, 1, "green", "reporter"),
            (-4, 2, "green", "militant"),
            # # Pièces rouges (en bas à droite)
            (4, -2, "red", "militant"),
            (4, -3, "red", "assassin"),
            (4, -4, "red", "chief"),
            (3, -4, "red", "reporter"),
            (2, -4, "red", "militant"),
            (3, -3, "red", "diplomat"),
            (2, -2, "red", "necromobile"),
            (2, -3, "red", "militant"),
            (3, -2, "red", "militant"),
            # Pièces jaunes (en bas)
            (0, 3, "yellow", "diplomat"),
            (-1, 3, "yellow", "militant"),
            (-2, 4, "yellow", "militant"),
            (-1, 4, "yellow", "assassin"),
            (1, 3, "yellow", "reporter"),
            (0, 4, "yellow", "chief"),
            (0, 2, "yellow", "necromobile"),
            (2, 2, "yellow", "militant"),
            (1, 2, "yellow", "militant"),
        ]
    elif nb_players == 4:
        return [
            # Pièces violettes (en bas à gauche)
            (-3, 4, "yellow", "assassin"),
            (-2, 4, "yellow", "militant"),
            (-4, 4, "yellow", "chief"),
            (-4, 3, "yellow", "reporter"),
            (-4, 2, "yellow", "militant"),
            (-3, 3, "yellow", "diplomat"),
            (-2, 3, "yellow", "militant"),
            (-3, 2, "yellow", "militant"),
            (-2, 2, "yellow", "necromobile"),
            (4, -2, "blue", "militant"),
            (4, -3, "blue", "assassin"),
            (4, -4, "blue", "chief"),
            (3, -4, "blue", "reporter"),
            (2, -4, "blue", "militant"),
            (3, -3, "blue", "diplomat"),
            (2, -2, "blue", "necromobile"),
            (2, -3, "blue", "militant"),
            (3, -2, "blue", "militant"),
            (4, 2, "green", "militant"),
            (4, 3, "green", "assassin"),
            (4, 4, "green", "chief"),
            (3, 4, "green", "reporter"),
            (2, 4, "green", "militant"),
            (3, 3, "green", "diplomat"),
            (2, 2, "green", "necromobile"),
            (2, 3, "green", "militant"),
            (3, 2, "green", "militant"),
            (-4, -2, "red", "militant"),
            (-4, -3, "red", "assassin"),
            (-4, -4, "red", "chief"),
            (-3, -4, "red", "reporter"),
            (-2, -4, "red", "militant"),
            (-3, -3, "red", "diplomat"),
            (-2, -2, "red", "necromobile"),
            (-2, -3, "red", "militant"),
            (-3, -2, "red", "militant"),
        ]



def get_directions(nb_players):
    if nb_players == 6:
        adjacent_directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, -1),
            (-1, 1),  # Directions existantes
        ]
        diag_directions = [
            (2, -1),
            (1, -2),
            (-1, -1),
            (-2, 1),
            (-1, 2),
            (1, 1),  # Nouvelles directions diagonales
        ]

    elif nb_players == 3:
        adjacent_directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, -1),
            (-1, 1),  # Directions existantes
        ]
        diag_directions = []

    elif nb_players == 4:
        adjacent_directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        diag_directions = [(1, -1), (1, 1), (-1, -1), (-1, 1)]

    all_directions = adjacent_directions + diag_directions
    return {
        "adjacent": adjacent_directions,
        "diagonal": diag_directions,
        "all": all_directions
    }
