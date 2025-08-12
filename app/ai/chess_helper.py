# Chess Helper Module
# Provides intelligent chess move suggestions and analysis using python-chess

import chess
import logging
import random
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

def get_smart_move_suggestions(fen: str, num_suggestions: int = 5) -> List[str]:
    """
    Get intelligent move suggestions for a chess position using chess engine principles

    Args:
        fen: The current board position in FEN notation
        num_suggestions: Number of move suggestions to return

    Returns:
        List of UCI format moves ranked by chess principles
    """
    try:
        board = chess.Board(fen)
        legal_moves = list(board.legal_moves)

        if not legal_moves:
            logger.warning("No legal moves available")
            return []

        # Score moves based on chess principles
        scored_moves = []

        for move in legal_moves:
            score = 0

            # Get the moving piece BEFORE making the move
            moving_piece = board.piece_at(move.from_square)

            # Capture bonus (check before making the move)
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                piece_values = {
                    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
                }
                score += piece_values.get(captured_piece.piece_type, 0) * 10

            # Make the move temporarily to analyze
            board.push(move)

            # Check bonus
            if board.is_check():
                score += 15

            # Checkmate bonus
            if board.is_checkmate():
                score += 1000

            # Piece development (knights and bishops to center)
            piece = board.piece_at(move.to_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                # Center squares
                center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
                extended_center = [chess.C3, chess.C4, chess.C5, chess.C6,
                                 chess.D3, chess.D6, chess.E3, chess.E6,
                                 chess.F3, chess.F4, chess.F5, chess.F6]

                if move.to_square in center_squares:
                    score += 8
                elif move.to_square in extended_center:
                    score += 4

            # MAJOR BONUS: Central pawn moves in opening
            if moving_piece and moving_piece.piece_type == chess.PAWN and move_count < 8:
                # Prioritize e2-e4, d2-d4, e7-e5, d7-d5
                central_pawn_moves = ["e2e4", "d2d4", "e7e5", "d7d5"]
                if move.uci() in central_pawn_moves:
                    score += 25
                    logger.debug(f"Major bonus for central pawn move: {move.uci()}")

            # MAJOR PENALTY: Premature pawn storms before development
            if moving_piece and moving_piece.piece_type == chess.PAWN and move_count < 12:
                # Penalize wing pawn moves (a,b,g,h files) before pieces are developed
                wing_pawn_files = [0, 1, 6, 7]  # a, b, g, h files
                if chess.square_file(move.to_square) in wing_pawn_files:
                    # Count developed pieces (not on starting squares)
                    starting_squares_white = {chess.A1, chess.B1, chess.C1, chess.D1, chess.E1, chess.F1, chess.G1, chess.H1}
                    starting_squares_black = {chess.A8, chess.B8, chess.C8, chess.D8, chess.E8, chess.F8, chess.G8, chess.H8}

                    developed_pieces = 0
                    for square in chess.SQUARES:
                        piece = board.piece_at(square)
                        if piece and piece.color == board.turn:
                            starting_squares = starting_squares_white if piece.color == chess.WHITE else starting_squares_black
                            if square not in starting_squares and piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                                developed_pieces += 1

                    if developed_pieces < 2:  # Less than 2 pieces developed
                        score -= 25
                        logger.debug(f"Heavy penalty for premature pawn storm: {move.uci()} with only {developed_pieces} pieces developed")

            # MAJOR BONUS: Castling (king safety is critical)
            if board.is_castling(move):
                score += 20
                logger.debug(f"Major bonus for castling: {move.uci()}")

            # BONUS: Moves that help enable castling
            if moving_piece and not board.has_castling_rights(board.turn) == False:  # If castling is still possible
                if moving_piece.piece_type in [chess.KNIGHT, chess.BISHOP] and move_count < 8:
                    # Check if this move clears a path for castling
                    castling_squares_white = {chess.F1, chess.G1, chess.B1, chess.C1, chess.D1}
                    castling_squares_black = {chess.F8, chess.G8, chess.B8, chess.C8, chess.D8}
                    castling_squares = castling_squares_white if moving_piece.color == chess.WHITE else castling_squares_black

                    if move.from_square in castling_squares:
                        score += 8
                        logger.debug(f"Bonus for clearing castling path: {move.uci()}")

            # Pawn promotion bonus
            if move.promotion:
                promotion_values = {
                    chess.QUEEN: 20, chess.ROOK: 10,
                    chess.BISHOP: 6, chess.KNIGHT: 6
                }
                score += promotion_values.get(move.promotion, 0)

            # Penalize dangerous moves
            if moving_piece:
                # Penalize early queen moves (before move 6)
                move_count = len(board.move_stack)
                if moving_piece.piece_type == chess.QUEEN and move_count < 6:
                    score -= 15
                    logger.debug(f"Penalizing early queen move {move.uci()} at move {move_count}")

                # Penalize moving the same piece twice in opening (before move 8)
                if move_count < 8:
                    previous_moves = [m for m in board.move_stack[-4:] if board.piece_at(m.from_square) and board.piece_at(m.from_square).piece_type == moving_piece.piece_type]
                    if len(previous_moves) > 0:
                        score -= 8
                        logger.debug(f"Penalizing repeated piece movement: {move.uci()}")

                # Penalize king moves in opening (unless castling)
                if moving_piece.piece_type == chess.KING and move_count < 10 and not board.is_castling(move):
                    score -= 20
                    logger.debug(f"Penalizing early king move: {move.uci()}")

                # HEAVY penalty for knight shuffling (moving to a square it just left)
                if moving_piece.piece_type == chess.KNIGHT and move_count > 2:
                    recent_moves = board.move_stack[-4:] if len(board.move_stack) >= 4 else board.move_stack
                    for recent_move in recent_moves:
                        if recent_move.to_square == move.from_square:
                            score -= 30
                            logger.debug(f"Heavy penalty for knight shuffling: {move.uci()}")
                            break

                # Penalty for moving pieces without purpose in opening
                if move_count < 12 and moving_piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                    # If the piece is already developed, penalize moving it again
                    developed_squares_white = {chess.F3, chess.F4, chess.F5, chess.E3, chess.E4, chess.E5,
                                             chess.D3, chess.D4, chess.D5, chess.C3, chess.C4, chess.C5}
                    developed_squares_black = {chess.F6, chess.F5, chess.F4, chess.E6, chess.E5, chess.E4,
                                             chess.D6, chess.D5, chess.D4, chess.C6, chess.C5, chess.C4}
                    developed_squares = developed_squares_white if moving_piece.color == chess.WHITE else developed_squares_black

                    if move.from_square in developed_squares:
                        score -= 12
                        logger.debug(f"Penalizing redevelopment: {move.uci()}")

                # PENALTY: Too many pawn moves without developing pieces
                if moving_piece.piece_type == chess.PAWN and move_count < 12:
                    # Count pawn moves vs piece development moves in recent history
                    recent_moves = board.move_stack[-6:] if len(board.move_stack) >= 6 else board.move_stack
                    pawn_moves = 0
                    development_moves = 0

                    for i, recent_move in enumerate(recent_moves):
                        if i % 2 == (0 if board.turn == chess.WHITE else 1):  # Same color as current player
                            piece_moved = board.piece_at(recent_move.to_square)
                            if piece_moved:
                                if piece_moved.piece_type == chess.PAWN:
                                    pawn_moves += 1
                                elif piece_moved.piece_type in [chess.KNIGHT, chess.BISHOP]:
                                    development_moves += 1

                    if pawn_moves >= 3 and development_moves <= 1:
                        score -= 15
                        logger.debug(f"Penalizing excessive pawn moves without development: {move.uci()}")

                # Bonus for developing new pieces in opening
                if move_count < 12:
                    starting_squares_white = {chess.B1, chess.C1, chess.F1, chess.G1}  # Knights and bishops
                    starting_squares_black = {chess.B8, chess.C8, chess.F8, chess.G8}
                    starting_squares = starting_squares_white if moving_piece.color == chess.WHITE else starting_squares_black

                    if move.from_square in starting_squares and moving_piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                        score += 6
                        logger.debug(f"Bonus for developing piece: {move.uci()}")

            # Avoid moving into attack - evaluate before making the move
            piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100}
            moving_piece_value = piece_values.get(moving_piece.piece_type, 1) if moving_piece else 1

            if board.is_attacked_by(not board.turn, move.to_square):
                # Only penalize if we're moving into danger without capturing
                if not captured_piece or moving_piece_value > piece_values.get(captured_piece.piece_type, 0):
                    score -= moving_piece_value * 3
                    logger.debug(f"Penalizing dangerous move: {move.uci()}")

            # Undo the move
            board.pop()

            scored_moves.append((move.uci(), score))

        # Sort by score (descending) and return top suggestions
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        top_moves = [move[0] for move in scored_moves[:num_suggestions]]

        logger.info(f"Generated {len(top_moves)} move suggestions for position")
        logger.debug(f"Top moves with scores: {scored_moves[:num_suggestions]}")

        return top_moves

    except Exception as e:
        logger.error(f"Error generating move suggestions: {e}")
        # Fallback to random legal moves
        try:
            board = chess.Board(fen)
            legal_moves = [move.uci() for move in board.legal_moves]
            return random.sample(legal_moves, min(num_suggestions, len(legal_moves)))
        except:
            return []

def validate_and_suggest_similar_move(move_uci: str, fen: str) -> Optional[str]:
    """
    Validate a move and suggest a similar legal move if invalid

    Args:
        move_uci: The move in UCI format to validate
        fen: The current board position

    Returns:
        Valid UCI move or None if no similar move found
    """
    try:
        board = chess.Board(fen)

        # Try the move as-is first
        try:
            move = chess.Move.from_uci(move_uci)
            if move in board.legal_moves:
                logger.debug(f"Move {move_uci} is valid")
                return move_uci
        except:
            pass

        # If invalid, try to find similar moves
        logger.warning(f"Move {move_uci} is invalid, searching for alternatives")

        if len(move_uci) >= 4:
            from_square = move_uci[:2]
            to_square = move_uci[2:4]

            # Look for moves from the same square
            for legal_move in board.legal_moves:
                legal_uci = legal_move.uci()
                if legal_uci.startswith(from_square):
                    logger.info(f"Found similar move: {legal_uci} (from same square as {move_uci})")
                    return legal_uci

            # Look for moves to the same square
            for legal_move in board.legal_moves:
                legal_uci = legal_move.uci()
                if legal_uci[2:4] == to_square:
                    logger.info(f"Found similar move: {legal_uci} (to same square as {move_uci})")
                    return legal_uci

        # Last resort: return a good move from suggestions
        suggestions = get_smart_move_suggestions(fen, 1)
        if suggestions:
            logger.info(f"Using smart suggestion {suggestions[0]} instead of invalid {move_uci}")
            return suggestions[0]

        return None

    except Exception as e:
        logger.error(f"Error validating move {move_uci}: {e}")
        return None

def get_position_description(fen: str) -> str:
    """
    Get a human-readable description of the chess position

    Args:
        fen: The board position in FEN notation

    Returns:
        String description of the position
    """
    try:
        board = chess.Board(fen)

        # Basic position info
        turn = "White" if board.turn == chess.WHITE else "Black"
        move_number = board.fullmove_number

        # Count pieces
        white_pieces = len(board.piece_map()) - len([p for p in board.piece_map().values() if not p.color])
        black_pieces = len([p for p in board.piece_map().values() if not p.color])

        # Game phase
        total_pieces = len(board.piece_map())
        if total_pieces > 20:
            phase = "Opening"
        elif total_pieces > 12:
            phase = "Middlegame"
        else:
            phase = "Endgame"

        # Special conditions
        conditions = []
        if board.is_check():
            conditions.append("CHECK")
        if board.is_checkmate():
            conditions.append("CHECKMATE")
        if board.is_stalemate():
            conditions.append("STALEMATE")
        if board.has_castling_rights(chess.WHITE):
            if board.castling_rights & chess.BB_H1:
                conditions.append("White can castle kingside")
            if board.castling_rights & chess.BB_A1:
                conditions.append("White can castle queenside")
        if board.has_castling_rights(chess.BLACK):
            if board.castling_rights & chess.BB_H8:
                conditions.append("Black can castle kingside")
            if board.castling_rights & chess.BB_A8:
                conditions.append("Black can castle queenside")

        description = f"Move {move_number}, {turn} to play, {phase} ({total_pieces} pieces)"
        if conditions:
            description += f", {', '.join(conditions)}"

        return description

    except Exception as e:
        logger.error(f"Error describing position: {e}")
        return f"FEN: {fen}"

def analyze_threats_and_opportunities(fen: str) -> dict:
    """
    Analyze the current position for threats and opportunities

    Args:
        fen: The board position in FEN notation

    Returns:
        Dictionary with analysis results
    """
    try:
        board = chess.Board(fen)
        analysis = {
            "threats": [],
            "opportunities": [],
            "tactical_motifs": []
        }

        # Check for hanging pieces
        for square, piece in board.piece_map().items():
            if piece.color == board.turn:
                # Check if piece is attacked and not defended
                if board.is_attacked_by(not board.turn, square):
                    defenders = len(board.attackers(board.turn, square))
                    attackers = len(board.attackers(not board.turn, square))

                    if attackers > defenders:
                        analysis["threats"].append(f"{piece.symbol()} on {chess.square_name(square)} is hanging")

        # Look for tactical opportunities
        for move in board.legal_moves:
            board.push(move)

            # Check for discovered attacks
            if board.is_check():
                analysis["opportunities"].append(f"Move {move.uci()} gives check")

            # Check for forks (attacking multiple pieces)
            attacking_squares = []
            for square in chess.SQUARES:
                if board.is_attacked_by(board.turn, square):
                    piece = board.piece_at(square)
                    if piece and piece.color != board.turn:
                        attacking_squares.append(square)

            if len(attacking_squares) >= 2:
                analysis["tactical_motifs"].append(f"Move {move.uci()} creates fork")

            board.pop()

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing position: {e}")
        return {"threats": [], "opportunities": [], "tactical_motifs": []}
