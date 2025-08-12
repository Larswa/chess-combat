"""
Simple workflow integration test
"""
import os

def test_environment_variables():
    """Test that required environment variables are set"""
    # These should be set by the CI workflow
    assert os.getenv("DATABASE_URL") is not None
    assert os.getenv("OPENAI_API_KEY") is not None
    assert os.getenv("GEMINI_API_KEY") is not None
    print(f"Database URL: {os.getenv('DATABASE_URL')}")
    print(f"OpenAI key set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    print(f"Gemini key set: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")

def test_sqlite_in_memory():
    """Test that SQLite in-memory database works"""
    from sqlalchemy import create_engine, text

    # This should work in CI
    engine = create_engine("sqlite:///:memory:")
    connection = engine.connect()
    result = connection.execute(text("SELECT 1 as test_value")).fetchone()
    assert result[0] == 1
    connection.close()
    print("✓ SQLite in-memory database working")

def test_imports():
    """Test that all critical imports work"""
    import chess
    import fastapi
    import sqlalchemy
    import pytest

    # Test chess library
    board = chess.Board()
    assert not board.is_game_over()

    print("✓ All critical imports successful")
