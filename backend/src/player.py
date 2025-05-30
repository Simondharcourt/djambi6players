import random


class Player:
    def __init__(self, color, pieces):
        self.color = color
        names = {
            (128, 0, 128): "Violet",
            (0, 0, 255): "Bleu",
            (255, 0, 0): "Rouge",
            (255, 105, 180): "Rose",
            (255, 255, 0): "Jaune",
            (0, 255, 0): "Vert",
        }
        self.name = names[color]
        self.pieces = pieces
        self.score = 0
        self.relative_score = 0
        self.threat_score = 0

    def compute_score(self, board):
        """Calcule le score actuel du joueur en fonction des pièces qu'il possède."""
        piece_values = {
            "militant": 60,
            "assassin": 120,
            "chief": 180,
            "diplomat": 120,
            "necromobile": 120,
            "reporter": 120,
        }
        score = sum(
            piece_values[piece.piece_class]
            for piece in self.pieces
            if not piece.is_dead
        )
        if any(
            piece.piece_class == "chief" and not piece.is_dead and piece.on_central_cell
            for piece in self.pieces
        ):
            score += (score - 180) * (
                len([player for player in board.players if player.color != self.color])
                - 1
            )

        self.score = score + self.evaluate_threat_score(board)

    def compute_relative_score(self, board):
        self.relative_score = (
            self.score * 600 // sum(player.score for player in list(set(board.players)))
        )
        return self.relative_score

    def evaluate_threat_score(self, board):
        threat_score = 0
        for piece in self.pieces:
            threat_score += piece.evaluate_threat_score(board)
        self.threat_score = threat_score
        return threat_score

    def get_all_valid_moves(self, board):
        all_moves = []
        for piece in self.pieces:
            moves = piece.all_possible_moves(board)
            if moves:
                all_moves.extend([(piece, move) for move in moves])
        return all_moves

    def play_turn(self, board):
        """Joue un tour : déplace une de ses pièces aléatoirement parmi les mouvements possibles."""
        all_moves = self.get_all_valid_moves(board)

        if not all_moves:
            return

        piece, move = random.choice(all_moves)
        piece.move(move[0], move[1], board)

    def change_color(self, new_color):
        self.color = new_color
        for piece in self.pieces:
            piece.color = new_color

    def remove_piece(self, piece):
        self.pieces.remove(piece)

    def add_piece(self, piece):
        self.pieces.append(piece)
        piece.color = self.color
