import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

# Unit test: does not require DB

def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

# Unit test: AI is mocked, no DB required
@patch("app.main.get_openai_chess_move", return_value="e2e4")
def test_ai_vs_ai(mock_ai):
    client = TestClient(app)
    response = client.post("/ai-vs-ai/", json={"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "moves": []})
    assert response.status_code == 200
    assert "fen" in response.json()
    assert "move_history" in response.json()

# Unit test for create_player (no DB commit)
def test_create_player_model():
    from app.db.models import Player
    player = Player(name="unit-test-player")
    assert player.name == "unit-test-player"

# Unit test for move model
def test_move_model():
    from app.db.models import Move
    move = Move(game_id=1, move="e2e4")
    assert move.move == "e2e4"
    assert move.game_id == 1
