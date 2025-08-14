"""Simple HTTP tests for actual functionality."""

import pytest

from nutrient_dws.errors import APIError, ValidationError
from nutrient_dws.http import send_request


class TestHttpSendRequest:
    """Test the actual send_request function."""

    @pytest.mark.asyncio
    async def test_send_request_exists(self):
        """Test that send_request function exists and can be called."""
        # This is a basic smoke test
        assert callable(send_request)

    def test_http_module_imports(self):
        """Test that HTTP module imports work."""
        from nutrient_dws import http

        assert hasattr(http, "send_request")


class TestHttpErrors:
    """Test HTTP error handling."""

    def test_api_error_creation(self):
        """Test creating API error."""
        error = APIError("Test error", 400)
        assert error.status_code == 400
        assert "Test error" in str(error)

    def test_validation_error_creation(self):
        """Test creating validation error."""
        error = ValidationError("Validation failed")
        assert "Validation failed" in str(error)
