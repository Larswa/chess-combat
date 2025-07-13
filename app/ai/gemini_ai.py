# Gemini AI Integration (Google Gemini API)
import os
import requests
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"

def get_gemini_chess_move(board_fen, move_history, invalid_moves=None):
    logger.info(f"Requesting move from Gemini API for position: {board_fen}")
    logger.debug(f"Move history: {move_history}")
    if invalid_moves:
        logger.debug(f"Invalid moves to avoid: {invalid_moves}")

    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable not set")
        # Use a smarter fallback based on common opening moves
        fallback_moves = ["e2e4", "d2d4", "g1f3", "c2c4", "e7e5", "d7d5", "g8f6", "c7c5"]
        if invalid_moves:
            # Find a fallback move that's not in the invalid moves list
            for move in fallback_moves:
                if move not in invalid_moves:
                    logger.warning(f"Falling back to move '{move}' (avoiding invalid moves)")
                    return move
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"

    prompt = f"You are a chess engine. Given the current board in FEN: {board_fen} and move history: {move_history}, return the best next move in UCI format (e.g., e2e4)."

    if invalid_moves:
        prompt += f" IMPORTANT: Do NOT suggest any of these invalid moves: {', '.join(invalid_moves)}. Choose a different legal move."

    prompt += " Only return the move."
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    # Try the v1 endpoint (not v1beta)
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    logger.debug(f"Sending request to Gemini API: {url}")

    try:
        response = requests.post(url, headers=headers, params=params, json=data)
        if response.status_code == 404:
            logger.warning("v1 endpoint not found, trying v1beta")
            # Try the v1beta endpoint as fallback
            url_beta = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            response = requests.post(url_beta, headers=headers, params=params, json=data)

        response.raise_for_status()

        try:
            move = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            logger.info(f"Gemini suggested move: {move}")
        except Exception as e:
            logger.warning(f"Error parsing Gemini response: {e}")
            move = response.text.strip()
            logger.info(f"Gemini raw response: {move}")

        return move

    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"  # Fallback move
