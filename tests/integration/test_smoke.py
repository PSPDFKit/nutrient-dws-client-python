"""Basic smoke test to validate integration test setup."""

import pytest

from nutrient_dws import NutrientClient

# Type annotation for mypy
API_KEY: str | None = None

try:
    from . import integration_config  # type: ignore[attr-defined]

    API_KEY = integration_config.API_KEY
except (ImportError, AttributeError):
    API_KEY = None


@pytest.mark.skipif(not API_KEY, reason="No API key available")
def test_api_connection():
    """Test that we can connect to the API."""
    client = NutrientClient(api_key=API_KEY)
    # Just verify client initialization works
    assert client._api_key == API_KEY
    assert hasattr(client, "convert_to_pdf")
    assert hasattr(client, "build")
