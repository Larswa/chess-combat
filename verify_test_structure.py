#!/usr/bin/env python3
"""
Simple test verification script to check if our test imports work correctly.
This doesn't run the actual tests but verifies the test structure.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all our test imports work"""
    try:
        # Test version module imports
        from app.version import get_version, get_build_date, get_version_info
        print("✓ Version module imports successful")

        # Test that version functions work
        version = get_version()
        build_date = get_build_date()
        version_info = get_version_info()

        print(f"✓ Version functions work: {version}, {build_date}")
        print(f"✓ Version info: {version_info}")

        # Test that routes import works (if FastAPI is available)
        try:
            from app.ui.routes import router
            print("✓ Routes import successful")
        except ImportError as ie:
            if 'fastapi' in str(ie).lower():
                print("⚠ Routes import skipped (FastAPI not available in test environment)")
            else:
                raise ie

        return True

    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def check_test_files():
    """Check that test files exist and have expected structure"""
    test_files = [
        'tests/test_app.py',
        'tests/test_integration.py',
        'tests/test_version.py'
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"✓ {test_file} exists")

            # Check for version-related test content
            with open(test_file, 'r') as f:
                content = f.read()
                if 'version' in content.lower():
                    print(f"  └─ Contains version tests")
        else:
            print(f"✗ {test_file} missing")

if __name__ == "__main__":
    print("Testing version functionality structure...")

    if test_imports():
        print("\n" + "="*50)
        print("✓ All imports successful!")
    else:
        print("\n" + "="*50)
        print("✗ Some imports failed!")
        sys.exit(1)

    print("\nChecking test files...")
    check_test_files()

    print("\n" + "="*50)
    print("Test structure verification complete!")
    print("\nTo run tests when dependencies are available:")
    print("  pytest tests/test_version.py -v                 # Version-specific tests")
    print("  pytest tests/ -m unit                           # Unit tests only")
    print("  pytest tests/ -m integration                    # Integration tests only")
    print("  pytest tests/ -m version                        # Version-related tests only")
    print("  pytest tests/                                   # All tests")
