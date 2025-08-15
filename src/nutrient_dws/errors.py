"""Error classes for Nutrient DWS client.
Provides consistent error handling across the library.
"""

from typing import Any


class NutrientError(Exception):
    """Base error class for all Nutrient DWS client errors.
    Provides consistent error handling across the library.
    """

    def __init__(
        self,
        message: str,
        code: str = "NUTRIENT_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize a NutrientError.

        Args:
            message: Error message
            code: Error code for programmatic error handling
            details: Additional error details
            status_code: HTTP status code if the error originated from an HTTP response
        """
        super().__init__(message)
        self.name = "NutrientError"
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code

        # Python doesn't have direct equivalent to Error.captureStackTrace,
        # but the stack trace is automatically captured

    def to_json(self) -> dict[str, Any]:
        """Returns a JSON representation of the error.

        Returns:
            Dict containing error details
        """
        return {
            "name": self.name,
            "message": str(self),
            "code": self.code,
            "details": self.details,
            "status_code": self.status_code,
            "stack": self.__traceback__,
        }

    def __str__(self) -> str:
        """Returns a string representation of the error.

        Returns:
            Formatted error string
        """
        result = f"{self.name}: {super().__str__()}"
        if self.code != "NUTRIENT_ERROR":
            result += f" ({self.code})"
        if self.status_code:
            result += f" [HTTP {self.status_code}]"
        return result

    @classmethod
    def wrap(cls, error: Any, message: str | None = None) -> "NutrientError":
        """Wraps an unknown error into a NutrientError.

        Args:
            error: The error to wrap
            message: Optional message to prepend

        Returns:
            A NutrientError instance
        """
        if isinstance(error, NutrientError):
            return error

        if isinstance(error, Exception):
            wrapped_message = f"{message}: {error!s}" if message else str(error)
            return NutrientError(
                wrapped_message,
                "WRAPPED_ERROR",
                {
                    "originalError": error.__class__.__name__,
                    "originalMessage": str(error),
                    "stack": error.__traceback__,
                },
            )

        error_message = message or "An unknown error occurred"
        return NutrientError(
            error_message, "UNKNOWN_ERROR", {"originalError": str(error)}
        )


class ValidationError(NutrientError):
    """Error thrown when input validation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize a ValidationError.

        Args:
            message: Error message
            details: Additional error details
            status_code: HTTP status code if applicable
        """
        super().__init__(message, "VALIDATION_ERROR", details, status_code)
        self.name = "ValidationError"


class APIError(NutrientError):
    """Error thrown when API requests fail."""

    def __init__(
        self,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an APIError.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message, "API_ERROR", details, status_code)
        self.name = "APIError"


class AuthenticationError(NutrientError):
    """Error thrown when authentication fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 401,
    ) -> None:
        """Initialize an AuthenticationError.

        Args:
            message: Error message
            details: Additional error details
            status_code: HTTP status code, defaults to 401
        """
        super().__init__(message, "AUTHENTICATION_ERROR", details, status_code)
        self.name = "AuthenticationError"


class NetworkError(NutrientError):
    """Error thrown when network requests fail."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize a NetworkError.

        Args:
            message: Error message
            details: Additional error details
            status_code: HTTP status code if applicable
        """
        super().__init__(message, "NETWORK_ERROR", details, status_code)
        self.name = "NetworkError"
