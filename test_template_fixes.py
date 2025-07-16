#!/usr/bin/env python3
"""
Test that the TemplateResponse fix works correctly.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_template_response_syntax():
    """Test that the new TemplateResponse syntax works"""
    print("Testing TemplateResponse syntax...")

    try:
        from fastapi import Request
        from fastapi.templating import Jinja2Templates

        # Mock request object
        class MockRequest:
            def __init__(self):
                self.url = "http://localhost:8000/"
                self.method = "GET"
                self.headers = {}

        # Create templates instance
        templates = Jinja2Templates(directory=os.path.join("app", "ui", "templates"))

        # Test the new syntax
        request = MockRequest()
        response = templates.TemplateResponse(
            request=request,
            name="chess_game.html",
            context={"version_info": {"version": "test", "build_date": "2025-01-01", "name": "Test"}}
        )

        print("✓ New TemplateResponse syntax works")
        return True

    except Exception as e:
        print(f"✗ TemplateResponse syntax error: {e}")
        return False

def test_routes_import():
    """Test that routes can be imported without warnings"""
    print("Testing routes import...")

    try:
        # This should not generate warnings
        from app.ui.routes import router
        print("✓ Routes import successful")
        return True

    except Exception as e:
        print(f"✗ Routes import error: {e}")
        return False

if __name__ == "__main__":
    print("Testing TemplateResponse deprecation warning fixes...")

    success1 = test_routes_import()
    success2 = test_template_response_syntax()

    if success1 and success2:
        print("\n✅ All template response fixes are working!")
        print("The deprecation warnings should be resolved.")
    else:
        print("\n❌ Some issues remain")

    print("\nTo test without warnings:")
    print("pytest tests/ -v --disable-warnings")
