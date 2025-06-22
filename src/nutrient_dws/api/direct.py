"""Direct API methods for supported document processing tools.

This file provides convenient methods that wrap the Nutrient Build API
for supported document processing operations.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

from nutrient_dws.file_handler import FileInput

if TYPE_CHECKING:
    from nutrient_dws.builder import BuildAPIWrapper
    from nutrient_dws.http_client import HTTPClient


class HasBuildMethod(Protocol):
    """Protocol for objects that have a build method."""

    def build(self, input_file: FileInput) -> "BuildAPIWrapper":
        """Build method signature."""
        ...

    @property
    def _http_client(self) -> "HTTPClient":
        """HTTP client property."""
        ...


class DirectAPIMixin:
    """Mixin class containing Direct API methods.

    These methods provide a simplified interface to common document
    processing operations. They internally use the Build API.

    Note: The API automatically converts supported document formats
    (DOCX, XLSX, PPTX) to PDF when processing.
    """

    def _process_file(
        self,
        tool: str,
        input_file: FileInput,
        output_path: Optional[str] = None,
        **options: Any,
    ) -> Optional[bytes]:
        """Process file method that will be provided by NutrientClient."""
        raise NotImplementedError("This method is provided by NutrientClient")

    def convert_to_pdf(
        self,
        input_file: FileInput,
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Convert a document to PDF.

        Converts Office documents (DOCX, XLSX, PPTX) to PDF format.
        This uses the API's implicit conversion - simply uploading a
        non-PDF document returns it as a PDF.

        Args:
            input_file: Input document (DOCX, XLSX, PPTX, etc).
            output_path: Optional path to save the output PDF.

        Returns:
            Converted PDF as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors (e.g., unsupported format).

        Note:
            HTML files are not currently supported by the API.
        """
        # Use builder with no actions - implicit conversion happens
        # Type checking: at runtime, self is NutrientClient which has these methods
        return self.build(input_file).execute(output_path)  # type: ignore[attr-defined,no-any-return]

    def flatten_annotations(
        self, input_file: FileInput, output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """Flatten annotations and form fields in a PDF.

        Converts all annotations and form fields into static page content.
        If input is an Office document, it will be converted to PDF first.

        Args:
            input_file: Input file (PDF or Office document).
            output_path: Optional path to save the output file.

        Returns:
            Processed file as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
        """
        return self._process_file("flatten-annotations", input_file, output_path)

    def rotate_pages(
        self,
        input_file: FileInput,
        output_path: Optional[str] = None,
        degrees: int = 0,
        page_indexes: Optional[List[int]] = None,
    ) -> Optional[bytes]:
        """Rotate pages in a PDF.

        Rotate all pages or specific pages by the specified degrees.
        If input is an Office document, it will be converted to PDF first.

        Args:
            input_file: Input file (PDF or Office document).
            output_path: Optional path to save the output file.
            degrees: Rotation angle (90, 180, 270, or -90).
            page_indexes: Optional list of page indexes to rotate (0-based).

        Returns:
            Processed file as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
        """
        options = {"degrees": degrees}
        if page_indexes is not None:
            options["page_indexes"] = page_indexes  # type: ignore
        return self._process_file("rotate-pages", input_file, output_path, **options)

    def ocr_pdf(
        self,
        input_file: FileInput,
        output_path: Optional[str] = None,
        language: str = "english",
    ) -> Optional[bytes]:
        """Apply OCR to a PDF to make it searchable.

        Performs optical character recognition on the PDF to extract text
        and make it searchable. If input is an Office document, it will
        be converted to PDF first.

        Args:
            input_file: Input file (PDF or Office document).
            output_path: Optional path to save the output file.
            language: OCR language. Supported: "english", "eng", "deu", "german".
                     Default is "english".

        Returns:
            Processed file as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
        """
        return self._process_file("ocr-pdf", input_file, output_path, language=language)

    def watermark_pdf(
        self,
        input_file: FileInput,
        output_path: Optional[str] = None,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        width: int = 200,
        height: int = 100,
        opacity: float = 1.0,
        position: str = "center",
    ) -> Optional[bytes]:
        """Add a watermark to a PDF.

        Adds a text or image watermark to all pages of the PDF.
        If input is an Office document, it will be converted to PDF first.

        Args:
            input_file: Input file (PDF or Office document).
            output_path: Optional path to save the output file.
            text: Text to use as watermark. Either text or image_url required.
            image_url: URL of image to use as watermark.
            width: Width of the watermark in points (required).
            height: Height of the watermark in points (required).
            opacity: Opacity of the watermark (0.0 to 1.0).
            position: Position of watermark. One of: "top-left", "top-center",
                     "top-right", "center", "bottom-left", "bottom-center",
                     "bottom-right".

        Returns:
            Processed file as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
            ValueError: If neither text nor image_url is provided.
        """
        if not text and not image_url:
            raise ValueError("Either text or image_url must be provided")

        options = {
            "width": width,
            "height": height,
            "opacity": opacity,
            "position": position,
        }

        if text:
            options["text"] = text
        else:
            options["image_url"] = image_url

        return self._process_file("watermark-pdf", input_file, output_path, **options)

    def apply_redactions(
        self,
        input_file: FileInput,
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Apply redaction annotations to permanently remove content.

        Applies any redaction annotations in the PDF to permanently remove
        the underlying content. If input is an Office document, it will
        be converted to PDF first.

        Args:
            input_file: Input file (PDF or Office document).
            output_path: Optional path to save the output file.

        Returns:
            Processed file as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
        """
        return self._process_file("apply-redactions", input_file, output_path)

    def split_pdf(
        self,
        input_file: FileInput,
        page_ranges: Optional[List[Dict[str, int]]] = None,
        output_paths: Optional[List[str]] = None,
    ) -> List[bytes]:
        """Split a PDF into multiple documents by page ranges.

        Splits a PDF into multiple files based on specified page ranges.
        Each range creates a separate output file.

        Args:
            input_file: Input PDF file.
            page_ranges: List of page range dictionaries. Each dict can contain:
                - 'start': Starting page index (0-based, inclusive). 0 = first page.
                - 'end': Ending page index (0-based, exclusive).
                        For example: {"start": 0, "end": 2} extracts pages 0-1 (first two pages).
                - If 'end' is omitted from dict, extracts from 'start' to end of document.
                Required parameter - must provide at least one range
            output_paths: Optional list of paths to save output files.
                          Must match length of page_ranges if provided.

        Returns:
            List of PDF bytes for each split, or empty list if output_paths provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
            ValueError: If page_ranges and output_paths length mismatch.

        Examples:
            # Split first two pages into separate files
            pages = client.split_pdf(
                "document.pdf",
                page_ranges=[{"start": 0, "end": 1}, {"start": 1, "end": 2}]
            )

            # Split by custom ranges
            parts = client.split_pdf(
                "document.pdf",
                page_ranges=[
                    {"start": 0, "end": 5},      # Pages 1-5
                    {"start": 5, "end": 10},     # Pages 6-10
                    {"start": 10}                # Pages 11 to end
                ]
            )

            # Save to specific files
            client.split_pdf(
                "document.pdf",
                page_ranges=[{"start": 0, "end": 2}, {"start": 2}],
                output_paths=["part1.pdf", "part2.pdf"]
            )
        """
        from nutrient_dws.file_handler import prepare_file_for_upload, save_file_output

        # Validate inputs
        if not page_ranges:
            raise ValueError("page_ranges is required - must provide at least one range")

        # Limit number of ranges to prevent excessive API calls
        if len(page_ranges) > 50:
            raise ValueError("Maximum 50 page ranges allowed per split operation")

        if output_paths and len(output_paths) != len(page_ranges):
            raise ValueError("output_paths length must match page_ranges length")

        results: List[bytes] = []

        # Process each page range as a separate API call
        for i, page_range in enumerate(page_ranges):
            # Prepare file for upload
            file_field, file_data = prepare_file_for_upload(input_file, "file")
            files = {file_field: file_data}

            # Build instructions for page extraction
            instructions = {"parts": [{"file": "file", "pages": page_range}], "actions": []}

            # Make API request
            # Type checking: at runtime, self is NutrientClient which has _http_client
            result = self._http_client.post(  # type: ignore[attr-defined]
                "/build",
                files=files,
                json_data=instructions,
            )

            # Handle output
            if output_paths and i < len(output_paths):
                save_file_output(result, output_paths[i])
            else:
                results.append(result)  # type: ignore[arg-type]

        return results if not output_paths else []

    def merge_pdfs(
        self,
        input_files: List[FileInput],
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Merge multiple PDF files into one.

        Combines multiple files into a single PDF in the order provided.
        Office documents (DOCX, XLSX, PPTX) will be automatically converted
        to PDF before merging.

        Args:
            input_files: List of input files (PDFs or Office documents).
            output_path: Optional path to save the output file.

        Returns:
            Merged PDF as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
            ValueError: If less than 2 files provided.

        Example:
            # Merge PDFs and Office documents
            client.merge_pdfs([
                "document1.pdf",
                "document2.docx",
                "spreadsheet.xlsx"
            ], "merged.pdf")
        """
        if len(input_files) < 2:
            raise ValueError("At least 2 files required for merge")

        from nutrient_dws.file_handler import prepare_file_for_upload, save_file_output

        # Prepare files for upload
        files = {}
        parts = []

        for i, file in enumerate(input_files):
            field_name = f"file{i}"
            file_field, file_data = prepare_file_for_upload(file, field_name)
            files[file_field] = file_data
            parts.append({"file": field_name})

        # Build instructions for merge (no actions needed)
        instructions = {"parts": parts, "actions": []}

        # Make API request
        # Type checking: at runtime, self is NutrientClient which has _http_client
        result = self._http_client.post(  # type: ignore[attr-defined]
            "/build",
            files=files,
            json_data=instructions,
        )

        # Handle output
        if output_path:
            save_file_output(result, output_path)
            return None
        else:
            return result  # type: ignore[no-any-return]

    def duplicate_pdf_pages(
        self,
        input_file: FileInput,
        page_indexes: List[int],
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Duplicate specific pages within a PDF document.

        Creates a new PDF containing the specified pages in the order provided.
        Pages can be duplicated multiple times by including their index multiple times.

        Args:
            input_file: Input PDF file.
            page_indexes: List of page indexes to include (0-based). 0 = first page.
                         Pages can be repeated to create duplicates.
                         Negative indexes are supported (-1 for last page).
                         For example: [0, 0, 1] duplicates the first page then includes the second.
            output_path: Optional path to save the output file.

        Returns:
            Processed PDF as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
            ValueError: If page_indexes is empty.

        Examples:
            # Duplicate first page twice, then include second page
            result = client.duplicate_pdf_pages(
                "document.pdf",
                page_indexes=[0, 0, 1]  # Page 1, Page 1, Page 2
            )

            # Include last page at beginning and end
            result = client.duplicate_pdf_pages(
                "document.pdf",
                page_indexes=[-1, 0, 1, 2, -1]  # Last, First, Second, Third, Last
            )

            # Save to specific file
            client.duplicate_pdf_pages(
                "document.pdf",
                page_indexes=[0, 2, 1],  # Reorder: Page 1, Page 3, Page 2
                output_path="reordered.pdf"
            )
        """
        from nutrient_dws.file_handler import prepare_file_for_upload, save_file_output

        # Validate inputs
        if not page_indexes:
            raise ValueError("page_indexes cannot be empty")

        # Prepare file for upload
        file_field, file_data = prepare_file_for_upload(input_file, "file")
        files = {file_field: file_data}

        # Build parts for each page index
        parts = []
        for page_index in page_indexes:
            if page_index < 0:
                # For negative indexes, use the index directly (API supports negative indexes)
                parts.append({"file": "file", "pages": {"start": page_index, "end": page_index}})
            else:
                # For positive indexes, create single-page range with exclusive end
                parts.append({
                    "file": "file",
                    "pages": {"start": page_index, "end": page_index + 1}
                })

        # Build instructions for duplication
        instructions = {"parts": parts, "actions": []}

        # Make API request
        # Type checking: at runtime, self is NutrientClient which has _http_client
        result = self._http_client.post(  # type: ignore[attr-defined]
            "/build",
            files=files,
            json_data=instructions,
        )

        # Handle output
        if output_path:
            save_file_output(result, output_path)
            return None
        else:
            return result  # type: ignore[no-any-return]

    def delete_pdf_pages(
        self,
        input_file: FileInput,
        page_indexes: List[int],
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Delete specific pages from a PDF document.

        Creates a new PDF with the specified pages removed. The API approach
        works by selecting all pages except those to be deleted.

        Args:
            input_file: Input PDF file.
            page_indexes: List of page indexes to delete (0-based). 0 = first page.
                         Must be unique, sorted in ascending order.
                         Negative indexes are NOT supported.
            output_path: Optional path to save the output file.

        Returns:
            Processed PDF as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
            ValueError: If page_indexes is empty or contains negative indexes.

        Examples:
            # Delete first and last pages (Note: negative indexes not supported)
            result = client.delete_pdf_pages(
                "document.pdf",
                page_indexes=[0, 2]  # Delete pages 1 and 3
            )

            # Delete specific pages (2nd and 4th pages)
            result = client.delete_pdf_pages(
                "document.pdf",
                page_indexes=[1, 3]  # 0-based indexing
            )

            # Save to specific file
            client.delete_pdf_pages(
                "document.pdf",
                page_indexes=[2, 4, 5],
                output_path="pages_deleted.pdf"
            )
        """
        from nutrient_dws.file_handler import prepare_file_for_upload, save_file_output

        # Validate inputs
        if not page_indexes:
            raise ValueError("page_indexes cannot be empty")

        # Check for negative indexes
        if any(idx < 0 for idx in page_indexes):
            negative_indexes = [idx for idx in page_indexes if idx < 0]
            raise ValueError(
                f"Negative page indexes not yet supported for deletion: {negative_indexes}"
            )

        # Prepare file for upload
        file_field, file_data = prepare_file_for_upload(input_file, "file")
        files = {file_field: file_data}

        # Sort page indexes to handle ranges efficiently
        sorted_indexes = sorted(set(page_indexes))  # Remove duplicates and sort

        # Build parts for pages to keep (excluding the ones to delete)
        parts = []

        # Start from page 0
        current_page = 0

        for delete_index in sorted_indexes:
            # Add range from current_page to delete_index (exclusive)
            if current_page < delete_index:
                parts.append(
                    {"file": "file", "pages": {"start": current_page, "end": delete_index}}
                )

            # Skip the deleted page
            current_page = delete_index + 1

        # Add remaining pages from current_page to end
        if current_page >= 0:  # Always add remaining pages
            parts.append({"file": "file", "pages": {"start": current_page}})

        # If no parts (edge case), raise error
        if not parts:
            raise ValueError("No valid pages to keep after deletion")

        # Build instructions for deletion (keeping non-deleted pages)
        instructions = {"parts": parts, "actions": []}

        # Make API request
        # Type checking: at runtime, self is NutrientClient which has _http_client
        result = self._http_client.post(  # type: ignore[attr-defined]
            "/build",
            files=files,
            json_data=instructions,
        )

        # Handle output
        if output_path:
            save_file_output(result, output_path)
            return None
        else:
            return result  # type: ignore[no-any-return]

    def add_page(
        self,
        input_file: FileInput,
        insert_index: int,
        page_count: int = 1,
        page_size: str = "A4",
        orientation: str = "portrait",
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Add blank pages to a PDF document.

        Inserts blank pages at the specified insertion index in the document.

        Args:
            input_file: Input PDF file.
            insert_index: Position to insert pages (0-based insertion index).
                         0 = insert before first page (at beginning)
                         1 = insert before second page (after first page)
                         -1 = insert after last page (at end)
            page_count: Number of blank pages to add (default: 1).
            page_size: Page size for new pages. Common values: "A4", "Letter",
                      "Legal", "A3", "A5" (default: "A4").
            orientation: Page orientation. Either "portrait" or "landscape"
                        (default: "portrait").
            output_path: Optional path to save the output file.

        Returns:
            Processed PDF as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
            ValueError: If page_count is less than 1 or if insert_index is
                       a negative number other than -1.

        Examples:
            # Add a single blank page at the beginning
            result = client.add_page("document.pdf", insert_index=0)

            # Add multiple pages at the end
            result = client.add_page(
                "document.pdf",
                insert_index=-1,  # Insert at end
                page_count=3,
                page_size="Letter",
                orientation="landscape"
            )

            # Add pages before third page and save to file
            client.add_page(
                "document.pdf",
                insert_index=2,  # Insert before third page
                page_count=2,
                output_path="with_blank_pages.pdf"
            )
        """
        from nutrient_dws.file_handler import prepare_file_for_upload, save_file_output

        # Validate inputs
        if page_count < 1:
            raise ValueError("page_count must be at least 1")
        if page_count > 100:
            raise ValueError("page_count cannot exceed 100 pages")
        if insert_index < -1:
            raise ValueError("insert_index must be -1 (for end) or a non-negative insertion index")

        # Prepare file for upload
        file_field, file_data = prepare_file_for_upload(input_file, "file")
        files = {file_field: file_data}

        # Build parts array
        parts: List[Dict[str, Any]] = []

        # Create new page part
        new_page_part = {
            "page": "new",
            "pageCount": page_count,
            "layout": {
                "size": page_size,
                "orientation": orientation,
            },
        }

        if insert_index == -1:
            # Insert at end: add all original pages first, then new pages
            parts.append({"file": "file"})
            parts.append(new_page_part)
        elif insert_index == 0:
            # Insert at beginning: add new pages first, then all original pages
            parts.append(new_page_part)
            parts.append({"file": "file"})
        else:
            # Insert at specific position: split original document
            # Add pages from start up to insertion point (0 to insert_index-1)
            parts.append({"file": "file", "pages": {"start": 0, "end": insert_index}})

            # Add new blank pages
            parts.append(new_page_part)

            # Add remaining pages from insertion point to end
            parts.append({"file": "file", "pages": {"start": insert_index}})

        # Build instructions for adding pages
        instructions = {"parts": parts, "actions": []}

        # Make API request
        # Type checking: at runtime, self is NutrientClient which has _http_client
        result = self._http_client.post(  # type: ignore[attr-defined]
            "/build",
            files=files,
            json_data=instructions,
        )

        # Handle output
        if output_path:
            save_file_output(result, output_path)
            return None
        else:
            return result  # type: ignore[no-any-return]

    def set_page_label(
        self,
        input_file: FileInput,
        labels: List[Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Set labels for specific pages in a PDF.

        Assigns custom labels/numbering to specific page ranges in a PDF document.
        Each label configuration specifies a page range and the label text to apply.

        Args:
            input_file: Input PDF file.
            labels: List of label configurations. Each dict must contain:
                   - 'pages': Page range dict with 'start' (required) and optionally 'end'
                   - 'label': String label to apply to those pages
                   Page ranges use 0-based indexing where 'end' is exclusive.
            output_path: Optional path to save the output file.

        Returns:
            Processed PDF as bytes, or None if output_path is provided.

        Raises:
            AuthenticationError: If API key is missing or invalid.
            APIError: For other API errors.
            ValueError: If labels list is empty or contains invalid configurations.

        Examples:
            # Set labels for different page ranges
            client.set_page_label(
                "document.pdf",
                labels=[
                    {"pages": {"start": 0, "end": 3}, "label": "Introduction"},
                    {"pages": {"start": 3, "end": 10}, "label": "Chapter 1"},
                    {"pages": {"start": 10}, "label": "Appendix"}
                ],
                output_path="labeled_document.pdf"
            )

            # Set label for single page
            client.set_page_label(
                "document.pdf",
                labels=[{"pages": {"start": 0, "end": 1}, "label": "Cover Page"}]
            )
        """
        from nutrient_dws.file_handler import prepare_file_for_upload, save_file_output

        # Validate inputs
        if not labels:
            raise ValueError("labels list cannot be empty")

        # Normalize labels to ensure proper format
        normalized_labels = []
        for i, label_config in enumerate(labels):
            if not isinstance(label_config, dict):
                raise ValueError(f"Label configuration {i} must be a dictionary")

            if "pages" not in label_config:
                raise ValueError(f"Label configuration {i} missing required 'pages' key")

            if "label" not in label_config:
                raise ValueError(f"Label configuration {i} missing required 'label' key")

            pages = label_config["pages"]
            if not isinstance(pages, dict) or "start" not in pages:
                raise ValueError(f"Label configuration {i} 'pages' must be a dict with 'start' key")

            # Normalize pages to ensure 'end' is present
            normalized_pages = {"start": pages["start"]}
            if "end" in pages:
                normalized_pages["end"] = pages["end"]
            else:
                # If no end is specified, use -1 to indicate "to end of document"
                normalized_pages["end"] = -1

            normalized_labels.append({"pages": normalized_pages, "label": label_config["label"]})

        # Prepare file for upload
        file_field, file_data = prepare_file_for_upload(input_file, "file")
        files = {file_field: file_data}

        # Build instructions with page labels in output configuration
        instructions = {
            "parts": [{"file": "file"}],
            "actions": [],
            "output": {"labels": normalized_labels},
        }

        # Make API request
        # Type checking: at runtime, self is NutrientClient which has _http_client
        result = self._http_client.post(  # type: ignore[attr-defined]
            "/build",
            files=files,
            json_data=instructions,
        )

        # Handle output
        if output_path:
            save_file_output(result, output_path)
            return None
        else:
            return result  # type: ignore[no-any-return]
