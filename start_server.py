#!/usr/bin/env python3
"""
Start the chess-combat server with environment variables loaded from .env file
"""

import os
import subprocess
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Loaded environment variables from .env file")
    else:
        print("❌ No .env file found")

if __name__ == "__main__":
    # Load environment variables
    load_env_file()

    # Show API key status (without revealing keys)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    print(f"OpenAI API Key: {'✅ Set' if openai_key.startswith('sk-') else '❌ Not set'}")
    print(f"Gemini API Key: {'✅ Set' if gemini_key else '❌ Not set'}")

    # Start the server
    print("🚀 Starting chess-combat server...")
    subprocess.run([
        "uvicorn", "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
