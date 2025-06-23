"""Nutrient DWS Python Client.

A Python client library for the Nutrient Document Web Services API.
"""

from nutrient_dws.client import NutrientClient
from nutrient_dws.exceptions import (
    APIError,
    AuthenticationError,
    FileProcessingError,
    NutrientError,
    NutrientTimeoutError,
    ValidationError,
)

__version__ = "1.0.2"
__all__ = [
    "APIError",
    "AuthenticationError",
    "FileProcessingError",
    "NutrientClient",
    "NutrientError",
    "NutrientTimeoutError",
    "ValidationError",
]
