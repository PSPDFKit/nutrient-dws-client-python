"""Nutrient DWS Python Client.

A Python client library for the Nutrient Document Web Services API.
"""

from nutrient_dws.client import NutrientClient
from nutrient_dws.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    NutrientError,
    ValidationError,
)
from nutrient_dws.inputs import (
    is_remote_file_input,
    process_file_input,
    process_remote_file_input,
    validate_file_input,
)
from nutrient_dws.utils import get_library_version, get_user_agent

__all__ = [
    "APIError",
    "AuthenticationError",
    "NetworkError",
    "NutrientClient",
    "NutrientError",
    "ValidationError",
    "get_library_version",
    "get_user_agent",
    "is_remote_file_input",
    "process_file_input",
    "process_remote_file_input",
    "validate_file_input",
]
