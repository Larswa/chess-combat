# Move Validator: Uses python-chess to validate moves
import chess

def validate_move(board_fen, move_uci):
    board = chess.Board(board_fen)
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            return True
        return False
    except Exception:
        return False
