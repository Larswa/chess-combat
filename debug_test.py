#!/usr/bin/env python3
"""
Simple test runner to check what's wrong
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/home/lars/source/chess-combat')

try:
    print("Testing imports...")

    # Test app import
    from app.ai.gemini_ai import extract_uci_move
    print("✓ Gemini AI import successful")

    # Test extract_uci_move function
    result = extract_uci_move("e2e4")
    print(f"✓ extract_uci_move test: {result}")

    # Test the new test file import
    import tests.test_gemini_ai
    print("✓ Test file import successful")

    print("\nAll imports successful!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
