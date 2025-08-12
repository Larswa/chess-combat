import openai
import os
import logging
from typing import List
from .chess_helper import get_smart_move_suggestions, validate_and_suggest_similar_move, get_position_description

logger = logging.getLogger(__name__)

def parse_structured_move_response(response: str, valid_moves: List[str]) -> str:
    """
    Parse structured AI response and extract move with multiple fallback strategies
    """
    import re

    logger.debug(f"Parsing response: '{response}' with valid moves: {valid_moves}")

    # Strategy 1: Parse structured format "MOVE: e2e4"
    move_match = re.search(r'MOVE:\s*([a-h][1-8][a-h][1-8][qrbn]?)', response, re.IGNORECASE)
    if move_match:
        move = move_match.group(1).lower()
        logger.debug(f"Found structured move: {move}")
        if move in valid_moves:
            return move

    # Strategy 2: Look for any UCI pattern in the response
    uci_pattern = r'\b([a-h][1-8][a-h][1-8][qrbn]?)\b'
    uci_matches = re.findall(uci_pattern, response.lower())

    for move in uci_matches:
        if move in valid_moves:
            logger.debug(f"Found valid UCI move in text: {move}")
            return move

    # Strategy 3: Check if entire response (stripped) is a valid move
    clean_response = response.strip().lower()
    if clean_response in valid_moves:
        logger.debug(f"Entire response is valid move: {clean_response}")
        return clean_response

    # Strategy 4: Try each valid move to see if it appears in response
    for move in valid_moves:
        if move.lower() in response.lower():
            logger.debug(f"Found valid move mentioned in response: {move}")
            return move

    logger.warning(f"Could not parse any valid move from response: '{response}'")
    return None

def get_openai_chess_move(board_fen: str, move_history: List[str] = None, session_id: str = None) -> str:
    logger.info(f"Requesting move from OpenAI API for position: {board_fen}")
    logger.debug(f"Move history: {move_history}")
    logger.debug(f"Session ID: {session_id}")

    # If we have a session ID, try to use the session manager for strategic continuity
    if session_id:
        try:
            from .ai_session_manager import session_manager

            # Get smart suggestions for the session manager
            smart_suggestions = get_smart_move_suggestions(board_fen, num_suggestions=5)

            # Use session-based strategic move
            move = session_manager.get_strategic_move(session_id, board_fen, move_history or [], smart_suggestions)
            if move:
                logger.info(f"OpenAI session {session_id} returned strategic move: {move}")
                return move
        except Exception as e:
            logger.warning(f"Session-based move failed, falling back to direct API: {e}")

    # Fallback to direct API call (original behavior)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.warning("Falling back to default move 'e2e4'")
        return "e2e4"

    logger.debug("Initializing OpenAI client")
    client = openai.OpenAI(api_key=api_key)

    # Create a more detailed prompt with game context
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
    
    # Get all legal moves for parsing validation
    import chess
    board = chess.Board(board_fen)
    all_legal_moves = [move.uci() for move in board.legal_moves]

    system_prompt = """You are a professional chess engine. Choose the best move from the suggested legal moves.

CRITICAL: You are receiving chess positions in FEN (Forsyth-Edwards Notation) format.
FEN FORMAT EXPLANATION:
- FEN describes the complete chess position in one string
- Format: "piece_placement active_color castling en_passant halfmove_clock fullmove_number"
- Example: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" = starting position

PIECE NOTATION IN FEN:
- Uppercase letters = White pieces: K(King) Q(Queen) R(Rook) B(Bishop) N(Knight) P(Pawn)
- Lowercase letters = Black pieces: k(king) q(queen) r(rook) b(bishop) n(knight) p(pawn)
- Numbers 1-8 = Number of empty squares
- "/" = Separates ranks (rows) from 8th rank to 1st rank

IMPORTANT INSTRUCTIONS:
1. You will be given a list of LEGAL moves that are already validated
2. Choose the BEST move from this list based on chess principles
3. Respond EXACTLY in the format: "MOVE: [uci_move]" followed by "REASON: [explanation]"
4. Do NOT suggest moves outside the provided list
5. UCI format examples: e2e4, g1f3, e7e8q (for pawn promotion)

Chess principles to consider:
- Captures (especially of valuable pieces)
- Checks and threats
- Piece development in opening
- Center control
- King safety"""

    user_prompt = f"""CURRENT POSITION:
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

Choose the BEST move from the legal options above:"""

    try:
        logger.debug("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use a better model for chess
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=50,  # Increased to allow for structured response
            temperature=0.1  # Lower temperature for more consistent moves
        )
        ai_response = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI raw response: {ai_response}")

        # Parse structured response using all legal moves for validation
        proposed_move = parse_structured_move_response(ai_response, all_legal_moves)

        if proposed_move:
            # Use chess helper to validate and suggest similar move if needed
            validated_move = validate_and_suggest_similar_move(proposed_move, board_fen)
            if validated_move:
                logger.info(f"OpenAI suggested move: {validated_move}")
                return validated_move
            else:
                logger.warning(f"OpenAI move {proposed_move} could not be validated")

        # If no valid move found, fall back to smart suggestions
        logger.warning(f"OpenAI returned unparseable response: {ai_response}")
        fallback_suggestions = get_smart_move_suggestions(board_fen, num_suggestions=1)
        if fallback_suggestions:
            logger.info(f"Using smart fallback move: {fallback_suggestions[0]}")
            return fallback_suggestions[0]

        # Ultimate fallback
        logger.error("No valid moves found, using default")
        return "e2e4"

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        # Use chess helper for emergency fallback
        emergency_suggestions = get_smart_move_suggestions(board_fen, num_suggestions=1)
        if emergency_suggestions:
            logger.info(f"Emergency fallback move: {emergency_suggestions[0]}")
            return emergency_suggestions[0]
        return "e2e4"  # Ultimate fallback
