import random
import copy
import logging
from player import Player

class MinMaxPlayer(Player):
    def __init__(self, color, pieces, depth=1):
        super().__init__(color, pieces)
        self.depth = depth

    def think_and_play_turn(self, board):
        """Joue un tour en utilisant l'algorithme MinMax avec élagage alpha-beta."""
        best_move = self.alpha_beta(board, self.depth, float('-inf'), float('inf'))[1]
        if best_move:
            piece, move = best_move
            piece.move(move[0], move[1], board)
            logging.info(f"MinMax a joué : {piece.piece_class} de ({piece.q}, {piece.r}) à {move}, eval: {self.evaluate_board(board)}")


    def get_best_moves(self): # should go in minmax class
        best_moves = {}
        for piece in self.pieces:
            for move, info in piece.opportunity_moves.items():
                score = info['victim_value'] - info['protected_value'] * piece.std_value
                if score > 0:
                    best_moves[move] = score
        best_moves = sorted(best_moves, key=lambda x: x.value, reverse=True)
        print(best_moves)
        return list(best_moves)


    def alpha_beta(self, board, depth, alpha, beta):
        if depth == 0:
            return self.evaluate_board(board), None

        best_moves = self.get_best_moves()
        if not best_moves:
            valid_moves = self.get_all_valid_moves(board)
            if not valid_moves:
                return self.evaluate_board(board), None
            best_moves = [random.choice(valid_moves)]

        logging.info(f'there is {len(best_moves)} good moves for {self.color}')

        max_eval = float('-inf')
        best_move = None
        for piece, move in best_moves:  # Utilisation des coups triés
                new_board = self.copy_board_state(board)
                new_piece = new_board.pieces_by_pos[(piece.q, piece.r)]
                new_piece.move(move[0], move[1], new_board)
                new_board.next_player()
                next_player = new_board.players[new_board.current_player_index]
                eval = -next_player.alpha_beta(new_board, depth - 1, -beta, -alpha)[0]  # Négamax
                if eval > max_eval:
                    max_eval = eval
                    best_move = (piece, move)
                    logging.info(f"max_eval: {max_eval}, best_move: {best_move}")
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
        return max_eval, best_move


    def evaluate_board(self, board):
        """Évalue le plateau en fonction de la différence de score relatif."""
        board.update_all_scores()
        print([player.relative_score for player in board.players])
        return self.relative_score

    def copy_board_state(self, board):
        """Crée une copie légère du plateau avec seulement les données nécessaires pour MinMax."""
        new_board = type(board)()
        
        new_pieces = [self.copy_piece(p) for p in board.pieces]
        new_board.pieces = new_pieces
        new_board.pieces_by_pos = {(p.q, p.r): p for p in new_pieces}
        
        pieces_by_color = {}
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
        """Crée une copie d'une pièce avec seulement les attributs essentiels."""
        # Créer une nouvelle instance avec tous les arguments requis
        new_piece = type(piece)(
            q=piece.q,
            r=piece.r,
            color=piece.color,
            piece_class=piece.piece_class,
            svg_path=piece.svg_path if hasattr(piece, 'svg_path') else None,
        )
        new_piece.is_dead = piece.is_dead
        return new_piece
    
    
