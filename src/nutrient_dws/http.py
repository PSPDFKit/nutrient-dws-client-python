"""HTTP request and response type definitions for API communication."""

import json
from collections.abc import Awaitable, Callable
from typing import Any, Generic, Literal, TypeGuard, TypeVar, Union, overload

import httpx
from typing_extensions import NotRequired, TypedDict

from nutrient_dws.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    NutrientError,
    ValidationError,
)
from nutrient_dws.inputs import FileInput, NormalizedFileData
from nutrient_dws.types.account_info import AccountInfo
from nutrient_dws.types.analyze_response import AnalyzeBuildResponse
from nutrient_dws.types.build_instruction import BuildInstructions
from nutrient_dws.types.build_response_json import BuildResponseJsonContents
from nutrient_dws.types.create_auth_token import (
    CreateAuthTokenParameters,
    CreateAuthTokenResponse,
)
from nutrient_dws.types.redact_data import RedactData
from nutrient_dws.types.sign_request import CreateDigitalSignature
from nutrient_dws.utils import get_user_agent


class BuildRequestData(TypedDict):
    instructions: BuildInstructions
    files: NotRequired[dict[str, NormalizedFileData]]


class AnalyzeBuildRequestData(TypedDict):
    instructions: BuildInstructions


class SignRequestOptions(TypedDict):
    image: NotRequired[FileInput]
    graphicImage: NotRequired[FileInput]


class SignRequestData(TypedDict):
    file: NormalizedFileData
    data: NotRequired[CreateDigitalSignature]
    image: NotRequired[NormalizedFileData]
    graphicImage: NotRequired[NormalizedFileData]


class RedactRequestData(TypedDict):
    data: RedactData
    fileKey: NotRequired[str]
    file: NotRequired[NormalizedFileData]


class DeleteTokenRequestData(TypedDict):
    id: str


# Methods and Endpoints types
Method = TypeVar("Method", bound=Literal["GET", "POST", "DELETE"])
Endpoint = TypeVar(
    "Endpoint",
    bound=Literal[
        "/account/info", "/build", "/analyze_build", "/sign", "/ai/redact", "/tokens"
    ],
)

# Type variables for generic types
Input = TypeVar(
    "Input",
    bound=CreateAuthTokenParameters
    | BuildRequestData
    | AnalyzeBuildRequestData
    | SignRequestData
    | RedactRequestData
    | DeleteTokenRequestData
    | None,
)
Output = TypeVar(
    "Output",
    bound=CreateAuthTokenResponse
    | str
    | bytes
    | BuildResponseJsonContents
    | AnalyzeBuildResponse
    | AccountInfo
    | None,
)


# Request configuration
class RequestConfig(TypedDict, Generic[Method, Endpoint, Input]):
    """HTTP request configuration for API calls."""

    method: Method
    endpoint: Endpoint
    data: Input  # The actual type depends on the method and endpoint
    headers: dict[str, str] | None


def is_get_account_info_request_config(
    request: RequestConfig[Method, Endpoint, Input],
) -> TypeGuard[RequestConfig[Literal["GET"], Literal["/account/info"], None]]:
    return request["method"] == "GET" and request["endpoint"] == "/account/info"


def is_post_build_request_config(
    request: RequestConfig[Method, Endpoint, Input],
) -> TypeGuard[RequestConfig[Literal["POST"], Literal["/build"], BuildRequestData]]:
    return request["method"] == "POST" and request["endpoint"] == "/build"


def is_post_analyse_build_request_config(
    request: RequestConfig[Method, Endpoint, Input],
) -> TypeGuard[
    RequestConfig[Literal["POST"], Literal["/analyze_build"], AnalyzeBuildRequestData]
]:
    return request["method"] == "POST" and request["endpoint"] == "/analyze_build"


def is_post_sign_request_config(
    request: RequestConfig[Method, Endpoint, Input],
) -> TypeGuard[RequestConfig[Literal["POST"], Literal["/sign"], SignRequestData]]:
    return request["method"] == "POST" and request["endpoint"] == "/sign"


def is_post_ai_redact_request_config(
    request: RequestConfig[Method, Endpoint, Input],
) -> TypeGuard[
    RequestConfig[Literal["POST"], Literal["/ai/redact"], RedactRequestData]
]:
    return request["method"] == "POST" and request["endpoint"] == "/ai/redact"


def is_post_tokens_request_config(
    request: RequestConfig[Method, Endpoint, Input],
) -> TypeGuard[
    RequestConfig[Literal["POST"], Literal["/tokens"], CreateAuthTokenParameters]
]:
    return request["method"] == "POST" and request["endpoint"] == "/tokens"


def is_delete_tokens_request_config(
    request: RequestConfig[Method, Endpoint, Input],
) -> TypeGuard[
    RequestConfig[Literal["DELETE"], Literal["/tokens"], DeleteTokenRequestData]
]:
    return request["method"] == "DELETE" and request["endpoint"] == "/tokens"


# API response
class ApiResponse(TypedDict, Generic[Output]):
    """Response from API call."""

    data: Output  # The actual type depends on the method and endpoint
    status: int
    statusText: str
    headers: dict[str, Any]


# Client options
class NutrientClientOptions(TypedDict):
    """Client options for Nutrient DWS API."""

    apiKey: str | Callable[[], str | Awaitable[str]]
    baseUrl: str | None
    timeout: int | None


async def resolve_api_key(api_key: str | Callable[[], str | Awaitable[str]]) -> str:
    """Resolves API key from string or function.

    Args:
        api_key: API key as string or function that returns a string

    Returns:
        Resolved API key as string

    Raises:
        AuthenticationError: If API key function returns invalid value
    """
    if isinstance(api_key, str):
        return api_key

    try:
        resolved_key = api_key()
        if isinstance(resolved_key, Awaitable):
            return await resolved_key
        if not isinstance(resolved_key, str) or len(resolved_key) == 0:
            raise AuthenticationError(
                "API key function must return a non-empty string",
                {"resolvedType": type(resolved_key).__name__},
            )
        return resolved_key
    except Exception as error:
        if isinstance(error, AuthenticationError):
            raise error
        raise AuthenticationError(
            "Failed to resolve API key from function", {"error": str(error)}
        )


def append_file_to_form_data(
    form_data: dict[str, Any], key: str, file: NormalizedFileData
) -> None:
    """Appends file to form data with proper format.

    Args:
        form_data: Form data dictionary
        key: Key for the file
        file: File data

    Raises:
        ValidationError: If file data is not in expected format
    """
    file_content, filename = file

    if not isinstance(file_content, bytes):
        raise ValidationError(
            "Expected bytes for file data", {"dataType": type(file_content).__name__}
        )

    form_data[key] = (filename, file_content)


def prepare_request_body(
    request_config: dict[str, Any], config: RequestConfig[Method, Endpoint, Input]
) -> dict[str, Any]:
    """Prepares request body with files and data.

    Args:
        request_config: Request configuration dictionary
        config: Request configuration

    Returns:
        Updated request configuration
    """
    if is_post_build_request_config(config):
        # Use multipart/form-data for file uploads
        files: dict[str, Any] = {}
        for key, value in config["data"]["files"].items():
            append_file_to_form_data(files, key, value)

        request_config["files"] = files
        request_config["data"] = {
            "instructions": json.dumps(config["data"]["instructions"])
        }

        return request_config

    if is_post_analyse_build_request_config(config):
        # JSON only request
        request_config["json"] = config["data"]["instructions"]

        return request_config

    if is_post_sign_request_config(config):
        files = {}
        append_file_to_form_data(files, "file", config["data"]["file"])

        if "image" in config["data"]:
            append_file_to_form_data(files, "image", config["data"]["image"])

        if "graphicImage" in config["data"]:
            append_file_to_form_data(
                files, "graphicImage", config["data"]["graphicImage"]
            )

        request_config["files"] = files

        data = {}
        if "data" in config["data"] and config["data"]["data"] is not None:
            data["data"] = json.dumps(config["data"]["data"])
        else:
            data["data"] = json.dumps(
                {
                    "signatureType": "cades",
                    "cadesLevel": "b-lt",
                }
            )

        request_config["data"] = data

        return request_config

    if is_post_ai_redact_request_config(config):
        if "file" in config["data"] and "fileKey" in config["data"]:
            files = {}
            append_file_to_form_data(
                files, config["data"]["fileKey"], config["data"]["file"]
            )

            request_config["files"] = files
            request_config["data"] = {"data": json.dumps(config["data"]["data"])}
        else:
            # JSON only request
            request_config["json"] = config["data"]["data"]

        return request_config

    # Fallback, passing data as JSON
    if "data" in config:
        request_config["json"] = config["data"]

    return request_config


def extract_error_message(data: Any) -> str | None:
    """Extracts error message from response data with comprehensive DWS error handling.

    Args:
        data: Response data

    Returns:
        Extracted error message or None if not found
    """
    if isinstance(data, dict):
        error_data = data

        # DWS-specific error fields (prioritized)
        if "error_description" in error_data and isinstance(
            error_data["error_description"], str
        ):
            return error_data["error_description"]

        if "error_message" in error_data and isinstance(
            error_data["error_message"], str
        ):
            return error_data["error_message"]

        # Common error message fields
        if "message" in error_data and isinstance(error_data["message"], str):
            return error_data["message"]

        if "error" in error_data and isinstance(error_data["error"], str):
            return error_data["error"]

        if "detail" in error_data and isinstance(error_data["detail"], str):
            return error_data["detail"]

        if "details" in error_data and isinstance(error_data["details"], str):
            return error_data["details"]

        # Handle nested error objects
        if "error" in error_data and isinstance(error_data["error"], dict):
            nested_error = error_data["error"]

            if "message" in nested_error and isinstance(nested_error["message"], str):
                return nested_error["message"]

            if "description" in nested_error and isinstance(
                nested_error["description"], str
            ):
                return nested_error["description"]

        # Handle errors array (common in validation responses)
        if (
            "errors" in error_data
            and isinstance(error_data["errors"], list)
            and error_data["errors"]
        ):
            first_error = error_data["errors"][0]

            if isinstance(first_error, str):
                return first_error

            if isinstance(first_error, dict):
                error_obj = first_error

                if "message" in error_obj and isinstance(error_obj["message"], str):
                    return error_obj["message"]

    return None


def create_http_error(status: int, status_text: str, data: Any) -> NutrientError:
    """Creates appropriate error for HTTP status codes.

    Args:
        status: HTTP status code
        status_text: HTTP status text
        data: Response data

    Returns:
        Appropriate NutrientError subclass
    """
    message = extract_error_message(data) or f"HTTP {status}: {status_text}"
    details = data if isinstance(data, dict) else {"response": data}

    if status in (401, 403):
        return AuthenticationError(message, details, status)

    if 400 <= status < 500:
        return ValidationError(message, details, status)

    return APIError(message, status, details)


def handle_response(response: httpx.Response) -> ApiResponse[Output]:
    """Handles HTTP response and converts to standardized format.

    Args:
        response: Response from the API

    Returns:
        Standardized API response

    Raises:
        NutrientError: For error responses
    """
    status = response.status_code
    status_text = response.reason_phrase
    headers: dict[str, Any] = dict(response.headers)

    try:
        data = response.json()
    except (ValueError, json.JSONDecodeError):
        data = response.content

    # Check for error status codes
    if status >= 400:
        raise create_http_error(status, status_text, data)

    return {
        "data": data,
        "status": status,
        "statusText": status_text,
        "headers": headers,
    }


def convert_error(
    error: Any, config: RequestConfig[Method, Endpoint, Input]
) -> NutrientError:
    """Converts various error types to NutrientError.

    Args:
        error: The error to convert
        config: Request configuration

    Returns:
        Converted NutrientError
    """
    if isinstance(error, NutrientError):
        return error

    if isinstance(error, (httpx.RequestError, httpx.HTTPStatusError)):
        response = getattr(error, "response", None)
        request = getattr(error, "request", None)
        message = str(error)

        if response is not None:
            # HTTP error response
            try:
                response_data = response.json()
            except (ValueError, json.JSONDecodeError):
                response_data = response.text
            return create_http_error(
                response.status_code, response.reason_phrase, response_data
            )

        if request is not None:
            # Network error (request made but no response)
            sanitized_headers = (config.get("headers") or {}).copy()
            if "Authorization" in sanitized_headers:
                del sanitized_headers["Authorization"]

            return NetworkError(
                "Network request failed",
                {
                    "message": message,
                    "endpoint": config["endpoint"],
                    "method": config["method"],
                    "headers": sanitized_headers,
                },
            )

        # Request setup error
        return ValidationError(
            "Request configuration error",
            {
                "message": message,
                "endpoint": config["endpoint"],
                "method": config["method"],
                "data": config.get("data"),
            },
        )

    # Unknown error
    return NutrientError(
        "Unexpected error occurred",
        "UNKNOWN_ERROR",
        {
            "error": str(error),
            "endpoint": config["endpoint"],
            "method": config["method"],
            "data": config.get("data"),
        },
    )


@overload
async def send_request(
    config: RequestConfig[Literal["GET"], Literal["/account/info"], None],
    client_options: NutrientClientOptions,
) -> ApiResponse[AccountInfo]: ...


@overload
async def send_request(
    config: RequestConfig[
        Literal["POST"], Literal["/tokens"], CreateAuthTokenParameters
    ],
    client_options: NutrientClientOptions,
) -> ApiResponse[CreateAuthTokenResponse]: ...


@overload
async def send_request(
    config: RequestConfig[Literal["POST"], Literal["/build"], BuildRequestData],
    client_options: NutrientClientOptions,
) -> ApiResponse[Union[BuildResponseJsonContents, bytes, str]]: ...


@overload
async def send_request(
    config: RequestConfig[
        Literal["POST"], Literal["/analyze_build"], AnalyzeBuildRequestData
    ],
    client_options: NutrientClientOptions,
) -> ApiResponse[AnalyzeBuildResponse]: ...


@overload
async def send_request(
    config: RequestConfig[Literal["POST"], Literal["/sign"], SignRequestData],
    client_options: NutrientClientOptions,
) -> ApiResponse[bytes]: ...


@overload
async def send_request(
    config: RequestConfig[Literal["POST"], Literal["/ai/redact"], RedactRequestData],
    client_options: NutrientClientOptions,
) -> ApiResponse[bytes]: ...


@overload
async def send_request(
    config: RequestConfig[
        Literal["DELETE"], Literal["/tokens"], DeleteTokenRequestData
    ],
    client_options: NutrientClientOptions,
) -> ApiResponse[None]: ...


async def send_request(
    config: RequestConfig[Method, Endpoint, Input],
    client_options: NutrientClientOptions,
) -> ApiResponse[Output]:
    """Sends HTTP request to Nutrient DWS Processor API.
    Handles authentication, file uploads, and error conversion.

    Args:
        config: Request configuration
        client_options: Client options

    Returns:
        API response

    Raises:
        NutrientError: For various error conditions
    """
    try:
        # Resolve API key (string or function)
        api_key = await resolve_api_key(client_options["apiKey"])

        # Build full URL
        base_url: str = client_options.get("baseUrl") or "https://api.nutrient.io"
        url = f"{base_url.rstrip('/')}{config['endpoint']}"

        headers = config.get("headers") or {}
        headers["Authorization"] = f"Bearer {api_key}"
        headers["User-Agent"] = get_user_agent()

        # Prepare request configuration
        request_config: dict[str, Any] = {
            "method": config["method"],
            "url": url,
            "headers": headers,
            "timeout": client_options.get("timeout", None),
        }

        # Prepare request body
        request_config = prepare_request_body(request_config, config)

        # Make request using httpx async client
        async with httpx.AsyncClient() as client:
            response = await client.request(**request_config)

        # Handle response
        return handle_response(response)
    except Exception as error:
        raise convert_error(error, config)
