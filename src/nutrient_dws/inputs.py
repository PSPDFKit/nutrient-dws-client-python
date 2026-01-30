import contextlib
import io
import os
from pathlib import Path
from typing import BinaryIO, TypeGuard
from urllib.parse import urlparse

import aiofiles

# Type definitions for file inputs
# Breaking change in v3.0.0: FileInput no longer includes URL strings
LocalFileInput = Path | bytes | BinaryIO
FileInputWithUrl = str | Path | bytes | BinaryIO
FileInput = LocalFileInput  # Breaking change: no longer accepts URL strings

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


def is_remote_file_input(file_input: FileInputWithUrl) -> TypeGuard[str]:
    """Check if the file input is a remote URL.

    Args:
        file_input: The file input to check

    Returns:
        True if the file input is a remote URL
    """
    return isinstance(file_input, str) and is_url(file_input)


async def process_file_input(
    file_input: LocalFileInput | FileInputWithUrl,
) -> NormalizedFileData:
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


# process_remote_file_input() has been removed in v3.0.0
# URLs are now passed to the server for secure server-side fetching
# This function was removed to prevent SSRF vulnerabilities


def validate_file_input(file_input: LocalFileInput | FileInputWithUrl) -> bool:
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


# get_pdf_page_count() has been removed in v3.0.0
# The API natively supports negative indices (-1 = last page)
# Client-side PDF parsing is no longer needed
# This removes ~40 lines of code and improves security
