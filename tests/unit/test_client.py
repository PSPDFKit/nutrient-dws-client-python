"""Unit tests for NutrientClient."""

import os

from nutrient_dws.client import NutrientClient


def test_client_init_with_api_key():
    """Test client initialization with API key."""
    client = NutrientClient(api_key="test-key")
    assert client is not None
    assert client._http_client._api_key == "test-key"


def test_client_init_with_env_var():
    """Test client initialization with environment variable."""
    # Save original value
    original = os.environ.get("NUTRIENT_API_KEY")

    try:
        os.environ["NUTRIENT_API_KEY"] = "env-key"
        client = NutrientClient()
        assert client._http_client._api_key == "env-key"
    finally:
        # Restore original value
        if original is not None:
            os.environ["NUTRIENT_API_KEY"] = original
        else:
            os.environ.pop("NUTRIENT_API_KEY", None)


def test_client_init_precedence():
    """Test that explicit API key takes precedence over env var."""
    # Save original value
    original = os.environ.get("NUTRIENT_API_KEY")

    try:
        os.environ["NUTRIENT_API_KEY"] = "env-key"
        client = NutrientClient(api_key="explicit-key")
        assert client._http_client._api_key == "explicit-key"
    finally:
        # Restore original value
        if original is not None:
            os.environ["NUTRIENT_API_KEY"] = original
        else:
            os.environ.pop("NUTRIENT_API_KEY", None)


def test_client_build_method():
    """Test that build() returns a BuildAPIWrapper."""
    client = NutrientClient(api_key="test-key")
    builder = client.build("test.pdf")

    # Check class name to avoid import issues
    assert builder.__class__.__name__ == "BuildAPIWrapper"


def test_client_has_direct_api_methods():
    """Test that client has direct API methods."""
    client = NutrientClient(api_key="test-key")

    # Check that direct API methods exist (from DirectAPIMixin)
    assert hasattr(client, "convert_to_pdf")
    assert hasattr(client, "flatten_annotations")
    assert hasattr(client, "rotate_pages")
    assert hasattr(client, "watermark_pdf")
    assert hasattr(client, "ocr_pdf")
    assert hasattr(client, "apply_redactions")
    assert hasattr(client, "merge_pdfs")
    assert hasattr(client, "split_pdf")
    assert hasattr(client, "duplicate_pdf_pages")
    assert hasattr(client, "delete_pdf_pages")
    assert hasattr(client, "add_page")
    assert hasattr(client, "set_page_label")


def test_client_context_manager():
    """Test client can be used as context manager."""
    with NutrientClient(api_key="test-key") as client:
        assert client is not None
        # Check that HTTP client is not closed
        assert hasattr(client._http_client, "_session")

    # After exiting context, HTTP client session should be closed
    # We can't directly check if closed, but the method should have been called


def test_client_close():
    """Test client close method."""
    client = NutrientClient(api_key="test-key")

    # Verify HTTP client exists
    assert hasattr(client, "_http_client")

    # Close should not raise an error
    client.close()


def test_set_page_label_validation():
    """Test set_page_label method validation logic."""
    from unittest.mock import Mock, patch

    import pytest

    client = NutrientClient(api_key="test-key")
    client._http_client = Mock()  # Mock the HTTP client to avoid actual API calls

    with (
        patch("nutrient_dws.file_handler.get_pdf_page_count") as mock_pdf_page_count,
    ):
        mock_pdf_page_count.return_value = 10

        # Test empty labels list
        with pytest.raises(ValueError, match="labels list cannot be empty"):
            client.set_page_label("test.pdf", [])

        # Test invalid label config (not a dict)
        with pytest.raises(ValueError, match="Label configuration 0 must be a dictionary"):
            client.set_page_label("test.pdf", ["invalid"])  # type: ignore[list-item]

        # Test missing 'pages' key
        with pytest.raises(ValueError, match="Label configuration 0 missing required 'pages' key"):
            client.set_page_label("test.pdf", [{"label": "Test"}])

        # Test missing 'label' key
        with pytest.raises(ValueError, match="Label configuration 0 missing required 'label' key"):
            client.set_page_label("test.pdf", [{"pages": {"start": 0}}])

        # Test invalid pages config (not a dict)
        with pytest.raises(
            ValueError, match="Label configuration 0 'pages' must be a dict with 'start' key"
        ):
            client.set_page_label("test.pdf", [{"pages": "invalid", "label": "Test"}])

        # Test missing 'start' key in pages
        with pytest.raises(
            ValueError, match="Label configuration 0 'pages' must be a dict with 'start' key"
        ):
            client.set_page_label("test.pdf", [{"pages": {"end": 5}, "label": "Test"}])


def test_set_page_label_valid_config():
    """Test set_page_label with valid configuration."""
    from unittest.mock import Mock, patch

    client = NutrientClient(api_key="test-key")

    # Mock HTTP client and file handler functions
    mock_http_client = Mock()
    mock_http_client.post.return_value = b"mock_pdf_bytes"
    client._http_client = mock_http_client

    with (
        patch("nutrient_dws.file_handler.prepare_file_for_upload") as mock_prepare,
        patch("nutrient_dws.file_handler.save_file_output") as mock_save,
        patch("nutrient_dws.file_handler.get_pdf_page_count") as mock_pdf_page_count,
    ):
        mock_prepare.return_value = ("file", ("filename.pdf", b"mock_file_data", "application/pdf"))
        mock_pdf_page_count.return_value = 10

        # Test valid configuration
        labels = [
            {"pages": {"start": 0, "end": 2}, "label": "Introduction"},
            {"pages": {"start": 3}, "label": "Content"},
        ]

        result = client.set_page_label("test.pdf", labels)

        # Expected normalized labels (implementation only includes 'end' if explicitly provided)
        expected_normalized_labels = [
            {"pages": {"start": 0, "end": 2}, "label": "Introduction"},
            {"pages": {"start": 3}, "label": "Content"},  # No 'end' means to end of document
        ]

        # Verify the API call was made with correct parameters
        mock_http_client.post.assert_called_once_with(
            "/build",
            files={"file": ("filename.pdf", b"mock_file_data", "application/pdf")},
            json_data={
                "parts": [{"file": "file"}],
                "actions": [],
                "output": {"labels": expected_normalized_labels},
            },
        )

        # Verify result
        assert result == b"mock_pdf_bytes"

        # Verify save_file_output was not called (no output_path)
        mock_save.assert_not_called()


def test_set_page_label_with_output_path():
    """Test set_page_label with output path."""
    from unittest.mock import Mock, patch

    client = NutrientClient(api_key="test-key")

    # Mock HTTP client and file handler functions
    mock_http_client = Mock()
    mock_http_client.post.return_value = b"mock_pdf_bytes"
    client._http_client = mock_http_client

    with (
        patch("nutrient_dws.file_handler.prepare_file_for_upload") as mock_prepare,
        patch("nutrient_dws.file_handler.save_file_output") as mock_save,
        patch("nutrient_dws.file_handler.get_pdf_page_count") as mock_pdf_page_count,
    ):
        mock_prepare.return_value = ("file", ("filename.pdf", b"mock_file_data", "application/pdf"))
        mock_pdf_page_count.return_value = 10

        labels = [{"pages": {"start": 0, "end": 0}, "label": "Cover"}]

        result = client.set_page_label("test.pdf", labels, output_path="/path/to/output.pdf")

        # Verify the API call was made
        mock_http_client.post.assert_called_once()

        # Verify save_file_output was called with correct parameters
        mock_save.assert_called_once_with(b"mock_pdf_bytes", "/path/to/output.pdf")

        # Verify result is None when output_path is provided
        assert result is None
