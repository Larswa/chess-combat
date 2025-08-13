"""
Simple OpenAI integration for chess moves.
Just presents board state and gets move decision.
"""

from openai import OpenAI
import os
import logging
import chess
import re

logger = logging.getLogger(__name__)

# Configure OpenAI client - will be created when needed
def _get_openai_client():
    """Get OpenAI client, let OpenAI library handle API key validation"""
    return OpenAI()  # OpenAI library will handle missing API key

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

def get_openai_chess_move(fen: str, move_history: list = None, invalid_moves: list = None) -> str:
    """
    Get a chess move from OpenAI with enhanced situational awareness.

    Args:
        fen: Current board position in FEN notation
        move_history: List of previous moves (optional)
        invalid_moves: List of invalid moves to avoid (optional)

    Returns:
        UCI move string (e.g., "e2e4")
    """
    try:
        # Get OpenAI client (this will check for API key)
        client = _get_openai_client()

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

        logger.debug(f"OpenAI prompt: {prompt}")

        # Get response from OpenAI using new client with GPT-4o (latest model)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert chess engine with deep strategic understanding. Analyze positions carefully and suggest the strongest moves based on tactical and positional considerations. Always end your response with a clear move in UCI notation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,  # Increased for detailed analysis but still controlled
            temperature=0.2  # Lower temperature for more consistent, logical analysis
        )

        if not response or not response.choices:
            logger.error("OpenAI returned empty response")
            return None

        # Extract move from response
        move_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI full response: {move_text}")

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

        # If still no move, try common chess notation patterns
        if not move:
            # Look for moves in algebraic notation and convert common ones
            common_moves = {
                '1.e4': 'e2e4', '1...e5': 'e7e5', '1...c5': 'c7c5', '1...e6': 'e7e6',
                'e4': 'e2e4', 'e5': 'e7e5', 'Nf3': 'g1f3', 'Nc6': 'b8c6',
                'Bb5': 'f1b5', 'Be7': 'f8e7', 'O-O': 'e1g1', 'O-O-O': 'e1c1'
            }
            for notation, uci in common_moves.items():
                if notation in move_text:
                    move = uci
                    break

        # Log what AI thinks about the board vs reality
        actual_board_info = f"White to move: {board.turn}, Castling: {board.castling_rights}, En passant: {board.ep_square}"
        logger.info(f"AI's board perception: {board_description}")
        logger.info(f"Actual board state: FEN={fen}")
        logger.info(f"Actual board info: {actual_board_info}")

        if move:
            logger.info(f"OpenAI suggested move: {move}")
            return move
        else:
            logger.warning(f"Could not extract valid move from OpenAI response: {move_text}")
            # Return fallback move for opening position
            return "e2e4"

    except ValueError as ve:
        # Re-raise ValueError (like missing API key) - don't fallback for configuration errors
        raise ve
    except Exception as e:
        # Check if it's an OpenAI-related error (configuration, API key, etc.)
        if "api_key" in str(e).lower() or "openai" in str(e).lower():
            # Re-raise OpenAI configuration errors
            raise e

        logger.error(f"Error getting move from OpenAI: {e}")
        # Return fallback move when API fails (e.g., network issues, parsing errors)
        return "e2e4"


def parse_structured_move_response(ai_response: str, valid_moves: list) -> str:
    """
    Parse structured AI response in the format:
    MOVE: e2e4
    REASON: Controls the center

    Falls back to extracting UCI move from anywhere in the text.
    """
    import re

    # First try to parse structured format
    lines = ai_response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.lower().startswith('move:'):
            # Extract the move after "MOVE:"
            move_part = line[5:].strip().lower()
            # Clean up any extra text and extract just the move
            move_match = re.match(r'^([a-h][1-8][a-h][1-8][qrbn]?)', move_part)
            if move_match:
                proposed_move = move_match.group(1)
                if proposed_move in valid_moves:
                    return proposed_move

    # Fall back to extracting any UCI move from the text
    return extract_uci_move_from_text(ai_response, valid_moves)


def extract_uci_move_from_text(text: str, valid_moves: list) -> str:
    """
    Extract a UCI format move from any text.
    Returns the first valid move found.
    """
    import re

    # Look for UCI pattern moves (e.g., e2e4, g1f3, etc.)
    move_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
    matches = re.findall(move_pattern, text.lower())

    for match in matches:
        if match in valid_moves:
            return match

    return None
