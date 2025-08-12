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

def get_gemini_chess_move(fen: str, move_history: list = None, invalid_moves: list = None) -> str:
    """
    Get a chess move from Gemini AI.

    Args:
        fen: Current board position in FEN notation
        move_history: List of previous moves (optional)
        invalid_moves: List of invalid moves to avoid (optional)

    Returns:
        UCI move string (e.g., "e2e4")
    """
    try:
        # Create board from FEN to get current position info
        board = chess.Board(fen)

        # Build a comprehensive prompt optimized for Gemini's chess capabilities
        prompt = f"""You are an expert chess player with deep understanding of tactics, strategy, and positional play.

Current position: {fen}
Turn: {"White" if board.turn else "Black"}

{f"Game history (last 10 moves): {' '.join(move_history[-10:])}" if move_history else ""}

{f"Invalid moves to avoid: {', '.join(invalid_moves[-5:])}" if invalid_moves else ""}

Analyze this position considering:
1. Tactical opportunities (pins, forks, discovered attacks, etc.)
2. Strategic factors (piece activity, pawn structure, king safety)
3. Opening principles or endgame technique as appropriate

First, describe the key features of the position.
Then provide your best move in UCI notation.

Format your response exactly like this:
BOARD: [analyze key pieces, threats, and strategic factors]
MOVE: [your move in UCI notation like e2e4]"""

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

    except Exception as e:
        logger.error(f"Error getting move from Gemini: {e}")
        # Return fallback move when API fails (e.g., no API key, network issues)
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
