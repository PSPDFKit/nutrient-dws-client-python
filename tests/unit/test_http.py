"""HTTP layer tests for Nutrient DWS Python Client."""

import json
from unittest.mock import MagicMock, patch

import pytest
import httpx

from nutrient_dws.errors import APIError, ValidationError, AuthenticationError, NetworkError
from nutrient_dws.http import (
    send_request,
    RequestConfig,
    NutrientClientOptions,
    BuildRequestData,
    resolve_api_key,
    extract_error_message,
    create_http_error,
)
from nutrient_dws.inputs import NormalizedFileData


class TestResolveApiKey:
    def test_resolve_string_api_key(self):
        result = resolve_api_key("test-api-key")
        assert result == "test-api-key"

    def test_resolve_function_api_key(self):
        def api_key_func():
            return "function-api-key"

        result = resolve_api_key(api_key_func)
        assert result == "function-api-key"

    def test_function_returns_empty_string(self):
        def empty_key_func():
            return ""

        with pytest.raises(AuthenticationError, match="API key function must return a non-empty string"):
            resolve_api_key(empty_key_func)

    def test_function_returns_none(self):
        def none_key_func():
            return None

        with pytest.raises(AuthenticationError, match="API key function must return a non-empty string"):
            resolve_api_key(none_key_func)

    def test_function_throws_error(self):
        def error_key_func():
            raise Exception("Token fetch failed")

        with pytest.raises(AuthenticationError, match="Failed to resolve API key from function"):
            resolve_api_key(error_key_func)


class TestExtractErrorMessage:
    def test_extract_error_description(self):
        data = {"error_description": "API key is invalid"}
        result = extract_error_message(data)
        assert result == "API key is invalid"

    def test_extract_error_message(self):
        data = {"error_message": "Request failed"}
        result = extract_error_message(data)
        assert result == "Request failed"

    def test_extract_message(self):
        data = {"message": "Validation failed"}
        result = extract_error_message(data)
        assert result == "Validation failed"

    def test_extract_nested_error_message(self):
        data = {"error": {"message": "Nested error"}}
        result = extract_error_message(data)
        assert result == "Nested error"

    def test_extract_errors_array(self):
        data = {"errors": ["First error", "Second error"]}
        result = extract_error_message(data)
        assert result == "First error"

    def test_extract_errors_object_array(self):
        data = {"errors": [{"message": "Object error"}]}
        result = extract_error_message(data)
        assert result == "Object error"

    def test_no_error_message(self):
        data = {"other": "data"}
        result = extract_error_message(data)
        assert result is None


class TestCreateHttpError:
    def test_create_authentication_error_401(self):
        error = create_http_error(401, "Unauthorized", {"message": "Invalid API key"})
        assert isinstance(error, AuthenticationError)
        assert error.message == "Invalid API key"
        assert error.status_code == 401

    def test_create_authentication_error_403(self):
        error = create_http_error(403, "Forbidden", {"message": "Access denied"})
        assert isinstance(error, AuthenticationError)
        assert error.message == "Access denied"
        assert error.status_code == 403

    def test_create_validation_error_400(self):
        error = create_http_error(400, "Bad Request", {"message": "Invalid parameters"})
        assert isinstance(error, ValidationError)
        assert error.message == "Invalid parameters"
        assert error.status_code == 400

    def test_create_api_error_500(self):
        error = create_http_error(500, "Internal Server Error", {"message": "Server error"})
        assert isinstance(error, APIError)
        assert error.message == "Server error"
        assert error.status_code == 500

    def test_fallback_message(self):
        error = create_http_error(404, "Not Found", {})
        assert error.message == "HTTP 404: Not Found"


class TestSendRequest:
    def setup_method(self):
        self.mock_client_options: NutrientClientOptions = {
            "apiKey": "test-api-key",
            "baseUrl": "https://api.test.com/v1",
            "timeout": None
        }

    @pytest.mark.asyncio
    async def test_successful_get_request(self):
        mock_response_data = {"result": "success"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = mock_response_data

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            result = await send_request(config, self.mock_client_options)

            # Verify the request was made correctly
            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert call_kwargs["method"] == "GET"
            assert call_kwargs["url"] == "https://api.test.com/v1/account/info"
            assert call_kwargs["headers"] == {"Authorization": "Bearer test-api-key"}
            assert call_kwargs["timeout"] is None

            assert result["data"] == {"result": "success"}
            assert result["status"] == 200
            assert result["statusText"] == "OK"
            assert result["headers"]["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_handle_function_api_key(self):
        def api_key_func():
            return "function-api-key"

        async_options: NutrientClientOptions = {
            "apiKey": api_key_func,
            "baseUrl": None,
            "timeout": None
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {}
            mock_response.json.return_value = {"result": "success"}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            await send_request(config, async_options)

            # Verify function API key was used
            mock_client.return_value.__aenter__.return_value.request.assert_called_once()
            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer function-api-key"

    @pytest.mark.asyncio
    async def test_throw_authentication_error_for_invalid_function_api_key(self):
        def empty_key_func():
            return ""

        async_options: NutrientClientOptions = {
            "apiKey": empty_key_func,
            "baseUrl": None,
            "timeout": None
        }

        config: RequestConfig[None] = {
            "endpoint": "/account/info",
            "method": "GET",
            "data": None,
            "headers": None
        }

        with pytest.raises(AuthenticationError, match="API key function must return a non-empty string"):
            await send_request(config, async_options)

    @pytest.mark.asyncio
    async def test_throw_authentication_error_when_function_fails(self):
        def error_key_func():
            raise Exception("Token fetch failed")

        async_options: NutrientClientOptions = {
            "apiKey": error_key_func,
            "baseUrl": None,
            "timeout": None
        }

        config: RequestConfig[None] = {
            "endpoint": "/account/info",
            "method": "GET",
            "data": None,
            "headers": None
        }

        with pytest.raises(AuthenticationError, match="Failed to resolve API key from function"):
            await send_request(config, async_options)

    @pytest.mark.asyncio
    async def test_send_json_data_with_proper_headers(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.reason_phrase = "Created"
            mock_response.headers = {}
            mock_response.json.return_value = {"id": 123}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            # Use analyze_build endpoint for JSON-only requests
            config: RequestConfig = {
                "endpoint": "/analyze_build",
                "method": "POST",
                "data": {
                    "instructions": {"parts": [{"file": "test.pdf"}]}
                },
                "headers": None
            }

            await send_request(config, self.mock_client_options)

            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert "json" in call_kwargs

    @pytest.mark.asyncio
    async def test_send_files_with_form_data(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {}
            mock_response.json.return_value = {"uploaded": True}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            file_data: NormalizedFileData = (b"\x01\x02\x03\x04", "file.bin")
            files_map: dict[str, NormalizedFileData] = {"document": file_data}

            build_data: BuildRequestData = {
                "files": files_map,
                "instructions": {
                    "parts": [{"file": "document"}],
                    "output": {"type": "pdf"}
                }
            }

            config: RequestConfig[BuildRequestData] = {
                "endpoint": "/build",
                "method": "POST",
                "data": build_data,
                "headers": None
            }

            await send_request(config, self.mock_client_options)

            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert "files" in call_kwargs
            assert "data" in call_kwargs

            # Check that files are properly formatted
            files = call_kwargs["files"]
            assert "document" in files
            assert files["document"][0] == "file.bin"  # filename
            assert files["document"][1] == b"\x01\x02\x03\x04"  # content

            # Check that instructions are JSON-encoded
            data = call_kwargs["data"]
            assert "instructions" in data
            instructions = json.loads(data["instructions"])
            assert instructions["parts"] == [{"file": "document"}]

    @pytest.mark.asyncio
    async def test_handle_401_authentication_error(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.reason_phrase = "Unauthorized"
            mock_response.headers = {}
            mock_response.json.return_value = {"error": "Invalid API key"}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            with pytest.raises(AuthenticationError) as exc_info:
                await send_request(config, self.mock_client_options)

            error = exc_info.value
            assert error.message == "Invalid API key"
            assert error.code == "AUTHENTICATION_ERROR"
            assert error.status_code == 401

    @pytest.mark.asyncio
    async def test_handle_400_validation_error(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.reason_phrase = "Bad Request"
            mock_response.headers = {}
            mock_response.json.return_value = {"message": "Invalid parameters"}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            # Use analyze_build endpoint for JSON-only requests
            config: RequestConfig = {
                "endpoint": "/analyze_build",
                "method": "POST",
                "data": {
                    "instructions": {}
                },
                "headers": None
            }

            with pytest.raises(ValidationError) as exc_info:
                await send_request(config, self.mock_client_options)

            error = exc_info.value
            assert error.message == "Invalid parameters"
            assert error.code == "VALIDATION_ERROR"
            assert error.status_code == 400

    @pytest.mark.asyncio
    async def test_handle_network_errors(self):
        with patch("httpx.AsyncClient") as mock_client:
            network_error = httpx.RequestError("Network Error")
            network_error.request = httpx.Request("GET", "https://api.test.com/v1/account/info")

            mock_client.return_value.__aenter__.return_value.request.side_effect = network_error

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            with pytest.raises(NetworkError) as exc_info:
                await send_request(config, self.mock_client_options)

            error = exc_info.value
            assert error.message == "Network request failed"
            assert error.code == "NETWORK_ERROR"

    @pytest.mark.asyncio
    async def test_not_leak_api_key_in_network_error_details(self):
        with patch("httpx.AsyncClient") as mock_client:
            network_error = httpx.RequestError("Network Error")
            network_error.request = httpx.Request("GET", "https://api.test.com/v1/account/info")

            mock_client.return_value.__aenter__.return_value.request.side_effect = network_error

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": {
                    "Authorization": "Bearer secret-api-key-that-should-not-leak",
                    "Content-Type": "application/json",
                    "X-Custom-Header": "custom-value"
                }
            }

            with pytest.raises(NetworkError) as exc_info:
                await send_request(config, self.mock_client_options)

            error = exc_info.value
            assert error.message == "Network request failed"
            assert error.code == "NETWORK_ERROR"

            # Verify headers are present but Authorization is sanitized
            assert "headers" in error.details
            headers = error.details["headers"]
            assert headers["X-Custom-Header"] == "custom-value"
            assert "Authorization" not in headers

            # Verify the API key is not present in the stringified error
            error_string = json.dumps(error.details)
            assert "secret-api-key-that-should-not-leak" not in error_string

    @pytest.mark.asyncio
    async def test_use_custom_timeout(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {}
            mock_response.json.return_value = {}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            custom_options = {**self.mock_client_options, "timeout": 60}
            await send_request(config, custom_options)

            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert call_kwargs["timeout"] == 60

    @pytest.mark.asyncio
    async def test_use_default_timeout_when_not_specified(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {}
            mock_response.json.return_value = {}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            await send_request(config, self.mock_client_options)

            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert call_kwargs["timeout"] is None

    @pytest.mark.asyncio
    async def test_handle_multiple_files_in_request(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {}
            mock_response.json.return_value = {"success": True}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            files_map: dict[str, NormalizedFileData] = {
                "file1": (b"\x01\x02\x03", "file1.bin"),
                "file2": (b"\x04\x05\x06", "file2.bin"),
                "file3": (b"\x07\x08\x09", "file3.bin")
            }

            build_data: BuildRequestData = {
                "files": files_map,
                "instructions": {
                    "parts": [{"file": "file1"}, {"file": "file2"}, {"file": "file3"}],
                    "output": {"type": "pdf"}
                }
            }

            config: RequestConfig[BuildRequestData] = {
                "endpoint": "/build",
                "method": "POST",
                "data": build_data,
                "headers": None
            }

            await send_request(config, self.mock_client_options)

            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            files = call_kwargs["files"]

            # Check all files are present
            assert "file1" in files
            assert "file2" in files
            assert "file3" in files

            # Check file content
            assert files["file1"] == ("file1.bin", b"\x01\x02\x03")
            assert files["file2"] == ("file2.bin", b"\x04\x05\x06")
            assert files["file3"] == ("file3.bin", b"\x07\x08\x09")

    @pytest.mark.asyncio
    async def test_handle_binary_response_data(self):
        with patch("httpx.AsyncClient") as mock_client:
            binary_data = b"PDF content here"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {"content-type": "application/pdf"}
            mock_response.json.side_effect = json.JSONDecodeError("Not JSON", "", 0)
            mock_response.content = binary_data

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            # Use analyze_build endpoint for JSON-only requests
            config: RequestConfig = {
                "endpoint": "/analyze_build",
                "method": "POST",
                "data": {
                    "instructions": {"parts": [{"file": "test.pdf"}]}
                },
                "headers": None
            }

            result = await send_request(config, self.mock_client_options)

            assert result["data"] == binary_data
            assert result["headers"]["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_strip_trailing_slashes_from_base_url(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {}
            mock_response.json.return_value = {}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            options_with_trailing_slash: NutrientClientOptions = {
                "apiKey": "test-key",
                "baseUrl": "https://api.nutrient.io/",
                "timeout": None
            }

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            await send_request(config, options_with_trailing_slash)

            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert call_kwargs["url"] == "https://api.nutrient.io/account/info"

    @pytest.mark.asyncio
    async def test_use_default_base_url_when_none(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.reason_phrase = "OK"
            mock_response.headers = {}
            mock_response.json.return_value = {}

            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            options_without_base_url: NutrientClientOptions = {
                "apiKey": "test-key",
                "baseUrl": None,
                "timeout": None
            }

            config: RequestConfig[None] = {
                "endpoint": "/account/info",
                "method": "GET",
                "data": None,
                "headers": None
            }

            await send_request(config, options_without_base_url)

            call_kwargs = mock_client.return_value.__aenter__.return_value.request.call_args.kwargs
            assert call_kwargs["url"] == "https://api.nutrient.io/account/info"
