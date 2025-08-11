# Gemini AI Integration (Google Gemini API)
import os
import requests
import logging
import json

logger = logging.getLogger(__name__)

def get_gemini_chess_move(board_fen, move_history):
    logger.info(f"Requesting move from Gemini API for position: {board_fen}")
    logger.debug(f"Move history: {move_history}")

    # Read API key at runtime to allow for testing with mocked environments
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"

    # Improved prompt for better chess move generation with game context
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

    prompt = f"""You are a professional chess engine. Analyze this chess position carefully and respond with ONLY the best move in UCI notation.

POSITION ANALYSIS:
- Current board position (FEN): {board_fen}
- Game phase: {game_phase}
- Move history: {move_history_text}
- Total moves played: {move_count}

CHESS STRATEGY GUIDELINES:
- Opening (moves 1-20): Develop pieces, control center, castle for safety
- Middlegame (moves 21-40): Look for tactics, improve piece coordination, attack weaknesses
- Endgame (40+ moves): Activate king, push passed pawns, simplify when ahead

REQUIREMENTS:
- Return ONLY the move in UCI format (examples: e2e4, g1f3, e1g1, e7e8q)
- No explanations, no additional text
- Choose a strong, strategic move that considers the current game phase
- Look for tactical opportunities (pins, forks, skewers)

Move:"""

    # Try different Gemini models in order of preference
    models_to_try = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]

    headers = {"Content-Type": "application/json"}

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": gemini_api_key}

        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,  # Lower temperature for more consistent responses
                "maxOutputTokens": 20,  # Increase slightly for flexibility
                "topP": 0.9,
                "topK": 40
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }

        logger.debug(f"Trying Gemini model: {model}")
        logger.debug(f"Request URL: {url}")

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=15
            )

            logger.debug(f"Response status code: {response.status_code}")

            if response.status_code == 404:
                logger.debug(f"Model {model} not available (404), trying next model")
                continue

            if response.status_code == 403:
                logger.error("API key invalid or insufficient permissions")
                logger.debug(f"Response: {response.text}")
                logger.warning("Falling back to default move 'e2e4'")
                return "e2e4"

            if response.status_code == 400:
                logger.error(f"Bad request to Gemini API: {response.text}")
                continue

            response.raise_for_status()

            try:
                response_data = response.json()
                logger.debug(f"Gemini API response: {json.dumps(response_data, indent=2)}")

                # Extract the move from the response
                if "candidates" in response_data and len(response_data["candidates"]) > 0:
                    candidate = response_data["candidates"][0]

                    # Check if content was blocked
                    if "finishReason" in candidate and candidate["finishReason"] == "SAFETY":
                        logger.warning("Gemini response was blocked by safety filters")
                        continue

                    if "content" in candidate and "parts" in candidate["content"]:
                        move_text = candidate["content"]["parts"][0]["text"].strip()

                        # Clean up the move text to extract just the UCI move
                        move = extract_uci_move(move_text)

                        if move:
                            logger.info(f"Gemini suggested move: {move} (from model: {model})")
                            return move
                        else:
                            logger.warning(f"No valid UCI move found in response: '{move_text}' (model: {model})")
                            continue

                logger.warning(f"Unexpected response structure from Gemini API (model: {model})")
                continue

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON response from Gemini API (model: {model}): {e}")
                logger.debug(f"Raw response: {response.text}")
                continue

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout calling Gemini API (model: {model})")
            continue
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error calling Gemini API (model: {model}): {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API (model: {model}): {e}")
            continue

    # If all models failed
    logger.error("All Gemini models failed or are unavailable")
    logger.warning("Falling back to default move 'e2e4'")
    return "e2e4"


def extract_uci_move(text):
    """Extract UCI format move from text response"""
    import re

    # Clean the text
    text = text.strip().lower()

    # Common UCI move patterns
    patterns = [
        r'\b([a-h][1-8][a-h][1-8][qrbn]?)\b',  # Standard UCI: e2e4, e7e8q
        r'\b(o-o-o|0-0-0)\b',                   # Long castling
        r'\b(o-o|0-0)\b',                       # Short castling
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            move = matches[0]
            # Convert castling notation
            if move in ['o-o', '0-0']:
                return 'e1g1'  # Assuming white castling, should be context-aware
            elif move in ['o-o-o', '0-0-0']:
                return 'e1c1'  # Assuming white castling, should be context-aware
            elif len(move) >= 4 and len(move) <= 5:
                return move

    return None
