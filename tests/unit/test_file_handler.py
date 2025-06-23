"""Comprehensive unit tests for file handling utilities."""

import io
import os
import tempfile
from pathlib import Path
from typing import BinaryIO, cast
from unittest.mock import Mock, patch

import pytest

from nutrient_dws.file_handler import (
    DEFAULT_CHUNK_SIZE,
    get_file_size,
    prepare_file_for_upload,
    prepare_file_input,
    save_file_output,
    stream_file_content,
)


class TestPrepareFileInput:
    """Test suite for prepare_file_input function."""

    def test_prepare_file_input_from_bytes(self):
        """Test preparing file input from bytes."""
        content = b"Hello, World!"
        result, filename = prepare_file_input(content)
        assert result == content
        assert filename == "document"

    def test_prepare_file_input_from_string_io(self):
        """Test preparing file input from StringIO-like object."""
        # Using BytesIO instead of StringIO for binary compatibility
        content = b"Test content"
        file_obj = io.BytesIO(content)
        result, filename = prepare_file_input(file_obj)
        assert result == content
        assert filename == "document"

    def test_prepare_file_input_from_file_path_string(self):
        """Test preparing file input from file path string."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"Test file content"
            temp_file.write(content)
            temp_file.flush()

            try:
                result, filename = prepare_file_input(temp_file.name)
                assert result == content
                assert filename == os.path.basename(temp_file.name)
            finally:
                os.unlink(temp_file.name)

    def test_prepare_file_input_from_pathlib_path(self):
        """Test preparing file input from pathlib.Path object."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"Test pathlib content"
            temp_file.write(content)
            temp_file.flush()

            try:
                path = Path(temp_file.name)
                result, filename = prepare_file_input(path)
                assert result == content
                assert filename == path.name
            finally:
                os.unlink(temp_file.name)

    def test_prepare_file_input_from_file_handle(self):
        """Test preparing file input from file handle."""
        with tempfile.NamedTemporaryFile() as temp_file:
            content = b"File handle content"
            temp_file.write(content)
            temp_file.seek(0)

            result, filename = prepare_file_input(cast("BinaryIO", temp_file))
            assert result == content
            assert filename == os.path.basename(temp_file.name)

    def test_prepare_file_input_from_string_file_handle(self):
        """Test preparing file input from file handle with string content."""
        string_content = "String content"
        string_file = io.StringIO(string_content)
        string_file.name = "test.txt"

        result, filename = prepare_file_input(cast("BinaryIO", string_file))
        assert result == string_content.encode()
        assert filename == "test.txt"

    def test_prepare_file_input_file_not_found_string(self):
        """Test FileNotFoundError for non-existent file path string."""
        with pytest.raises(FileNotFoundError, match="File not found: /non/existent/file.txt"):
            prepare_file_input("/non/existent/file.txt")

    def test_prepare_file_input_file_not_found_path(self):
        """Test FileNotFoundError for non-existent pathlib.Path."""
        path = Path("/non/existent/file.txt")
        with pytest.raises(FileNotFoundError, match="File not found:"):
            prepare_file_input(path)

    def test_prepare_file_input_unsupported_type(self):
        """Test ValueError for unsupported input type."""
        with pytest.raises(ValueError, match="Unsupported file input type"):
            prepare_file_input(123)  # type: ignore

    def test_prepare_file_input_file_handle_with_path_name(self):
        """Test file handle with path-like name attribute."""
        with tempfile.NamedTemporaryFile() as temp_file:
            content = b"Content with path name"
            temp_file.write(content)
            temp_file.seek(0)

            # Mock the name to be a path-like object
            temp_file.name = Path(temp_file.name)  # type: ignore

            result, filename = prepare_file_input(cast("BinaryIO", temp_file))
            assert result == content
            assert filename == os.path.basename(str(temp_file.name))


class TestPrepareFileForUpload:
    """Test suite for prepare_file_for_upload function."""

    def test_prepare_file_for_upload_small_file(self):
        """Test preparing small file for upload (loads into memory)."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"Small file content"
            temp_file.write(content)
            temp_file.flush()

            try:
                field_name, (filename, file_content, content_type) = prepare_file_for_upload(
                    temp_file.name, "test_field"
                )

                assert field_name == "test_field"
                assert filename == os.path.basename(temp_file.name)
                assert file_content == content
                assert content_type == "application/octet-stream"
            finally:
                os.unlink(temp_file.name)

    def test_prepare_file_for_upload_large_file(self):
        """Test preparing large file for upload (uses file handle)."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Create a file larger than 10MB threshold
            large_content = b"x" * (11 * 1024 * 1024)  # 11MB
            temp_file.write(large_content)
            temp_file.flush()

            try:
                field_name, (filename, file_handle, content_type) = prepare_file_for_upload(
                    temp_file.name, "large_field"
                )

                assert field_name == "large_field"
                assert filename == os.path.basename(temp_file.name)
                assert hasattr(file_handle, "read")  # Should be file handle
                assert content_type == "application/octet-stream"

                # Clean up the file handle
                if hasattr(file_handle, "close"):
                    file_handle.close()
            finally:
                os.unlink(temp_file.name)

    def test_prepare_file_for_upload_pathlib_path(self):
        """Test preparing pathlib.Path for upload."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"Pathlib content"
            temp_file.write(content)
            temp_file.flush()

            try:
                path = Path(temp_file.name)
                field_name, (filename, file_content, content_type) = prepare_file_for_upload(path)

                assert field_name == "file"  # default field name
                assert filename == path.name
                assert file_content == content
                assert content_type == "application/octet-stream"
            finally:
                os.unlink(temp_file.name)

    def test_prepare_file_for_upload_bytes(self):
        """Test preparing bytes for upload."""
        content = b"Bytes content"

        field_name, (filename, file_content, content_type) = prepare_file_for_upload(
            content, "bytes_field"
        )

        assert field_name == "bytes_field"
        assert filename == "document"
        assert file_content == content
        assert content_type == "application/octet-stream"

    def test_prepare_file_for_upload_file_handle(self):
        """Test preparing file handle for upload."""
        content = b"File handle content"
        file_obj = io.BytesIO(content)
        file_obj.name = "test_file.pdf"

        field_name, (filename, file_handle, content_type) = prepare_file_for_upload(
            file_obj, "handle_field"
        )

        assert field_name == "handle_field"
        assert filename == "test_file.pdf"
        assert file_handle is file_obj
        assert content_type == "application/octet-stream"

    def test_prepare_file_for_upload_file_handle_with_path_name(self):
        """Test file handle with path-like name attribute."""
        content = b"Content with path name"
        file_obj = io.BytesIO(content)
        file_obj.name = Path("/path/to/test_file.pdf")

        field_name, (filename, file_handle, content_type) = prepare_file_for_upload(file_obj)

        assert field_name == "file"
        assert filename == "test_file.pdf"  # basename extracted
        assert file_handle is file_obj
        assert content_type == "application/octet-stream"

    def test_prepare_file_for_upload_file_not_found(self):
        """Test FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found: /non/existent/file.txt"):
            prepare_file_for_upload("/non/existent/file.txt")

    def test_prepare_file_for_upload_unsupported_type(self):
        """Test ValueError for unsupported input type."""
        with pytest.raises(ValueError, match="Unsupported file input type"):
            prepare_file_for_upload(123)  # type: ignore


class TestSaveFileOutput:
    """Test suite for save_file_output function."""

    def test_save_file_output_basic(self):
        """Test basic file saving."""
        content = b"Test content to save"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "output.pdf")
            save_file_output(content, output_path)

            # Verify file was saved correctly
            saved_content = Path(output_path).read_bytes()
            assert saved_content == content

    def test_save_file_output_creates_directories(self):
        """Test that save_file_output creates parent directories."""
        content = b"Content with nested path"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "nested", "deep", "output.pdf")
            save_file_output(content, output_path)

            # Verify directories were created
            assert os.path.exists(os.path.dirname(output_path))

            # Verify file was saved correctly
            saved_content = Path(output_path).read_bytes()
            assert saved_content == content

    def test_save_file_output_overwrites_existing(self):
        """Test that save_file_output overwrites existing files."""
        original_content = b"Original content"
        new_content = b"New content"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "overwrite.pdf")

            # Create initial file
            Path(output_path).write_bytes(original_content)

            # Overwrite with new content
            save_file_output(new_content, output_path)

            # Verify new content
            saved_content = Path(output_path).read_bytes()
            assert saved_content == new_content

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_bytes")
    def test_save_file_output_propagates_os_error(self, mock_write, mock_mkdir):
        """Test that save_file_output propagates OSError."""
        mock_write.side_effect = OSError("Permission denied")
        mock_mkdir.return_value = None  # mkdir succeeds

        with pytest.raises(OSError, match="Permission denied"):
            save_file_output(b"content", "/some/path")


class TestStreamFileContent:
    """Test suite for stream_file_content function."""

    def test_stream_file_content_basic(self):
        """Test basic file streaming."""
        content = b"Content to stream in chunks"

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            try:
                chunks = list(stream_file_content(temp_file.name, chunk_size=8))
                streamed_content = b"".join(chunks)

                assert streamed_content == content
                assert len(chunks) == 4  # 26 bytes in chunks of 8
            finally:
                os.unlink(temp_file.name)

    def test_stream_file_content_large_file(self):
        """Test streaming large file with default chunk size."""
        # Create content larger than default chunk size
        content = b"x" * (DEFAULT_CHUNK_SIZE + 1000)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            try:
                chunks = list(stream_file_content(temp_file.name))
                streamed_content = b"".join(chunks)

                assert streamed_content == content
                assert len(chunks) == 2  # Should be split into 2 chunks
            finally:
                os.unlink(temp_file.name)

    def test_stream_file_content_empty_file(self):
        """Test streaming empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.flush()  # Empty file

            try:
                chunks = list(stream_file_content(temp_file.name))
                assert chunks == []
            finally:
                os.unlink(temp_file.name)

    def test_stream_file_content_file_not_found(self):
        """Test FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found: /non/existent/file.txt"):
            list(stream_file_content("/non/existent/file.txt"))

    def test_stream_file_content_custom_chunk_size(self):
        """Test streaming with custom chunk size."""
        content = b"Custom chunk size test content"

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            try:
                chunks = list(stream_file_content(temp_file.name, chunk_size=5))
                streamed_content = b"".join(chunks)

                assert streamed_content == content
                assert len(chunks) == 6  # 30 bytes in chunks of 5
                assert all(len(chunk) <= 5 for chunk in chunks)
            finally:
                os.unlink(temp_file.name)


class TestGetFileSize:
    """Test suite for get_file_size function."""

    def test_get_file_size_from_bytes(self):
        """Test getting file size from bytes."""
        content = b"Hello, World!"
        size = get_file_size(content)
        assert size == 13

    def test_get_file_size_from_bytesio(self):
        """Test getting file size from BytesIO."""
        content = b"Test content"
        file_obj = io.BytesIO(content)
        size = get_file_size(file_obj)
        assert size == 12

    def test_get_file_size_from_file_path(self):
        """Test getting file size from file path string."""
        content = b"File path content test"

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            try:
                size = get_file_size(temp_file.name)
                assert size == len(content)
            finally:
                os.unlink(temp_file.name)

    def test_get_file_size_from_pathlib_path(self):
        """Test getting file size from pathlib.Path."""
        content = b"Pathlib size test"

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            try:
                path = Path(temp_file.name)
                size = get_file_size(path)
                assert size == len(content)
            finally:
                os.unlink(temp_file.name)

    def test_get_file_size_file_not_found(self):
        """Test get_file_size returns None for non-existent file."""
        size = get_file_size("/non/existent/file.txt")
        assert size is None

    def test_get_file_size_seekable_file_object(self):
        """Test get_file_size with seekable file object."""
        content = b"Seekable file content"

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(content)
            temp_file.seek(5)  # Move to middle of file

            size = get_file_size(cast("BinaryIO", temp_file))
            assert size == len(content)

            # Verify position was restored
            assert temp_file.tell() == 5

    def test_get_file_size_non_seekable_file_object(self):
        """Test get_file_size with non-seekable file object."""
        # Create a mock file object that raises on seek operations
        mock_file = Mock()
        mock_file.seek.side_effect = io.UnsupportedOperation("not seekable")
        mock_file.tell.side_effect = io.UnsupportedOperation("not seekable")

        size = get_file_size(mock_file)
        assert size is None

    def test_get_file_size_file_object_with_os_error(self):
        """Test get_file_size handles OSError during seeking."""
        mock_file = Mock()
        mock_file.tell.side_effect = OSError("OS error during tell")

        size = get_file_size(mock_file)
        assert size is None

    def test_get_file_size_unsupported_type(self):
        """Test get_file_size returns None for unsupported types."""
        size = get_file_size(123)  # type: ignore
        assert size is None

    def test_get_file_size_empty_bytes(self):
        """Test get_file_size with empty bytes."""
        size = get_file_size(b"")
        assert size == 0

    def test_get_file_size_empty_file(self):
        """Test get_file_size with empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.flush()  # Empty file

            try:
                size = get_file_size(temp_file.name)
                assert size == 0
            finally:
                os.unlink(temp_file.name)


class TestFileHandlerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_prepare_file_input_bytesio_at_end(self):
        """Test prepare_file_input with BytesIO positioned at end."""
        content = b"BytesIO at end test"
        file_obj = io.BytesIO(content)
        file_obj.seek(0, 2)  # Seek to end

        result, filename = prepare_file_input(file_obj)
        assert result == content
        assert filename == "document"

    def test_prepare_file_for_upload_exactly_10mb(self):
        """Test prepare_file_for_upload with file exactly at 10MB threshold."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Create exactly 10MB file
            content = b"x" * (10 * 1024 * 1024)
            temp_file.write(content)
            temp_file.flush()

            try:
                field_name, (filename, file_content, content_type) = prepare_file_for_upload(
                    temp_file.name
                )

                # Should load into memory (not streaming) at exactly 10MB
                assert isinstance(file_content, bytes)
                assert file_content == content
            finally:
                os.unlink(temp_file.name)

    def test_file_handle_name_attribute_edge_cases(self):
        """Test file handle with various name attribute types."""
        content = b"Name attribute test"

        # Test with bytes name
        file_obj = io.BytesIO(content)
        file_obj.name = b"/path/to/file.pdf"

        result, filename = prepare_file_input(file_obj)
        assert result == content
        assert filename == "file.pdf"
