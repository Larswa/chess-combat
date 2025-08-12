#!/usr/bin/env python3
"""
Quick test to see GPT-4o chess move quality
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_gpt4_move_quality():
    """Test a few moves to see GPT-4o quality"""

    print("🧠 Testing GPT-4o Chess Move Quality")
    print("=" * 50)

    # Test 1: Starting position
    print("\n1️⃣ Starting Position")
    payload = {
        "ai_engine": "openai",
        "auto_play": False,
        "num_moves": 2
    }

    try:
        response = requests.post(f"{BASE_URL}/ai-vs-ai/", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Moves played: {data.get('moves_played', 0)}")
            print(f"   Opening moves made")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Test 2: Give it a tactical position
    print("\n2️⃣ Quick tactical test from middlegame")
    payload = {
        "ai_engine": "openai",
        "auto_play": False,
        "num_moves": 1,
        "starting_fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"
    }

    try:
        response = requests.post(f"{BASE_URL}/ai-vs-ai/", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tactical position handled")
            print(f"   Moves: {data.get('moves_played', 0)}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

    print("\n🔍 Check server logs to see the detailed GPT-4o analysis!")
    print("   Look for much more strategic thinking compared to GPT-3.5-turbo")

if __name__ == "__main__":
    test_gpt4_move_quality()
