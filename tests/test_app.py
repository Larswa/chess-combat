import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, mock_open
import os

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

# Unit tests for version functionality
def test_version_api_endpoint():
    """Test the /api/version endpoint returns proper JSON structure"""
    client = TestClient(app)
    response = client.get("/api/version")
    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert "build_date" in data
    assert "name" in data
    assert data["name"] == "Chess Combat"

@patch.dict(os.environ, {"BUILD_DATE": "2025-01-15"})
@patch("builtins.open", mock_open(read_data="1.2.3\n"))
def test_get_version_info_with_build_date():
    """Test version info when BUILD_DATE environment variable is set"""
    from app.version import get_version_info

    result = get_version_info()
    assert result["version"] == "1.2.3"
    assert result["build_date"] == "2025-01-15"
    assert result["name"] == "Chess Combat"

@patch("builtins.open", mock_open(read_data="2.1.0\n"))
@patch("os.path.getmtime", return_value=1674000000)  # Mock timestamp
def test_get_version_info_without_build_date(mock_getmtime):
    """Test version info fallback when BUILD_DATE is not set"""
    from app.version import get_version_info
    import os

    # Remove BUILD_DATE if it exists
    if "BUILD_DATE" in os.environ:
        del os.environ["BUILD_DATE"]

    result = get_version_info()
    assert result["version"] == "2.1.0"
    assert result["name"] == "Chess Combat"
    # Should have some date (either from file mtime or current date)
    assert len(result["build_date"]) == 10  # YYYY-MM-DD format

@patch("builtins.open", side_effect=FileNotFoundError)
def test_get_version_unknown_fallback(mock_open_error):
    """Test version fallback when VERSION.txt file is not found"""
    from app.version import get_version

    result = get_version()
    assert result == "unknown"

def test_homepage_contains_version_footer():
    """Test that the homepage contains the version footer structure"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200

    content = response.text
    # Check for footer structure
    assert '<footer' in content
    assert 'id="version-info"' in content
    assert 'Chess Combat' in content
