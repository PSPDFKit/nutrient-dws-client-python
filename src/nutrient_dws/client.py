"""Main client module for Nutrient DWS API."""

import os
from typing import Any

from nutrient_dws.api.direct import DirectAPIMixin
from nutrient_dws.builder import BuildAPIWrapper
from nutrient_dws.file_handler import FileInput
from nutrient_dws.http_client import HTTPClient


class NutrientClient(DirectAPIMixin):
    r"""Main client for interacting with Nutrient DWS API.

    This client provides two ways to interact with the API:

    1. Direct API: Individual method calls for single operations
       Example: client.convert_to_pdf(input_file="document.docx")

    2. Builder API: Fluent interface for chaining multiple operations
       Example: client.build(input_file="doc.docx").add_step("convert-to-pdf").execute()

    Args:
        api_key: API key for authentication. If not provided, will look for
            NUTRIENT_API_KEY environment variable.
        timeout: Request timeout in seconds. Defaults to 300.

    Raises:
        AuthenticationError: When making API calls without a valid API key.

    Example:
        >>> from nutrient_dws import NutrientClient
        >>> client = NutrientClient(api_key="your-api-key")
        >>> # Direct API
        >>> pdf = client.convert_to_pdf(input_file="document.docx")
        >>> # Builder API
        >>> client.build(input_file="document.docx") \\
        ...       .add_step(tool="convert-to-pdf") \\
        ...       .add_step(tool="ocr-pdf") \\
        ...       .execute(output_path="output.pdf")
    """

    def __init__(self, api_key: str | None = None, timeout: int = 300) -> None:
        """Initialize the Nutrient client."""
        # Get API key from parameter or environment
        self._api_key = api_key or os.environ.get("NUTRIENT_API_KEY")
        self._timeout = timeout

        # Initialize HTTP client
        self._http_client = HTTPClient(api_key=self._api_key, timeout=timeout)

        # Direct API methods will be added dynamically

    def build(self, input_file: FileInput) -> BuildAPIWrapper:
        """Start a Builder API workflow.

        Args:
            input_file: Input file (path, bytes, or file-like object).

        Returns:
            BuildAPIWrapper instance for chaining operations.

        Example:
            >>> builder = client.build(input_file="document.pdf")
            >>> builder.add_step(tool="rotate-pages", options={"degrees": 90})
            >>> result = builder.execute()
        """
        return BuildAPIWrapper(client=self, input_file=input_file)

    def _process_file(
        self,
        tool: str,
        input_file: FileInput,
        output_path: str | None = None,
        **options: Any,
    ) -> bytes | None:
        """Process a file using the Direct API.

        This is the internal method used by all Direct API methods.
        It internally uses the Build API with a single action.

        Args:
            tool: The tool identifier from the API.
            input_file: Input file to process.
            output_path: Optional path to save the output.
            **options: Tool-specific options.

        Returns:
            Processed file as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
        """
        # Use the builder API with a single step
        builder = self.build(input_file)
        builder.add_step(tool, options)
        return builder.execute(output_path)

    def close(self) -> None:
        """Close the HTTP client session."""
        self._http_client.close()

    def __enter__(self) -> "NutrientClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
