# Gemini AI Integration (Google Gemini API)
import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"

def get_gemini_chess_move(board_fen, move_history):
    prompt = f"You are a chess engine. Given the current board in FEN: {board_fen} and move history: {move_history}, return the best next move in UCI format (e.g., e2e4). Only return the move."
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    # Try the v1 endpoint (not v1beta)
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    response = requests.post(url, headers=headers, params=params, json=data)
    if response.status_code == 404:
        # Try the v1beta endpoint as fallback
        url_beta = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        response = requests.post(url_beta, headers=headers, params=params, json=data)
    response.raise_for_status()
    try:
        move = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        move = response.text
    return move
