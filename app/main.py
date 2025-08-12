# Entry point for the FastAPI app
from fastapi import FastAPI, Depends, Body, Query, status, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.ui.routes import router as ui_router
from app.db.crud import get_session_local, get_game, create_player
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
    try:
        logger.info("Creating database tables...")
        from app.db.crud import get_engine
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.info("Running without database - some features may be limited")
    yield
    # Shutdown code (if any)
    logger.info("Shutting down Chess Combat FastAPI application")

def create_app(test_engine=None):
    """Factory function to create the FastAPI app with optional test database injection"""
    if test_engine:
        # Inject test database before creating the app
        from app.db.crud import set_database_engine
        set_database_engine(test_engine)

    app = FastAPI(lifespan=lifespan)

    # Include routers
    app.include_router(ui_router)

    # Mount static files (for custom JS/CSS if needed)
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "ui", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    return app

# Create the default app instance
app = create_app()

# Dependency for DB session
def get_db():
    logger.debug("Creating new database session")
    SessionLocal = get_session_local()
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
        from app.db.crud import create_player_strict
        player_obj = create_player_strict(db, player.name)
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
    auto_play: bool = Query(False, description="If true, play until game over automatically"),
    max_moves: int = Query(100, description="Maximum moves to play in auto mode")
):
    """
    Simple AI vs AI chess game.
    Just presents board state to AI and implements their move decisions.
    """
    logger.info(f"Starting AI vs AI game - AI: {ai}, auto_play: {auto_play}")
    logger.debug(f"Starting FEN: {fen}")
    logger.debug(f"Initial moves: {moves}")

    board = chess.Board(fen)
    move_history = moves.copy()
    ai_moves = []
    invalid_moves = []

    def get_ai_move():
        """Get move from AI - just present board state and invalid moves"""
        logger.debug(f"Requesting move from {ai} AI")
        current_fen = board.fen()

        # Get recent invalid moves to avoid
        recent_invalid = [im["move"] for im in invalid_moves[-3:] if im.get("move")]

        if ai == "gemini":
            from app.ai.gemini_ai import get_gemini_chess_move
            return get_gemini_chess_move(current_fen, move_history, recent_invalid)
        else:
            from app.ai.openai_ai import get_openai_chess_move
            return get_openai_chess_move(current_fen, move_history, recent_invalid)

    def play_one_move():
        """Play one move with simple retry logic"""
        logger.debug("Playing one move...")
        current_fen = board.fen()

        # Simple retry logic (max 3 attempts)
        max_attempts = 3
        for attempt in range(max_attempts):
            move_uci = get_ai_move()
            logger.info(f"AI suggested move (attempt {attempt + 1}): {move_uci}")

            if not move_uci:
                logger.error("AI returned no move")
                invalid_moves.append({"move": "none", "fen": current_fen, "reason": "no_move_returned"})
                continue

            try:
                move = chess.Move.from_uci(move_uci)

                if enforce_rules:
                    if move in board.legal_moves:
                        # Valid move - play it
                        board.push(move)
                        move_history.append(move_uci)
                        ai_moves.append(move_uci)
                        logger.info(f"Move {move_uci} accepted and played")
                        return True
                    else:
                        logger.warning(f"Move {move_uci} is illegal (attempt {attempt + 1})")
                        invalid_moves.append({"move": move_uci, "fen": current_fen, "reason": "illegal"})
                else:
                    # Rules not enforced - play any pseudo-legal move
                    if move in board.pseudo_legal_moves:
                        board.push(move)
                        move_history.append(move_uci)
                        ai_moves.append(move_uci)
                        logger.info(f"Move {move_uci} played (rules not enforced)")
                        return True
                    else:
                        logger.warning(f"Move {move_uci} is not pseudo-legal (attempt {attempt + 1})")
                        invalid_moves.append({"move": move_uci, "fen": current_fen, "reason": "not_pseudo_legal"})

            except ValueError as e:
                logger.warning(f"Invalid move format '{move_uci}': {e} (attempt {attempt + 1})")
                invalid_moves.append({"move": move_uci, "fen": current_fen, "reason": f"invalid_format: {e}"})

        logger.error(f"Failed to get valid move after {max_attempts} attempts")
        return False

    # Execute the game
    if auto_play:
        logger.info("Starting auto-play mode")
        move_count = 0
        while not board.is_game_over() and move_count < max_moves:
            move_count += 1
            logger.debug(f"Auto-play move {move_count}")
            success = play_one_move()
            if not success:
                logger.error(f"Auto-play stopped due to repeated invalid moves at move {move_count}")
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


# Health check endpoint
@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "chess-combat"}
