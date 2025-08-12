#!/usr/bin/env python3
"""
Test script to verify AI board state understanding.
This will show what the AI thinks it sees vs actual board state.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_ai_board_understanding():
    """Test if AI correctly understands the board state"""
    print("🧠 Testing AI Board State Understanding")
    print("=" * 50)

    # Test 1: Starting position
    print("\n1️⃣ Starting Position Test")
    payload = {
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "moves": [],
        "ai": "openai",
        "auto_play": False,
        "max_moves": 2
    }

    response = requests.post(f"{BASE_URL}/ai-vs-ai/", json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Starting position - Moves played: {len(result['ai_moves'])}")
        if result['ai_moves']:
            print(f"   First move: {result['ai_moves'][0]}")

    # Test 2: Mid-game position
    print("\n2️⃣ Mid-Game Position Test")
    # This is after: 1.e4 e5 2.Nf3 Nc6 3.Bb5
    mid_game_fen = "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    mid_game_moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]

    payload = {
        "fen": mid_game_fen,
        "moves": mid_game_moves,
        "ai": "openai",
        "auto_play": False,
        "max_moves": 2
    }

    response = requests.post(f"{BASE_URL}/ai-vs-ai/", json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Mid-game position - Moves played: {len(result['ai_moves'])}")
        if result['ai_moves']:
            print(f"   Move from position: {result['ai_moves'][0]}")

    # Test 3: Complex position with potential tactics
    print("\n3️⃣ Tactical Position Test")
    # Position where there might be a tactic
    tactical_fen = "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3"
    tactical_moves = ["e2e4", "e7e5", "f1c4", "g8f6"]

    payload = {
        "fen": tactical_fen,
        "moves": tactical_moves,
        "ai": "openai",
        "auto_play": False,
        "max_moves": 2
    }

    response = requests.post(f"{BASE_URL}/ai-vs-ai/", json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Tactical position - Moves played: {len(result['ai_moves'])}")
        if result['ai_moves']:
            print(f"   Move in tactical position: {result['ai_moves'][0]}")

    print("\n📋 Check the server logs to see:")
    print("   - What the AI thinks it sees on the board")
    print("   - The actual FEN position we sent")
    print("   - Any differences between AI perception and reality")

if __name__ == "__main__":
    try:
        test_ai_board_understanding()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to chess-combat server at http://localhost:8000")
        print("   Make sure the server is running")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
