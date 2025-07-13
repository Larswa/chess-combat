# UI/API routes for FastAPI
from fastapi import APIRouter, Request, Body, status, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.db.crud import get_game, create_game, add_move, create_player
from app.db.models import Game, Move
from app.db.deps import get_db
from sqlalchemy.orm import Session
import os
import chess

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


# Main UI route

@router.get("/", response_class=HTMLResponse)
def chess_game(request: Request):
    return templates.TemplateResponse(request, "chess_game.html")

# --- API for UI ---

@router.post("/api/new-game")
def api_new_game(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Create a new game. Expects: {mode: 'human-vs-ai'|'ai-vs-ai', color: 'white'|'black'}
    Returns: {game_id, fen, moves: []}
    """
    mode = data.get('mode')
    color = data.get('color')
    # For now, create two players (Human and AI) or two AIs
    if mode == 'human-vs-ai':
        white_name = 'Human' if color == 'white' else 'AI'
        black_name = 'AI' if color == 'white' else 'Human'
    else:
        white_name = 'AI1'
        black_name = 'AI2'
    # Ensure players exist
    white_player = create_player(db, white_name)
    black_player = create_player(db, black_name)
    # Create game
    game = create_game(db, white_player.id, black_player.id)
    board = chess.Board()
    return {"game_id": game.id, "fen": board.fen(), "moves": []}

@router.post("/api/move")
def api_move(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Make a move. Expects: {game_id, move: 'e2e4', enforce_rules: true/false}
    Returns: {fen, moves, status}
    """
    game_id = data.get('game_id')
    move_uci = data.get('move')
    enforce_rules = data.get('enforce_rules', True)  # Default to True

    game = get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Rebuild board from moves
    import chess
    board = chess.Board()
    moves = [m.move for m in game.moves]
    for m in moves:
        if enforce_rules:
            board.push_uci(m)
        else:
            # If rules are not enforced, we need to manually update the board
            try:
                board.push_uci(m)
            except:
                # If the move is invalid, create a new board and set position manually
                pass

    # Try to make the move
    if enforce_rules:
        try:
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

    # Check if this is a human-vs-ai game and not over
    white_player = getattr(game, 'white_id', None)
    black_player = getattr(game, 'black_id', None)
    # Use player names to determine mode (simple logic)
    mode = None
    if hasattr(game, 'white') and hasattr(game, 'black'):
        if (game.white.name == 'Human' and game.black.name == 'AI') or (game.white.name == 'AI' and game.black.name == 'Human'):
            mode = 'human-vs-ai'
    if mode == 'human-vs-ai' and (not enforce_rules or not board.is_game_over()):
        # AI move
        import random
        if enforce_rules:
            # AI makes random legal move when rules are enforced
            legal_moves = list(board.legal_moves)
            if legal_moves:
                ai_move = random.choice([m.uci() for m in legal_moves])
                board.push_uci(ai_move)
                add_move(db, game_id, ai_move)
                moves.append(ai_move)
                return {"fen": board.fen(), "moves": moves, "status": "ok", "ai_move": ai_move}
        else:
            # AI makes any random move when rules are not enforced
            # Generate a random move from any square to any square
            squares = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8',
                      'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8',
                      'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8',
                      'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8',
                      'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8',
                      'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8',
                      'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8',
                      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8']
            ai_move = random.choice(squares) + random.choice(squares)
            # Don't validate the move, just save it
            add_move(db, game_id, ai_move)
            moves.append(ai_move)
            return {"fen": board.fen(), "moves": moves, "status": "ok", "ai_move": ai_move}
    return {"fen": board.fen(), "moves": moves, "status": "ok"}

@router.get("/api/game/{game_id}")
def api_get_game(game_id: int, db: Session = Depends(get_db)):
    """
    Get game state. Returns: {fen, moves, status}
    """
    game = get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    import chess
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
