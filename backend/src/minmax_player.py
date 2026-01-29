import copy
import logging
import random

from backend.src.player import Player


class MinMaxPlayer(Player):
    def __init__(self, color, pieces, depth=1):
        super().__init__(color, pieces)
        self.depth = depth

    def think_and_play_turn(self, board):
        """Plays a turn using the MinMax algorithm with alpha-beta pruning."""
        best_move = self.alpha_beta(board, self.depth, float("-inf"), float("inf"))[1]
        if best_move:
            piece, move = best_move
            piece.move(move[0], move[1], board)
            logging.info(
                f"MinMax played: {piece.piece_class} from ({piece.q}, {piece.r}) to {move}, eval: {self.evaluate_board(board)}"
            )

    def get_best_moves(self, board):  # should go in minmax class
        best_moves: dict[tuple, float] = {}
        for piece in self.pieces:
            best_moves.update(piece.update_piece_best_moves(board))
        best_moves_sorted = sorted(best_moves.items(), key=lambda x: x[1], reverse=True)
        print(best_moves_sorted)
        return [
            move[0] for move in best_moves_sorted
        ]  # Returns only the tuples (piece, move)

    def alpha_beta(self, board, depth, alpha, beta):
        if depth == 0:
            return self.evaluate_board(board), None

        best_moves = self.get_best_moves(board)
        if not best_moves:
            valid_moves = self.get_all_valid_moves(board)
            if not valid_moves:
                return self.evaluate_board(board), None
            best_moves = [random.choice(valid_moves)]

        logging.info(f"there is {len(best_moves)} good moves for {self.color}")

        max_eval = float("-inf")
        best_move = None
        for piece, move in best_moves:  # Use sorted moves
            new_board = self.copy_board_state(board)
            new_piece = new_board.pieces_by_pos[(piece.q, piece.r)]
            new_piece.move(move[0], move[1], new_board)
            new_board.next_player()
            next_player = new_board.players[new_board.current_player_index]
            eval = -next_player.alpha_beta(new_board, depth - 1, -beta, -alpha)[
                0
            ]  # Negamax
            if eval > max_eval:
                max_eval = eval
                best_move = (piece, move)
                logging.info(f"max_eval: {max_eval}, best_move: {best_move}")
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move

    def evaluate_board(self, board):
        """Evaluates the board based on the relative score difference."""
        board.update_all_scores()
        print([player.relative_score for player in board.players])
        return self.relative_score

    def copy_board_state(self, board):
        """Creates a lightweight copy of the board with only the data needed for MinMax."""
        new_board = type(board)()

        new_pieces = [self.copy_piece(p) for p in board.pieces]
        new_board.pieces = new_pieces
        new_board.pieces_by_pos = {(p.q, p.r): p for p in new_pieces}

        pieces_by_color: dict[tuple[int, int, int], list] = {}
        for piece in new_pieces:
            pieces_by_color.setdefault(piece.color, []).append(piece)

        new_board.players = [
            type(player)(player.color, pieces_by_color[player.color])
            for player in board.players
        ]

        new_board.current_player_index = board.current_player_index
        new_board.rl = True
        return new_board

    def copy_piece(self, piece):
        """Creates a copy of a piece with only the essential attributes."""
        # Create a new instance with all required arguments
        new_piece = type(piece)(
            q=piece.q,
            r=piece.r,
            color=piece.color,
            piece_class=piece.piece_class,
            svg_path=piece.svg_path if hasattr(piece, "svg_path") else None,
        )
        new_piece.is_dead = piece.is_dead
        return new_piece
