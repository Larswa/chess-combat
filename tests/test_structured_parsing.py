#!/usr/bin/env python3
"""
Unit tests for structured AI response parsing
"""
import pytest
import sys
import os
sys.path.insert(0, '/home/lars/source/chess-combat')

from app.ai.openai_ai import parse_structured_move_response

class TestStructuredParsing:
    """Test the new structured response parser"""

    def test_structured_format_parsing(self):
        """Test parsing of structured MOVE: format"""
        valid_moves = ["e2e4", "d2d4", "g1f3", "b1c3", "c2c4", "f2f4"]

        test_cases = [
            ("MOVE: e2e4\nREASON: Controls the center", "e2e4"),
            ("MOVE: g1f3\nREASON: Develops knight toward center", "g1f3"),
            ("move: d2d4\nreason: controls center squares", "d2d4"),
            ("Move: B1C3\nReason: Knight development", "b1c3"),
        ]

        for response, expected in test_cases:
            result = parse_structured_move_response(response, valid_moves)
            assert result == expected, f"Failed for response: {response}"

    def test_uci_move_extraction(self):
        """Test extraction of UCI moves from text"""
        valid_moves = ["e2e4", "d2d4", "g1f3", "b1c3"]

        test_cases = [
            ("I think the best move here is e2e4 because it controls the center", "e2e4"),
            ("Let me play g1f3 to develop my knight", "g1f3"),
            ("e2e4", "e2e4"),
            ("G1F3", "g1f3"),
        ]

        for response, expected in test_cases:
            result = parse_structured_move_response(response, valid_moves)
            assert result == expected, f"Failed for response: {response}"

    def test_invalid_moves_return_none(self):
        """Test that invalid moves return None"""
        valid_moves = ["e2e4", "d2d4", "g1f3", "b1c3"]

        invalid_cases = [
            "MOVE: e2e5\nREASON: Invalid move",
            "I suggest h8g7 which is illegal",
            "No valid moves found",
            "",
        ]

        for response in invalid_cases:
            result = parse_structured_move_response(response, valid_moves)
            assert result is None, f"Should return None for: {response}"

    def test_promotion_moves(self):
        """Test parsing of pawn promotion moves"""
        promotion_moves = ["a7a8q", "b7b8r", "c7c8n", "d7d8b"]

        test_cases = [
            ("MOVE: a7a8q\nREASON: Promote to queen", "a7a8q"),
            ("The pawn promotes: a7a8q", "a7a8q"),
            ("a7a8q", "a7a8q"),
        ]

        for response, expected in test_cases:
            result = parse_structured_move_response(response, promotion_moves)
            assert result == expected, f"Failed for promotion: {response}"

    def test_fallback_strategies(self):
        """Test multiple fallback parsing strategies"""
        valid_moves = ["e2e4", "d2d4", "g1f3", "b1c3"]

        # Test with extra formatting
        result = parse_structured_move_response("**MOVE: f2f4**\n*Reason: King's Indian Attack*", ["f2f4"])
        assert result == "f2f4"

        # Test case insensitive matching
        result = parse_structured_move_response("E2E4", valid_moves)
        assert result == "e2e4"

        # Test move mentioned in longer text
        result = parse_structured_move_response("After analyzing the position, I believe g1f3 is best", valid_moves)
        assert result == "g1f3"
