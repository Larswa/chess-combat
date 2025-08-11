#!/usr/bin/env python3
"""
Test for Gemini AI integration
"""
import pytest
import os
import unittest
from unittest.mock import patch, MagicMock
from app.ai.gemini_ai import extract_uci_move, get_gemini_chess_move

class TestGeminiAI:
    """Test Gemini AI functionality"""

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
        # Mock environment without API key
        with patch.dict(os.environ, {}, clear=True):
            # Should return default fallback move
            move = get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "e2e4", "Should return fallback move when no API key"

    @patch('app.ai.gemini_ai.requests.post')
    def test_gemini_api_success(self, mock_post):
        """Test successful Gemini API response"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "e2e4"}]
                },
                "finishReason": "STOP"
            }]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            move = get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "e2e4"
            assert mock_post.called

    @patch('app.ai.gemini_ai.requests.post')
    def test_gemini_api_404_fallback(self, mock_post):
        """Test Gemini API 404 fallback to other models"""
        # Mock 404 responses for all models
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            move = get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "e2e4"  # Should fallback to default move
            assert mock_post.call_count > 1  # Should try multiple models

    @patch('app.ai.gemini_ai.requests.post')
    def test_gemini_api_403_error(self, mock_post):
        """Test Gemini API 403 (authentication) error"""
        # Mock 403 response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "invalid-key"}):
            move = get_gemini_chess_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])
            assert move == "e2e4"  # Should fallback to default move
            assert mock_post.called
