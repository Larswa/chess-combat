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

        # Build a simple, clear prompt
        prompt = f"""You are playing chess. Here's the current position:

FEN: {fen}
Turn: {"White" if board.turn else "Black"}

{f"Previous moves: {' '.join(move_history[-10:])}" if move_history else ""}

{f"Don't play these invalid moves: {', '.join(invalid_moves[-5:])}" if invalid_moves else ""}

Please respond with only your move in UCI notation (like e2e4 or g1f3).
Just the move, nothing else."""

        logger.debug(f"Gemini prompt: {prompt}")

        # Get response from Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        if not response or not response.text:
            logger.error("Gemini returned empty response")
            return None

        # Extract move from response
        move_text = response.text.strip()
        logger.debug(f"Gemini raw response: {move_text}")

        # Try to find a UCI move pattern (4-5 characters like e2e4 or e7e8q)
        move_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
        matches = re.findall(move_pattern, move_text.lower())

        if matches:
            move = matches[0]
            logger.info(f"Gemini suggested move: {move}")
            return move
        else:
            logger.warning(f"Could not extract valid move from Gemini response: {move_text}")
            return None

    except Exception as e:
        logger.error(f"Error getting move from Gemini: {e}")
        return None
