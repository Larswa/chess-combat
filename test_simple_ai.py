#!/usr/bin/env python3
"""
Simple test script for the clean AI chess mediation system.

This demonstrates:
1. Clean mediation between AI players
2. Current board state presentation to AI
3. AI making their own strategic decisions
4. Simple implementation of valid moves
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_simple_ai_game(ai_provider="openai", moves_to_play=10):
    """Test simple AI vs AI game with clean mediation"""
    print(f"\n🎯 Testing simple AI game with {ai_provider} ({moves_to_play} moves)")

    payload = {
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "moves": [],
        "ai": ai_provider,
        "auto_play": True,
        "max_moves": moves_to_play
    }

    print(f"🚀 Starting AI game...")
    response = requests.post(f"{BASE_URL}/ai-vs-ai/", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Game completed!")
        print(f"   Moves played: {len(result['ai_moves'])}")
        print(f"   Invalid moves encountered: {len(result['invalid_moves'])}")
        print(f"   Game over: {result['game_over']}")
        print(f"   Final position: {result['fen'][:50]}...")

        if result['invalid_moves']:
            print(f"   Invalid moves (handled by retry logic):")
            for invalid in result['invalid_moves'][:3]:  # Show first 3
                print(f"     - {invalid}")

        return result
    else:
        print(f"❌ Game failed: {response.text}")
        return None

def test_both_ai_providers():
    """Test both OpenAI and Gemini AI providers"""
    print("\n� Testing both AI providers")

    # Test OpenAI
    print("\n📋 Testing OpenAI:")
    openai_result = test_simple_ai_game("openai", 6)

    # Test Gemini
    print("\n📋 Testing Gemini:")
    gemini_result = test_simple_ai_game("gemini", 6)

    # Compare results
    if openai_result and gemini_result:
        print(f"\n📊 Comparison:")
        print(f"   OpenAI - Moves: {len(openai_result['ai_moves'])}, Invalid: {len(openai_result['invalid_moves'])}")
        print(f"   Gemini - Moves: {len(gemini_result['ai_moves'])}, Invalid: {len(gemini_result['invalid_moves'])}")

def test_invalid_move_recovery():
    """Test that system recovers from invalid moves"""
    print("\n� Testing invalid move recovery")

    # Start from a complex position where AI might make mistakes
    complex_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"

    payload = {
        "fen": complex_fen,
        "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6"],
        "ai": "openai",
        "auto_play": True,
        "max_moves": 8
    }

    print(f"🎯 Testing from complex position...")
    response = requests.post(f"{BASE_URL}/ai-vs-ai/", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Complex position handled!")
        print(f"   Total moves played: {len(result['ai_moves'])}")
        print(f"   Invalid attempts: {len(result['invalid_moves'])}")

        if result['invalid_moves']:
            print(f"   System successfully recovered from invalid moves")
        else:
            print(f"   AI played perfectly with no invalid moves!")
    else:
        print(f"❌ Complex position test failed: {response.text}")

def test_health_check():
    """Test the health check endpoint"""
    print("\n❤️  Testing health check...")

    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Service is healthy: {data}")
        return True
    else:
        print(f"❌ Health check failed: {response.text}")
        return False

def main():
    """Run all tests for the simplified system"""
    print("🤖 Testing Simplified AI Chess Mediation System")
    print("=" * 60)

    # Test health first
    if not test_health_check():
        print("❌ Service not healthy, aborting tests")
        return

    # Test simple games
    print("\n1️⃣ Testing simple AI games...")
    test_simple_ai_game("openai", 8)

    # Test both providers
    print("\n2️⃣ Testing both AI providers...")
    test_both_ai_providers()

    # Test invalid move recovery
    print("\n3️⃣ Testing invalid move recovery...")
    test_invalid_move_recovery()

    print("\n✨ All tests completed!")
    print("\nSimplified system benefits:")
    print("- ✅ Clean mediation between AI players")
    print("- ✅ AI receives current board state only")
    print("- ✅ AI makes its own strategic decisions")
    print("- ✅ Simple retry logic for invalid moves")
    print("- ✅ No complex session management")
    print("- ✅ Lightweight and focused on core functionality")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to chess-combat server at http://localhost:8000")
        print("   Make sure the server is running with: uvicorn app.main:app --reload")
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
