"""HTTP client abstraction for API communication."""

import json
import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from nutrient_dws.exceptions import (
    APIError,
    AuthenticationError,
    NutrientTimeoutError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with connection pooling and retry logic."""

    def __init__(self, api_key: str | None, timeout: int = 300) -> None:
        """Initialize HTTP client with authentication.

        Args:
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key
        self._timeout = timeout
        self._session = self._create_session()
        self._base_url = "https://api.pspdfkit.com"

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()

        # Configure retries with exponential backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,  # We'll handle status codes ourselves
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        headers = {
            "User-Agent": "nutrient-dws-python-client/0.1.0",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        session.headers.update(headers)

        return session

    def _handle_response(self, response: requests.Response) -> bytes:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: Response from the API.

        Returns:
            Response content as bytes.

        Raises:
            AuthenticationError: For 401/403 responses.
            ValidationError: For 422 responses.
            APIError: For other error responses.
        """
        # Extract request ID if available
        request_id = response.headers.get("X-Request-Id")

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            # Try to parse error message from response
            error_message = f"HTTP {response.status_code}"
            error_details = None

            try:
                error_data = response.json()
                error_message = error_data.get("message", error_message)
                error_details = error_data.get("errors", error_data.get("details"))
            except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
                # If response is not JSON, use text content
                if response.text:
                    error_message = f"{error_message}: {response.text[:200]}"

            # Handle specific status codes
            if response.status_code in (401, 403):
                raise AuthenticationError(
                    error_message or "Authentication failed. Check your API key."
                ) from None
            elif response.status_code == 422:
                raise ValidationError(
                    error_message or "Request validation failed",
                    errors=error_details,
                ) from None
            else:
                raise APIError(
                    error_message,
                    status_code=response.status_code,
                    response_body=response.text,
                    request_id=request_id,
                ) from None

        return response.content

    def post(
        self,
        endpoint: str,
        files: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> bytes:
        """Make POST request to API.

        Args:
            endpoint: API endpoint path.
            files: Files to upload.
            data: Form data.
            json_data: JSON data (for multipart requests).

        Returns:
            Response content as bytes.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            TimeoutError: If request times out.
            APIError: For other API errors.
        """
        if not self._api_key:
            raise AuthenticationError("API key is required but not provided")

        url = f"{self._base_url}{endpoint}"
        logger.debug(f"POST {url}")

        # Prepare multipart data if json_data is provided
        prepared_data = data or {}
        if json_data is not None:
            prepared_data["instructions"] = json.dumps(json_data)

        try:
            response = self._session.post(
                url,
                files=files,
                data=prepared_data,
                timeout=self._timeout,
            )
        except requests.exceptions.Timeout as e:
            raise NutrientTimeoutError(f"Request timed out after {self._timeout} seconds") from e
        except requests.exceptions.ConnectionError as e:
            raise APIError(f"Connection error: {e!s}") from e
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e!s}") from e

        logger.debug(f"Response: {response.status_code}")

        # Clean up file handles after request
        if files:
            for _, file_data in files.items():
                if hasattr(file_data, 'close'):
                    file_data.close()
                elif isinstance(file_data, tuple) and len(file_data) > 1:
                    file_obj = file_data[1]
                    if hasattr(file_obj, 'close'):
                        file_obj.close()

        return self._handle_response(response)

    def close(self) -> None:
        """Close the session."""
        self._session.close()

    def __enter__(self) -> "HTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
