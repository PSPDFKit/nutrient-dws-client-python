"""Comprehensive integration tests for Direct API methods.

These tests require a valid API key configured in integration_config.py and
test all Direct API methods against the live Nutrient DWS API.
"""

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
class TestDirectAPIIntegration:
    """Comprehensive integration tests for all Direct API methods."""

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

    @pytest.fixture
    def sample_docx_path(self):
        """Get path to sample DOCX file for testing."""
        import os

        return os.path.join(os.path.dirname(__file__), "..", "data", "sample.docx")

    @pytest.fixture
    def sample_multipage_pdf_path(self):
        """Get path to multi-page sample PDF file for testing."""
        import os

        return os.path.join(os.path.dirname(__file__), "..", "data", "sample_multipage.pdf")

    # Tests for convert_to_pdf
    def test_convert_to_pdf_from_docx(self, client, sample_docx_path):
        """Test convert_to_pdf method with DOCX input."""
        result = client.convert_to_pdf(sample_docx_path)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_convert_to_pdf_with_output_file(self, client, sample_docx_path, tmp_path):
        """Test convert_to_pdf method saving to output file."""
        output_path = str(tmp_path / "converted.pdf")

        result = client.convert_to_pdf(sample_docx_path, output_path=output_path)

        assert result is None
        assert (tmp_path / "converted.pdf").exists()
        assert (tmp_path / "converted.pdf").stat().st_size > 0
        assert_is_pdf(output_path)

    def test_convert_to_pdf_from_pdf_passthrough(self, client, sample_pdf_path):
        """Test convert_to_pdf method with PDF input (should pass through)."""
        result = client.convert_to_pdf(sample_pdf_path)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    # Tests for flatten_annotations
    def test_flatten_annotations_integration(self, client, sample_pdf_path):
        """Test flatten_annotations method with live API."""
        result = client.flatten_annotations(sample_pdf_path)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_flatten_annotations_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test flatten_annotations method saving to output file."""
        output_path = str(tmp_path / "flattened.pdf")

        result = client.flatten_annotations(sample_pdf_path, output_path=output_path)

        assert result is None
        assert (tmp_path / "flattened.pdf").exists()
        assert_is_pdf(output_path)

    # Tests for rotate_pages
    def test_rotate_pages_integration(self, client, sample_pdf_path):
        """Test rotate_pages method with live API."""
        result = client.rotate_pages(sample_pdf_path, degrees=90)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_rotate_pages_specific_pages(self, client, sample_pdf_path):
        """Test rotate_pages method with specific page indexes."""
        result = client.rotate_pages(sample_pdf_path, degrees=180, page_indexes=[0])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_rotate_pages_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test rotate_pages method saving to output file."""
        output_path = str(tmp_path / "rotated.pdf")

        result = client.rotate_pages(sample_pdf_path, degrees=270, output_path=output_path)

        assert result is None
        assert (tmp_path / "rotated.pdf").exists()
        assert_is_pdf(output_path)

    # Tests for ocr_pdf
    def test_ocr_pdf_integration(self, client, sample_pdf_path):
        """Test ocr_pdf method with live API."""
        result = client.ocr_pdf(sample_pdf_path, language="english")

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_ocr_pdf_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test ocr_pdf method saving to output file."""
        output_path = str(tmp_path / "ocr.pdf")

        result = client.ocr_pdf(sample_pdf_path, language="english", output_path=output_path)

        assert result is None
        assert (tmp_path / "ocr.pdf").exists()
        assert_is_pdf(output_path)

    # Tests for watermark_pdf
    def test_watermark_pdf_text_integration(self, client, sample_pdf_path):
        """Test watermark_pdf method with text watermark."""
        result = client.watermark_pdf(
            sample_pdf_path, text="DRAFT", width=200, height=100, opacity=0.5
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_watermark_pdf_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test watermark_pdf method saving to output file."""
        output_path = str(tmp_path / "watermarked.pdf")

        result = client.watermark_pdf(
            sample_pdf_path,
            text="CONFIDENTIAL",
            width=150,
            height=75,
            position="top-right",
            output_path=output_path,
        )

        assert result is None
        assert (tmp_path / "watermarked.pdf").exists()
        assert_is_pdf(output_path)

    # Tests for apply_redactions
    def test_apply_redactions_integration(self, client, sample_pdf_path):
        """Test apply_redactions method with live API."""
        result = client.apply_redactions(sample_pdf_path)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_apply_redactions_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test apply_redactions method saving to output file."""
        output_path = str(tmp_path / "redacted.pdf")

        result = client.apply_redactions(sample_pdf_path, output_path=output_path)

        assert result is None
        assert (tmp_path / "redacted.pdf").exists()
        assert_is_pdf(output_path)

    # Tests for merge_pdfs
    def test_merge_pdfs_integration(self, client, sample_pdf_path, tmp_path):
        """Test merge_pdfs method with live API."""
        # Create a second PDF by copying the sample
        second_pdf_path = str(tmp_path / "second.pdf")
        import shutil

        shutil.copy2(sample_pdf_path, second_pdf_path)

        result = client.merge_pdfs([sample_pdf_path, second_pdf_path])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_merge_pdfs_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test merge_pdfs method saving to output file."""
        # Create a second PDF by copying the sample
        second_pdf_path = str(tmp_path / "second.pdf")
        output_path = str(tmp_path / "merged.pdf")
        import shutil

        shutil.copy2(sample_pdf_path, second_pdf_path)

        result = client.merge_pdfs([sample_pdf_path, second_pdf_path], output_path=output_path)

        assert result is None
        assert (tmp_path / "merged.pdf").exists()
        assert_is_pdf(output_path)

    def test_merge_pdfs_error_single_file(self, client, sample_pdf_path):
        """Test merge_pdfs method with single file raises error."""
        with pytest.raises(ValueError, match="At least 2 files required"):
            client.merge_pdfs([sample_pdf_path])

    # Tests for split_pdf
    def test_split_pdf_integration(self, client, sample_multipage_pdf_path, tmp_path):
        """Test split_pdf method with live API."""
        # Test splitting PDF into two parts - multi-page PDF has 3 pages
        page_ranges = [
            {"start": 0, "end": 0},  # First page
            {"start": 1},  # Remaining pages
        ]

        # Test getting bytes back
        result = client.split_pdf(sample_multipage_pdf_path, page_ranges=page_ranges)

        assert isinstance(result, list)
        assert len(result) == 2  # Should return exactly 2 parts
        assert all(isinstance(pdf_bytes, bytes) for pdf_bytes in result)
        assert all(len(pdf_bytes) > 0 for pdf_bytes in result)

        # Verify both results are valid PDFs
        for pdf_bytes in result:
            assert_is_pdf(pdf_bytes)

        # Verify the number of pages in each output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
        assert get_pdf_page_count(result[0]) == 1  # First PDF should have 1 page
        assert get_pdf_page_count(result[1]) == total_page_count - 1  # Second PDF should have the remaining pages

    def test_split_pdf_with_output_files(self, client, sample_multipage_pdf_path, tmp_path):
        """Test split_pdf method saving to output files."""
        output_paths = [str(tmp_path / "page1.pdf"), str(tmp_path / "remaining.pdf")]

        page_ranges = [
            {"start": 0, "end": 0},  # First page
            {"start": 1},  # Remaining pages
        ]

        # Test saving to files
        result = client.split_pdf(
            sample_multipage_pdf_path, page_ranges=page_ranges, output_paths=output_paths
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
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
        assert get_pdf_page_count(str(tmp_path / "remaining.pdf")) == total_page_count - 1 # Second PDF should have remaining pages

    def test_split_pdf_no_ranges_error(self, client, sample_pdf_path):
        """Test split_pdf with no ranges returns first page by default."""
        # When no page_ranges provided, should default to first page
        result = client.split_pdf(sample_pdf_path)

        assert isinstance(result, list)
        assert len(result) == 1  # Should return single PDF (first page)
        assert isinstance(result[0], bytes)
        assert len(result[0]) > 0
        assert_is_pdf(result[0])

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result[0]) == 1  # Should contain only the first page

    def test_split_pdf_output_paths_length_mismatch_error(self, client, sample_pdf_path):
        """Test split_pdf method with mismatched output_paths and page_ranges lengths."""
        page_ranges = [{"start": 0, "end": 1}, {"start": 1}]
        output_paths = ["page1.pdf"]  # Only one path for two ranges

        with pytest.raises(ValueError, match="output_paths length must match page_ranges length"):
            client.split_pdf(sample_pdf_path, page_ranges=page_ranges, output_paths=output_paths)

    def test_split_pdf_too_many_ranges_error(self, client, sample_pdf_path):
        """Test split_pdf method with too many ranges raises error."""
        # Create 51 ranges (exceeds the 50 limit)
        page_ranges = [{"start": i, "end": i + 1} for i in range(51)]

        with pytest.raises(ValueError, match="Maximum 50 page ranges allowed"):
            client.split_pdf(sample_pdf_path, page_ranges=page_ranges)

    # Tests for duplicate_pdf_pages
    def test_duplicate_pdf_pages_basic(self, client, sample_pdf_path):
        """Test duplicate_pdf_pages method with basic duplication."""
        # Test duplicating first page twice (works with single-page PDF)
        result = client.duplicate_pdf_pages(sample_pdf_path, page_indexes=[0, 0])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result) == 2  # Should have 2 pages (duplicated the first page)

    def test_duplicate_pdf_pages_reorder(self, client, sample_multipage_pdf_path):
        """Test duplicate_pdf_pages method with page reordering."""
        # Test reordering pages (multi-page PDF has 3 pages)
        result = client.duplicate_pdf_pages(sample_multipage_pdf_path, page_indexes=[1, 0])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result) == 2  # Should have 2 pages (page 2 and page 1)

    def test_duplicate_pdf_pages_with_output_file(
        self, client, sample_multipage_pdf_path, tmp_path
    ):
        """Test duplicate_pdf_pages method saving to output file."""
        output_path = str(tmp_path / "duplicated.pdf")

        # Test duplicating and saving to file (multi-page PDF has 3 pages)
        result = client.duplicate_pdf_pages(
            sample_multipage_pdf_path, page_indexes=[0, 0, 1], output_path=output_path
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
        # Test using negative indexes (last page - works with single-page PDF)
        result = client.duplicate_pdf_pages(sample_pdf_path, page_indexes=[-1, 0, -1])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        assert get_pdf_page_count(result) == 3  # Should have 3 pages (last page, first page, last page)

    def test_duplicate_pdf_pages_empty_indexes_error(self, client, sample_pdf_path):
        """Test duplicate_pdf_pages method with empty page_indexes raises error."""
        with pytest.raises(ValueError, match="page_indexes cannot be empty"):
            client.duplicate_pdf_pages(sample_pdf_path, page_indexes=[])

    # Tests for delete_pdf_pages
    def test_delete_pdf_pages_basic(self, client, sample_multipage_pdf_path):
        """Test delete_pdf_pages method with basic page deletion."""
        # Test deleting first page (multi-page PDF has 3 pages)
        result = client.delete_pdf_pages(sample_multipage_pdf_path, page_indexes=[0])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
        assert get_pdf_page_count(result) == total_page_count - 1  # Should have 2 pages (deleted first page from 3-page PDF)

    def test_delete_pdf_pages_multiple(self, client, sample_multipage_pdf_path):
        """Test delete_pdf_pages method with multiple page deletion."""
        # Test deleting multiple pages (deleting pages 1 and 3 from 3-page PDF)
        result = client.delete_pdf_pages(sample_multipage_pdf_path, page_indexes=[0, 2])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
        assert get_pdf_page_count(result) == total_page_count - 2  # Should have 1 page (deleted pages 1 and 3 from 3-page PDF)

    def test_delete_pdf_pages_with_output_file(self, client, sample_multipage_pdf_path, tmp_path):
        """Test delete_pdf_pages method saving to output file."""
        output_path = str(tmp_path / "pages_deleted.pdf")

        # Test deleting pages and saving to file
        result = client.delete_pdf_pages(
            sample_multipage_pdf_path, page_indexes=[1], output_path=output_path
        )

        # Should return None when saving to file
        assert result is None

        # Check that output file was created
        assert (tmp_path / "pages_deleted.pdf").exists()
        assert (tmp_path / "pages_deleted.pdf").stat().st_size > 0
        assert_is_pdf(output_path)

        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
        assert get_pdf_page_count(output_path) == total_page_count - 1  # Should have 2 pages (deleted page 2 from 3-page PDF)

    def test_delete_pdf_pages_negative_indexes_error(self, client, sample_pdf_path):
        """Test delete_pdf_pages method with negative indexes raises error."""
        # Currently negative indexes are not supported for deletion
        with pytest.raises(ValueError, match="Negative page indexes not yet supported"):
            client.delete_pdf_pages(sample_pdf_path, page_indexes=[-1])

    def test_delete_pdf_pages_empty_indexes_error(self, client, sample_pdf_path):
        """Test delete_pdf_pages method with empty page_indexes raises error."""
        with pytest.raises(ValueError, match="page_indexes cannot be empty"):
            client.delete_pdf_pages(sample_pdf_path, page_indexes=[])

    def test_delete_pdf_pages_duplicate_indexes(self, client, sample_multipage_pdf_path):
        """Test delete_pdf_pages method with duplicate page indexes."""
        # Test that duplicate indexes are handled correctly (should remove duplicates)
        result = client.delete_pdf_pages(sample_multipage_pdf_path, page_indexes=[0, 0, 1])

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
        assert get_pdf_page_count(result) == total_page_count - 2  # Should have 1 page (deleted pages 1 and 2 from 3-page PDF)

    # Tests for add_page
    def test_add_page_at_beginning(self, client, sample_pdf_path):
        """Test add_page method inserting at the beginning."""
        # Test inserting at beginning (insert_index=0)
        result = client.add_page(sample_pdf_path, insert_index=0)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 1

    def test_add_page_multiple_pages(self, client, sample_multipage_pdf_path):
        """Test add_page method with multiple pages."""
        # Test adding multiple blank pages before second page
        result = client.add_page(sample_multipage_pdf_path, insert_index=1, page_count=3)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 3

    def test_add_page_at_end(self, client, sample_pdf_path):
        """Test add_page method inserting at the end."""
        # Test inserting at end using -1
        result = client.add_page(sample_pdf_path, insert_index=-1, page_count=2)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 2

    def test_add_page_before_specific_page(self, client, sample_multipage_pdf_path):
        """Test add_page method inserting before a specific page."""
        # Test inserting before page 3 (insert_index=2)
        result = client.add_page(sample_multipage_pdf_path, insert_index=2, page_count=1)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
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
        assert_is_pdf(result)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_pdf_path)
        assert get_pdf_page_count(result) == total_page_count + 2

    def test_add_page_with_output_file(self, client, sample_multipage_pdf_path, tmp_path):
        """Test add_page method saving to output file."""
        output_path = str(tmp_path / "with_blank_pages.pdf")

        # Test adding pages and saving to file
        result = client.add_page(
            sample_multipage_pdf_path, insert_index=1, page_count=2, output_path=output_path
        )

        # Should return None when saving to file
        assert result is None

        # Check that output file was created
        assert (tmp_path / "with_blank_pages.pdf").exists()
        assert (tmp_path / "with_blank_pages.pdf").stat().st_size > 0
        assert_is_pdf(output_path)
        # Verify the number of pages in the output PDF
        total_page_count = get_pdf_page_count(sample_multipage_pdf_path)
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

        # Test excessive page count
        with pytest.raises(ValueError, match="page_count cannot exceed 100"):
            client.add_page(sample_pdf_path, insert_index=0, page_count=101)

    def test_add_page_invalid_position_error(self, client, sample_pdf_path):
        """Test add_page method with invalid insert_index raises error."""
        # Test invalid negative position (anything below -1)
        with pytest.raises(ValueError, match="insert_index must be -1"):
            client.add_page(sample_pdf_path, insert_index=-2, page_count=1)

        with pytest.raises(ValueError, match="insert_index must be -1"):
            client.add_page(sample_pdf_path, insert_index=-5, page_count=1)

    # Tests for set_page_label
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

    def test_set_page_label_multiple_ranges(self, client, sample_multipage_pdf_path):
        """Test set_page_label method with multiple page ranges."""
        labels = [
            {"pages": {"start": 0, "end": 0}, "label": "i"},
            {"pages": {"start": 1, "end": 1}, "label": "intro"},
        ]

        result = client.set_page_label(sample_multipage_pdf_path, labels)

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
