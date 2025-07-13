# Entry point for the FastAPI app
from fastapi import FastAPI, Depends, Body, Query, status, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.ui.routes import router as ui_router
from app.db.crud import SessionLocal, get_game, create_player
from app.db.models import Base
from app.ai.openai_ai import get_openai_chess_move
from app.ai.gemini_ai import get_gemini_chess_move
import chess
from contextlib import asynccontextmanager
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
import logging
import os
from app.logging_config import setup_logging

# Setup logging
debug_mode = os.getenv("DEBUG", "false").lower() == "true"
setup_logging(debug=debug_mode)
logger = logging.getLogger(__name__)

class PlayerCreate(BaseModel):
    name: str

class GameCreate(BaseModel):
    white_id: int
    black_id: int

class MoveCreate(BaseModel):
    move: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("Starting up Chess Combat FastAPI application")
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=SessionLocal.kw["bind"])
    logger.info("Database tables created successfully")
    yield
    # Shutdown code (if any)
    logger.info("Shutting down Chess Combat FastAPI application")

app = FastAPI(lifespan=lifespan)
app.include_router(ui_router)

# Mount static files (for custom JS/CSS if needed)
import os
static_dir = os.path.join(os.path.dirname(__file__), "ui", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Dependency for DB session
def get_db():
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing database session")
        db.close()

# Example endpoint using DB
@app.get("/games/{game_id}")
def read_game(game_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching game with ID: {game_id}")
    game = get_game(db, game_id)
    if not game:
        logger.warning(f"Game with ID {game_id} not found")
        return {"error": "Game not found"}
    logger.info(f"Successfully retrieved game {game_id}")
    return {"id": game.id, "white_id": game.white_id, "black_id": game.black_id, "created_at": str(game.created_at)}

@app.post("/players/")
def create_player_endpoint(player: PlayerCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new player: {player.name}")
    try:
        player_obj = create_player(db, player.name)
        logger.info(f"Successfully created player with ID: {player_obj.id}")
        return {"id": player_obj.id, "name": player_obj.name}
    except IntegrityError:
        logger.warning(f"Player creation failed - name '{player.name}' already exists")
        db.rollback()
        raise HTTPException(status_code=409, detail="Player name already exists")

@app.post("/games/", status_code=status.HTTP_200_OK)
def create_game_endpoint(game: GameCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new game: white_id={game.white_id}, black_id={game.black_id}")
    from app.db.crud import create_game
    game_obj = create_game(db, game.white_id, game.black_id)
    logger.info(f"Successfully created game with ID: {game_obj.id}")
    return {"id": game_obj.id, "white_id": game_obj.white_id, "black_id": game_obj.black_id}

@app.post("/games/{game_id}/moves", status_code=status.HTTP_200_OK)
def add_move_endpoint(game_id: int, move: MoveCreate, db: Session = Depends(get_db)):
    logger.info(f"Adding move '{move.move}' to game {game_id}")
    from app.db.crud import add_move
    move_obj = add_move(db, game_id, move.move)
    logger.info(f"Successfully added move with ID: {move_obj.id}")
    return {"id": move_obj.id, "game_id": move_obj.game_id, "move": move_obj.move}

@app.post("/ai-vs-ai/")
def ai_vs_ai(
    fen: str = Body(chess.STARTING_FEN),
    moves: list = Body(default=[]),
    ai: str = Query("openai", description="Which AI to use: 'openai' or 'gemini'"),
    enforce_rules: bool = Query(True, description="Enforce chess rules (illegal moves not allowed)"),
    auto_play: bool = Query(False, description="If true, play until game over automatically")
):
    logger.info(f"Starting AI vs AI game - AI: {ai}, auto_play: {auto_play}, enforce_rules: {enforce_rules}")
    logger.debug(f"Starting FEN: {fen}")
    logger.debug(f"Initial moves: {moves}")

    board = chess.Board(fen)
    move_history = moves.copy()
    ai_moves = []
    invalid_moves = []
    position_invalid_moves = {}  # Track invalid moves per FEN position

    def get_ai_move(current_fen):
        logger.debug(f"Requesting move from {ai} AI")
        # Get invalid moves for this position
        invalid_for_position = position_invalid_moves.get(current_fen, [])

        if ai == "gemini":
            return get_gemini_chess_move(current_fen, move_history, invalid_for_position)
        else:
            return get_openai_chess_move(current_fen, move_history, invalid_for_position)

    def play_one_move():
        current_fen = board.fen()
        max_attempts = 5  # Maximum retry attempts for each move

        for attempt in range(max_attempts):
            logger.debug(f"Move attempt {attempt + 1}/{max_attempts}")
            move_uci = get_ai_move(current_fen)
            logger.info(f"AI suggested move: {move_uci} (attempt {attempt + 1})")

            try:
                move = chess.Move.from_uci(move_uci)
                if move in board.pseudo_legal_moves:
                    if enforce_rules:
                        if move in board.legal_moves:
                            board.push(move)
                            move_history.append(move_uci)
                            ai_moves.append(move_uci)
                            logger.info(f"Move {move_uci} accepted and played on attempt {attempt + 1}")
                            return True, None
                        else:
                            reason = "illegal"
                            logger.warning(f"Move {move_uci} is illegal (attempt {attempt + 1})")
                    else:
                        board.push(move)
                        move_history.append(move_uci)
                        ai_moves.append(move_uci)
                        logger.info(f"Move {move_uci} played (rules not enforced)")
                        return True, None
                else:
                    reason = "not pseudo-legal"
                    logger.warning(f"Move {move_uci} is not pseudo-legal (attempt {attempt + 1})")

                # Track this invalid move for the current position
                if current_fen not in position_invalid_moves:
                    position_invalid_moves[current_fen] = []
                position_invalid_moves[current_fen].append(move_uci)

                invalid_moves.append({
                    "move": move_uci,
                    "fen": current_fen,
                    "reason": reason,
                    "attempt": attempt + 1
                })

            except Exception as e:
                reason = str(e)
                logger.error(f"Error processing move {move_uci}: {reason} (attempt {attempt + 1})")

                # Track this invalid move for the current position
                if current_fen not in position_invalid_moves:
                    position_invalid_moves[current_fen] = []
                position_invalid_moves[current_fen].append(move_uci)

                invalid_moves.append({
                    "move": move_uci,
                    "fen": current_fen,
                    "reason": reason,
                    "attempt": attempt + 1
                })

        # If we've exhausted all attempts, try to make any legal move
        logger.warning(f"Failed to get valid move after {max_attempts} attempts, trying any legal move")
        legal_moves = list(board.legal_moves)
        if legal_moves:
            fallback_move = legal_moves[0]
            board.push(fallback_move)
            move_history.append(fallback_move.uci())
            ai_moves.append(fallback_move.uci())
            logger.info(f"Used fallback legal move: {fallback_move.uci()}")
            return True, None
        else:
            logger.error("No legal moves available - game should be over")
            return False, "No legal moves available"

    if auto_play:
        logger.info("Starting auto-play mode")
        move_count = 0
        while not board.is_game_over():
            move_count += 1
            logger.debug(f"Auto-play move {move_count}")
            play_one_move()
            if move_count > 200:  # Safety limit
                logger.warning("Auto-play stopped due to move limit (200)")
                break
        logger.info(f"Auto-play completed after {move_count} moves")
    else:
        logger.info("Playing 2 moves (one for each side)")
        for i in range(2):  # Each AI makes one move (white, then black)
            if board.is_game_over():
                logger.info(f"Game over after {i} moves")
                break
            logger.debug(f"Playing move {i+1}/2")
            play_one_move()

    result = {
        "fen": board.fen(),
        "move_history": move_history,
        "ai_moves": ai_moves,
        "invalid_moves": invalid_moves,
        "game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None
    }

    logger.info(f"AI vs AI game completed. Total moves: {len(ai_moves)}, Invalid moves: {len(invalid_moves)}")
    if board.is_game_over():
        logger.info(f"Game result: {board.result()}")

    return result
