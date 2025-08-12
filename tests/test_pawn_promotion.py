#!/usr/bin/env python3
"""
Unit tests for pawn promotion handling
"""
import pytest
import chess
import sys
import os
sys.path.insert(0, '/home/lars/source/chess-combat')

class TestPawnPromotion:
    """Test automatic pawn promotion logic"""

    def test_white_pawn_promotion_detection(self):
        """Test detection of white pawn promotion to 8th rank"""
        board = chess.Board("8/P7/1KB5/4k3/8/8/8/8 w - - 0 55")  # White pawn on a7

        move_uci = "a7a8"

        # Test promotion detection logic
        if len(move_uci) == 4:
            from_square = chess.parse_square(move_uci[:2])
            to_square = chess.parse_square(move_uci[2:4])
            piece = board.piece_at(from_square)

            # Check if this is a pawn promotion
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                    # Auto-promote to queen
                    move_uci += "q"

        assert move_uci == "a7a8q", "Should auto-promote white pawn to queen"

        # Test the move works
        board.push_uci(move_uci)
        piece_on_a8 = board.piece_at(chess.parse_square("a8"))
        assert piece_on_a8.piece_type == chess.QUEEN, "Should have queen on a8"
        assert piece_on_a8.color == chess.WHITE, "Should be white queen"

    def test_black_pawn_promotion_detection(self):
        """Test detection of black pawn promotion to 1st rank"""
        board = chess.Board("8/8/1KB5/4k3/8/8/p7/8 b - - 0 55")  # Black pawn on a2

        move_uci = "a2a1"

        # Test promotion detection logic
        if len(move_uci) == 4:
            from_square = chess.parse_square(move_uci[:2])
            to_square = chess.parse_square(move_uci[2:4])
            piece = board.piece_at(from_square)

            # Check if this is a pawn promotion
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                    # Auto-promote to queen
                    move_uci += "q"

        assert move_uci == "a2a1q", "Should auto-promote black pawn to queen"

        # Test the move works
        board.push_uci(move_uci)
        piece_on_a1 = board.piece_at(chess.parse_square("a1"))
        assert piece_on_a1.piece_type == chess.QUEEN, "Should have queen on a1"
        assert piece_on_a1.color == chess.BLACK, "Should be black queen"

    def test_non_promotion_moves_unchanged(self):
        """Test that non-promotion moves are not modified"""
        board = chess.Board()  # Starting position

        move_uci = "e2e4"
        original_move = move_uci

        # Test promotion detection logic
        if len(move_uci) == 4:
            from_square = chess.parse_square(move_uci[:2])
            to_square = chess.parse_square(move_uci[2:4])
            piece = board.piece_at(from_square)

            # Check if this is a pawn promotion
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                    # Auto-promote to queen
                    move_uci += "q"

        assert move_uci == original_move, "Regular moves should not be modified"

        # Test the move works
        board.push_uci(move_uci)
        assert board.fen() != chess.Board().fen(), "Board should have changed"

    def test_non_pawn_moves_unchanged(self):
        """Test that non-pawn moves to 8th rank are not modified"""
        # Position where a rook can move to 8th rank
        board = chess.Board("7k/8/8/8/8/8/8/R6K w - - 0 1")

        move_uci = "a1a8"
        original_move = move_uci

        # Test promotion detection logic
        if len(move_uci) == 4:
            from_square = chess.parse_square(move_uci[:2])
            to_square = chess.parse_square(move_uci[2:4])
            piece = board.piece_at(from_square)

            # Check if this is a pawn promotion
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                    # Auto-promote to queen
                    move_uci += "q"

        assert move_uci == original_move, "Rook moves should not be modified"

        # Test the move works
        board.push_uci(move_uci)
        piece_on_a8 = board.piece_at(chess.parse_square("a8"))
        assert piece_on_a8.piece_type == chess.ROOK, "Should still be a rook"

    def test_already_promoted_moves_unchanged(self):
        """Test that moves with promotion suffix are not modified"""
        board = chess.Board("8/P7/1KB5/4k3/8/8/8/8 w - - 0 55")

        move_uci = "a7a8r"  # Already has promotion to rook
        original_move = move_uci

        # Test promotion detection logic (should only apply to 4-character moves)
        if len(move_uci) == 4:
            from_square = chess.parse_square(move_uci[:2])
            to_square = chess.parse_square(move_uci[2:4])
            piece = board.piece_at(from_square)

            # Check if this is a pawn promotion
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_square) == 0):
                    # Auto-promote to queen
                    move_uci += "q"

        assert move_uci == original_move, "Moves with existing promotion should not be modified"

        # Test the move works
        board.push_uci(move_uci)
        piece_on_a8 = board.piece_at(chess.parse_square("a8"))
        assert piece_on_a8.piece_type == chess.ROOK, "Should have rook (not queen)"
