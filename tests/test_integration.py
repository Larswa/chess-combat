import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(autouse=True)
def cleanup_player():
    # Cleanup before and after each test
    from app.db.crud import SessionLocal
    db = SessionLocal()
    try:
        db.execute("DELETE FROM players WHERE name = 'pytest-player'")
        db.commit()
        yield
        db.execute("DELETE FROM players WHERE name = 'pytest-player'")
        db.commit()
    finally:
        db.close()

def test_create_player():
    client = TestClient(app)
    response = client.post("/players/", json={"name": "pytest-player"})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "pytest-player"
