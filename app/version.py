"""Version and build information utilities."""
import os
from datetime import datetime
from typing import Optional

def get_version() -> str:
    """Get the application version from VERSION.txt file."""
    try:
        version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION.txt")
        with open(version_file, 'r') as f:
            return f.read().strip()
    except Exception:
        return "unknown"

def get_build_date() -> str:
    """Get the build/release date. In production, this could come from build metadata."""
    # For now, we'll use a hardcoded date or environment variable
    # In CI/CD, you could set this as an environment variable during build
    build_date = os.getenv("BUILD_DATE")
    if build_date:
        return build_date

    # Fallback: try to get from VERSION.txt modification time
    try:
        version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION.txt")
        mtime = os.path.getmtime(version_file)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")

def get_version_info() -> dict:
    """Get complete version information."""
    return {
        "version": get_version(),
        "build_date": get_build_date(),
        "name": "Chess Combat"
    }
