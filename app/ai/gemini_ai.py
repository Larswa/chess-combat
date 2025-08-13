"""
Simple Gemini AI integration for chess moves.
Just presents board state and gets move decision.
"""

import google.generativeai as genai
import os
import logging
import chess
import re

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def _analyze_position_context(board: chess.Board, move_history: list = None) -> str:
    """
    Analyze the current position to provide rich contextual awareness to the AI.
    This gives the AI situational intelligence without teaching chess rules.
    """
    context = []

    # Game phase awareness
    piece_count = len(board.piece_map())
    if piece_count > 24:
        context.append("Early game - pieces are still developing")
    elif piece_count > 12:
        context.append("Middle game - active piece maneuvering phase")
    else:
        context.append("Late game - precision and calculation critical")

    # Material balance awareness
    white_material = sum([piece.piece_type for piece in board.piece_map().values() if piece.color])
    black_material = sum([piece.piece_type for piece in board.piece_map().values() if not piece.color])
    material_diff = white_material - black_material
    if abs(material_diff) > 2:
        leader = "White" if material_diff > 0 else "Black"
        context.append(f"Material imbalance: {leader} has significant advantage")

    # King safety awareness
    white_king_square = board.king(chess.WHITE)
    black_king_square = board.king(chess.BLACK)

    if white_king_square and board.is_attacked_by(chess.BLACK, white_king_square):
        context.append("White king under direct pressure")
    if black_king_square and board.is_attacked_by(chess.WHITE, black_king_square):
        context.append("Black king under direct pressure")

    # Check status
    if board.is_check():
        context.append(f"{'White' if board.turn else 'Black'} king is in check - immediate response required")

    # Capture opportunities
    captures = [move for move in board.legal_moves if board.is_capture(move)]
    if captures:
        context.append(f"{len(captures)} capture possibilities available")

    # Center control awareness
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    controlled_by_current = sum(1 for sq in center_squares if board.is_attacked_by(board.turn, sq))
    context.append(f"You control {controlled_by_current}/4 central squares")

    # Piece mobility
    current_moves = len(list(board.legal_moves))
    board.turn = not board.turn  # Switch to opponent
    opponent_moves = len(list(board.legal_moves))
    board.turn = not board.turn  # Switch back

    if current_moves > opponent_moves + 5:
        context.append("You have significantly more piece mobility")
    elif opponent_moves > current_moves + 5:
        context.append("Opponent has significantly more piece mobility")

    # Recent activity pattern
    if move_history and len(move_history) >= 4:
        recent_moves = move_history[-4:]
        repeated_pieces = []
        for i in range(0, len(recent_moves), 2):
            if i + 2 < len(recent_moves):
                if recent_moves[i][:2] == recent_moves[i+2][:2]:
                    repeated_pieces.append(recent_moves[i][:2])
        if repeated_pieces:
            context.append(f"Recent pattern: piece on {repeated_pieces[0]} has moved multiple times")

    # Castling status
    can_castle_kingside = board.has_kingside_castling_rights(board.turn)
    can_castle_queenside = board.has_queenside_castling_rights(board.turn)
    if can_castle_kingside or can_castle_queenside:
        context.append("Castling still available for improved king safety")

    # Pawn structure insights
    pawns = [sq for sq, piece in board.piece_map().items()
             if piece.piece_type == chess.PAWN and piece.color == board.turn]
    if len(pawns) > 0:
        files = [chess.square_file(sq) for sq in pawns]
        doubled = len(files) != len(set(files))
        if doubled:
            context.append("You have doubled pawns - consider piece activity compensation")

    return " | ".join(context)

def get_gemini_chess_move(fen: str, move_history: list = None, invalid_moves: list = None) -> str:
    """
    Get a chess move from Gemini AI with enhanced situational awareness.

    Args:
        fen: Current board position in FEN notation
        move_history: List of previous moves (optional)
        invalid_moves: List of invalid moves to avoid (optional)

    Returns:
        UCI move string (e.g., "e2e4")
    """
    try:
        # Check if API key is configured
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("Gemini API key not configured")
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")

        # Create board from FEN to get current position info
        board = chess.Board(fen)

        # Enhanced situational awareness
        position_context = _analyze_position_context(board, move_history)

        # Build a comprehensive prompt with rich context
        prompt = f"""You are analyzing a chess position with complete situational awareness.

CURRENT BOARD STATE:
Position: {fen}
Turn: {"White" if board.turn else "Black"} to move

SITUATIONAL CONTEXT:
{position_context}

RECENT GAME FLOW:
{f"Last 8 moves: {' '.join(move_history[-8:])}" if move_history and len(move_history) > 0 else "Game just started"}
{f"Moves that failed: {', '.join(invalid_moves[-3:])}" if invalid_moves else "No invalid attempts"}

AVAILABLE OPTIONS:
You have {len(list(board.legal_moves))} legal moves available.

Your task: Choose the most intelligent move considering the current threats, opportunities, and position dynamics described above.

Provide your analysis and move in this exact format:
BOARD: [Your assessment of the key features and dynamics in this specific position]
MOVE: [your move in UCI notation like e2e4]

Be decisive and choose the move that best responds to the current position."""

        logger.debug(f"Gemini prompt: {prompt}")

        # Get response from Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        if not response or not response.text:
            logger.error("Gemini returned empty response")
            return None

        # Extract move from response
        move_text = response.text.strip()
        logger.info(f"Gemini full response: {move_text}")

        # Extract board description and move
        board_description = ""
        move = None

        if "BOARD:" in move_text and "MOVE:" in move_text:
            lines = move_text.split('\n')
            for line in lines:
                if line.startswith("BOARD:"):
                    board_description = line[6:].strip()
                elif line.startswith("MOVE:"):
                    move_line = line[5:].strip()
                    # Extract UCI move from the move line
                    move_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
                    matches = re.findall(move_pattern, move_line.lower())
                    if matches:
                        move = matches[0]
        else:
            # Fallback: try to extract move from anywhere in response
            move_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
            matches = re.findall(move_pattern, move_text.lower())
            if matches:
                move = matches[0]

        # Log what AI thinks about the board vs reality
        actual_board_info = f"White to move: {board.turn}, Castling: {board.castling_rights}, En passant: {board.ep_square}"
        logger.info(f"AI's board perception: {board_description}")
        logger.info(f"Actual board state: FEN={fen}")
        logger.info(f"Actual board info: {actual_board_info}")

        if move:
            logger.info(f"Gemini suggested move: {move}")
            return move
        else:
            logger.warning(f"Could not extract valid move from Gemini response: {move_text}")
            # Return fallback move for opening position
            return "e2e4"

    except ValueError as ve:
        # Re-raise ValueError (like missing API key) - don't fallback for configuration errors
        raise ve
    except Exception as e:
        logger.error(f"Error getting move from Gemini: {e}")
        # Return fallback move when API fails (e.g., network issues, parsing errors)
        return "e2e4"


def extract_uci_move(text: str) -> str:
    """
    Extract a UCI format move from text.
    Handles both UCI notation and common chess notation.
    Returns the first valid move found or None.
    """
    import re

    if not text:
        return None

    text_lower = text.lower()

    # Handle castling notation first
    if "o-o-o" in text_lower or "0-0-0" in text_lower:
        return "e1c1"  # Long castling
    elif "o-o" in text_lower or "0-0" in text_lower:
        return "e1g1"  # Short castling

    # Look for UCI pattern moves (e.g., e2e4, g1f3, etc.)
    move_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
    matches = re.findall(move_pattern, text_lower)

    if matches:
        return matches[0]

    return None
