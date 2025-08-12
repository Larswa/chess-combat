#!/usr/bin/env python3
"""
Test for Gemini AI integration - Unit tests only
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.gemini_ai import extract_uci_move

class TestGeminiAI:
    """Test Gemini AI functionality with unit tests"""

    def test_extract_uci_move(self):
        """Test UCI move extraction from various text formats"""

        # Test cases: (input_text, expected_move)
        test_cases = [
            ("e2e4", "e2e4"),
            ("The best move is e2e4.", "e2e4"),
            ("I recommend g1f3 as the opening move.", "g1f3"),
            ("Move: d2d4", "d2d4"),
            ("e7e8q", "e7e8q"),  # Promotion
            ("O-O", "e1g1"),     # Castling short
            ("o-o", "e1g1"),     # Castling short (lowercase)
            ("0-0", "e1g1"),     # Castling short (zeros)
            ("O-O-O", "e1c1"),   # Castling long
            ("o-o-o", "e1c1"),   # Castling long (lowercase)
            ("0-0-0", "e1c1"),   # Castling long (zeros)
            ("invalid move", None),  # No valid move
            ("", None),          # Empty string
            ("a1a8", "a1a8"),    # Valid move
        ]

        for input_text, expected in test_cases:
            result = extract_uci_move(input_text)
            assert result == expected, f"extract_uci_move('{input_text}') returned '{result}', expected '{expected}'"

    def test_gemini_no_api_key(self):
        """Test Gemini AI behavior when no API key is set"""
        from app.ai.gemini_ai import get_gemini_chess_move

        # Mock environment without API key
        with patch.dict(os.environ, {}, clear=True):
            # Should return default fallback move
            move = get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "e2e4", "Should return fallback move when no API key"

    @patch('app.ai.gemini_ai.requests')
    def test_gemini_api_mocked(self, mock_requests):
        """Test Gemini API with completely mocked requests"""
        from app.ai.gemini_ai import get_gemini_chess_move

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "MOVE: d2d4\nREASON: Controls center squares and opens lines"}]
                },
                "finishReason": "STOP"
            }]
        }
        mock_requests.post.return_value = mock_response

        # Set up environment with API key
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False):
            move = get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "d2d4"
            assert mock_requests.post.called

    def test_gemini_with_move_history(self):
        """Test Gemini AI with a realistic move history"""
        from app.ai.gemini_ai import get_gemini_chess_move

        # Test with some opening moves
        move_history = ["e2e4", "e7e5", "g1f3", "b8c6"]
        board_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

        # Mock environment without API key to get fallback
        with patch.dict(os.environ, {}, clear=True):
            move = get_gemini_chess_move(board_fen, move_history)
            # Should still return fallback move even with complex position
            assert move == "e2e4", "Should return fallback move when no API key, regardless of position"
