import openai
import os
import logging

logger = logging.getLogger(__name__)

def get_openai_chess_move(board_fen, move_history):
    logger.info(f"Requesting move from OpenAI API for position: {board_fen}")
    logger.debug(f"Move history: {move_history}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"

    logger.debug("Initializing OpenAI client")
    client = openai.OpenAI(api_key=api_key)
    prompt = f"You are a chess engine. Given the current board in FEN: {board_fen} and move history: {move_history}, return the best next move in UCI format (e.g., e2e4). Only return the move."

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