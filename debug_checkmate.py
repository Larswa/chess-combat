#!/usr/bin/env python3
"""
Debug script to test checkmate detection
"""
import os
import sys
sys.path.insert(0, '.')

# Set up environment
os.environ.setdefault("OPENAI_API_KEY", "test_key")
os.environ.setdefault("GEMINI_API_KEY", "test_key")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.db.models import Base
from app.main import create_app
import chess

def test_checkmate():
    print("Creating test database...")
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True
    )
    
    Base.metadata.create_all(bind=test_engine)
    app = create_app(test_engine=test_engine)
    
    print("Creating test client...")
    with TestClient(app) as client:
        # Create game
        print("Creating game...")
        game_data = {"mode": "human-vs-human", "color": "white", "ai_engine": "random"}
        response = client.post("/api/new-game", json=game_data)
        print(f"Game creation response: {response.status_code}, {response.json()}")
        
        game_id = response.json()["game_id"]
        
        # Play fool's mate
        print("Playing fool's mate sequence...")
        moves = ["f2f3", "e7e5", "g2g4", "d8h4"]
        
        for i, move in enumerate(moves):
            print(f"\nMove {i+1}: {move}")
            move_data = {"game_id": game_id, "move": move, "enforce_rules": True}
            response = client.post("/api/move", json=move_data)
            print(f"Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"FEN: {result.get('fen')}")
                print(f"Status: {result.get('status')}")
                
                # Check the board state
                if result.get('fen'):
                    board = chess.Board(result['fen'])
                    print(f"Game over: {board.is_game_over()}")
                    print(f"Checkmate: {board.is_checkmate()}")
            else:
                print(f"Error: {response.text}")
                
        # Final game state
        print(f"\nGetting final game state...")
        response = client.get(f"/api/game/{game_id}")
        print(f"Final state response: {response.status_code}")
        if response.status_code == 200:
            state = response.json()
            print(f"Final state: {state}")
            
            # Verify final position
            if state.get('fen'):
                board = chess.Board(state['fen'])
                print(f"Final board game over: {board.is_game_over()}")
                print(f"Final board checkmate: {board.is_checkmate()}")

if __name__ == "__main__":
    test_checkmate()
