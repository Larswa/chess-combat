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
            # Should raise ValueError when no API key is configured
            with pytest.raises(ValueError, match="Gemini API key not configured"):
                get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])

    @patch('app.ai.gemini_ai.genai.GenerativeModel')
    def test_gemini_api_mocked(self, mock_generative_model):
        """Test Gemini API with completely mocked GenerativeModel"""
        from app.ai.gemini_ai import get_gemini_chess_move

        # Mock the response object
        mock_response = MagicMock()
        mock_response.text = "BOARD: Opening position with standard development opportunities\nMOVE: d2d4"

        # Mock the model and its generate_content method
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model

        # Set up environment with API key
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False):
            move = get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "d2d4"
            assert mock_generative_model.called
            assert mock_model.generate_content.called

    def test_gemini_with_move_history(self):
        """Test Gemini AI with a realistic move history"""
        from app.ai.gemini_ai import get_gemini_chess_move

        # Test with some opening moves
        move_history = ["e2e4", "e7e5", "g1f3", "b8c6"]
        board_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

        # Mock environment without API key - should raise exception
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Gemini API key not configured"):
                get_gemini_chess_move(board_fen, move_history)
