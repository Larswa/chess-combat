# Entry point for the FastAPI app
from fastapi import FastAPI, Depends, Body, Query
from sqlalchemy.orm import Session
from app.ui.routes import router as ui_router
from app.db.crud import SessionLocal, get_game, create_player
from app.db.models import Base
from app.ai.openai_ai import get_openai_chess_move
from app.ai.gemini_ai import get_gemini_chess_move
import chess
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    Base.metadata.create_all(bind=SessionLocal.kw["bind"])
    yield
    # Shutdown code (if any)

app = FastAPI(lifespan=lifespan)
app.include_router(ui_router)

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Example endpoint using DB
@app.get("/games/{game_id}")
def read_game(game_id: int, db: Session = Depends(get_db)):
    game = get_game(db, game_id)
    if not game:
        return {"error": "Game not found"}
    return {"id": game.id, "white_id": game.white_id, "black_id": game.black_id, "created_at": str(game.created_at)}

@app.post("/players/")
def create_player_endpoint(name: str = Body(...), db: Session = Depends(get_db)):
    player = create_player(db, name)
    return {"id": player.id, "name": player.name}

@app.post("/ai-vs-ai/")
def ai_vs_ai(
    fen: str = Body(chess.STARTING_FEN),
    moves: list = Body(default=[]),
    ai: str = Query("openai", description="Which AI to use: 'openai' or 'gemini'"),
    enforce_rules: bool = Query(True, description="Enforce chess rules (illegal moves not allowed)"),
    auto_play: bool = Query(False, description="If true, play until game over automatically")
):
    board = chess.Board(fen)
    move_history = moves.copy()
    ai_moves = []
    invalid_moves = []
    def get_ai_move():
        if ai == "gemini":
            return get_gemini_chess_move(board.fen(), move_history)
        else:
            return get_openai_chess_move(board.fen(), move_history)
    def play_one_move():
        move_uci = get_ai_move()
        try:
            move = chess.Move.from_uci(move_uci)
            if move in board.pseudo_legal_moves:
                if enforce_rules:
                    if move in board.legal_moves:
                        board.push(move)
                        move_history.append(move_uci)
                        ai_moves.append(move_uci)
                    else:
                        invalid_moves.append({"move": move_uci, "fen": board.fen(), "reason": "illegal"})
                else:
                    board.push(move)
                    move_history.append(move_uci)
                    ai_moves.append(move_uci)
            else:
                invalid_moves.append({"move": move_uci, "fen": board.fen(), "reason": "not pseudo-legal"})
            return True, None
        except Exception as e:
            invalid_moves.append({"move": move_uci, "fen": board.fen(), "reason": str(e)})
            return True, None  # Continue autoplay
    if auto_play:
        while not board.is_game_over():
            play_one_move()
    else:
        for _ in range(2):  # Each AI makes one move (white, then black)
            if board.is_game_over():
                break
            play_one_move()
    return {
        "fen": board.fen(),
        "move_history": move_history,
        "ai_moves": ai_moves,
        "invalid_moves": invalid_moves,
        "game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None
    }
