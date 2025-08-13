"""
CI-friendly test configuration with mocked dependencies
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Mock environment variables for CI
os.environ.setdefault("OPENAI_API_KEY", "mock-key-for-testing")
os.environ.setdefault("GEMINI_API_KEY", "mock-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Mock AI responses
def mock_openai_response(*args, **kwargs):
    """Mock OpenAI API response"""
    return "e2e4"  # Simple move

def mock_gemini_response(*args, **kwargs):
    """Mock Gemini API response"""
    return "e2e4"  # Simple move

@pytest.fixture(scope="module", autouse=True)
def setup_ci_mocks():
    """Setup mocked AI services for CI testing"""
    # Start with mocked AI services
    with patch('app.ai.openai_ai.get_openai_chess_move', side_effect=mock_openai_response), \
         patch('app.ai.gemini_ai.get_gemini_chess_move', side_effect=mock_gemini_response):
        yield

@pytest.fixture(scope="function")
def ci_client():
    """Test client with injected test database"""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base

    # Create test database with StaticPool to ensure shared in-memory database
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create app with injected test database
    from app.main import create_app
    app = create_app(test_engine=test_engine)

    with TestClient(app) as client:
        yield client

def test_ci_game_creation(ci_client):
    """Test game creation in CI environment"""
    game_data = {
        "mode": "human-vs-ai",
        "color": "white",
        "ai_engine": "random"
    }
    response = ci_client.post("/api/new-game", json=game_data)
    assert response.status_code == 200
    data = response.json()
    assert "game_id" in data
    assert "fen" in data

def test_ci_move_making(ci_client):
    """Test move making in CI environment"""
    # Create game
    game_data = {"mode": "human-vs-ai", "color": "white", "ai_engine": "random"}
    response = ci_client.post("/api/new-game", json=game_data)
    game_id = response.json()["game_id"]

    # Make move
    move_data = {
        "game_id": game_id,
        "move": "e2e4",
        "ai_engine": "random",
        "enforce_rules": True
    }
    response = ci_client.post("/api/move", json=move_data)
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"  # Game should be in progress after a valid move

def test_ci_checkmate_detection(ci_client):
    """Test checkmate detection in CI environment"""
    # Create game in human vs human mode to have full control
    game_data = {"mode": "human-vs-human", "color": "white", "ai_engine": "random"}
    response = ci_client.post("/api/new-game", json=game_data)
    game_id = response.json()["game_id"]

    # Play fool's mate - fastest checkmate in chess
    # 1. f3 e5 2. g4 Qh4#
    moves = ["f2f3", "e7e5", "g2g4", "d8h4"]

    for i, move in enumerate(moves):
        move_data = {
            "game_id": game_id,
            "move": move,
            "enforce_rules": True
        }
        response = ci_client.post("/api/move", json=move_data)
        assert response.status_code == 200

        move_result = response.json()
        print(f"Move {i+1}: {move} -> FEN: {move_result.get('fen', 'N/A')}")
        print(f"Move {i+1}: Status: {move_result.get('status', 'N/A')}")

    # The key insight: check if the final move response indicates checkmate
    # The status should now indicate checkmate
    final_status = move_result.get('status', 'unknown')
    print(f"Final move status: {final_status}")

    # Check both the status message and the chess board state
    assert "checkmate" in final_status.lower(), f"Status should indicate checkmate, but got: {final_status}"

    # Also verify with chess library
    final_fen = move_result.get('fen')
    if final_fen:
        import chess
        board = chess.Board(final_fen)
        print(f"Board from final FEN is_game_over: {board.is_game_over()}")
        print(f"Board from final FEN is_checkmate: {board.is_checkmate()}")

        # This should be True if our move sequence worked
        assert board.is_game_over(), f"Game should be over after fool's mate, but board state is: {final_fen}"
        assert board.is_checkmate(), f"Should be checkmate after fool's mate, but board state is: {final_fen}"
    else:
        pytest.fail("No FEN returned from final move")

if __name__ == "__main__":
    # Run as standalone script for CI
    import subprocess
    result = subprocess.run(["python", "-m", "pytest", __file__, "-v"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    exit(result.returncode)
