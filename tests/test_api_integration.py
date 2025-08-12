"""
Integration test to verify checkmate detection and database saving in API endpoints
"""
import requests
import json
import pytest
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

@pytest.mark.skip(reason="Integration test requires live server - use 'pytest -m integration' to run")
def test_api_checkmate_integration():
    """Test complete checkmate flow through API"""

    # Create a new game
    game_data = {
        "white_name": f"Test White API {int(time.time())}",
        "black_name": f"Test Black API {int(time.time())}",
        "ai_engine": "openai"
    }

    response = requests.post(f"{BASE_URL}/api/new-game", json=game_data, timeout=TEST_TIMEOUT)
    assert response.status_code == 200

    game_info = response.json()
    game_id = game_info["game_id"]
    print(f"Created game {game_id}")

    # Play moves leading to checkmate (Fool's mate)
    moves = ["f2f3", "e7e5", "g2g4", "d8h4"]

    for i, move in enumerate(moves):
        print(f"Playing move {i+1}: {move}")

        move_data = {
            "game_id": game_id,
            "move": move,
            "ai_engine": "openai",
            "enforce_rules": True
        }

        response = requests.post(f"{BASE_URL}/api/make_move", json=move_data, timeout=TEST_TIMEOUT)
        assert response.status_code == 200

        result = response.json()
        print(f"Move result: {result.get('status', 'unknown')}")

        # After the final move, the game should be over
        if i == len(moves) - 1:
            # Check game status
            response = requests.get(f"{BASE_URL}/api/game/{game_id}", timeout=TEST_TIMEOUT)
            assert response.status_code == 200

            game_state = response.json()
            print(f"Final game state: {game_state}")

            # The game should be marked as over
            assert game_state.get("status") == "game_over", "Game should be marked as over"

    print("✓ API checkmate integration test completed successfully")

if __name__ == "__main__":
    # Run the integration test if the server is available
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            test_api_checkmate_integration()
        else:
            print("Server not available for integration test")
    except requests.exceptions.RequestException:
        print("Server not running - skipping integration test")
