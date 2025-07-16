"""
Comprehensive tests for version functionality and footer display.
This module tests all aspects of version handling including:
- Version reading from files
- Build date handling
- API endpoints
- Template rendering
- Environment variable handling
"""

import pytest
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient


class TestVersionModule:
    """Unit tests for the version module itself"""

    def test_get_version_from_file(self):
        """Test reading version from VERSION.txt file"""
        from app.version import get_version

        with patch("builtins.open", mock_open(read_data="1.5.3\n")):
            result = get_version()
            assert result == "1.5.3"

    def test_get_version_file_not_found(self):
        """Test version fallback when file doesn't exist"""
        from app.version import get_version

        with patch("builtins.open", side_effect=FileNotFoundError):
            result = get_version()
            assert result == "unknown"

    def test_get_version_permission_error(self):
        """Test version fallback when file permission is denied"""
        from app.version import get_version

        with patch("builtins.open", side_effect=PermissionError):
            result = get_version()
            assert result == "unknown"

    @patch.dict(os.environ, {"BUILD_DATE": "2025-12-25"})
    def test_get_build_date_from_env(self):
        """Test build date from environment variable"""
        from app.version import get_build_date

        result = get_build_date()
        assert result == "2025-12-25"

    @patch("os.path.getmtime", return_value=1640995200)  # 2022-01-01 00:00:00 UTC
    @patch("builtins.open", mock_open(read_data="1.0.0"))
    def test_get_build_date_from_file_mtime(self, mock_file):
        """Test build date fallback to file modification time"""
        from app.version import get_build_date

        # Remove BUILD_DATE if it exists
        if "BUILD_DATE" in os.environ:
            del os.environ["BUILD_DATE"]

        result = get_build_date()
        assert result == "2022-01-01"

    def test_get_build_date_fallback_to_current(self):
        """Test build date fallback to current date"""
        from app.version import get_build_date
        from datetime import datetime

        # Remove BUILD_DATE if it exists
        if "BUILD_DATE" in os.environ:
            del os.environ["BUILD_DATE"]

        with patch("os.path.getmtime", side_effect=OSError):
            result = get_build_date()
            current_date = datetime.now().strftime("%Y-%m-%d")
            assert result == current_date

    @patch("builtins.open", mock_open(read_data="2.0.1\n"))
    @patch.dict(os.environ, {"BUILD_DATE": "2025-06-15"})
    def test_get_version_info_complete(self):
        """Test complete version info structure"""
        from app.version import get_version_info

        result = get_version_info()
        expected = {
            "version": "2.0.1",
            "build_date": "2025-06-15",
            "name": "Chess Combat"
        }
        assert result == expected


class TestVersionAPI:
    """Tests for version-related API endpoints"""

    def setup_method(self):
        """Setup test client"""
        from app.main import app
        self.client = TestClient(app)

    def test_version_endpoint_structure(self):
        """Test /api/version endpoint returns correct structure"""
        response = self.client.get("/api/version")

        assert response.status_code == 200
        data = response.json()

        required_fields = ["version", "build_date", "name"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_version_endpoint_data_types(self):
        """Test /api/version endpoint returns correct data types"""
        response = self.client.get("/api/version")
        data = response.json()

        assert isinstance(data["version"], str)
        assert isinstance(data["build_date"], str)
        assert isinstance(data["name"], str)

    def test_version_endpoint_content_type(self):
        """Test /api/version endpoint returns JSON content type"""
        response = self.client.get("/api/version")

        assert response.headers.get("content-type") == "application/json"

    @patch("app.ui.routes.get_version_info")
    def test_version_endpoint_calls_version_function(self, mock_get_version):
        """Test that version endpoint calls the version function"""
        mock_get_version.return_value = {
            "version": "test",
            "build_date": "2025-01-01",
            "name": "Test App"
        }

        response = self.client.get("/api/version")

        assert response.status_code == 200
        mock_get_version.assert_called_once()


class TestVersionTemplateIntegration:
    """Tests for version integration with HTML templates"""

    def setup_method(self):
        """Setup test client"""
        from app.main import app
        self.client = TestClient(app)

    def test_homepage_contains_footer(self):
        """Test homepage contains version footer"""
        response = self.client.get("/")

        assert response.status_code == 200
        content = response.text

        # Check for footer structure
        assert '<footer' in content
        assert 'id="version-info"' in content

    def test_homepage_contains_version_fallback_script(self):
        """Test homepage contains JavaScript fallback for version loading"""
        response = self.client.get("/")
        content = response.text

        # Check for JavaScript that fetches version
        assert '/api/version' in content
        assert 'fetch(' in content

    @patch("app.ui.routes.get_version_info")
    def test_homepage_version_template_data(self, mock_get_version):
        """Test that homepage receives version data in template context"""
        mock_version_data = {
            "version": "3.2.1",
            "build_date": "2025-03-15",
            "name": "Chess Combat"
        }
        mock_get_version.return_value = mock_version_data

        response = self.client.get("/")

        assert response.status_code == 200
        mock_get_version.assert_called_once()

        # Check that version data appears in rendered HTML
        content = response.text
        # Should contain either the version directly or template logic
        version_present = (
            "3.2.1" in content or
            "version_info" in content
        )
        assert version_present


class TestVersionEnvironmentHandling:
    """Tests for environment variable handling in version functionality"""

    def test_version_with_build_date_env_var(self):
        """Test version handling when BUILD_DATE environment variable is set"""
        from app.version import get_version_info

        test_date = "2025-08-20"
        with patch.dict(os.environ, {"BUILD_DATE": test_date}):
            with patch("builtins.open", mock_open(read_data="1.0.0\n")):
                result = get_version_info()
                assert result["build_date"] == test_date

    def test_version_without_build_date_env_var(self):
        """Test version handling when BUILD_DATE environment variable is not set"""
        from app.version import get_version_info

        # Ensure BUILD_DATE is not set
        env_without_build_date = {k: v for k, v in os.environ.items() if k != "BUILD_DATE"}

        with patch.dict(os.environ, env_without_build_date, clear=True):
            with patch("builtins.open", mock_open(read_data="1.0.0\n")):
                with patch("os.path.getmtime", return_value=1672531200):  # 2023-01-01
                    result = get_version_info()
                    assert result["build_date"] == "2023-01-01"


# Pytest markers for test organization
pytestmark = [
    pytest.mark.unit,  # Can add this marker to run only unit tests
]
