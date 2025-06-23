"""Comprehensive unit tests for HTTPClient."""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from nutrient_dws.exceptions import (
    APIError,
    AuthenticationError,
    NutrientTimeoutError,
)
from nutrient_dws.http_client import HTTPClient


class TestHTTPClientInitialization:
    """Test suite for HTTPClient initialization."""

    def test_http_client_init_default(self):
        """Test HTTP client initialization with defaults."""
        client = HTTPClient(api_key="test-key")
        assert client._api_key == "test-key"
        assert client._base_url == "https://api.pspdfkit.com"
        assert client._timeout == 300

    def test_http_client_init_custom_timeout(self):
        """Test HTTP client with custom timeout."""
        client = HTTPClient(api_key="test-key", timeout=60)
        assert client._timeout == 60

    def test_http_client_init_no_api_key(self):
        """Test HTTP client initialization without API key."""
        client = HTTPClient(api_key=None)
        assert client._api_key is None

    def test_http_client_init_empty_api_key(self):
        """Test HTTP client initialization with empty API key."""
        client = HTTPClient(api_key="")
        assert client._api_key == ""

    def test_http_client_creates_session(self):
        """Test that HTTP client creates a requests session."""
        client = HTTPClient(api_key="test-key")
        assert hasattr(client, "_session")
        assert isinstance(client._session, requests.Session)

    def test_http_client_session_headers(self):
        """Test that session has proper headers set."""
        client = HTTPClient(api_key="test-key")
        assert "Authorization" in client._session.headers
        assert client._session.headers["Authorization"] == "Bearer test-key"
        assert "User-Agent" in client._session.headers
        assert "nutrient-dws" in client._session.headers["User-Agent"]

    def test_http_client_context_manager(self):
        """Test HTTP client can be used as context manager."""
        with HTTPClient(api_key="test-key") as client:
            assert client is not None
            assert hasattr(client, "_session")


class TestHTTPClientMethods:
    """Test suite for HTTPClient HTTP methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = HTTPClient(api_key="test-key")

    @patch("requests.Session.request")
    def test_post_method_with_json(self, mock_request):
        """Test POST request with JSON data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"POST response"
        mock_request.return_value = mock_response

        json_data = {"key": "value"}
        result = self.client.post("/test", json_data=json_data)

        assert result == b"POST response"
        # Check that the request was made correctly
        assert mock_request.called
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://api.pspdfkit.com/test"

    @patch("requests.Session.request")
    def test_post_method_with_files(self, mock_request):
        """Test POST request with files."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"POST response"
        mock_request.return_value = mock_response

        files = {"file": ("test.pdf", b"file content", "application/pdf")}
        result = self.client.post("/test", files=files)

        assert result == b"POST response"
        # Check that the request was made correctly
        assert mock_request.called
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://api.pspdfkit.com/test"

    @patch("requests.Session.request")
    def test_post_with_both_files_and_json(self, mock_request):
        """Test POST request with both files and JSON data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"POST response"
        mock_request.return_value = mock_response

        files = {"file": ("test.pdf", b"file content", "application/pdf")}
        json_data = {"actions": [{"type": "rotate"}]}
        result = self.client.post("/test", files=files, json_data=json_data)

        assert result == b"POST response"
        assert mock_request.called

    def test_post_without_api_key_raises_error(self):
        """Test POST without API key raises AuthenticationError."""
        client = HTTPClient(api_key=None)

        with pytest.raises(AuthenticationError, match="API key is required"):
            client.post("/test")


class TestHTTPClientErrorHandling:
    """Test suite for HTTPClient error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = HTTPClient(api_key="test-key")

    @patch("requests.Session.request")
    def test_authentication_error_401(self, mock_request):
        """Test 401 authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError, match="HTTP 401: Unauthorized"):
            self.client.post("/test")

    @patch("requests.Session.request")
    def test_authentication_error_403(self, mock_request):
        """Test 403 forbidden error handling."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError, match="HTTP 403: Forbidden"):
            self.client.post("/test")

    @patch("requests.Session.request")
    def test_api_error_400(self, mock_request):
        """Test 400 bad request error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            self.client.post("/test")

        assert exc_info.value.status_code == 400
        assert exc_info.value.response_body == "Bad request"

    @patch("requests.Session.request")
    def test_api_error_500(self, mock_request):
        """Test 500 internal server error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            self.client.post("/test")

        assert exc_info.value.status_code == 500
        assert exc_info.value.response_body == "Internal server error"

    @patch("requests.Session.request")
    def test_timeout_error(self, mock_request):
        """Test timeout error handling."""
        mock_request.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(NutrientTimeoutError, match="Request timed out"):
            self.client.post("/test")

    @patch("requests.Session.request")
    def test_connection_error(self, mock_request):
        """Test connection error handling."""
        mock_request.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(APIError, match="Connection failed"):
            self.client.post("/test")

    @patch("requests.Session.request")
    def test_requests_exception(self, mock_request):
        """Test generic requests exception handling."""
        mock_request.side_effect = requests.RequestException("Request failed")

        with pytest.raises(APIError, match="Request failed"):
            self.client.post("/test")

    @patch("requests.Session.request")
    def test_api_error_with_json_response(self, mock_request):
        """Test API error with JSON error response."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = '{"message": "Validation failed", "details": "Invalid file format"}'
        mock_response.json.return_value = {
            "message": "Validation failed",
            "details": "Invalid file format",
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        from nutrient_dws.exceptions import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            self.client.post("/test")

        assert "Validation failed" in str(exc_info.value)


class TestHTTPClientResponseHandling:
    """Test suite for HTTPClient response handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = HTTPClient(api_key="test-key")

    @patch("requests.Session.request")
    def test_successful_response_with_content(self, mock_request):
        """Test successful response with content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"PDF content here"
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.client.post("/test")
        assert result == b"PDF content here"

    @patch("requests.Session.request")
    def test_successful_response_empty_content(self, mock_request):
        """Test successful response with empty content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b""
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.client.post("/test")
        assert result == b""

    @patch("requests.Session.request")
    def test_successful_response_201(self, mock_request):
        """Test successful 201 Created response."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.content = b"Created content"
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.client.post("/test")
        assert result == b"Created content"

    @patch("requests.Session.request")
    def test_successful_response_204(self, mock_request):
        """Test successful 204 No Content response."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.client.post("/test")
        assert result == b""


class TestHTTPClientContextManager:
    """Test suite for HTTPClient context manager functionality."""

    def test_context_manager_enters_and_exits(self):
        """Test context manager enter and exit."""
        with HTTPClient(api_key="test-key") as client:
            assert client is not None
            assert hasattr(client, "_session")

        # Session should be closed after exiting context
        # Note: We can't directly test if session is closed in requests,
        # but we can verify the close method was accessible

    def test_context_manager_exception_handling(self):
        """Test context manager handles exceptions properly."""
        try:
            with HTTPClient(api_key="test-key") as client:
                assert client is not None
                raise ValueError("Test exception")
        except ValueError:
            pass  # Exception should be propagated

    def test_manual_close(self):
        """Test manual close method."""
        client = HTTPClient(api_key="test-key")

        # Close should not raise an error
        client.close()

        # Verify session is accessible (requests doesn't provide a closed property)
        assert hasattr(client, "_session")


class TestHTTPClientEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = HTTPClient(api_key="test-key")

    @patch("requests.Session.post")
    def test_request_with_all_parameters(self, mock_post):
        """Test request with all possible parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"Full request"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        files = {"file": ("test.pdf", b"content", "application/pdf")}
        json_data = {"action": "process"}
        data = {"key": "value"}

        result = self.client.post("/test", json_data=json_data, files=files, data=data)

        assert result == b"Full request"
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_very_large_response(self, mock_post):
        """Test handling of very large response."""
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = large_content
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.post("/test")
        assert result == large_content
        assert len(result) == 10 * 1024 * 1024

    def test_client_with_none_api_key_no_auth_header(self):
        """Test that None API key doesn't set Authorization header."""
        client = HTTPClient(api_key=None)
        assert "Authorization" not in client._session.headers

    def test_client_with_empty_api_key_no_auth_header(self):
        """Test that empty API key doesn't set Authorization header."""
        client = HTTPClient(api_key="")
        assert "Authorization" not in client._session.headers
