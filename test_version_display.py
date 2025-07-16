#!/usr/bin/env python3
"""Test the version display without running the full server."""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Test with a controlled BUILD_DATE
os.environ['BUILD_DATE'] = '2025-07-17'

from app.version import get_version_info

print("Testing version functionality...")
version_info = get_version_info()
print(f"Version info: {version_info}")

# Simulate what the template would display
expected_display = f"{version_info['name']} v{version_info['version']} ({version_info['build_date']})"
print(f"Expected display: {expected_display}")

# Test without BUILD_DATE env var
del os.environ['BUILD_DATE']
version_info_no_env = get_version_info()
print(f"Without BUILD_DATE env: {version_info_no_env}")
