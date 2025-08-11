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

    # Create a more detailed prompt with game context
    move_count = len(move_history)
    game_phase = "opening" if move_count < 20 else "middlegame" if move_count < 40 else "endgame"

    # Format move history in a more readable way
    move_pairs = []
    for i in range(0, len(move_history), 2):
        white_move = move_history[i] if i < len(move_history) else ""
        black_move = move_history[i + 1] if i + 1 < len(move_history) else ""
        move_number = (i // 2) + 1
        if black_move:
            move_pairs.append(f"{move_number}. {white_move} {black_move}")
        elif white_move:
            move_pairs.append(f"{move_number}. {white_move}")

    move_history_text = " ".join(move_pairs) if move_pairs else "Starting position"

    system_prompt = """You are a strong chess engine. Analyze the position carefully and return the best move in UCI format.

Important guidelines:
- Consider tactical threats, piece safety, and strategic plans
- In the opening, develop pieces and control the center
- In the middlegame, look for tactical opportunities and improve piece coordination
- In the endgame, activate your king and push passed pawns
- Always return ONLY the move in UCI format (e.g., e2e4, g1f3, e1g1)"""

    user_prompt = f"""Analyze this chess position:

Current position (FEN): {board_fen}
Game phase: {game_phase}
Move history: {move_history_text}
Total moves played: {move_count}

Return the best move in UCI format. Consider the current position carefully and make a strong strategic or tactical move."""

    try:
        logger.debug("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use a better model for chess
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=20,  # Allow a bit more tokens for flexibility
            temperature=0.1  # Lower temperature for more consistent moves
        )
        move = response.choices[0].message.content.strip()

        # Clean up the response to extract just the move
        import re
        # Look for UCI format moves (e.g., e2e4, g1f3, etc.)
        uci_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'
        matches = re.findall(uci_pattern, move.lower())

        if matches:
            clean_move = matches[0]
            logger.info(f"OpenAI suggested move: {clean_move}")
            return clean_move
        else:
            logger.warning(f"Could not extract UCI move from response: {move}")
            logger.info(f"OpenAI raw response: {move}")
            return move  # Return as-is if no UCI pattern found

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"  # Fallback move