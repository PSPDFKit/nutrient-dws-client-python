"""Integration tests against the live Nutrient DWS API.

These tests require a valid API key configured in integration_config.py.
"""

from __future__ import annotations

import pytest

from nutrient_dws import NutrientClient
from nutrient_dws.file_handler import get_pdf_page_count

try:
    from . import integration_config  # type: ignore[attr-defined]

    API_KEY: str | None = integration_config.API_KEY
    BASE_URL: str | None = getattr(integration_config, "BASE_URL", None)
    TIMEOUT: int = getattr(integration_config, "TIMEOUT", 60)
except ImportError:
    API_KEY = None
    BASE_URL = None
    TIMEOUT = 60


def assert_is_pdf(file_path_or_bytes: str | bytes) -> None:
    """Assert that a file or bytes is a valid PDF.

    Args:
        file_path_or_bytes: Path to file or bytes content to check.
    """
    if isinstance(file_path_or_bytes, (str, bytes)):
        if isinstance(file_path_or_bytes, str):
            with open(file_path_or_bytes, "rb") as f:
                content = f.read(8)
        else:
            content = file_path_or_bytes[:8]

        # Check PDF magic number
        assert content.startswith(b"%PDF-"), (
            f"File does not start with PDF magic number, got: {content!r}"
        )
    else:
        raise ValueError("Input must be file path string or bytes")


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestLiveAPI:
    """Integration tests against live API."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        client = NutrientClient(api_key=API_KEY, timeout=TIMEOUT)
        yield client
        client.close()

    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF file for testing."""
        import os

        return os.path.join(os.path.dirname(__file__), "..", "data", "sample.pdf")

    def test_client_initialization(self):
        """Test that client initializes correctly with API key."""
        client = NutrientClient(api_key=API_KEY)
        assert client._api_key == API_KEY
        client.close()

    def test_client_missing_api_key(self):
        """Test that client works without API key but fails on API calls."""
        client = NutrientClient()
        # Should not raise during initialization
        assert client is not None
        client.close()

    def test_basic_api_connectivity(self, client, sample_pdf_path):
        """Test basic API connectivity with a simple operation."""
        # This test will depend on what operations are available
        # For now, we'll test that we can create a builder without errors
        builder = client.build(input_file=sample_pdf_path)
        assert builder is not None

    @pytest.mark.skip(reason="Requires specific tool implementation")
    def test_convert_operation(self, client, sample_pdf_path, tmp_path):
        """Test a basic convert operation (example - adjust based on available tools)."""
        # This is an example - adjust based on actual available tools
        # output_path = tmp_path / "output.pdf"
        # result = client.convert_to_pdf(input_file=sample_pdf_path, output_path=str(output_path))

        # assert output_path.exists()
        # assert output_path.stat().st_size > 0

    def test_builder_api_basic(self, client, sample_pdf_path):
        """Test basic builder API functionality."""
        builder = client.build(input_file=sample_pdf_path)

        # Test that we can add steps without errors
        # This will need to be updated based on actual available tools
        # builder.add_step("example-tool", {})

        assert builder is not None

    def test_split_pdf_integration(self, client, sample_pdf_path, tmp_path):
        """Test split_pdf method with live API."""
        # Test splitting PDF into two parts - sample PDF should have multiple pages
        page_ranges = [
            {"start": 0, "end": 0},  # First page
            {"start": 1},  # Remaining pages
        ]

        # Test getting bytes back
        result = client.split_pdf(sample_pdf_path, page_ranges=page_ranges)

        assert isinstance(result, list)
        assert len(result) == 2  # Should return exactly 2 parts since sample has multiple pages
        assert all(isinstance(pdf_bytes, bytes) for pdf_bytes in result)
        assert all(len(pdf_bytes) > 0 for pdf_bytes in result)

        # Verify both results are valid PDFs
        for pdf_bytes in result:
            assert_is_pdf(pdf_bytes)

        # Verify the number of pages in each output PDF
        assert get_pdf_page_count(result[0]) == 1  # First PDF should have 1 page
        # The second PDF should have the remaining pages (total pages - 1)
        total_pages = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result[1]) == total_pages - 1

    def test_split_pdf_with_output_files(self, client, sample_pdf_path, tmp_path):
        """Test split_pdf method saving to output files."""
        output_paths = [str(tmp_path / "page1.pdf"), str(tmp_path / "remaining.pdf")]

        page_ranges = [
            {"start": 0, "end": 0},  # First page
            {"start": 1},  # Remaining pages
        ]

        # Test saving to files
        result = client.split_pdf(
            sample_pdf_path, page_ranges=page_ranges, output_paths=output_paths
        )

        # Should return empty list when saving to files
        assert result == []

        # Check that output files were created
        assert (tmp_path / "page1.pdf").exists()
        assert (tmp_path / "page1.pdf").stat().st_size > 0
        assert_is_pdf(str(tmp_path / "page1.pdf"))

        # Verify the number of pages in the first output PDF
        assert get_pdf_page_count(str(tmp_path / "page1.pdf")) == 1  # First PDF should have 1 page

        # Second file should exist since sample PDF has multiple pages
        assert (tmp_path / "remaining.pdf").exists()
        assert (tmp_path / "remaining.pdf").stat().st_size > 0
        assert_is_pdf(str(tmp_path / "remaining.pdf"))

        # Verify the number of pages in the second output PDF
        # The second PDF should have the remaining pages (total pages - 1)
        total_pages = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(str(tmp_path / "remaining.pdf")) == total_pages - 1

    def test_split_pdf_single_page_default(self, client, sample_pdf_path):
        """Test split_pdf with default behavior (single page)."""
        # Test default splitting (should extract first page)
        result = client.split_pdf(sample_pdf_path)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], bytes)
        assert len(result[0]) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result[0])

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result[0]) == 1  # Should contain only the first page

    def test_set_page_label_integration(self, client, sample_pdf_path, tmp_path):
        """Test set_page_label method with live API."""
        labels = [{"pages": {"start": 0, "end": 0}, "label": "Cover"}]

        output_path = str(tmp_path / "labeled.pdf")

        # Try to set page labels
        result = client.set_page_label(sample_pdf_path, labels, output_path=output_path)

        # If successful, verify output
        assert result is None  # Should return None when output_path provided
        assert (tmp_path / "labeled.pdf").exists()
        assert_is_pdf(output_path)

    def test_set_page_label_return_bytes(self, client, sample_pdf_path):
        """Test set_page_label method returning bytes."""
        labels = [{"pages": {"start": 0, "end": 0}, "label": "i"}]

        # Test getting bytes back
        result = client.set_page_label(sample_pdf_path, labels)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_set_page_label_multiple_ranges(self, client, sample_pdf_path):
        """Test set_page_label method with multiple page ranges."""
        labels = [
            {"pages": {"start": 0, "end": 0}, "label": "i"},
            {"pages": {"start": 1, "end": 1}, "label": "intro"},
            {"pages": {"start": 2, "end": 2}, "label": "final"},
        ]

        result = client.set_page_label(sample_pdf_path, labels)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_set_page_label_single_page(self, client, sample_pdf_path):
        """Test set_page_label method with single page label."""
        labels = [{"pages": {"start": 0, "end": 0}, "label": "Cover Page"}]

        result = client.set_page_label(sample_pdf_path, labels)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_set_page_label_empty_labels_error(self, client, sample_pdf_path):
        """Test set_page_label method with empty labels raises error."""
        with pytest.raises(ValueError, match="labels list cannot be empty"):
            client.set_page_label(sample_pdf_path, labels=[])

    def test_set_page_label_invalid_label_config_error(self, client, sample_pdf_path):
        """Test set_page_label method with invalid label configuration raises error."""
        # Missing 'pages' key
        with pytest.raises(ValueError, match="missing required 'pages' key"):
            client.set_page_label(sample_pdf_path, labels=[{"label": "test"}])

        # Missing 'label' key
        with pytest.raises(ValueError, match="missing required 'label' key"):
            client.set_page_label(sample_pdf_path, labels=[{"pages": {"start": 0}}])

        # Invalid pages format
        with pytest.raises(ValueError, match="'pages' must be a dict with 'start' key"):
            client.set_page_label(sample_pdf_path, labels=[{"pages": "invalid", "label": "test"}])

    def test_duplicate_pdf_pages_basic(self, client, sample_pdf_path):
        """Test duplicate_pdf_pages method with basic duplication."""
        # Test duplicating first page twice
        result = client.duplicate_pdf_pages(sample_pdf_path, page_indexes=[0, 0])

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result) == 2  # Should have 2 pages (duplicated the first page)

    def test_duplicate_pdf_pages_reorder(self, client, sample_pdf_path):
        """Test duplicate_pdf_pages method with page reordering."""
        # Test reordering pages (assumes sample PDF has at least 2 pages)
        result = client.duplicate_pdf_pages(sample_pdf_path, page_indexes=[1, 0])

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result) == 2  # Should have 2 pages (page 2 and page 1)

    def test_duplicate_pdf_pages_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test duplicate_pdf_pages method saving to output file."""
        output_path = str(tmp_path / "duplicated.pdf")

        # Test duplicating and saving to file
        result = client.duplicate_pdf_pages(
            sample_pdf_path, page_indexes=[0, 0, 1], output_path=output_path
        )

        # Should return None when saving to file
        assert result is None

        # Check that output file was created
        assert (tmp_path / "duplicated.pdf").exists()
        assert (tmp_path / "duplicated.pdf").stat().st_size > 0
        assert_is_pdf(output_path)

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(output_path) == 3  # Should have 3 pages (page 1, page 1, page 2)

    def test_duplicate_pdf_pages_negative_indexes(self, client, sample_pdf_path):
        """Test duplicate_pdf_pages method with negative indexes."""
        # Test using negative indexes (last page)
        result = client.duplicate_pdf_pages(sample_pdf_path, page_indexes=[-1, 0, -1])

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result) == 3  # Should have 3 pages (last page, first page, last page)

    def test_duplicate_pdf_pages_empty_indexes_error(self, client, sample_pdf_path):
        """Test duplicate_pdf_pages method with empty page_indexes raises error."""
        with pytest.raises(ValueError, match="page_indexes cannot be empty"):
            client.duplicate_pdf_pages(sample_pdf_path, page_indexes=[])

    def test_delete_pdf_pages_basic(self, client, sample_pdf_path):
        """Test delete_pdf_pages method with basic page deletion."""
        # Test deleting first page (assuming sample PDF has at least 2 pages)
        result = client.delete_pdf_pages(sample_pdf_path, page_indexes=[0])

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        total_pages = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_pages - 1  # Should have one less page than original

    def test_delete_pdf_pages_multiple(self, client, sample_pdf_path):
        """Test delete_pdf_pages method with multiple page deletion."""
        # Test deleting multiple pages
        result = client.delete_pdf_pages(sample_pdf_path, page_indexes=[0, 2])

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        total_pages = get_pdf_page_count(sample_pdf_path)
        # Should have two less pages than original (deleted pages 1 and 3)
        assert get_pdf_page_count(result) == total_pages - 2

    def test_delete_pdf_pages_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test delete_pdf_pages method saving to output file."""
        output_path = str(tmp_path / "pages_deleted.pdf")

        # Test deleting pages and saving to file
        result = client.delete_pdf_pages(sample_pdf_path, page_indexes=[1], output_path=output_path)

        # Should return None when saving to file
        assert result is None

        # Check that output file was created
        assert (tmp_path / "pages_deleted.pdf").exists()
        assert (tmp_path / "pages_deleted.pdf").stat().st_size > 0
        assert_is_pdf(output_path)

        # Verify the number of pages in the output PDF
        total_pages = get_pdf_page_count(sample_pdf_path)
        # Should have one less page than original (deleted page 2)
        assert get_pdf_page_count(output_path) == total_pages - 1

    def test_delete_pdf_pages_negative_indexes_error(self, client, sample_pdf_path):
        """Test delete_pdf_pages method with negative indexes raises error."""
        # Currently negative indexes are not supported for deletion
        with pytest.raises(ValueError, match="Negative page indexes not yet supported"):
            client.delete_pdf_pages(sample_pdf_path, page_indexes=[-1])

    def test_delete_pdf_pages_empty_indexes_error(self, client, sample_pdf_path):
        """Test delete_pdf_pages method with empty page_indexes raises error."""
        with pytest.raises(ValueError, match="page_indexes cannot be empty"):
            client.delete_pdf_pages(sample_pdf_path, page_indexes=[])

    def test_delete_pdf_pages_duplicate_indexes(self, client, sample_pdf_path):
        """Test delete_pdf_pages method with duplicate page indexes."""
        # Test that duplicate indexes are handled correctly (should remove duplicates)
        result = client.delete_pdf_pages(sample_pdf_path, page_indexes=[0, 0, 1])

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        total_pages = get_pdf_page_count(sample_pdf_path)
        # Should have two less pages than original (deleted pages 1 and 2)
        assert get_pdf_page_count(result) == total_pages - 2

    @pytest.fixture
    def sample_docx_path(self):
        """Get path to sample DOCX file for testing."""
        import os

        return os.path.join(os.path.dirname(__file__), "..", "data", "sample.docx")

    def test_convert_to_pdf_from_docx(self, client, sample_docx_path):
        """Test convert_to_pdf method with DOCX input."""
        # Test converting DOCX to PDF and getting bytes back
        result = client.convert_to_pdf(sample_docx_path)

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

    def test_convert_to_pdf_with_output_file(self, client, sample_docx_path, tmp_path):
        """Test convert_to_pdf method saving to output file."""
        output_path = str(tmp_path / "converted.pdf")

        # Test converting and saving to file
        result = client.convert_to_pdf(sample_docx_path, output_path=output_path)

        # Should return None when saving to file
        assert result is None

        # Check that output file was created
        assert (tmp_path / "converted.pdf").exists()
        assert (tmp_path / "converted.pdf").stat().st_size > 0
        assert_is_pdf(output_path)

    def test_convert_to_pdf_from_pdf_passthrough(self, client, sample_pdf_path):
        """Test convert_to_pdf method with PDF input (should pass through)."""
        # Test that PDF input passes through unchanged
        result = client.convert_to_pdf(sample_pdf_path)

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)

    def test_add_page_at_beginning(self, client, sample_pdf_path):
        """Test add_page method inserting at the beginning."""
        # Test inserting at beginning (insert_index=0)
        result = client.add_page(sample_pdf_path, insert_index=0)

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 1

    def test_add_page_multiple_pages(self, client, sample_pdf_path):
        """Test add_page method with multiple pages."""
        # Test adding multiple blank pages before second page
        result = client.add_page(sample_pdf_path, insert_index=1, page_count=3)

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 3

    def test_add_page_at_end(self, client, sample_pdf_path):
        """Test add_page method inserting at the end."""
        # Test inserting at end using -1
        result = client.add_page(sample_pdf_path, insert_index=-1, page_count=2)

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 2

    def test_add_page_before_specific_page(self, client, sample_pdf_path):
        """Test add_page method inserting before a specific page."""
        # Test inserting before page 3 (insert_index=2)
        result = client.add_page(sample_pdf_path, insert_index=2, page_count=1)

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 1

    def test_add_page_custom_size_orientation(self, client, sample_pdf_path):
        """Test add_page method with custom page size and orientation."""
        # Test adding Letter-sized landscape pages at beginning
        result = client.add_page(
            sample_pdf_path,
            insert_index=0,
            page_size="Letter",
            orientation="landscape",
            page_count=2,
        )

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify result is a valid PDF
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 2

    def test_add_page_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test add_page method saving to output file."""
        output_path = str(tmp_path / "with_blank_pages.pdf")

        # Test adding pages and saving to file
        result = client.add_page(
            sample_pdf_path, insert_index=1, page_count=2, output_path=output_path
        )

        # Should return None when saving to file
        assert result is None

        # Check that output file was created
        assert (tmp_path / "with_blank_pages.pdf").exists()
        assert (tmp_path / "with_blank_pages.pdf").stat().st_size > 0
        assert_is_pdf(output_path)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(output_path) == total_page_count + 2

    def test_add_page_different_page_sizes(self, client, sample_pdf_path):
        """Test add_page method with different page sizes."""
        # Test various page sizes
        page_sizes = ["A4", "Letter", "Legal", "A3", "A5"]

        for page_size in page_sizes:
            result = client.add_page(sample_pdf_path, insert_index=0, page_size=page_size)

            assert isinstance(result, bytes)
            assert len(result) > 0
            assert_is_pdf(result)
            # Verify the number of pages in the output PDF
            total_page_count = get_pdf_page_count(sample_pdf_path)
            assert get_pdf_page_count(result) == total_page_count + 1

    def test_add_page_invalid_page_count_error(self, client, sample_pdf_path):
        """Test add_page method with invalid page_count raises error."""
        # Test zero page count
        with pytest.raises(ValueError, match="page_count must be at least 1"):
            client.add_page(sample_pdf_path, insert_index=0, page_count=0)

        # Test negative page count
        with pytest.raises(ValueError, match="page_count must be at least 1"):
            client.add_page(sample_pdf_path, insert_index=0, page_count=-1)

    def test_add_page_invalid_position_error(self, client, sample_pdf_path):
        """Test add_page method with invalid insert_index raises error."""
        # Test invalid negative position (anything below -1)
        with pytest.raises(ValueError, match="insert_index must be -1"):
            client.add_page(sample_pdf_path, insert_index=-2, page_count=1)

        with pytest.raises(ValueError, match="insert_index must be -1"):
            client.add_page(sample_pdf_path, insert_index=-5, page_count=1)
