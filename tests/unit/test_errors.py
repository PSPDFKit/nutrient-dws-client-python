"""Simple error tests for actual functionality."""

import pytest

from nutrient_dws.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    NutrientError,
    ValidationError,
)


class TestNutrientErrorSimple:
    """Test basic error functionality."""

    def test_nutrient_error_creation(self):
        """Test creating basic NutrientError."""
        error = NutrientError("Test message")
        assert isinstance(error, Exception)
        assert isinstance(error, NutrientError)
        assert "Test message" in str(error)

    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, NutrientError)
        assert "Validation failed" in str(error)

    def test_api_error_creation(self):
        """Test creating APIError."""
        error = APIError("API failed", 400)
        assert isinstance(error, NutrientError)
        assert "API failed" in str(error)
        assert error.status_code == 400

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, NutrientError)
        assert "Auth failed" in str(error)

    def test_network_error_creation(self):
        """Test creating NetworkError."""
        error = NetworkError("Network failed")
        assert isinstance(error, NutrientError)
        assert "Network failed" in str(error)


class TestErrorHierarchy:
    """Test error inheritance hierarchy."""

    def test_all_errors_inherit_from_nutrient_error(self):
        """Test that all custom errors inherit from NutrientError."""
        errors = [
            ValidationError("Test"),
            APIError("Test", 400),
            AuthenticationError("Test"),
            NetworkError("Test"),
        ]

        for error in errors:
            assert isinstance(error, NutrientError)
            assert isinstance(error, Exception)

    def test_error_codes(self):
        """Test that errors have appropriate codes."""
        validation_error = ValidationError("Test")
        assert validation_error.code == "VALIDATION_ERROR"

        api_error = APIError("Test", 400)
        assert api_error.code == "API_ERROR"

        auth_error = AuthenticationError("Test")
        assert auth_error.code == "AUTHENTICATION_ERROR"

        network_error = NetworkError("Test")
        assert network_error.code == "NETWORK_ERROR"


class TestErrorRaising:
    """Test raising and catching errors."""

    def test_raise_and_catch_validation_error(self):
        """Test raising and catching ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid input")

        assert "Invalid input" in str(exc_info.value)

    def test_raise_and_catch_api_error(self):
        """Test raising and catching APIError."""
        with pytest.raises(APIError) as exc_info:
            raise APIError("API request failed", 500)

        assert "API request failed" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    def test_catch_base_error(self):
        """Test catching specific errors as NutrientError."""
        with pytest.raises(NutrientError):
            raise ValidationError("Test validation error")

        with pytest.raises(NutrientError):
            raise APIError("Test API error", 400)

    def test_error_context_managers(self):
        """Test errors work in context managers."""
        try:
            raise ValidationError("Context test")
        except NutrientError as e:
            assert isinstance(e, ValidationError)
            assert "Context test" in str(e)
