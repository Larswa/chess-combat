#!/usr/bin/env python3
"""
Test for OpenAI AI integration - Unit tests only
"""
import pytest
import os
import re
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.openai_ai import get_openai_chess_move

class TestOpenAI:
    """Test OpenAI AI functionality with unit tests"""

    def test_openai_no_api_key(self):
        """Test OpenAI AI behavior when no API key is set"""
        # Mock environment without API key
        with patch.dict(os.environ, {}, clear=True):
            # Should raise exception when no API key is configured
            with pytest.raises(Exception, match="api_key client option must be set"):
                get_openai_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])

    @patch('app.ai.openai_ai._get_openai_client')
    def test_openai_api_success(self, mock_get_client):
        """Test successful OpenAI API response"""
        # Mock the client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "MOVE: d2d4\nREASON: Controls center squares"
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            move = get_openai_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "d2d4"
            assert mock_client.chat.completions.create.called

    @patch('app.ai.openai_ai._get_openai_client')
    def test_openai_with_move_history(self, mock_get_client):
        """Test OpenAI AI with realistic move history and context"""
        # Mock the client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "MOVE: f1c4\nREASON: Developing bishop to active square"
        mock_client.chat.completions.create.return_value = mock_response

        # Test with some opening moves
        move_history = ["e2e4", "e7e5", "g1f3", "b8c6"]
        board_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            move = get_openai_chess_move(board_fen, move_history)
            assert move == "f1c4"

            # Verify the API was called with enhanced context
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']

            # Check that the user message contains game phase information
            user_message = messages[1]['content']
            assert "opening" in user_message.lower()
            assert "e2e4 e7e5 g1f3 b8c6" in user_message  # Check move history is included
            assert "Game history" in user_message

    def test_openai_uci_extraction(self):
        """Test UCI move extraction from various OpenAI responses"""
        # This would be tested in the actual function, but let's test the regex pattern
        import re

        test_cases = [
            ("The best move is e2e4.", "e2e4"),
            ("I suggest d2d4 as a strong opening.", "d2d4"),
            ("Move: g1f3", "g1f3"),
            ("e7e8q (promoting to queen)", "e7e8q"),
            ("invalid response", None),
        ]

        uci_pattern = r'\b[a-h][1-8][a-h][1-8][qrbn]?\b'

        for response_text, expected in test_cases:
            matches = re.findall(uci_pattern, response_text.lower())
            result = matches[0] if matches else None
            assert result == expected, f"UCI extraction from '{response_text}' returned '{result}', expected '{expected}'"
