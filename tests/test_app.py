import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

# Unit test: does not require DB

def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Chess Combat Service" in response.json().get("message", "")

# Unit test: AI is mocked, no DB required
@patch("app.main.get_openai_chess_move", return_value="e2e4")
def test_ai_vs_ai(mock_ai):
    client = TestClient(app)
    response = client.post("/ai-vs-ai/", json={"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "moves": []})
    assert response.status_code == 200
    assert "fen" in response.json()
    assert "move_history" in response.json()
