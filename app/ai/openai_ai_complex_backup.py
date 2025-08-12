"""
Simple OpenAI integration for chess moves.
Just presents board state and gets move decision.
"""

import openai
import os
import logging
import chess
import re

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

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
        
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
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

    # Strategy 4: Try each valid move to see if it appears in response
    for move in valid_moves:
        if move.lower() in response.lower():
            logger.debug(f"Found valid move mentioned in response: {move}")
            return move

    logger.warning(f"Could not parse any valid move from response: '{response}'")
    return None

def get_openai_chess_move(board_fen: str, move_history: List[str] = None, session_id: str = None, invalid_moves: List[str] = None) -> str:
    logger.info(f"Requesting move from OpenAI API for position: {board_fen}")
    logger.debug(f"Move history: {move_history}")
    logger.debug(f"Session ID: {session_id}")
    logger.debug(f"Invalid moves to avoid: {invalid_moves}")

    # If we have a session ID, try to use the session manager for strategic continuity
    if session_id:
        try:
            from .ai_session_manager import session_manager

            # Use session-based strategic move (pass invalid_moves to avoid repetition)
            move = session_manager.get_strategic_move(session_id, board_fen, move_history or [], invalid_moves or [])
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

    # Get all legal moves for the AI to choose from
    import chess
    board = chess.Board(board_fen)
    all_legal_moves = [move.uci() for move in board.legal_moves]

    # Get critical position analysis including threats and safety
    from .chess_helper import analyze_threats_and_opportunities, get_position_description
    
    position_analysis = analyze_threats_and_opportunities(board_fen)
    position_description = get_position_description(board_fen)
    
    # Analyze which pieces are under attack
    attacked_pieces = []
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == board.turn:
            if board.is_attacked_by(not board.turn, square):
                piece_name = piece.symbol().upper()
                square_name = chess.square_name(square)
                attacked_pieces.append(f"{piece_name} on {square_name}")

    # Check which squares are dangerous (under enemy attack)
    dangerous_squares = []
    for square in chess.SQUARES:
        if board.is_attacked_by(not board.turn, square):
            dangerous_squares.append(chess.square_name(square))

    threats_text = ""
    if position_analysis["threats"]:
        threats_text += f"\n⚠️ THREATS: {'; '.join(position_analysis['threats'])}"
    if attacked_pieces:
        threats_text += f"\n⚠️ YOUR PIECES UNDER ATTACK: {', '.join(attacked_pieces)}"
    if dangerous_squares:
        threats_text += f"\n⚠️ DANGEROUS SQUARES (enemy controls): {', '.join(dangerous_squares[:10])}{'...' if len(dangerous_squares) > 10 else ''}"
    if position_analysis["opportunities"]:
        threats_text += f"\n✅ OPPORTUNITIES: {'; '.join(position_analysis['opportunities'])}"

    system_prompt = """You are a world-class chess grandmaster AI. You have deep understanding of chess strategy, tactics, and opening principles.

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

CHESS PRINCIPLES TO FOLLOW:
OPENING (moves 1-15):
- Control the center (e4, d4, e5, d5)
- Develop knights before bishops
- Castle early for king safety
- Don't move the same piece twice unless necessary
- Don't bring queen out too early
- AVOID premature pawn storms on the wings (like a2a4, b2b4, g2g4, h2h4)

MIDDLEGAME:
- Improve piece coordination
- Create threats and tactics
- Consider pawn breaks
- Maintain king safety

ENDGAME:
- Activate your king
- Push passed pawns
- Use your pieces efficiently

RESPONSE FORMAT - You MUST respond in this exact format:
MOVE: [uci_move]
REASON: [brief_reason]

Example:
MOVE: g1f3
REASON: Develops knight and controls central squares"""

    # Add information about invalid moves to avoid
    invalid_moves_text = ""
    if invalid_moves:
        invalid_moves_text = f"\n\n🚫 MOVES TO AVOID (already tried and failed):\n{', '.join(invalid_moves)}\nDO NOT suggest these moves again!"

    user_prompt = f"""CURRENT POSITION (FEN): {board_fen}
POSITION: {position_description}

🛡️ CRITICAL SAFETY ANALYSIS:{threats_text}

LEGAL MOVE OPTIONS (UCI format):
{', '.join(all_legal_moves[:20])}{'...' if len(all_legal_moves) > 20 else ''}{invalid_moves_text}

Game context: {game_phase} phase (move {move_count})
Move history: {move_history_text}

⚠️ CRITICAL INSTRUCTIONS:
1. DO NOT move pieces to dangerous squares (under enemy attack) unless capturing a more valuable piece
2. SAVE pieces that are under attack - move them to safety or defend them
3. AVOID moving valuable pieces (Queen, Rook) into danger
4. Look for tactical opportunities but prioritize piece safety
5. NEVER suggest moves from the "MOVES TO AVOID" list above

Analyze the position and choose the BEST move from the legal options. Consider:
1. PIECE SAFETY (priority #1)
2. Material balance
3. King safety
4. Piece activity
5. Control of center
6. Tactical opportunities

RESPONSE FORMAT:
MOVE: [uci_move]
REASON: [brief_reason]"""

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
            # Validate the move is actually legal
            validated_move = validate_and_suggest_similar_move(proposed_move, board_fen)
            if validated_move:
                logger.info(f"OpenAI suggested move: {validated_move}")
                return validated_move
            else:
                logger.warning(f"OpenAI move {proposed_move} could not be validated")

        # If no valid move found, use a simple fallback
        logger.warning(f"OpenAI returned unparseable response: {ai_response}")
        if all_legal_moves:
            # Just return the first legal move as emergency fallback
            logger.info(f"Using emergency fallback move: {all_legal_moves[0]}")
            return all_legal_moves[0]

        # Ultimate fallback
        logger.error("No legal moves found, using default")
        return "e2e4"

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        # Use simple emergency fallback
        import chess
        board = chess.Board(board_fen)
        legal_moves = [move.uci() for move in board.legal_moves]
        if legal_moves:
            logger.info(f"Emergency fallback move: {legal_moves[0]}")
            return legal_moves[0]
        return "e2e4"  # Ultimate fallback
