import pytest
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import text
import uuid

@pytest.fixture(autouse=True)
def cleanup_player():
    # Cleanup before and after each test
    from app.db.crud import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM moves WHERE game_id IN (SELECT id FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%'))"))
        db.execute(text("DELETE FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%')"))
        db.execute(text("DELETE FROM players WHERE name LIKE 'pytest-player%'"))
        db.commit()
        yield
        db.execute(text("DELETE FROM moves WHERE game_id IN (SELECT id FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%'))"))
        db.execute(text("DELETE FROM games WHERE white_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%') OR black_id IN (SELECT id FROM players WHERE name LIKE 'pytest-player%')"))
        db.execute(text("DELETE FROM players WHERE name LIKE 'pytest-player%'"))
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
