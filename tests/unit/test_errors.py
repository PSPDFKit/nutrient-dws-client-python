"""Simple error tests for actual functionality."""

import json
import pytest

from nutrient_dws.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    NutrientError,
    ValidationError,
)


class TestNutrientError:
    def test_create_base_error_with_message_and_code(self):
        error = NutrientError("Test error", "TEST_ERROR")

        assert error.message == "Test error"
        assert error.code == "TEST_ERROR"
        assert error.__class__.__name__ == "NutrientError"
        assert hasattr(error, "__traceback__")
        assert error.details is None
        assert error.status_code is None

    def test_include_details_when_provided(self):
        details = {"foo": "bar", "baz": 123}
        error = NutrientError("Test error", "TEST_ERROR", details)

        assert error.details == details

    def test_include_status_code_when_provided(self):
        error = NutrientError("Test error", "TEST_ERROR", {"foo": "bar"}, 400)

        assert error.status_code == 400

    def test_is_instance_of_exception(self):
        error = NutrientError("Test error", "TEST_ERROR")

        assert isinstance(error, Exception)
        assert isinstance(error, NutrientError)


class TestValidationError:
    def test_create_validation_error_with_default_code(self):
        error = ValidationError("Invalid input")

        assert error.message == "Invalid input"
        assert error.code == "VALIDATION_ERROR"
        assert error.__class__.__name__ == "ValidationError"

    def test_inherit_from_nutrient_error(self):
        error = ValidationError("Invalid input")

        assert isinstance(error, Exception)
        assert isinstance(error, NutrientError)
        assert isinstance(error, ValidationError)

    def test_accept_details_and_status_code(self):
        details = {"field": "email", "reason": "invalid format"}
        error = ValidationError("Invalid input", details, 422)

        assert error.details == details
        assert error.status_code == 422


class TestAPIError:
    def test_create_api_error_with_status_code(self):
        error = APIError("Server error", 500)

        assert error.message == "Server error"
        assert error.code == "API_ERROR"
        assert error.__class__.__name__ == "APIError"
        assert error.status_code == 500

    def test_inherit_from_nutrient_error(self):
        error = APIError("Server error", 500)

        assert isinstance(error, Exception)
        assert isinstance(error, NutrientError)
        assert isinstance(error, APIError)

    def test_accept_details(self):
        details = {"endpoint": "/convert", "method": "POST"}
        error = APIError("Server error", 500, details)

        assert error.details == details


class TestAuthenticationError:
    def test_create_authentication_error_with_default_code(self):
        error = AuthenticationError("Invalid API key")

        assert error.message == "Invalid API key"
        assert error.code == "AUTHENTICATION_ERROR"
        assert error.__class__.__name__ == "AuthenticationError"

    def test_inherit_from_nutrient_error(self):
        error = AuthenticationError("Invalid API key")

        assert isinstance(error, Exception)
        assert isinstance(error, NutrientError)
        assert isinstance(error, AuthenticationError)

    def test_accept_details_and_status_code(self):
        details = {"reason": "expired token"}
        error = AuthenticationError("Invalid API key", details, 401)

        assert error.details == details
        assert error.status_code == 401


class TestNetworkError:
    def test_create_network_error_with_default_code(self):
        error = NetworkError("Connection failed")

        assert error.message == "Connection failed"
        assert error.code == "NETWORK_ERROR"
        assert error.__class__.__name__ == "NetworkError"

    def test_inherit_from_nutrient_error(self):
        error = NetworkError("Connection failed")

        assert isinstance(error, Exception)
        assert isinstance(error, NutrientError)
        assert isinstance(error, NetworkError)

    def test_accept_details(self):
        details = {"timeout": 30000, "endpoint": "https://api.nutrient.io"}
        error = NetworkError("Connection failed", details)

        assert error.details == details


class TestErrorSerialization:
    def test_serialize_to_json_correctly(self):
        error = ValidationError("Invalid input", {"field": "email"}, 422)
        error_dict = {
            "message": error.message,
            "code": error.code,
            "name": error.__class__.__name__,
            "details": error.details,
            "status_code": error.status_code,
        }
        json_str = json.dumps(error_dict)
        parsed = json.loads(json_str)

        assert parsed["message"] == "Invalid input"
        assert parsed["code"] == "VALIDATION_ERROR"
        assert parsed["name"] == "ValidationError"
        assert parsed["details"] == {"field": "email"}
        assert parsed["status_code"] == 422

    def test_maintain_error_properties_when_caught(self):
        def throw_and_catch():
            try:
                raise APIError("Test error", 500, {"foo": "bar"})
            except Exception as e:
                return e

        error = throw_and_catch()
        assert error is not None
        assert error.message == "Test error"
        assert error.code == "API_ERROR"
        assert error.status_code == 500
        assert error.details == {"foo": "bar"}


class TestToStringMethod:
    def test_format_error_with_default_code(self):
        error = NutrientError("Test error")
        assert str(error) == "NutrientError: Test error"

    def test_include_custom_code_when_provided(self):
        error = NutrientError("Test error", "CUSTOM_CODE")
        assert str(error) == "NutrientError: Test error (CUSTOM_CODE)"

    def test_include_status_code_when_provided(self):
        error = NutrientError("Test error", "CUSTOM_CODE", {}, 404)
        assert str(error) == "NutrientError: Test error (CUSTOM_CODE) [HTTP 404]"

    def test_include_status_code_without_custom_code(self):
        error = NutrientError("Test error", "NUTRIENT_ERROR", {}, 500)
        assert str(error) == "NutrientError: Test error [HTTP 500]"


class TestWrapMethod:
    def test_return_original_error_if_nutrient_error(self):
        original_error = ValidationError("Original error")
        wrapped_error = NutrientError.wrap(original_error)

        assert wrapped_error is original_error

    def test_wrap_standard_exception_instances(self):
        original_error = Exception("Standard error")
        wrapped_error = NutrientError.wrap(original_error)

        assert isinstance(wrapped_error, NutrientError)
        assert wrapped_error.message == "Standard error"
        assert wrapped_error.code == "WRAPPED_ERROR"
        assert wrapped_error.details == {
            "originalError": "Exception",
            "originalMessage": "Standard error",
            "stack": None,
        }

    def test_wrap_standard_exception_instances_with_custom_message(self):
        original_error = Exception("Standard error")
        wrapped_error = NutrientError.wrap(original_error, "Custom prefix")

        assert isinstance(wrapped_error, NutrientError)
        assert wrapped_error.message == "Custom prefix: Standard error"
        assert wrapped_error.code == "WRAPPED_ERROR"

    def test_handle_non_exception_objects(self):
        wrapped_error = NutrientError.wrap("String error")

        assert isinstance(wrapped_error, NutrientError)
        assert wrapped_error.message == "An unknown error occurred"
        assert wrapped_error.code == "UNKNOWN_ERROR"
        assert wrapped_error.details == {
            "originalError": "String error",
        }

    def test_handle_non_exception_objects_with_custom_message(self):
        wrapped_error = NutrientError.wrap(None, "Custom message")

        assert isinstance(wrapped_error, NutrientError)
        assert wrapped_error.message == "Custom message"
        assert wrapped_error.code == "UNKNOWN_ERROR"
        assert wrapped_error.details == {
            "originalError": "None",
        }
