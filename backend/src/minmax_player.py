import random
import copy
import logging
from player import Player

class MinMaxPlayer(Player):
    def __init__(self, color, pieces, depth=1):
        super().__init__(color, pieces)
        self.depth = depth

    def play_turn(self, board):
        """Joue un tour en utilisant l'algorithme MinMax pour choisir le meilleur mouvement."""
        best_move = self.minmax(board, self.depth, True)[1]
        if best_move:
            piece, move = best_move
            piece.move(move[0], move[1], board)
            logging.info(f"MinMax a joué : {piece.piece_class} de ({piece.q}, {piece.r}) à {move}")

    def minmax(self, board, depth, maximizing_player):
        if depth == 0:
            return self.evaluate_board(board), None

        valid_moves = self.get_all_valid_moves(board)

        if not valid_moves:
            return self.evaluate_board(board), None

        if maximizing_player:
            max_eval = float('-inf')
            best_move = None
            for piece, moves in valid_moves:
                for move in moves:
                    new_board = self.copy_board_state(board)
                    new_piece = new_board.pieces_by_pos[(piece.q, piece.r)]
                    new_piece.move(move[0], move[1], new_board)
                    new_board.next_player()
                    next_player = new_board.players[new_board.current_player_index]
                    eval = next_player.minmax(new_board, depth - 1, False)[0]
                    print(f"eval: {eval}, max_eval: {max_eval}")
                    if eval > max_eval:
                        max_eval = eval
                        best_move = (piece, move)
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            for piece, moves in valid_moves:
                for move in moves:
                    new_board = self.copy_board_state(board)
                    new_piece = new_board.pieces_by_pos[(piece.q, piece.r)]
                    new_piece.move(move[0], move[1], new_board)
                    new_board.next_player()
                    next_player = new_board.players[new_board.current_player_index]
                    eval = next_player.minmax(new_board, depth - 1, False)[0]
                    if eval < min_eval:
                        min_eval = eval
                        best_move = (piece, move)
            return min_eval, best_move

    def evaluate_board(self, board):
        """Évalue le plateau en fonction de la différence de score relatif."""
        board.update_all_scores()
        print([player.relative_score for player in board.players])
        return self.relative_score

    def copy_board_state(self, board):
        """Crée une copie légère du plateau avec seulement les données nécessaires pour MinMax."""
        new_board = type(board)()
        new_board.pieces = [self.copy_piece(p) for p in board.pieces]
        new_board.pieces_by_pos = {(p.q, p.r): p for p in new_board.pieces}
        
        # Créer de nouveaux joueurs avec leurs pièces respectives
        new_board.players = []
        for player in board.players:
            player_pieces = [p for p in new_board.pieces if p.color == player.color]
            new_player = type(player)(player.color, player_pieces)
            new_board.players.append(new_player)
        
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
            svg_path=piece.svg_path if hasattr(piece, 'svg_path') else None
        )
        new_piece.is_dead = piece.is_dead
        return new_piece
    
    
