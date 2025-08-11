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

    # Gemini AI Integration (Google Gemini API)
import os
import requests
import logging
import json
from typing import List
from .chess_helper import get_smart_move_suggestions, validate_and_suggest_similar_move, get_position_description

logger = logging.getLogger(__name__)

def get_gemini_chess_move(board_fen: str, move_history: List[str] = None, session_id: str = None) -> str:
    logger.info(f"Requesting move from Gemini API for position: {board_fen}")
    logger.debug(f"Move history: {move_history}")
    logger.debug(f"Session ID: {session_id}")

    # If we have a session ID, try to use the session manager for strategic continuity
    if session_id:
        try:
            from .ai_session_manager import session_manager
            from .chess_helper import get_smart_move_suggestions

            # Get smart suggestions for the session manager
            smart_suggestions = get_smart_move_suggestions(board_fen, num_suggestions=5)

            # Use session-based strategic move
            move = session_manager.get_strategic_move(session_id, board_fen, move_history or [], smart_suggestions)
            if move:
                logger.info(f"Gemini session {session_id} returned strategic move: {move}")
                return move
        except Exception as e:
            logger.warning(f"Session-based move failed, falling back to direct API: {e}")

    # Fallback to direct API call (original behavior)
    # Read API key at runtime to allow for testing with mocked environments
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"

    # Improved prompt for better chess move generation with game context
    move_count = len(move_history) if move_history else 0
    game_phase = "opening" if move_count < 20 else "middlegame" if move_count < 40 else "endgame"

    # Format move history in a more readable way
    move_pairs = []
    if move_history:
        for i in range(0, len(move_history), 2):
            white_move = move_history[i] if i < len(move_history) else ""
            black_move = move_history[i + 1] if i + 1 < len(move_history) else ""
            move_number = (i // 2) + 1
            if black_move:
                move_pairs.append(f"{move_number}. {white_move} {black_move}")
            elif white_move:
                move_pairs.append(f"{move_number}. {white_move}")

    move_history_text = " ".join(move_pairs) if move_pairs else "Starting position"

    # Get smart move suggestions to guide the AI
    smart_suggestions = get_smart_move_suggestions(board_fen, num_suggestions=3)
    position_desc = get_position_description(board_fen)

    # Get smart move suggestions using chess helper
    try:
        from .chess_helper import get_smart_move_suggestions, get_position_description
        smart_suggestions = get_smart_move_suggestions(board_fen, num_suggestions=8)
        position_desc = get_position_description(board_fen)

        logger.info(f"Chess helper provided {len(smart_suggestions)} move suggestions: {smart_suggestions}")
    except Exception as e:
        logger.error(f"Error getting chess helper suggestions: {e}")
        smart_suggestions = []
        position_desc = "Unable to analyze position"

    prompt = f"""You are a professional chess grandmaster. Choose the best move from the suggested legal moves.

CRITICAL: You are receiving chess positions in FEN (Forsyth-Edwards Notation) format.
FEN FORMAT EXPLANATION:
- FEN is the standard notation for describing complete chess positions
- Format: "piece_placement active_color castling en_passant halfmove_clock fullmove_number"
- Example: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" = starting position

UNDERSTANDING FEN PIECE PLACEMENT:
- Board is read from rank 8 (top) to rank 1 (bottom), left to right
- Uppercase = White pieces: K(King) Q(Queen) R(Rook) B(Bishop) N(Knight) P(Pawn)
- Lowercase = Black pieces: k(king) q(queen) r(rook) b(bishop) n(knight) p(pawn)
- Numbers 1-8 = Count of consecutive empty squares
- "/" = Separator between ranks

INSTRUCTIONS:
1. You will be given a list of LEGAL moves that are already validated
2. Choose the BEST move from this list based on chess principles
3. Respond EXACTLY in the format: "MOVE: [uci_move]" followed by "REASON: [explanation]"
4. Do NOT suggest moves outside the provided list
5. UCI format examples: e2e4, g1f3, e7e8q (for pawn promotion)

CURRENT POSITION (FEN): {board_fen}
{position_desc}

LEGAL MOVE OPTIONS (choose the best one):
{', '.join(smart_suggestions) if smart_suggestions else 'No suggestions available'}

Game context: {game_phase} phase
Move history: {move_history_text}

RESPONSE FORMAT - You MUST respond in this exact format:
MOVE: [uci_move]
REASON: [brief_reason]

Example:
MOVE: e2e4
REASON: Controls center and develops pieces

Choose the BEST move from the options above:"""

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
                        logger.debug(f"Gemini raw response: {move_text}")

                        # Parse structured response
                        from .openai_ai import parse_structured_move_response
                        proposed_move = parse_structured_move_response(move_text, smart_suggestions)

                        if proposed_move:
                            # Validate the move using chess helper
                            from .chess_helper import validate_and_suggest_similar_move

                            try:
                                valid_move = validate_and_suggest_similar_move(proposed_move, board_fen)
                                if valid_move:
                                    logger.info(f"Gemini suggested move: {valid_move} (from model: {model}, original: {proposed_move})")
                                    return valid_move
                                else:
                                    logger.warning(f"Gemini move {proposed_move} is invalid, no similar move found (model: {model})")
                                    continue
                            except Exception as e:
                                logger.warning(f"Error validating Gemini move {proposed_move}: {e}")
                                continue
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

    # If all models failed, use chess helper to suggest a good move
    logger.error("All Gemini models failed or are unavailable")

    try:
        from .chess_helper import get_smart_move_suggestions
        suggestions = get_smart_move_suggestions(board_fen, num_suggestions=1)
        if suggestions:
            fallback_move = suggestions[0]
            logger.warning(f"Falling back to chess engine suggestion: {fallback_move}")
            return fallback_move
    except Exception as e:
        logger.error(f"Error getting chess engine fallback: {e}")

    logger.warning("Falling back to default move 'e2e4'")
    return "e2e4"


def extract_uci_move(text, board_fen=None):
    """Extract UCI format move from text response"""
    import re

    # Clean the text - remove common prefixes and suffixes
    original_text = text.strip()

    # Remove chess notation prefixes like "..." and whitespace
    cleaned_text = re.sub(r'^\.+\s*', '', original_text.strip())
    cleaned_text = re.sub(r'\s*\+?\s*$', '', cleaned_text)  # Remove check symbols and trailing spaces

    logger.debug(f"Cleaning move text: '{original_text}' -> '{cleaned_text}'")

    # First try UCI patterns (case insensitive)
    text_lower = cleaned_text.lower()
    patterns = [
        r'\b([a-h][1-8][a-h][1-8][qrbn]?)\b',  # Standard UCI: e2e4, e7e8q
        r'\b(o-o-o|0-0-0)\b',                   # Long castling
        r'\b(o-o|0-0)\b',                       # Short castling
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            move = matches[0]
            # Convert castling notation
            if move in ['o-o', '0-0']:
                return 'e1g1'  # Assuming white castling, should be context-aware
            elif move in ['o-o-o', '0-0-0']:
                return 'e1c1'  # Assuming white castling, should be context-aware
            elif len(move) >= 4 and len(move) <= 5:
                return move

    # If no UCI pattern found, try to parse as algebraic notation
    if board_fen and cleaned_text:
        try:
            import chess
            board = chess.Board(board_fen)

            # Try to parse as algebraic notation - DON'T convert to lowercase!
            parsed_move = board.parse_san(cleaned_text)
            uci_move = parsed_move.uci()
            logger.info(f"Gemini move converted from algebraic ({cleaned_text}) to UCI: {uci_move}")
            return uci_move
        except Exception as parse_error:
            logger.warning(f"Could not parse algebraic notation: {cleaned_text}, error: {parse_error}")

    return None

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
