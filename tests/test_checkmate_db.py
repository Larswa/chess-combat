#!/usr/bin/env python3
"""
Test script to verify checkmate detection and database saving functionality
"""
import chess
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.models import Game, Player, Move
from app.db.crud import create_player, create_game, add_move, update_game_result
from app.db.deps import get_db
from app.ui.routes_fixed import get_game_termination, check_and_update_game_result
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_checkmate_detection():
    """Test that checkmate is properly detected and saved"""
    # Create a checkmate position (Fool's mate)
    board = chess.Board()
    moves = ["f2f3", "e7e5", "g2g4", "d8h4"]  # Fool's mate

    for move in moves:
        board.push_uci(move)
        print(f"Move: {move}, Game over: {board.is_game_over()}")

    # Check final state
    print(f"Final position - Game over: {board.is_game_over()}")
    print(f"Is checkmate: {board.is_checkmate()}")
    print(f"Result: {board.result()}")
    print(f"Termination: {get_game_termination(board)}")

    # Use assertions instead of return
    assert board.is_game_over(), "Game should be over"
    assert board.is_checkmate(), "Position should be checkmate"
    assert board.result() == "0-1", "Black should win"
    assert get_game_termination(board) == "checkmate", "Termination should be checkmate"

def test_database_update():
    """Test database update functionality"""
    # Setup database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chess:chess@localhost:5432/chess")
    engine = create_engine(DATABASE_URL)

    # Create tables if they don't exist (needed for SQLite in-memory)
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Create test players
    white_player = create_player(db, f"Test White {os.getpid()}")
    black_player = create_player(db, f"Test Black {os.getpid()}")

    # Create test game
    game = create_game(db, white_player.id, black_player.id)
    print(f"Created test game with ID: {game.id}")

    # Test checkmate position
    board = chess.Board()
    moves = ["f2f3", "e7e5", "g2g4", "d8h4"]  # Fool's mate

    for move in moves:
        board.push_uci(move)
        add_move(db, game.id, move)

    # Update game result
    result = board.result()
    termination = get_game_termination(board)
    updated_game = update_game_result(db, game.id, result, termination)

    print(f"Game {game.id} updated with result: {updated_game.result}, termination: {updated_game.termination}")
    print(f"Is finished: {updated_game.is_finished}, Finished at: {updated_game.finished_at}")

    # Use assertions instead of return
    assert updated_game is not None, "Game should be updated successfully"
    assert updated_game.result == "0-1", "Result should be 0-1 (black wins)"
    assert updated_game.termination == "checkmate", "Termination should be checkmate"
    assert updated_game.is_finished == "true", "Game should be marked as finished"
    assert updated_game.finished_at is not None, "Finished timestamp should be set"

    db.close()
