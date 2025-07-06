# AI Service: Handles AI API integration
import requests

def get_ai_move(board_state, ai_url):
    # Send board state to AI and get move
    response = requests.post(ai_url, json={"board": board_state})
    return response.json().get("move")
