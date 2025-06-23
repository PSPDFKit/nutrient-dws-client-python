"""Comprehensive unit tests for Direct API methods."""

import tempfile
from typing import BinaryIO, cast
from unittest.mock import Mock, patch

import pytest

from nutrient_dws.client import NutrientClient


class TestDirectAPIMethods:
    """Test suite for Direct API methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NutrientClient(api_key="test-key")
        self.mock_response = b"mocked-pdf-content"

    @patch("nutrient_dws.client.NutrientClient.build")
    def test_convert_to_pdf_with_bytes_return(self, mock_build):
        """Test convert_to_pdf returns bytes when no output_path."""
        mock_builder = Mock()
        mock_builder.execute.return_value = self.mock_response
        mock_build.return_value = mock_builder

        result = self.client.convert_to_pdf(b"test content")

        assert result == self.mock_response
        mock_build.assert_called_once_with(b"test content")
        mock_builder.execute.assert_called_once_with(None)

    @patch("nutrient_dws.client.NutrientClient.build")
    def test_convert_to_pdf_with_output_path(self, mock_build):
        """Test convert_to_pdf saves to file when output_path provided."""
        mock_builder = Mock()
        mock_builder.execute.return_value = None
        mock_build.return_value = mock_builder

        result = self.client.convert_to_pdf("input.docx", "output.pdf")

        assert result is None
        mock_build.assert_called_once_with("input.docx")
        mock_builder.execute.assert_called_once_with("output.pdf")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_flatten_annotations(self, mock_process):
        """Test flatten_annotations method."""
        mock_process.return_value = self.mock_response

        result = self.client.flatten_annotations("test.pdf")

        assert result == self.mock_response
        mock_process.assert_called_once_with("flatten-annotations", "test.pdf", None)

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_flatten_annotations_with_output_path(self, mock_process):
        """Test flatten_annotations with output path."""
        mock_process.return_value = None

        result = self.client.flatten_annotations("test.pdf", "output.pdf")

        assert result is None
        mock_process.assert_called_once_with("flatten-annotations", "test.pdf", "output.pdf")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_rotate_pages_default_params(self, mock_process):
        """Test rotate_pages with default parameters."""
        mock_process.return_value = self.mock_response

        result = self.client.rotate_pages("test.pdf")

        assert result == self.mock_response
        mock_process.assert_called_once_with("rotate-pages", "test.pdf", None, degrees=0)

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_rotate_pages_with_degrees(self, mock_process):
        """Test rotate_pages with specific degrees."""
        mock_process.return_value = self.mock_response

        result = self.client.rotate_pages("test.pdf", degrees=90)

        assert result == self.mock_response
        mock_process.assert_called_once_with("rotate-pages", "test.pdf", None, degrees=90)

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_rotate_pages_with_page_indexes(self, mock_process):
        """Test rotate_pages with specific page indexes."""
        mock_process.return_value = self.mock_response

        result = self.client.rotate_pages("test.pdf", degrees=180, page_indexes=[0, 2, 4])

        assert result == self.mock_response
        mock_process.assert_called_once_with(
            "rotate-pages", "test.pdf", None, degrees=180, page_indexes=[0, 2, 4]
        )

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_ocr_pdf_default_language(self, mock_process):
        """Test ocr_pdf with default language."""
        mock_process.return_value = self.mock_response

        result = self.client.ocr_pdf("test.pdf")

        assert result == self.mock_response
        mock_process.assert_called_once_with("ocr-pdf", "test.pdf", None, language="english")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_ocr_pdf_custom_language(self, mock_process):
        """Test ocr_pdf with custom language."""
        mock_process.return_value = self.mock_response

        result = self.client.ocr_pdf("test.pdf", language="german")

        assert result == self.mock_response
        mock_process.assert_called_once_with("ocr-pdf", "test.pdf", None, language="german")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_watermark_pdf_with_text(self, mock_process):
        """Test watermark_pdf with text watermark."""
        mock_process.return_value = self.mock_response

        result = self.client.watermark_pdf("test.pdf", text="CONFIDENTIAL")

        assert result == self.mock_response
        mock_process.assert_called_once_with(
            "watermark-pdf",
            "test.pdf",
            None,
            text="CONFIDENTIAL",
            width=200,
            height=100,
            opacity=1.0,
            position="center",
        )

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_watermark_pdf_with_image_url(self, mock_process):
        """Test watermark_pdf with image URL."""
        mock_process.return_value = self.mock_response

        result = self.client.watermark_pdf(
            "test.pdf",
            image_url="https://example.com/logo.png",
            width=150,
            height=75,
            opacity=0.5,
            position="top-right",
        )

        assert result == self.mock_response
        mock_process.assert_called_once_with(
            "watermark-pdf",
            "test.pdf",
            None,
            image_url="https://example.com/logo.png",
            width=150,
            height=75,
            opacity=0.5,
            position="top-right",
        )

    def test_watermark_pdf_no_text_or_image_raises_error(self):
        """Test watermark_pdf raises ValueError when neither text nor image_url provided."""
        with pytest.raises(ValueError, match="Either text or image_url must be provided"):
            self.client.watermark_pdf("test.pdf")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_apply_redactions(self, mock_process):
        """Test apply_redactions method."""
        mock_process.return_value = self.mock_response

        result = self.client.apply_redactions("test.pdf")

        assert result == self.mock_response
        mock_process.assert_called_once_with("apply-redactions", "test.pdf", None)

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_apply_redactions_with_output_path(self, mock_process):
        """Test apply_redactions with output path."""
        mock_process.return_value = None

        result = self.client.apply_redactions("test.pdf", "redacted.pdf")

        assert result is None
        mock_process.assert_called_once_with("apply-redactions", "test.pdf", "redacted.pdf")

    @patch("nutrient_dws.file_handler.prepare_file_for_upload")
    @patch("nutrient_dws.file_handler.save_file_output")
    def test_merge_pdfs_returns_bytes(self, mock_save, mock_prepare):
        """Test merge_pdfs returns bytes when no output_path."""
        # Mock file preparation
        mock_prepare.side_effect = [
            ("file0", ("file0", b"content1", "application/pdf")),
            ("file1", ("file1", b"content2", "application/pdf")),
        ]

        # Mock HTTP client
        self.client._http_client.post = Mock(return_value=self.mock_response)  # type: ignore

        result = self.client.merge_pdfs(["file1.pdf", "file2.pdf"])  # type: ignore[arg-type]

        assert result == self.mock_response
        assert mock_prepare.call_count == 2
        mock_save.assert_not_called()

        # Verify HTTP client was called correctly
        self.client._http_client.post.assert_called_once()
        call_args = self.client._http_client.post.call_args
        assert call_args[0][0] == "/build"
        assert "files" in call_args[1]
        assert "json_data" in call_args[1]

    @patch("nutrient_dws.file_handler.prepare_file_for_upload")
    @patch("nutrient_dws.file_handler.save_file_output")
    def test_merge_pdfs_saves_to_file(self, mock_save, mock_prepare):
        """Test merge_pdfs saves to file when output_path provided."""
        # Mock file preparation
        mock_prepare.side_effect = [
            ("file0", ("file0", b"content1", "application/pdf")),
            ("file1", ("file1", b"content2", "application/pdf")),
        ]

        # Mock HTTP client
        self.client._http_client.post = Mock(return_value=self.mock_response)  # type: ignore

        result = self.client.merge_pdfs(["file1.pdf", "file2.pdf"], "merged.pdf")

        assert result is None
        mock_save.assert_called_once_with(self.mock_response, "merged.pdf")

    def test_merge_pdfs_insufficient_files_raises_error(self):
        """Test merge_pdfs raises ValueError when less than 2 files provided."""
        with pytest.raises(ValueError, match="At least 2 files required for merge"):
            self.client.merge_pdfs(["single_file.pdf"])

        with pytest.raises(ValueError, match="At least 2 files required for merge"):
            self.client.merge_pdfs([])

    @patch("nutrient_dws.file_handler.prepare_file_for_upload")
    def test_merge_pdfs_multiple_files(self, mock_prepare):
        """Test merge_pdfs with multiple files."""
        # Mock file preparation for 3 files
        mock_prepare.side_effect = [
            ("file0", ("file0", b"content1", "application/pdf")),
            ("file1", ("file1", b"content2", "application/pdf")),
            ("file2", ("file2", b"content3", "application/pdf")),
        ]

        # Mock HTTP client
        self.client._http_client.post = Mock(return_value=self.mock_response)  # type: ignore

        files = ["file1.pdf", "file2.pdf", "file3.pdf"]
        result = self.client.merge_pdfs(files)  # type: ignore[arg-type]

        assert result == self.mock_response
        assert mock_prepare.call_count == 3

        # Verify the instruction structure
        call_args = self.client._http_client.post.call_args
        json_data = call_args[1]["json_data"]
        assert len(json_data["parts"]) == 3
        assert json_data["parts"][0] == {"file": "file0"}
        assert json_data["parts"][1] == {"file": "file1"}
        assert json_data["parts"][2] == {"file": "file2"}
        assert json_data["actions"] == []


class TestDirectAPIFileTypes:
    """Test Direct API methods with different file input types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NutrientClient(api_key="test-key")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_direct_api_with_file_path(self, mock_process):
        """Test Direct API methods with file path input."""
        mock_process.return_value = b"result"

        self.client.flatten_annotations("/path/to/file.pdf")
        mock_process.assert_called_once_with("flatten-annotations", "/path/to/file.pdf", None)

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_direct_api_with_bytes_input(self, mock_process):
        """Test Direct API methods with bytes input."""
        mock_process.return_value = b"result"
        file_content = b"PDF content here"

        self.client.ocr_pdf(file_content)
        mock_process.assert_called_once_with("ocr-pdf", file_content, None, language="english")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_direct_api_with_file_like_object(self, mock_process):
        """Test Direct API methods with file-like object."""
        mock_process.return_value = b"result"

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"test content")
            temp_file.seek(0)

            self.client.rotate_pages(cast("BinaryIO", temp_file), degrees=90)
            mock_process.assert_called_once_with(
                "rotate-pages", cast("BinaryIO", temp_file), None, degrees=90
            )


class TestDirectAPIErrorHandling:
    """Test error handling in Direct API methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NutrientClient(api_key="test-key")

    def test_watermark_pdf_validation_error(self):
        """Test watermark_pdf parameter validation."""
        # Test missing text and image_url
        with pytest.raises(ValueError, match="Either text or image_url must be provided"):
            self.client.watermark_pdf("test.pdf")

        # Test empty text and no image_url
        with pytest.raises(ValueError, match="Either text or image_url must be provided"):
            self.client.watermark_pdf("test.pdf", text="")

        # Test None text and no image_url
        with pytest.raises(ValueError, match="Either text or image_url must be provided"):
            self.client.watermark_pdf("test.pdf", text=None)

    def test_merge_pdfs_validation_error(self):
        """Test merge_pdfs parameter validation."""
        # Test empty list
        with pytest.raises(ValueError, match="At least 2 files required for merge"):
            self.client.merge_pdfs([])

        # Test single file
        with pytest.raises(ValueError, match="At least 2 files required for merge"):
            self.client.merge_pdfs(["single.pdf"])

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_direct_api_propagates_exceptions(self, mock_process):
        """Test that Direct API methods propagate exceptions from _process_file."""
        from nutrient_dws.exceptions import APIError

        mock_process.side_effect = APIError("API error", 400, "Bad request")

        with pytest.raises(APIError):
            self.client.flatten_annotations("test.pdf")

    @patch("nutrient_dws.client.NutrientClient.build")
    def test_convert_to_pdf_propagates_exceptions(self, mock_build):
        """Test that convert_to_pdf propagates exceptions from build().execute()."""
        from nutrient_dws.exceptions import AuthenticationError

        mock_builder = Mock()
        mock_builder.execute.side_effect = AuthenticationError("Invalid API key")
        mock_build.return_value = mock_builder

        with pytest.raises(AuthenticationError):
            self.client.convert_to_pdf("test.docx")


class TestDirectAPIBoundaryConditions:
    """Test boundary conditions and edge cases for Direct API methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = NutrientClient(api_key="test-key")

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_rotate_pages_boundary_degrees(self, mock_process):
        """Test rotate_pages with boundary degree values."""
        mock_process.return_value = b"result"

        # Test valid degree values
        for degrees in [90, 180, 270, -90]:
            self.client.rotate_pages("test.pdf", degrees=degrees)
            mock_process.assert_called_with("rotate-pages", "test.pdf", None, degrees=degrees)

        # Test zero degrees (no rotation)
        self.client.rotate_pages("test.pdf", degrees=0)
        mock_process.assert_called_with("rotate-pages", "test.pdf", None, degrees=0)

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_watermark_pdf_boundary_opacity(self, mock_process):
        """Test watermark_pdf with boundary opacity values."""
        mock_process.return_value = b"result"

        # Test minimum opacity
        self.client.watermark_pdf("test.pdf", text="TEST", opacity=0.0)
        mock_process.assert_called_with(
            "watermark-pdf",
            "test.pdf",
            None,
            text="TEST",
            width=200,
            height=100,
            opacity=0.0,
            position="center",
        )

        # Test maximum opacity
        self.client.watermark_pdf("test.pdf", text="TEST", opacity=1.0)
        mock_process.assert_called_with(
            "watermark-pdf",
            "test.pdf",
            None,
            text="TEST",
            width=200,
            height=100,
            opacity=1.0,
            position="center",
        )

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_watermark_pdf_all_positions(self, mock_process):
        """Test watermark_pdf with all valid position values."""
        mock_process.return_value = b"result"

        positions = [
            "top-left",
            "top-center",
            "top-right",
            "center",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        ]

        for position in positions:
            self.client.watermark_pdf("test.pdf", text="TEST", position=position)
            mock_process.assert_called_with(
                "watermark-pdf",
                "test.pdf",
                None,
                text="TEST",
                width=200,
                height=100,
                opacity=1.0,
                position=position,
            )

    @patch("nutrient_dws.client.NutrientClient._process_file")
    def test_ocr_pdf_all_languages(self, mock_process):
        """Test ocr_pdf with all supported languages."""
        mock_process.return_value = b"result"

        languages = ["english", "eng", "deu", "german"]

        for language in languages:
            self.client.ocr_pdf("test.pdf", language=language)
            mock_process.assert_called_with("ocr-pdf", "test.pdf", None, language=language)

    @patch("nutrient_dws.file_handler.prepare_file_for_upload")
    def test_merge_pdfs_maximum_files(self, mock_prepare):
        """Test merge_pdfs with many files."""
        # Create 10 files to test performance with larger lists
        files = [f"file{i}.pdf" for i in range(10)]

        # Mock file preparation
        mock_prepare.side_effect = [
            (f"file{i}", (f"file{i}", f"content{i}".encode(), "application/pdf")) for i in range(10)
        ]

        # Mock HTTP client
        self.client._http_client.post = Mock(return_value=b"merged_result")  # type: ignore

        result = self.client.merge_pdfs(files)  # type: ignore[arg-type]

        assert result == b"merged_result"
        assert mock_prepare.call_count == 10

        # Verify instruction structure
        call_args = self.client._http_client.post.call_args
        json_data = call_args[1]["json_data"]
        assert len(json_data["parts"]) == 10
        assert json_data["actions"] == []
