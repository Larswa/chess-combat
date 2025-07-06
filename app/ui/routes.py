# UI/API routes for FastAPI
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/")
def index():
    return {"message": "Chess Combat Service"}

@router.post("/move")
def submit_move(move: str):
    # Accept move from human player
    return {"status": "received", "move": move}
