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

__version__ = "1.0.2"
__all__ = [
    "APIError",
    "AuthenticationError",
    "NetworkError",
    "NutrientClient",
    "NutrientError",
    "ValidationError",
]
