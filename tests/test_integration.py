import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import text
import uuid

@pytest.fixture(autouse=True)
def cleanup_player():
    # Cleanup before and after each test
    from app.db.crud import get_session_local
    from app.db.models import Base
    from app.db.crud import get_engine

    # Ensure tables exist
    Base.metadata.create_all(bind=get_engine())

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Clean up test data - use try/except to handle missing tables
        try:
            db.execute(text("DELETE FROM moves WHERE game_id IN (SELECT id FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%'))"))
        except Exception:
            pass  # Table might not exist yet

        try:
            db.execute(text("DELETE FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%')"))
        except Exception:
            pass

        try:
            db.execute(text("DELETE FROM players WHERE name LIKE 'pytest-player%'"))
        except Exception:
            pass

        db.commit()
        yield

        # Cleanup after test
        try:
            db.execute(text("DELETE FROM moves WHERE game_id IN (SELECT id FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%'))"))
        except Exception:
            pass

        try:
            db.execute(text("DELETE FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%')"))
        except Exception:
            pass

        try:
            db.execute(text("DELETE FROM players WHERE name LIKE 'pytest-player%'"))
        except Exception:
            pass

        db.commit()
    finally:
        db.close()

def test_create_player():
    client = TestClient(app)
    name = f"pytest-player-{uuid.uuid4()}"
    response = client.post("/players/", json={"name": name})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == name

def test_create_player_duplicate():
    client = TestClient(app)
    name = f"pytest-player-dup-{uuid.uuid4()}"
    client.post("/players/", json={"name": name})
    response = client.post("/players/", json={"name": name})
    assert response.status_code == 409
    assert response.json().get("detail") == "Player name already exists"

def test_create_and_get_game():
    client = TestClient(app)
    name1 = f"pytest-player1-{uuid.uuid4()}"
    name2 = f"pytest-player2-{uuid.uuid4()}"
    p1 = client.post("/players/", json={"name": name1}).json()
    p2 = client.post("/players/", json={"name": name2}).json()
    response = client.post("/games/", json={"white_id": p1["id"], "black_id": p2["id"]})
    assert response.status_code == 200
    game_id = response.json()["id"]
    get_resp = client.get(f"/games/{game_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["white_id"] == p1["id"]
    assert get_resp.json()["black_id"] == p2["id"]
    # No manual cleanup needed, fixture handles it

def test_add_move_and_retrieve():
    client = TestClient(app)
    name1 = f"pytest-player3-{uuid.uuid4()}"
    name2 = f"pytest-player4-{uuid.uuid4()}"
    p1 = client.post("/players/", json={"name": name1}).json()
    p2 = client.post("/players/", json={"name": name2}).json()
    game_resp = client.post("/games/", json={"white_id": p1["id"], "black_id": p2["id"]})
    game_id = game_resp.json()["id"]
    move_resp = client.post(f"/games/{game_id}/moves", json={"move": "e2e4"})
    assert move_resp.status_code == 200
    get_resp = client.get(f"/games/{game_id}")
    assert get_resp.status_code == 200
    # No manual cleanup needed, fixture handles it

@pytest.mark.integration
def test_version_api_integration():
    """Integration test for version API endpoint"""
    client = TestClient(app)
    response = client.get("/api/version")

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "version" in data
    assert "build_date" in data
    assert "name" in data

    # Verify data types and formats
    assert isinstance(data["version"], str)
    assert isinstance(data["build_date"], str)
    assert isinstance(data["name"], str)

    # Verify version format (should be semantic versioning)
    version_parts = data["version"].split(".")
    assert len(version_parts) >= 3  # Major.Minor.Patch

    # Verify date format (YYYY-MM-DD)
    assert len(data["build_date"]) == 10
    assert data["build_date"][4] == "-"
    assert data["build_date"][7] == "-"

    # Verify name
    assert data["name"] == "Chess Combat"

@pytest.mark.integration
def test_homepage_version_footer_integration():
    """Integration test to verify version footer appears in homepage"""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    content = response.text

    # Check for footer HTML structure
    assert '<footer' in content
    assert 'id="version-info"' in content

    # Check for version template logic
    assert 'version_info' in content or 'Chess Combat' in content

    # Check for JavaScript fallback
    assert '/api/version' in content
    assert 'fetch(' in content

@pytest.mark.integration
def test_version_consistency_integration():
    """Integration test to ensure version consistency between API and UI"""
    client = TestClient(app)

    # Get version from API
    api_response = client.get("/api/version")
    assert api_response.status_code == 200
    api_version_data = api_response.json()

    # Get homepage
    ui_response = client.get("/")
    assert ui_response.status_code == 200
    ui_content = ui_response.text

    # The UI should either contain the version in server-side template
    # or have JavaScript to fetch it from API
    version_in_ui = (
        api_version_data["version"] in ui_content or
        '/api/version' in ui_content  # JavaScript fallback exists
    )

    assert version_in_ui, "Version should be available in UI either server-side or via JavaScript"
