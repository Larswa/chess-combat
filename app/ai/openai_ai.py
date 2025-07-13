import openai
import os
import logging

logger = logging.getLogger(__name__)

def get_openai_chess_move(board_fen, move_history, invalid_moves=None):
    logger.info(f"Requesting move from OpenAI API for position: {board_fen}")
    logger.debug(f"Move history: {move_history}")
    if invalid_moves:
        logger.debug(f"Invalid moves to avoid: {invalid_moves}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
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

    logger.debug("Initializing OpenAI client")
    client = openai.OpenAI(api_key=api_key)

    prompt = f"You are a chess engine. Given the current board in FEN: {board_fen} and move history: {move_history}, return the best next move in UCI format (e.g., e2e4)."

    if invalid_moves:
        prompt += f" IMPORTANT: Do NOT suggest any of these invalid moves: {', '.join(invalid_moves)}. Choose a different legal move."

    prompt += " Only return the move."

    try:
        logger.debug("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            # model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a chess engine."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.2
        )
        move = response.choices[0].message.content.strip()
        logger.info(f"OpenAI suggested move: {move}")
        return move
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"  # Fallback move