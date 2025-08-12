#!/usr/bin/env python3
"""
Test script to verify checkmate detection and database saving functionality
"""
import chess
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

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
        try:
            board.push_uci(move)
            print(f"Move: {move}, Game over: {board.is_game_over()}")
        except Exception as e:
            print(f"Error with move {move}: {e}")
            return False

    # Check final state
    print(f"Final position - Game over: {board.is_game_over()}")
    print(f"Is checkmate: {board.is_checkmate()}")
    print(f"Result: {board.result()}")
    print(f"Termination: {get_game_termination(board)}")

    return board.is_game_over() and board.is_checkmate()

def test_database_update():
    """Test database update functionality"""
    try:
        # Setup database connection
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chess:chess@localhost:5432/chess")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Create test players
        white_player = create_player(db, "Test White")
        black_player = create_player(db, "Test Black")

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

        db.close()
        return True

    except Exception as e:
        print(f"Database test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing checkmate detection...")
    if test_checkmate_detection():
        print("✓ Checkmate detection works!")
    else:
        print("✗ Checkmate detection failed!")

    print("\nTesting database update...")
    if test_database_update():
        print("✓ Database update works!")
    else:
        print("✗ Database update failed!")
