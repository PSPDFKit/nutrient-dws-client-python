"""File handling utilities for input/output operations."""

import contextlib
import io
import os
from collections.abc import Generator
from pathlib import Path
from typing import BinaryIO, Optional, Union

FileInput = Union[str, Path, bytes, BinaryIO]

# Default chunk size for streaming operations (1MB)
DEFAULT_CHUNK_SIZE = 1024 * 1024


def prepare_file_input(file_input: FileInput) -> tuple[bytes, str]:
    """Convert various file input types to bytes.

    Args:
        file_input: File path, bytes, or file-like object.

    Returns:
        tuple of (file_bytes, filename).

    Raises:
        FileNotFoundError: If file path doesn't exist.
        ValueError: If input type is not supported.
    """
    # Handle different file input types
    if isinstance(file_input, Path):
        if not file_input.exists():
            raise FileNotFoundError(f"File not found: {file_input}")
        return file_input.read_bytes(), file_input.name
    elif isinstance(file_input, str):
        path = Path(file_input)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_input}")
        return path.read_bytes(), path.name
    elif isinstance(file_input, bytes):
        return file_input, "document"
    elif hasattr(file_input, "read"):
        # Handle file-like objects
        # Save current position if seekable
        current_pos = None
        if hasattr(file_input, "seek") and hasattr(file_input, "tell"):
            try:
                current_pos = file_input.tell()
                file_input.seek(0)  # Read from beginning
            except (OSError, io.UnsupportedOperation):
                pass

        content = file_input.read()
        if isinstance(content, str):
            content = content.encode()

        # Restore position if we saved it
        if current_pos is not None:
            with contextlib.suppress(OSError, io.UnsupportedOperation):
                file_input.seek(current_pos)

        filename = getattr(file_input, "name", "document")
        if hasattr(filename, "__fspath__"):
            filename = os.path.basename(os.fspath(filename))
        elif isinstance(filename, bytes):
            filename = os.path.basename(filename.decode())
        elif isinstance(filename, str):
            filename = os.path.basename(filename)
        return content, str(filename)
    else:
        raise ValueError(f"Unsupported file input type: {type(file_input)}")


def prepare_file_for_upload(
    file_input: FileInput,
    field_name: str = "file",
) -> tuple[str, tuple[str, Union[bytes, BinaryIO], str]]:
    """Prepare file for multipart upload.

    Args:
        file_input: File path, bytes, or file-like object.
        field_name: Form field name for the file.

    Returns:
        tuple of (field_name, (filename, file_content_or_stream, content_type)).

    Raises:
        FileNotFoundError: If file path doesn't exist.
        ValueError: If input type is not supported.
    """
    content_type = "application/octet-stream"

    # Handle different file input types
    path: Optional[Path]
    if isinstance(file_input, Path):
        path = file_input
    elif isinstance(file_input, str):
        path = Path(file_input)
    else:
        path = None

    # Handle path-based inputs
    if path is not None:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # For large files, return file handle instead of reading into memory
        file_size = path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB threshold
            # Note: File handle is intentionally not using context manager
            # as it needs to remain open for streaming upload by HTTP client
            file_handle = open(path, "rb")  # noqa: SIM115
            return field_name, (path.name, file_handle, content_type)
        else:
            return field_name, (path.name, path.read_bytes(), content_type)

    # Handle non-path inputs
    if isinstance(file_input, bytes):
        return field_name, ("document", file_input, content_type)
    elif hasattr(file_input, "read"):
        filename = getattr(file_input, "name", "document")
        if hasattr(filename, "__fspath__"):
            filename = os.path.basename(os.fspath(filename))
        elif isinstance(filename, bytes):
            filename = os.path.basename(filename.decode())
        elif isinstance(filename, str):
            filename = os.path.basename(filename)
        return field_name, (str(filename), file_input, content_type)  # type: ignore[return-value]
    else:
        raise ValueError(f"Unsupported file input type: {type(file_input)}")


def save_file_output(content: bytes, output_path: str) -> None:
    """Save file content to disk.

    Args:
        content: File bytes to save.
        output_path: Path where to save the file.

    Raises:
        OSError: If file cannot be written.
    """
    path = Path(output_path)
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def stream_file_content(
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Generator[bytes, None, None]:
    """Stream file content in chunks.

    Args:
        file_path: Path to the file to stream.
        chunk_size: Size of each chunk in bytes.

    Yields:
        Chunks of file content.

    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk


def get_file_size(file_input: FileInput) -> Optional[int]:
    """Get size of file input if available.

    Args:
        file_input: File path, bytes, or file-like object.

    Returns:
        File size in bytes, or None if size cannot be determined.
    """
    if isinstance(file_input, Path):
        if file_input.exists():
            return file_input.stat().st_size
    elif isinstance(file_input, str):
        path = Path(file_input)
        if path.exists():
            return path.stat().st_size
    elif isinstance(file_input, bytes):
        return len(file_input)
    elif hasattr(file_input, "seek") and hasattr(file_input, "tell"):
        # For seekable file-like objects
        try:
            current_pos = file_input.tell()
            file_input.seek(0, 2)  # Seek to end
            size = file_input.tell()
            file_input.seek(current_pos)  # Restore position
            return size
        except (OSError, io.UnsupportedOperation):
            pass

    return None
