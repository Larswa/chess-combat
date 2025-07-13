# UI/API routes for FastAPI
from fastapi import APIRouter, Request
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
def index():
    logger.info("Index endpoint accessed")
    return {"message": "Chess Combat Service"}

@router.post("/move")
def submit_move(move: str):
    logger.info(f"Move submitted: {move}")
    # Accept move from human player
    return {"status": "received", "move": move}
