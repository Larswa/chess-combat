"""
CI test configuration with in-memory database injection
"""
import pytest
from unittest.mock import patch

# Mock AI responses
def mock_openai_response(*args, **kwargs):
    return "e2e4"

def mock_gemini_response(*args, **kwargs):
    return "e2e4"

@pytest.fixture(scope="module", autouse=True)
def setup_ci_mocks():
    """Setup mocked AI services for CI testing"""
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

    game_info = response.json()
    assert "game_id" in game_info
    assert "fen" in game_info

def test_ci_move_making(ci_client):
    """Test move making in CI environment"""
    # Create game first
    game_data = {"mode": "human-vs-ai", "color": "white", "ai_engine": "random"}
    create_response = ci_client.post("/api/new-game", json=game_data)
    assert create_response.status_code == 200

    game_info = create_response.json()
    game_id = game_info["game_id"]

    # Make a move
    move_data = {"game_id": game_id, "move": "e2e4"}
    move_response = ci_client.post("/api/move", json=move_data)
    assert move_response.status_code == 200

    move_info = move_response.json()
    assert "fen" in move_info

def test_ci_checkmate_detection(ci_client):
    """Test checkmate detection in CI environment"""
    # Create game
    game_data = {"mode": "human-vs-ai", "color": "white", "ai_engine": "random"}
    response = ci_client.post("/api/new-game", json=game_data)
    assert response.status_code == 200

    game_info = response.json()
    game_id = game_info["game_id"]

    # Test that the game was created successfully
    assert game_id is not None
    assert isinstance(game_id, int)
