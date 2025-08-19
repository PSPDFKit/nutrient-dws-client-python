import contextlib
import io
import os
import re
from pathlib import Path
from typing import BinaryIO, TypeGuard
from urllib.parse import urlparse

import aiofiles
import httpx

FileInput = str | Path | bytes | BinaryIO

NormalizedFileData = tuple[bytes, str]


def is_url(string: str) -> bool:
    """Checks if a given string is a valid URL.

    Args:
        string: The string to validate.

    Returns:
        True if the string is a valid URL, False otherwise.
    """
    try:
        result = urlparse(string)
        # A valid URL must have a scheme (e.g., 'http') and a network location (e.g., 'www.google.com')
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_valid_pdf(file_bytes: bytes) -> bool:
    """Check if a file is a valid PDF."""
    return file_bytes.startswith(b"%PDF-")


def is_remote_file_input(file_input: FileInput) -> TypeGuard[str]:
    """Check if the file input is a remote URL.

    Args:
        file_input: The file input to check

    Returns:
        True if the file input is a remote URL
    """
    return isinstance(file_input, str) and is_url(file_input)


async def process_file_input(file_input: FileInput) -> NormalizedFileData:
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
            async with aiofiles.open(file_input, "rb") as f:
                content = await f.read()
            return content, file_input.name
        case str():
            path = Path(file_input)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_input}")
            async with aiofiles.open(path, "rb") as f:
                content = await f.read()
            return content, path.name
        case bytes():
            return file_input, "document"
        case _ if hasattr(file_input, "read"):
            # Handle file-like objects (both sync and async)
            if hasattr(file_input, "aread"):
                # Async file-like object
                current_pos = None
                if hasattr(file_input, "seek") and hasattr(file_input, "tell"):
                    try:
                        current_pos = (
                            await file_input.atell()
                            if hasattr(file_input, "atell")
                            else file_input.tell()
                        )
                        if hasattr(file_input, "aseek"):
                            await file_input.aseek(0)
                        else:
                            file_input.seek(0)
                    except (OSError, io.UnsupportedOperation):
                        pass

                content = await file_input.aread()
                if isinstance(content, str):
                    content = content.encode()

                # Restore position if we saved it
                if current_pos is not None:
                    with contextlib.suppress(OSError, io.UnsupportedOperation):
                        if hasattr(file_input, "aseek"):
                            await file_input.aseek(current_pos)
                        else:
                            file_input.seek(current_pos)
            else:
                # Synchronous file-like object
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


async def process_remote_file_input(url: str) -> NormalizedFileData:
    """Convert various file input types to bytes."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        # This will raise an exception for bad responses (4xx or 5xx status codes)
        response.raise_for_status()
        # The .content attribute holds the raw bytes of the response
        file_bytes = response.content

    filename = "downloaded_file"
    # Try to get filename from 'Content-Disposition' header first
    header = response.headers.get("content-disposition")
    if header:
        # Use regex to find a filename in the header
        match = re.search(r'filename="?([^"]+)"?', header)
        if match:
            filename = match.group(1)

    return file_bytes, filename


def validate_file_input(file_input: FileInput) -> bool:
    """Validate that the file input is in a supported format.

    Args:
        file_input: The file input to validate

    Returns:
        True if the file input is valid
    """
    if isinstance(file_input, (bytes, str)):
        return True
    elif isinstance(file_input, Path):
        return file_input.exists() and file_input.is_file()
    elif hasattr(file_input, "read"):
        return True
    return False


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Zero dependency way to get the number of pages in a PDF.

    Args:
        pdf_bytes: PDF file bytes

    Returns:
        Number of pages in a PDF.
    """
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
