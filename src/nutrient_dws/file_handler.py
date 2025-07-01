"""File handling utilities for input/output operations."""

import contextlib
import io
import os
import re
from collections.abc import Generator
from pathlib import Path
from typing import BinaryIO

FileInput = str | Path | bytes | BinaryIO

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
    # Handle different file input types using pattern matching
    match file_input:
        case Path() if not file_input.exists():
            raise FileNotFoundError(f"File not found: {file_input}")
        case Path():
            return file_input.read_bytes(), file_input.name
        case str():
            path = Path(file_input)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_input}")
            return path.read_bytes(), path.name
        case bytes():
            return file_input, "document"
        case _ if hasattr(file_input, "read"):
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
        case _:
            raise ValueError(f"Unsupported file input type: {type(file_input)}")


def prepare_file_for_upload(
    file_input: FileInput,
    field_name: str = "file",
) -> tuple[str, tuple[str, bytes | BinaryIO, str]]:
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

    # Handle different file input types using pattern matching
    path: Path | None
    match file_input:
        case Path():
            path = file_input
        case str():
            path = Path(file_input)
        case _:
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
    match file_input:
        case bytes():
            return field_name, ("document", file_input, content_type)
        case _ if hasattr(file_input, "read"):
            filename = getattr(file_input, "name", "document")
            if hasattr(filename, "__fspath__"):
                filename = os.path.basename(os.fspath(filename))
            elif isinstance(filename, bytes):
                filename = os.path.basename(filename.decode())
            elif isinstance(filename, str):
                filename = os.path.basename(filename)
            return field_name, (str(filename), file_input, content_type)  # type: ignore[return-value]
        case _:
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


def get_file_size(file_input: FileInput) -> int | None:
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


def get_pdf_page_count(pdf_input: FileInput) -> int:
    """Zero dependency way to get the number of pages in a PDF.

    Args:
        pdf_input: File path, bytes, or file-like object. Has to be of a PDF file

    Returns:
        Number of pages in a PDF.
    """
    if isinstance(pdf_input, (str, Path)):
        with open(pdf_input, "rb") as f:
            pdf_bytes = f.read()
    elif isinstance(pdf_input, bytes):
        pdf_bytes = pdf_input
    elif hasattr(pdf_input, "read") and hasattr(pdf_input, "seek") and hasattr(pdf_input, "tell"):
        pos = pdf_input.tell()
        pdf_input.seek(0)
        pdf_bytes = pdf_input.read()
        pdf_input.seek(pos)
    else:
        raise TypeError("Unsupported input type. Expected str, Path, bytes, or seekable BinaryIO.")

    # Find all PDF objects
    objects = re.findall(rb"(\d+)\s+(\d+)\s+obj(.*?)endobj", pdf_bytes, re.DOTALL)

    # Get the Catalog Object
    catalog_obj = None
    for _obj_num, _gen_num, obj_data in objects:
        if b"/Type" in obj_data and b"/Catalog" in obj_data:
            catalog_obj = obj_data
            break

    if not catalog_obj:
        raise ValueError("Could not find /Catalog object in PDF.")

    # Extract /Pages reference (e.g. 3 0 R)
    pages_ref_match = re.search(rb"/Pages\s+(\d+)\s+(\d+)\s+R", catalog_obj)
    if not pages_ref_match:
        raise ValueError("Could not find /Pages reference in /Catalog.")
    pages_obj_num = pages_ref_match.group(1).decode()
    pages_obj_gen = pages_ref_match.group(2).decode()

    # Step 3: Find the referenced /Pages object
    pages_obj_pattern = rf"{pages_obj_num}\s+{pages_obj_gen}\s+obj(.*?)endobj".encode()
    pages_obj_match = re.search(pages_obj_pattern, pdf_bytes, re.DOTALL)
    if not pages_obj_match:
        raise ValueError("Could not find root /Pages object.")
    pages_obj_data = pages_obj_match.group(1)

    # Step 4: Extract /Count
    count_match = re.search(rb"/Count\s+(\d+)", pages_obj_data)
    if not count_match:
        raise ValueError("Could not find /Count in root /Pages object.")

    return int(count_match.group(1))
