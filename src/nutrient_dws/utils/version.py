from importlib.metadata import PackageNotFoundError, version


def get_library_version() -> str:
    """Gets the current version of the Nutrient DWS Python Client library."""
    try:
        return version("nutrient-dws")
    except PackageNotFoundError:
        # fallback for when running from source (not installed yet)
        from importlib.metadata import metadata

        return metadata("nutrient-dws")["Version"]


def get_user_agent() -> str:
    """Creates a User-Agent string for HTTP requests."""
    return f"nutrient-dws/{get_library_version()}"
