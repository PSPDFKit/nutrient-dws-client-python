"""Custom exceptions for Nutrient DWS client."""

from typing import Any, Optional


class NutrientError(Exception):
    """Base exception for all Nutrient client errors."""

    pass


class AuthenticationError(NutrientError):
    """Raised when authentication fails (401/403 errors).

    This typically indicates:
    - Missing API key
    - Invalid API key
    - Expired API key
    - Insufficient permissions
    """

    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize AuthenticationError."""
        super().__init__(message)


class APIError(NutrientError):
    """Raised for general API errors.

    Attributes:
        status_code: HTTP status code from the API.
        response_body: Raw response body from the API for debugging.
        request_id: Request ID for tracking (if available).
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Initialize APIError with status code and response body."""
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.request_id = request_id

    def __str__(self) -> str:
        """String representation with all available error details."""
        parts = [str(self.args[0]) if self.args else "API Error"]

        if self.status_code:
            parts.append(f"Status: {self.status_code}")

        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")

        if self.response_body:
            parts.append(f"Response: {self.response_body}")

        return " | ".join(parts)


class ValidationError(NutrientError):
    """Raised when request validation fails."""

    def __init__(self, message: str, errors: Optional[dict[str, Any]] = None) -> None:
        """Initialize ValidationError with validation details."""
        super().__init__(message)
        self.errors = errors or {}


class NutrientTimeoutError(NutrientError):
    """Raised when a request times out."""

    pass


class FileProcessingError(NutrientError):
    """Raised when file processing fails."""

    pass
