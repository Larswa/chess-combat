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

# Configure OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

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
        if not client:
            logger.error("OpenAI API key not configured")
            return None

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

        logger.debug(f"OpenAI prompt: {prompt}")

        # Get response from OpenAI using new client
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a chess engine. Respond only with UCI moves."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.7
        )

        if not response or not response.choices:
            logger.error("OpenAI returned empty response")
            return None

        # Extract move from response
        move_text = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI raw response: {move_text}")

        # Try to find a UCI move pattern (4-5 characters like e2e4 or e7e8q)
        move_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
        matches = re.findall(move_pattern, move_text.lower())

        if matches:
            move = matches[0]
            logger.info(f"OpenAI suggested move: {move}")
            return move
        else:
            logger.warning(f"Could not extract valid move from OpenAI response: {move_text}")
            return None

    except Exception as e:
        logger.error(f"Error getting move from OpenAI: {e}")
        return None
