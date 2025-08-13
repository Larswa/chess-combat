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

def get_deployment_timestamp() -> str:
    """Get the deployment timestamp with date and time."""
    # First check for BUILD_TIMESTAMP environment variable (with time)
    build_timestamp = os.getenv("BUILD_TIMESTAMP")
    if build_timestamp:
        return build_timestamp

    # Check for BUILD_DATE environment variable (date only) and add current time
    build_date = os.getenv("BUILD_DATE")
    if build_date:
        try:
            # If BUILD_DATE is just a date, append current time
            if len(build_date) == 10 and build_date.count('-') == 2:  # YYYY-MM-DD format
                current_time = datetime.now().strftime("%H:%M:%S")
                return f"{build_date} {current_time}"
            else:
                return build_date  # Assume it already includes time
        except Exception:
            pass

    # Fallback: use current datetime (represents when the application started)
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_version_info() -> dict:
    """Get complete version information."""
    return {
        "version": get_version(),
        "build_date": get_build_date(),
        "deployment_timestamp": get_deployment_timestamp(),
        "release_timestamp": get_deployment_timestamp(),  # Alias for clarity
        "name": "Chess Combat"
    }
