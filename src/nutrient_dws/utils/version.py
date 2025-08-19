import os
from importlib.metadata import version as pkg_version


def get_library_version() -> str:
    """Gets the current version of the Nutrient DWS Python Client library.

    Strategy: Try importlib.metadata.version("nutrient-dws"); on any failure, return "0.0.0-dev".
    """
    if os.getenv("PYTHON_ENV") == "development":
        return "0.0.0-dev"
    try:
        return pkg_version("nutrient-dws")
    except Exception:
        return "0.0.0-dev"


def get_user_agent() -> str:
    """Creates a User-Agent string for HTTP requests."""
    package_version = get_library_version()
    return f"nutrient-dws/{package_version}"
