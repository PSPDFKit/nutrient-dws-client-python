import io
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from nutrient_dws.inputs import (
    get_pdf_page_count,
    is_remote_file_input,
    is_valid_pdf,
    process_file_input,
    process_remote_file_input,
    validate_file_input,
    FileInput,
)
from tests.helpers import sample_pdf, TestDocumentGenerator


def create_test_bytes(content: str = "test content") -> bytes:
    """Create test bytes data."""
    return content.encode("utf-8")


class TestValidateFileInput:
    def test_validate_string_inputs(self):
        assert validate_file_input("test.pdf") is True
        assert validate_file_input("https://example.com/file.pdf") is True

    def test_validate_bytes_objects(self):
        test_bytes = create_test_bytes()
        assert validate_file_input(test_bytes) is True

    def test_validate_path_objects(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
        ):
            assert validate_file_input(Path("test.pdf")) is True

    def test_validate_file_like_objects(self):
        mock_file = io.BytesIO(b"test content")
        assert validate_file_input(mock_file) is True

    def test_reject_invalid_inputs(self):
        assert validate_file_input(None) is False
        assert validate_file_input(123) is False
        assert validate_file_input({}) is False


class TestProcessFileInputBytes:
    @pytest.mark.asyncio
    async def test_process_bytes_object(self):
        test_bytes = create_test_bytes("test content")
        result = await process_file_input(test_bytes)

        assert result[0] == test_bytes
        assert result[1] == "document"


class TestProcessFileInputFilePath:
    @pytest.mark.asyncio
    async def test_process_file_path_string(self):
        mock_file_data = b"test file content"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("aiofiles.open") as mock_aiofiles_open,
        ):
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_data)
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_file)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_aiofiles_open.return_value = mock_context_manager

            result = await process_file_input("/path/to/test.pdf")

            assert result[1] == "test.pdf"
            assert result[0] == mock_file_data

    @pytest.mark.asyncio
    async def test_process_path_object(self):
        mock_file_data = b"test file content"
        test_path = Path("/path/to/test.pdf")

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("aiofiles.open") as mock_aiofiles_open,
        ):
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_data)
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_file)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_aiofiles_open.return_value = mock_context_manager

            result = await process_file_input(test_path)

            assert result[1] == "test.pdf"
            assert result[0] == mock_file_data

    @pytest.mark.asyncio
    async def test_throw_error_for_non_existent_file(self):
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                await process_file_input("/path/to/nonexistent.pdf")

    @pytest.mark.asyncio
    async def test_throw_error_for_other_errors(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("aiofiles.open", side_effect=OSError("Some other error")),
        ):
            with pytest.raises(OSError):
                await process_file_input("/path/to/test.pdf")


class TestProcessFileInputFileObjects:
    @pytest.mark.asyncio
    async def test_process_sync_file_object(self):
        test_content = b"test file content"
        mock_file = io.BytesIO(test_content)
        mock_file.name = "test.pdf"

        result = await process_file_input(mock_file)

        assert result[0] == test_content
        assert result[1] == "test.pdf"

    @pytest.mark.asyncio
    async def test_process_file_object_without_name(self):
        test_content = b"test file content"
        mock_file = io.BytesIO(test_content)

        result = await process_file_input(mock_file)

        assert result[0] == test_content
        assert result[1] == "document"


class TestIsRemoteFileInput:
    @pytest.mark.parametrize(
        "input_data,expected",
        [
            ("https://example.com/test.pdf", True),
            ("http://example.com/test.pdf", True),
            ("ftp://example.com/test.pdf", True),
            ("test.pdf", False),
            ("/path/to/test.pdf", False),
            (b"test", False),
            (Path("test.pdf"), False),
        ],
    )
    def test_remote_file_detection(self, input_data, expected):
        assert is_remote_file_input(input_data) is expected


class TestProcessFileInputInvalidInputs:
    @pytest.mark.asyncio
    async def test_throw_for_unsupported_types(self):
        with pytest.raises(ValueError):
            await process_file_input(123)

        with pytest.raises(ValueError):
            await process_file_input({})

    @pytest.mark.asyncio
    async def test_throw_for_none(self):
        with pytest.raises(ValueError):
            await process_file_input(None)


class TestProcessRemoteFileInput:
    @pytest.mark.asyncio
    async def test_process_url_string_input(self):
        mock_response_data = b"test pdf content"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.content = mock_response_data
            mock_response.headers = {}
            mock_response.raise_for_status = Mock(return_value=None)
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await process_remote_file_input("https://example.com/test.pdf")

            assert result[0] == mock_response_data
            assert result[1] == "downloaded_file"

    @pytest.mark.asyncio
    async def test_process_url_with_content_disposition_header(self):
        mock_response_data = b"test pdf content"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.content = mock_response_data
            mock_response.headers = {
                "content-disposition": 'attachment; filename="document.pdf"'
            }
            mock_response.raise_for_status = Mock(return_value=None)
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await process_remote_file_input("https://example.com/test.pdf")

            assert result[0] == mock_response_data
            assert result[1] == "document.pdf"

    @pytest.mark.asyncio
    async def test_throw_error_for_http_error(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock(side_effect=Exception("HTTP 404"))
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            with pytest.raises(Exception):
                await process_remote_file_input("https://example.com/test.pdf")


class TestGetPdfPageCount:
    def test_pdf_with_1_page(self):
        pdf_bytes = TestDocumentGenerator.generate_simple_pdf_content("Text")
        result = get_pdf_page_count(pdf_bytes)
        assert result == 1

    def test_pdf_with_6_pages(self):
        result = get_pdf_page_count(sample_pdf)
        assert result == 6

    def test_throw_for_invalid_pdf_no_objects(self):
        invalid_pdf = b"%PDF-1.4\n%%EOF"

        with pytest.raises(ValueError, match="Could not find /Catalog object"):
            get_pdf_page_count(invalid_pdf)

    def test_throw_for_invalid_pdf_no_catalog(self):
        invalid_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /NotCatalog >>\nendobj\n%%EOF"

        with pytest.raises(ValueError, match="Could not find /Catalog object"):
            get_pdf_page_count(invalid_pdf)

    def test_throw_for_catalog_without_pages_reference(self):
        invalid_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"

        with pytest.raises(ValueError, match="Could not find /Pages reference"):
            get_pdf_page_count(invalid_pdf)

    def test_throw_for_missing_pages_object(self):
        invalid_pdf = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
        )

        with pytest.raises(ValueError, match="Could not find root /Pages object"):
            get_pdf_page_count(invalid_pdf)

    def test_throw_for_pages_object_without_count(self):
        invalid_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages >>\nendobj\n%%EOF"

        with pytest.raises(ValueError, match="Could not find /Count"):
            get_pdf_page_count(invalid_pdf)


class TestIsValidPdf:
    def test_return_true_for_valid_pdf_files(self):
        # Test with generated PDF
        valid_pdf_bytes = TestDocumentGenerator.generate_simple_pdf_content(
            "Test content"
        )
        result = is_valid_pdf(valid_pdf_bytes)
        assert result is True

        # Test with sample PDF
        result = is_valid_pdf(sample_pdf)
        assert result is True

    def test_return_false_for_non_pdf_files(self):
        # Test with non-PDF bytes
        non_pdf_bytes = b"This is not a PDF file"
        result = is_valid_pdf(non_pdf_bytes)
        assert result is False

    def test_return_false_for_partial_pdf_header(self):
        # Test with partial PDF header
        partial_pdf = b"%PD"
        result = is_valid_pdf(partial_pdf)
        assert result is False

    def test_return_false_for_empty_bytes(self):
        result = is_valid_pdf(b"")
        assert result is False
