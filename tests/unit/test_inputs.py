import io
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from nutrient_dws.inputs import (
    is_remote_file_input,  # Still used internally
    process_file_input,
    validate_file_input,
    FileInput,
    LocalFileInput,
    UrlFileInput,
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


# Tests for process_remote_file_input, get_pdf_page_count, and is_valid_pdf removed in v3.0.0
# These functions were removed from the public API for security reasons (SSRF protection)
# and to eliminate client-side PDF parsing (leveraging server-side negative index support)
