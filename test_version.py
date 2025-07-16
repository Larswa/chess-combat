#!/usr/bin/env python3
"""Simple test script to verify version functionality."""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.version import get_version_info

if __name__ == "__main__":
    print("Testing version functionality...")
    version_info = get_version_info()
    print(f"Version Info: {version_info}")

    # Test individual functions
    from app.version import get_version, get_build_date
    print(f"Version: {get_version()}")
    print(f"Build Date: {get_build_date()}")
