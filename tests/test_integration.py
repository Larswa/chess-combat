import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_create_player():
    client = TestClient(app)
    response = client.post("/players/", json={"name": "pytest-player"})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "pytest-player"
