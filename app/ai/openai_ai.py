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

def get_openai_chess_move(fen: str, move_history: list = None, invalid_moves: list = None) -> str:
    """
    Get a chess move from OpenAI.

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

        # Build a comprehensive prompt optimized for GPT-4's chess capabilities
        prompt = f"""You are an expert chess player with deep understanding of tactics, strategy, and positional play.

Current position: {fen}
Turn: {"White" if board.turn else "Black"}

{f"Game history (last 10 moves): {' '.join(move_history[-10:])}" if move_history else ""}

{f"Invalid moves to avoid: {', '.join(invalid_moves[-5:])}" if invalid_moves else ""}

Analyze this position considering:
1. Tactical opportunities (pins, forks, discovered attacks, etc.)
2. Strategic factors (piece activity, pawn structure, king safety)
3. Opening principles or endgame technique as appropriate

IMPORTANT: You MUST provide a move in UCI notation at the end.

Format your response exactly like this:
BOARD: [analyze key pieces, threats, and strategic factors]
MOVE: [your move in UCI notation like e2e4]

Remember: Always end with "MOVE: [uci_move]" - this is required!"""

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
