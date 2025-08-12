"""
In-memory test configuration for CI/build agents
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.db.models import Base

@pytest.fixture(scope="function")
def test_client():
    """Create test client with in-memory database"""
    # Create in-memory SQLite engine with StaticPool
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

def test_in_memory_checkmate(test_client):
    """Test checkmate detection using in-memory database"""
    # Create a game in human vs human mode for full control
    game_data = {
        "mode": "human-vs-human",
        "color": "white",
        "ai_engine": "random"
    }
    response = test_client.post("/api/new-game", json=game_data)
    assert response.status_code == 200

    game_info = response.json()
    game_id = game_info["game_id"]

    # Play fool's mate sequence
    moves = ["f2f3", "e7e5", "g2g4", "d8h4"]

    for move in moves:
        move_data = {
            "game_id": game_id,
            "move": move,
            "enforce_rules": True
        }
        response = test_client.post("/api/move", json=move_data)
        assert response.status_code == 200

    # Check final game state
    response = test_client.get(f"/api/game/{game_id}")
    assert response.status_code == 200

    game_state = response.json()
    assert game_state["status"] == "game_over"
