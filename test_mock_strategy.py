#!/usr/bin/env python3
"""
Test the mocking strategy for version tests.
"""

import sys
import os
from unittest.mock import patch

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_mock_strategy():
    """Test that the mock strategy works correctly"""
    print("Testing mock strategy...")

    try:
        # Test that we can mock the function where it's imported
        with patch("app.ui.routes.get_version_info") as mock_func:
            mock_func.return_value = {"version": "test", "build_date": "2025-01-01", "name": "Test"}

            # Import after mocking
            from app.ui.routes import api_version

            # This should use the mocked function
            result = api_version()

            print(f"✓ Mock result: {result}")
            print(f"✓ Mock called: {mock_func.called}")
            print(f"✓ Call count: {mock_func.call_count}")

            if mock_func.called:
                print("✓ Mocking strategy works!")
                return True
            else:
                print("✗ Mocking strategy failed - function not called")
                return False

    except Exception as e:
        print(f"✗ Error testing mock strategy: {e}")
        return False

def test_import_structure():
    """Test the import structure to understand the issue"""
    print("\nTesting import structure...")

    try:
        # Check what get_version_info is imported as in routes
        from app.ui import routes

        # Check if the function exists in the routes module
        if hasattr(routes, 'get_version_info'):
            print("✓ get_version_info is available in routes module")

            # Test calling it directly
            result = routes.get_version_info()
            print(f"✓ Direct call result: {result}")

        else:
            print("✗ get_version_info not found in routes module")
            print(f"Available attributes: {[attr for attr in dir(routes) if not attr.startswith('_')]}")

    except Exception as e:
        print(f"✗ Error checking import structure: {e}")

if __name__ == "__main__":
    print("Testing version test mocking strategy...")

    test_import_structure()
    success = test_mock_strategy()

    if success:
        print("\n✅ Mock strategy should work in tests!")
    else:
        print("\n❌ Mock strategy needs adjustment")

    print("\nThe fixed tests should now work correctly.")
