# UI/API routes for FastAPI
from fastapi import APIRouter, Request, Body, status, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.db.crud import get_game, create_game, add_move, create_player
from app.db.models import Game, Move
from app.db.deps import get_db
from app.ai.openai_ai import get_openai_chess_move
from app.ai.gemini_ai import get_gemini_chess_move
from app.version import get_version_info
from sqlalchemy.orm import Session
import os
import chess
import random
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


# Main UI route

@router.get("/", response_class=HTMLResponse)
def chess_game(request: Request):
    logger.info("Serving chess game UI")
    version_info = get_version_info()
    return templates.TemplateResponse(request=request, name="chess_game.html", context={"version_info": version_info})

# Version endpoint
@router.get("/api/version")
def api_version():
    """Get version information."""
    return get_version_info()

# --- API for UI ---

@router.post("/api/new-game")
def api_new_game(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Create a new game. Expects: {mode: 'human-vs-ai'|'ai-vs-ai', color: 'white'|'black', ai_engine: 'random'|'openai'|'gemini'}
    Returns: {game_id, fen, moves: []}
    """
    logger.info(f"Creating new game: {data}")
    mode = data.get('mode')
    color = data.get('color')
    ai_engine = data.get('ai_engine', 'random')

    # For now, create two players (Human and AI) or two AIs or two Humans
    if mode == 'human-vs-ai':
        white_name = 'Human' if color == 'white' else f'AI_{ai_engine}'
        black_name = f'AI_{ai_engine}' if color == 'white' else 'Human'
    elif mode == 'human-vs-human':
        white_name = 'Human_White'
        black_name = 'Human_Black'
    else:  # ai-vs-ai or any other mode
        white_name = f'AI1_{ai_engine}'
        black_name = f'AI2_{ai_engine}'

    logger.debug(f"Creating players: white={white_name}, black={black_name}")
    # Ensure players exist
    white_player = create_player(db, white_name)
    black_player = create_player(db, black_name)

    # Create game
    game = create_game(db, white_player.id, black_player.id)

    # Ensure the game is committed to database immediately
    db.flush()
    db.commit()

    board = chess.Board()
    logger.info(f"Created game {game.id} with players {white_player.id} vs {black_player.id}")
    return {"game_id": game.id, "fen": board.fen(), "moves": []}

@router.post("/api/move")
def api_move(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Make a move. Expects: {game_id, move: 'e2e4', enforce_rules: true/false, ai_engine: 'random'|'openai'|'gemini'}
    Returns: {fen, moves, status}
    """
    logger.info(f"Processing move: {data}")
    game_id = data.get('game_id')
    move_uci = data.get('move')
    enforce_rules = data.get('enforce_rules', True)  # Default to True
    ai_engine = data.get('ai_engine', 'random')

    game = get_game(db, game_id)
    if not game:
        logger.warning(f"Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Game not found")

    # Rebuild board from moves
    board = chess.Board()
    moves = [m.move for m in game.moves]
    for m in moves:
        if enforce_rules:
            board.push_uci(m)
        else:
            try:
                board.push_uci(m)
            except:
                pass

    # Try to make the move
    if enforce_rules:
        try:
            # Check for pawn promotion - if a pawn is moving to the 8th or 1st rank without promotion suffix
            if len(move_uci) == 4:
                from_square = chess.parse_square(move_uci[:2])
                to_square = chess.parse_square(move_uci[2:4])
                piece = board.piece_at(from_square)

                # Check if this is a pawn promotion
                if piece and piece.piece_type == chess.PAWN:
                    if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                       (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                        # Auto-promote to queen
                        move_uci += "q"
                        logger.info(f"Auto-promoting pawn: {move_uci}")

            board.push_uci(move_uci)
        except Exception as e:
            return {"fen": board.fen(), "moves": moves, "status": f"invalid: {str(e)}"}
    else:
        # When rules are not enforced, try to make the move anyway
        try:
            board.push_uci(move_uci)
        except:
            # If it fails, we'll allow it anyway and save it
            pass

    # Save move
    add_move(db, game_id, move_uci)
    moves.append(move_uci)

    # Ensure move is committed immediately
    db.flush()
    db.commit()

    # Check if this is a human-vs-ai game and not over
    white_player = getattr(game, 'white_id', None)
    black_player = getattr(game, 'black_id', None)
    # Use player names to determine mode (simple logic)
    mode = None
    if hasattr(game, 'white') and hasattr(game, 'black'):
        if ('Human' in game.white.name and 'AI_' in game.black.name) or ('AI_' in game.white.name and 'Human' in game.black.name):
            mode = 'human-vs-ai'
        elif ('AI1_' in game.white.name and 'AI2_' in game.black.name):
            mode = 'ai-vs-ai'
        elif ('Human_' in game.white.name and 'Human_' in game.black.name):
            mode = 'human-vs-human'

    # AI move logic for both human-vs-ai and ai-vs-ai modes
    should_make_ai_move = False
    if mode == 'human-vs-ai':
        if enforce_rules:
            should_make_ai_move = not board.is_game_over()
        else:
            should_make_ai_move = True  # Always make AI move when rules disabled
    elif mode == 'ai-vs-ai':
        if enforce_rules:
            should_make_ai_move = not board.is_game_over()
        else:
            should_make_ai_move = True  # Always make AI move when rules disabled
    # For human-vs-human, never make automatic AI moves

    if should_make_ai_move:
        # Get move history for AI
        move_history = [m.move for m in game.moves]

        # Get AI move using the selected engine
        ai_move = get_ai_move(ai_engine, board, board.fen(), move_history, enforce_rules, game_id)

        if ai_move:
            logger.debug(f"AI suggested move: {ai_move}")
            if enforce_rules:
                # Check for pawn promotion for AI moves too
                if len(ai_move) == 4:
                    from_square = chess.parse_square(ai_move[:2])
                    to_square = chess.parse_square(ai_move[2:4])
                    piece = board.piece_at(from_square)

                    # Check if this is a pawn promotion
                    if piece and piece.piece_type == chess.PAWN:
                        if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                           (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                            # Auto-promote to queen
                            ai_move += "q"
                            logger.info(f"Auto-promoting AI pawn: {ai_move}")

                try:
                    board.push_uci(ai_move)
                except:
                    # If AI move is invalid, fallback to random legal move
                    legal_moves = list(board.legal_moves)
                    if legal_moves:
                        ai_move = random.choice([m.uci() for m in legal_moves])
                        board.push_uci(ai_move)
            else:
                # When rules are disabled, try to make the move but don't fail if invalid
                try:
                    board.push_uci(ai_move)
                except:
                    # If it fails, we'll still save it as a move
                    pass

            add_move(db, game_id, ai_move)
            moves.append(ai_move)

            # Ensure AI move is committed immediately
            db.flush()
            db.commit()

            # Check game status after AI move
            game_status = "in_progress"
            if enforce_rules and board.is_game_over():
                if board.is_checkmate():
                    winner = "White" if board.turn == chess.BLACK else "Black"
                    game_status = f"checkmate - {winner} wins!"
                    result = f"{1 if winner == 'White' else 0}-{0 if winner == 'White' else 1}"
                    logger.info(f"Game {game_id} ended: {game_status}")
                elif board.is_stalemate():
                    game_status = "stalemate - Draw!"
                    result = "1/2-1/2"
                    logger.info(f"Game {game_id} ended: {game_status}")
                elif board.is_insufficient_material():
                    game_status = "draw - Insufficient material"
                    result = "1/2-1/2"
                    logger.info(f"Game {game_id} ended: {game_status}")
                else:
                    game_status = "draw"
                    result = "1/2-1/2"
                    logger.info(f"Game {game_id} ended: {game_status}")

                # Update game in database
                from app.db.crud import update_game_result
                try:
                    update_game_result(db, game_id, result, game_status.split(' - ')[0])
                    # Ensure game result is committed immediately
                    db.flush()
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to update game result: {e}")

            return {"fen": board.fen(), "moves": moves, "status": game_status, "ai_move": ai_move}
        else:
            logger.warning("AI did not return any move")
    else:
        logger.debug("AI move not needed or conditions not met")

    # Check game status after human move
    game_status = "in_progress"
    if enforce_rules and board.is_game_over():
        if board.is_checkmate():
            winner = "White" if board.turn == chess.BLACK else "Black"
            game_status = f"checkmate - {winner} wins!"
            result = f"{1 if winner == 'White' else 0}-{0 if winner == 'White' else 1}"
            logger.info(f"Game {game_id} ended: {game_status}")
        elif board.is_stalemate():
            game_status = "stalemate - Draw!"
            result = "1/2-1/2"
            logger.info(f"Game {game_id} ended: {game_status}")
        elif board.is_insufficient_material():
            game_status = "draw - Insufficient material"
            result = "1/2-1/2"
            logger.info(f"Game {game_id} ended: {game_status}")
        else:
            game_status = "draw"
            result = "1/2-1/2"
            logger.info(f"Game {game_id} ended: {game_status}")

        # Update game in database
        from app.db.crud import update_game_result
        try:
            update_game_result(db, game_id, result, game_status.split(' - ')[0])
            # Ensure game result is committed immediately
            db.flush()
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to update game result: {e}")

    return {"fen": board.fen(), "moves": moves, "status": game_status}

@router.get("/api/game/{game_id}")
def api_get_game(game_id: int, db: Session = Depends(get_db)):
    """
    Get game state. Returns: {fen, moves, status}
    """
    game = get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    board = chess.Board()
    moves = [m.move for m in game.moves]
    for m in moves:
        board.push_uci(m)
    status = "in_progress"
    if board.is_game_over():
        status = "game_over"
    return {"fen": board.fen(), "moves": moves, "status": status}

@router.post("/move")
def submit_move(move: str):
    # Accept move from human player
    return {"status": "received", "move": move}

@router.post("/api/ai-move")
def api_ai_move(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Make an AI move. Expects: {game_id, enforce_rules: true/false, ai_engine: 'random'|'openai'|'gemini'}
    Returns: {fen, moves, status, ai_move}
    """
    game_id = data.get('game_id')
    enforce_rules = data.get('enforce_rules', True)
    ai_engine = data.get('ai_engine', 'random')

    game = get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Rebuild board from moves
    board = chess.Board()
    moves = [m.move for m in game.moves]
    for m in moves:
        if enforce_rules:
            board.push_uci(m)
        else:
            try:
                board.push_uci(m)
            except:
                pass

    # Check game mode
    mode = None
    if hasattr(game, 'white') and hasattr(game, 'black'):
        if ('AI1_' in game.white.name and 'AI2_' in game.black.name):
            mode = 'ai-vs-ai'

    if mode == 'ai-vs-ai' and (not enforce_rules or not board.is_game_over()):
        # Get move history for AI
        move_history = [m.move for m in game.moves]

        # Get AI move using the selected engine
        ai_move = get_ai_move(ai_engine, board, board.fen(), move_history, enforce_rules, game_id)

        if ai_move:
            if enforce_rules:
                # Check for pawn promotion for AI moves
                if len(ai_move) == 4:
                    from_square = chess.parse_square(ai_move[:2])
                    to_square = chess.parse_square(ai_move[2:4])
                    piece = board.piece_at(from_square)

                    # Check if this is a pawn promotion
                    if piece and piece.piece_type == chess.PAWN:
                        if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                           (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                            # Auto-promote to queen
                            ai_move += "q"
                            logger.info(f"Auto-promoting AI pawn in AI-vs-AI: {ai_move}")

                try:
                    board.push_uci(ai_move)
                except:
                    # If AI move is invalid, fallback to random legal move
                    legal_moves = list(board.legal_moves)
                    if legal_moves:
                        ai_move = random.choice([m.uci() for m in legal_moves])
                        board.push_uci(ai_move)
            else:
                # When rules are disabled, try to make the move but don't fail if invalid
                try:
                    board.push_uci(ai_move)
                except:
                    # If it fails, we'll still save it as a move
                    pass

            add_move(db, game_id, ai_move)
            moves.append(ai_move)
            return {"fen": board.fen(), "moves": moves, "status": "ok", "ai_move": ai_move}
        else:
            logger.warning("AI did not return any move in AI-vs-AI")
            return {"fen": board.fen(), "moves": moves, "status": "no_move"}

    return {"fen": board.fen(), "moves": moves, "status": "no_move"}

@router.get("/api/games")
def api_get_all_games(db: Session = Depends(get_db)):
    """
    Get all games for history display
    Returns: [{id, white_player, black_player, created_at, move_count, status, result, termination}]
    """
    logger.info("Loading game history - starting request")
    from sqlalchemy import func
    try:
        logger.debug("Querying database for games")
        games = db.query(Game).order_by(Game.created_at.desc()).limit(50).all()
        logger.info(f"Found {len(games)} games in database")

        result = []
        for game in games:
            try:
                logger.debug(f"Processing game {game.id}")
                # Count moves
                move_count = db.query(func.count(Move.id)).filter(Move.game_id == game.id).scalar() or 0

                # Safely get player names
                white_name = "Unknown"
                black_name = "Unknown"
                try:
                    if game.white:
                        white_name = game.white.name
                except Exception as e:
                    logger.warning(f"Error getting white player name for game {game.id}: {e}")
                try:
                    if game.black:
                        black_name = game.black.name
                except Exception as e:
                    logger.warning(f"Error getting black player name for game {game.id}: {e}")

                # Determine game status from database
                is_finished = getattr(game, 'is_finished', 'false')
                if is_finished == "true":
                    status = "Finished"
                    # Format result description
                    game_result = getattr(game, 'result', None)
                    if game_result == "1-0":
                        result_desc = f"{white_name} wins"
                    elif game_result == "0-1":
                        result_desc = f"{black_name} wins"
                    elif game_result == "1/2-1/2":
                        result_desc = "Draw"
                    else:
                        result_desc = game_result or "Game finished"

                    # Add termination reason if available
                    termination = getattr(game, 'termination', None)
                    if termination:
                        result_desc += f" by {termination}"
                else:
                    status = "In Progress"
                    result_desc = "Game ongoing"

                # Safely format dates
                created_at_str = "Unknown"
                finished_at_str = None
                try:
                    if game.created_at:
                        created_at_str = game.created_at.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.warning(f"Error formatting created_at for game {game.id}: {e}")

                try:
                    finished_at = getattr(game, 'finished_at', None)
                    if finished_at:
                        finished_at_str = finished_at.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.warning(f"Error formatting finished_at for game {game.id}: {e}")

                result.append({
                    "id": game.id,
                    "white_player": white_name,
                    "black_player": black_name,
                    "created_at": created_at_str,
                    "move_count": move_count,
                    "status": status,
                    "result": getattr(game, 'result', None),
                    "result_description": result_desc,
                    "termination": getattr(game, 'termination', None),
                    "finished_at": finished_at_str
                })
                logger.debug(f"Successfully processed game {game.id}")
            except Exception as e:
                logger.warning(f"Error processing game {game.id}: {e}")
                # Skip this game but continue with others
                continue

        logger.info(f"Successfully processed {len(result)} games for history display")
        return {"games": result}
    except Exception as e:
        logger.error(f"Error loading games: {e}", exc_info=True)
        return {"games": [], "error": f"Failed to load games: {str(e)}"}@router.get("/api/game/{game_id}/moves")
def api_get_game_moves(game_id: int, db: Session = Depends(get_db)):
    """
    Get all moves for a specific game
    Returns: {game_info, moves: [{move_number, white_move, black_move}]}
    """
    game = get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    moves = db.query(Move).filter(Move.game_id == game_id).order_by(Move.id).all()

    # Group moves by pairs (white, black)
    move_pairs = []
    for i in range(0, len(moves), 2):
        white_move = moves[i].move if i < len(moves) else ""
        black_move = moves[i + 1].move if i + 1 < len(moves) else ""
        move_pairs.append({
            "move_number": (i // 2) + 1,
            "white_move": white_move,
            "black_move": black_move
        })

    return {
        "game_info": {
            "id": game.id,
            "white_player": game.white.name if game.white else "Unknown",
            "black_player": game.black.name if game.black else "Unknown",
            "created_at": game.created_at.strftime("%Y-%m-%d %H:%M:%S")
        },
        "moves": move_pairs
    }

def get_ai_move(ai_engine, board, board_fen, move_history, enforce_rules=True, game_id=None):
    """
    Get AI move based on the selected engine, with optional session support
    """
    logger.debug(f"Getting AI move with engine: {ai_engine}, enforce_rules: {enforce_rules}")

    # Create session ID for strategic continuity
    session_id = None
    if game_id:
        # Determine which color is to move based on move count
        move_count = len(move_history)
        current_player_color = "white" if move_count % 2 == 0 else "black"
        session_id = f"game_{game_id}_{current_player_color}_{ai_engine}"

        # Create session if it doesn't exist
        try:
            from app.ai.ai_session_manager import session_manager
            existing_session = session_manager.get_session(session_id)
            if not existing_session:
                session_manager.create_session(session_id, ai_engine)
                logger.info(f"Created AI session: {session_id}")
        except Exception as e:
            logger.warning(f"Could not create AI session: {e}")
            session_id = None

    if ai_engine == 'openai':
        try:
            move = get_openai_chess_move(board_fen, move_history, session_id)
            if move:
                logger.info(f"OpenAI returned move: {move}")
                return move
            else:
                logger.warning("OpenAI returned no move")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to random move
            ai_engine = 'random'
    elif ai_engine == 'gemini':
        try:
            move = get_gemini_chess_move(board_fen, move_history, session_id)
            if move:
                logger.info(f"Gemini returned move: {move}")
                return move
            else:
                logger.warning("Gemini returned no move")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Fallback to random move
            ai_engine = 'random'

    # Random moves (fallback or selected)
    if enforce_rules:
        legal_moves = list(board.legal_moves)
        if legal_moves:
            random_move = random.choice([m.uci() for m in legal_moves])
            logger.info(f"Using random legal move: {random_move}")
            return random_move
        else:
            logger.error("No legal moves available!")
            return None
    else:
        # Generate random move when rules are disabled
        squares = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8',
                  'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8',
                  'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8',
                  'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8',
                  'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8',
                  'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8',
                  'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8',
                  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8']
        from_square = random.choice(squares)
        to_square = random.choice(squares)
        # Ensure different squares
        while to_square == from_square:
            to_square = random.choice(squares)
        random_move = from_square + to_square
        logger.info(f"Using random move (rules disabled): {random_move}")
        return random_move

    logger.error("Failed to generate any move")
    return None
