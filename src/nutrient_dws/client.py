"""Main client for interacting with the Nutrient Document Web Services API."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Literal, cast

from nutrient_dws.builder.builder import StagedWorkflowBuilder
from nutrient_dws.builder.constant import BuildActions
from nutrient_dws.builder.staged_builders import (
    ApplicableAction,
    BufferOutput,
    ContentOutput,
    JsonContentOutput,
    OutputFormat,
    TypedWorkflowResult,
    WorkflowInitialStage,
    WorkflowWithPartsStage,
)
from nutrient_dws.errors import NutrientError, ValidationError
from nutrient_dws.http import (
    NutrientClientOptions,
    ParseRequestData,
    RedactRequestData,
    RequestConfig,
    SignRequestData,
    SignRequestOptions,
    send_request,
)
from nutrient_dws.inputs import (
    FileInput,
    LocalFileInput,
    is_valid_pdf,
    process_file_input,
)
from nutrient_dws.types.account_info import AccountInfo
from nutrient_dws.types.build_actions import (
    ApplyXfdfActionOptions,
    BaseCreateRedactionsOptions,
    CreateRedactionsStrategyOptionsPreset,
    CreateRedactionsStrategyOptionsRegex,
    CreateRedactionsStrategyOptionsText,
    ImageWatermarkActionOptions,
    SearchPreset,
    TextWatermarkActionOptions,
)
from nutrient_dws.types.build_output import (
    JSONContentOutputOptions,
    Label,
    Metadata,
    OptimizePdf,
    PDFOutputOptions,
    PDFUserPermission,
)
from nutrient_dws.types.create_auth_token import (
    CreateAuthTokenParameters,
    CreateAuthTokenResponse,
)
from nutrient_dws.types.misc import OcrLanguage, PageRange, Pages
from nutrient_dws.types.parse import (
    ParseInstructions,
    ParseMode,
    ParseOutput,
    ParseOutputFormat,
    ParseResponse,
)
from nutrient_dws.types.redact_data import RedactOptions
from nutrient_dws.types.sign_request import CreateDigitalSignature

if TYPE_CHECKING:
    from nutrient_dws.types.input_parts import FilePartOptions


def normalize_page_params(
    pages: PageRange | None = None,
    page_count: int | None = None,
) -> Pages:
    """Normalize page parameters according to the requirements:
    - start and end are inclusive
    - start defaults to 0 (first page)
    - end defaults to -1 (last page)
    - negative end values loop from the end of the document.

    Args:
        pages: The page parameters to normalize
        page_count: The total number of pages in the document (required for negative indices)

    Returns:
        Normalized page parameters
    """
    start = pages.get("start", 0) if pages else 0
    end = pages.get("end", -1) if pages else -1

    # Handle negative end values if page_count is provided
    if page_count is not None and start < 0:
        start = page_count + start

    if page_count is not None and end < 0:
        end = page_count + end

    return {"start": start, "end": end}


class NutrientClient:
    """Main client for interacting with the Nutrient Document Web Services API.

    Example:
        Server-side usage with an API key:

        ```python
        client = NutrientClient(api_key='your_api_key')
        ```

        Client-side usage with token provider:

        ```python
        async def get_token():
            # Your token retrieval logic here
            return 'your-token'

        client = NutrientClient(api_key=get_token)
        ```
    """

    def __init__(
        self,
        api_key: str | Callable[[], str | Awaitable[str]],
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Create a new NutrientClient instance.

        Args:
            api_key: API key or API key getter
            base_url: DWS Base url
            timeout: DWS request timeout

        Raises:
            ValidationError: If options are invalid
        """
        options = NutrientClientOptions(
            apiKey=api_key, baseUrl=base_url, timeout=timeout
        )
        self._validate_options(options)
        self.options = options

    def _validate_options(self, options: NutrientClientOptions) -> None:
        """Validate client options.

        Args:
            options: Configuration options to validate

        Raises:
            ValidationError: If options are invalid
        """
        if not options:
            raise ValidationError("Client options are required")

        if not options.get("apiKey"):
            raise ValidationError("API key is required")

        api_key = options["apiKey"]
        if not (isinstance(api_key, str) or callable(api_key)):
            raise ValidationError(
                "API key must be a string or a function that returns a string"
            )

        base_url = options.get("baseUrl")
        if base_url is not None and not isinstance(base_url, str):
            raise ValidationError("Base URL must be a string")

    async def get_account_info(self) -> AccountInfo:
        """Get account information for the current API key.

        Returns:
            Account information

        Example:
            ```python
            account_info = await client.get_account_info()
            print(account_info['subscriptionType'])
            ```
        """
        response: Any = await send_request(
            {
                "method": "GET",
                "endpoint": "/account/info",
                "data": None,
                "headers": None,
            },
            self.options,
        )

        return cast("AccountInfo", response["data"])

    async def create_token(
        self, params: CreateAuthTokenParameters
    ) -> CreateAuthTokenResponse:
        """Create a new authentication token.

        Args:
            params: Parameters for creating the token

        Returns:
            The created token information

        Example:
            ```python
            token = await client.create_token({
                'allowedOperations': ['annotations_api'],
                'expirationTime': 3600  # 1 hour
            })
            print(token['id'])
            ```
        """
        response: Any = await send_request(
            {
                "method": "POST",
                "endpoint": "/tokens",
                "data": params,
                "headers": None,
            },
            self.options,
        )

        return cast("CreateAuthTokenResponse", response["data"])

    async def delete_token(self, token_id: str) -> None:
        """Delete an authentication token.

        Args:
            token_id: ID of the token to delete

        Example:
            ```python
            await client.delete_token('token-id-123')
            ```
        """
        await send_request(
            {
                "method": "DELETE",
                "endpoint": "/tokens",
                "data": cast("Any", {"id": token_id}),
                "headers": None,
            },
            self.options,
        )

    def workflow(self, override_timeout: int | None = None) -> WorkflowInitialStage:
        r"""Create a new WorkflowBuilder for chaining multiple operations.

        Args:
            override_timeout: Set a custom timeout for the workflow (in milliseconds)

        Returns:
            A new WorkflowBuilder instance

        Example:
            ```python
            result = await client.workflow() \\
                .add_file_part('document.docx') \\
                .apply_action(BuildActions.ocr('english')) \\
                .output_pdf() \\
                .execute()
            ```
        """
        options = self.options.copy()
        if override_timeout is not None:
            options["timeout"] = override_timeout

        return StagedWorkflowBuilder(options)

    def _process_typed_workflow_result(
        self, result: TypedWorkflowResult
    ) -> BufferOutput | ContentOutput | JsonContentOutput:
        """Helper function that takes a TypedWorkflowResult, throws any errors, and returns the specific output type.

        Args:
            result: The TypedWorkflowResult to process

        Returns:
            The specific output type from the result

        Raises:
            NutrientError: If the workflow was not successful or if output is missing
        """
        if not result["success"]:
            # If there are errors, throw the first one
            errors = result.get("errors")
            if errors and len(errors) > 0:
                raise errors[0]["error"]
            # If no specific errors but operation failed
            raise NutrientError(
                "Workflow operation failed without specific error details",
                "WORKFLOW_ERROR",
            )

        # Check if output exists
        output = result.get("output")
        if not output:
            raise NutrientError(
                "Workflow completed successfully but no output was returned",
                "MISSING_OUTPUT",
            )

        return output

    async def sign(
        self,
        pdf: LocalFileInput,
        data: CreateDigitalSignature | None = None,
        options: SignRequestOptions | None = None,
    ) -> BufferOutput:
        """Sign a PDF document.

        **Security Note**: This method only accepts local files (paths, bytes, file objects)
        due to an API limitation. URLs are not supported. For remote files, fetch them first
        with proper URL validation.

        Args:
            pdf: The local PDF file to sign (no URLs)
            data: Signature data
            options: Additional options (image, graphicImage)

        Returns:
            The signed PDF file output

        Example:
            ```python
            # Example 1: Sign a local file
            result = await client.sign('document.pdf', {
                'signatureType': 'cms',
                'flatten': False,
                'cadesLevel': 'b-lt'
            })

            # Example 2: Sign a remote file (fetch first)
            import httpx
            async with httpx.AsyncClient() as http:
                # Validate URL before fetching
                url = 'https://trusted-domain.com/document.pdf'
                if not url.startswith('https://trusted-domain.com/'):
                    raise ValueError('URL not from trusted domain')

                response = await http.get(url, timeout=10.0)
                response.raise_for_status()
                pdf_bytes = response.content

            result = await client.sign(pdf_bytes, {
                'signatureType': 'cms'
            })

            # Access the signed PDF buffer
            pdf_buffer = result['buffer']

            # Get the MIME type of the output
            print(result['mimeType'])  # 'application/pdf'

            # Save the buffer to a file
            with open('signed-document.pdf', 'wb') as f:
                f.write(pdf_buffer)
            ```
        """
        # Process as local file only (no URL support)
        normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Prepare optional files (local files only)
        normalized_image = None
        normalized_graphic_image = None

        if options:
            if "image" in options:
                image = options["image"]
                normalized_image = await process_file_input(image)

            if "graphicImage" in options:
                graphic_image = options["graphicImage"]
                normalized_graphic_image = await process_file_input(graphic_image)

        request_data = {
            "file": normalized_file,
            "data": data,
        }

        if normalized_image:
            request_data["image"] = normalized_image
        if normalized_graphic_image:
            request_data["graphicImage"] = normalized_graphic_image

        response: Any = await send_request(
            {
                "method": "POST",
                "endpoint": "/sign",
                "data": cast("SignRequestData", request_data),
                "headers": None,
            },
            self.options,
        )

        buffer = response["data"]

        return {
            "mimeType": "application/pdf",
            "filename": "output.pdf",
            "buffer": buffer,
        }

    async def watermark_text(
        self,
        file: FileInput,
        text: str,
        options: TextWatermarkActionOptions | None = None,
    ) -> BufferOutput:
        """Add a text watermark to a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The input file to watermark (URLs supported)
            text: The watermark text
            options: Watermark options

        Returns:
            The watermarked document

        Example:
            ```python
            result = await client.watermark_text('document.pdf', 'CONFIDENTIAL', {
                'opacity': 0.5,
                'fontSize': 24
            })

            # Works with URLs too
            result = await client.watermark_text('https://example.com/doc.pdf', 'CONFIDENTIAL')

            # Access the watermarked PDF buffer
            pdf_buffer = result['buffer']

            # Save the buffer to a file
            with open('watermarked-document.pdf', 'wb') as f:
                f.write(pdf_buffer)
            ```
        """
        watermark_action = BuildActions.watermark_text(text, options)

        builder = self.workflow().add_file_part(file, None, [watermark_action])

        result = await builder.output_pdf().execute()
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def watermark_image(
        self,
        file: FileInput,
        image: FileInput,
        options: ImageWatermarkActionOptions | None = None,
    ) -> BufferOutput:
        """Add an image watermark to a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The input file to watermark (URLs supported)
            image: The watermark image. Can be a file path (string or Path),
                bytes, file-like object, or a URL to a remote image.
            options: Watermark options

        Returns:
            The watermarked document

        Example:
            ```python
            # Using a local file path
            result = await client.watermark_image('document.pdf', 'watermark.png', {
                'opacity': 0.5
            })

            # Using a Path object
            from pathlib import Path
            result = await client.watermark_image('document.pdf', Path('logo.png'))

            # Using bytes (e.g., from a database or API)
            with open('logo.png', 'rb') as f:
                image_bytes = f.read()
            result = await client.watermark_image('document.pdf', image_bytes)

            # Using a remote URL
            result = await client.watermark_image(
                'document.pdf',
                'https://example.com/logo.png'
            )

            # Access the watermarked PDF buffer
            pdf_buffer = result['buffer']
            ```
        """
        watermark_action = BuildActions.watermark_image(image, options)

        builder = self.workflow().add_file_part(file, None, [watermark_action])

        result = await builder.output_pdf().execute()
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def convert(
        self,
        file: FileInput,
        target_format: OutputFormat,
    ) -> BufferOutput | ContentOutput | JsonContentOutput:
        """Convert a document to a different format.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The input file to convert (URLs supported)
            target_format: The target format to convert to

        Returns:
            The specific output type based on the target format

        Example:
            ```python
            # Convert DOCX to PDF
            pdf_result = await client.convert('document.docx', 'pdf')
            pdf_buffer = pdf_result['buffer']

            # Convert PDF to image
            image_result = await client.convert('document.pdf', 'png')
            png_buffer = image_result['buffer']

            # Convert to HTML
            html_result = await client.convert('document.pdf', 'html')
            html_content = html_result['content']

            # Works with URLs
            pdf_result = await client.convert('https://example.com/document.docx', 'pdf')
            ```
        """
        builder = self.workflow().add_file_part(file)

        if target_format == "pdf":
            result = await builder.output_pdf().execute()
        elif target_format == "pdfa":
            result = await builder.output_pdfa().execute()
        elif target_format == "pdfua":
            result = await builder.output_pdfua().execute()
        elif target_format == "docx":
            result = await builder.output_office("docx").execute()
        elif target_format == "xlsx":
            result = await builder.output_office("xlsx").execute()
        elif target_format == "pptx":
            result = await builder.output_office("pptx").execute()
        elif target_format == "html":
            result = await builder.output_html("page").execute()
        elif target_format == "markdown":
            result = await builder.output_markdown().execute()
        elif target_format in ["png", "jpeg", "jpg", "webp"]:
            result = await builder.output_image(
                cast("Literal['png', 'jpeg', 'jpg', 'webp']", target_format),
                {"dpi": 300},
            ).execute()
        else:
            raise ValidationError(f"Unsupported target format: {target_format}")

        return self._process_typed_workflow_result(result)

    async def ocr(
        self,
        file: FileInput,
        language: OcrLanguage | list[OcrLanguage],
    ) -> BufferOutput:
        """Perform OCR (Optical Character Recognition) on a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The input file to perform OCR on
            language: The language(s) to use for OCR. Can be a single language
                or a list of languages for multi-language documents.

        Returns:
            The OCR result

        Example:
            ```python
            # Single language OCR
            result = await client.ocr('scanned-document.pdf', 'english')

            # Multi-language OCR for documents with mixed content
            result = await client.ocr('multilang-document.pdf', ['english', 'german', 'french'])

            # Access the OCR-processed PDF buffer
            pdf_buffer = result['buffer']
            ```
        """
        ocr_action = BuildActions.ocr(language)

        builder = self.workflow().add_file_part(file, None, [ocr_action])

        result = await builder.output_pdf().execute()
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def extract_text(
        self,
        file: FileInput,
        pages: PageRange | None = None,
    ) -> JsonContentOutput:
        """Extract text content from a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The file to extract text from (URLs supported)
            pages: Optional page range to extract text from

        Returns:
            The extracted text data

        Example:
            ```python
            result = await client.extract_text('document.pdf')
            print(result['data'])

            # Extract text from specific pages
            result = await client.extract_text('document.pdf', {'start': 0, 'end': 2})

            # Works with URLs
            result = await client.extract_text('https://example.com/doc.pdf')

            # Access the extracted text content
            text_content = result['data']['pages'][0]['plainText']
            ```
        """
        normalized_pages = normalize_page_params(pages) if pages else None

        part_options = (
            cast("FilePartOptions", {"pages": normalized_pages})
            if normalized_pages
            else None
        )

        result = (
            await self.workflow()
            .add_file_part(file, part_options)
            .output_json(
                cast("JSONContentOutputOptions", {"plainText": True, "tables": False})
            )
            .execute()
        )

        return cast("JsonContentOutput", self._process_typed_workflow_result(result))

    async def extract_table(
        self,
        file: FileInput,
        pages: PageRange | None = None,
    ) -> JsonContentOutput:
        """Extract table content from a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The file to extract table from (URLs supported)
            pages: Optional page range to extract tables from

        Returns:
            The extracted table data

        Example:
            ```python
            result = await client.extract_table('document.pdf')

            # Works with URLs
            result = await client.extract_table('https://example.com/doc.pdf')

            # Access the extracted tables
            tables = result['data']['pages'][0]['tables']

            # Process the first table if available
            if tables and len(tables) > 0:
                first_table = tables[0]
                print(f"Table has {len(first_table['rows'])} rows")
            ```
        """
        normalized_pages = normalize_page_params(pages) if pages else None

        part_options = (
            cast("FilePartOptions", {"pages": normalized_pages})
            if normalized_pages
            else None
        )

        result = (
            await self.workflow()
            .add_file_part(file, part_options)
            .output_json(
                cast("JSONContentOutputOptions", {"plainText": False, "tables": True})
            )
            .execute()
        )

        return cast("JsonContentOutput", self._process_typed_workflow_result(result))

    async def extract_key_value_pairs(
        self,
        file: FileInput,
        pages: PageRange | None = None,
    ) -> JsonContentOutput:
        """Extract key value pair content from a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The file to extract KVPs from (URLs supported)
            pages: Optional page range to extract KVPs from

        Returns:
            The extracted KVPs data

        Example:
            ```python
            result = await client.extract_key_value_pairs('document.pdf')

            # Works with URLs
            result = await client.extract_key_value_pairs('https://example.com/doc.pdf')

            # Access the extracted key-value pairs
            kvps = result['data']['pages'][0]['keyValuePairs']

            # Process the key-value pairs
            if kvps and len(kvps) > 0:
                for kvp in kvps:
                    print(f"Key: {kvp['key']}, Value: {kvp['value']}")
            ```
        """
        normalized_pages = normalize_page_params(pages) if pages else None

        part_options = (
            cast("FilePartOptions", {"pages": normalized_pages})
            if normalized_pages
            else None
        )

        result = (
            await self.workflow()
            .add_file_part(file, part_options)
            .output_json(
                cast(
                    "JSONContentOutputOptions",
                    {"plainText": False, "tables": False, "keyValuePairs": True},
                )
            )
            .execute()
        )

        return cast("JsonContentOutput", self._process_typed_workflow_result(result))

    async def parse(
        self,
        file: LocalFileInput,
        mode: ParseMode = "structure",
        output_format: ParseOutputFormat = "spatial",
    ) -> ParseResponse:
        """Parse a document using the Data Extraction API (`/extraction/parse`).

        The Data Extraction API is billed against **extraction credits**, which
        are a separate billing bucket from the **processor API credits**
        consumed by `/build`, `/sign`, OCR, and other Processor API endpoints.

        Per-page extraction-credit costs by mode:

        - `text`: 1 extraction credit / page — fast Markdown extraction from
          born-digital documents (no OCR or AI).
        - `structure`: 1.5 extraction credits / page — OCR-based spatial
          extraction with bounding boxes (default).
        - `understand`: 9 extraction credits / page — AI-augmented layout
          analysis, table detection, and semantic classification.
        - `agentic`: 18 extraction credits / page — VLM-augmented extraction
          building on `understand` mode.

        Output format selects the shape under `response.output`:

        - `spatial` (default): `output.elements` — typed elements (paragraph,
          table, formula, picture, keyValueRegion, handwriting) with bounds,
          confidence, and reading order.
        - `markdown`: `output.markdown` — a whole-document Markdown string,
          well suited for RAG / search indexing pipelines.

        **Security note**: this method only accepts local files (paths, bytes,
        file objects) because the underlying API surface for this endpoint is
        multipart-only. For remote inputs, fetch them client-side with
        appropriate URL validation first.

        Args:
            file: The document to parse (local files only — paths, bytes, or
                file-like objects).
            mode: Processing mode. See per-mode credit costs above. Defaults
                to `"structure"`.
            output_format: Output shape — `"spatial"` for typed elements or
                `"markdown"` for a Markdown document. Defaults to
                `"spatial"`.

        Returns:
            The full parse response envelope, including `output`, `metrics`,
            `usage` (the extraction-credit accounting), and `configuration`.

        Example:
            ```python
            # Spatial elements with full layout analysis (9 extraction credits / page)
            response = await client.parse('contract.pdf', mode='understand')
            for element in response['output']['elements']:
                if element['type'] == 'table':
                    print(element['rowCount'], element['columnCount'])

            # Whole-document Markdown from a born-digital PDF (1 extraction credit / page)
            response = await client.parse(
                'report.pdf', mode='text', output_format='markdown'
            )
            print(response['output']['markdown'])

            # Inspect billing
            usage = response['usage']['data_extraction_credits']
            print(f"Cost: {usage['cost']} extraction credits "
                  f"(remaining: {usage['remainingCredits']})")
            ```
        """
        # Multipart-only endpoint; only local file inputs are supported.
        normalized_file = await process_file_input(file)

        instructions: ParseInstructions = {
            "mode": mode,
            "output": cast("ParseOutput", {"format": output_format}),
        }

        request_data: ParseRequestData = {
            "file": normalized_file,
            "instructions": instructions,
        }

        config = RequestConfig(
            method="POST",
            endpoint="/extraction/parse",
            data=request_data,
            headers=None,
        )

        response: Any = await send_request(config, self.options)
        return cast("ParseResponse", response["data"])

    async def set_page_labels(
        self,
        pdf: FileInput,
        labels: list[Label],
    ) -> BufferOutput:
        """Set page labels for a PDF document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        PDF validation is performed server-side.

        Args:
            pdf: The PDF file to modify (URLs supported)
            labels: Array of label objects with pages and label properties

        Returns:
            The document with updated page labels

        Example:
            ```python
            result = await client.set_page_labels('document.pdf', [
                {'pages': [0, 1, 2], 'label': 'Cover'},
                {'pages': [3, 4, 5], 'label': 'Chapter 1'}
            ])

            # Works with URLs
            result = await client.set_page_labels('https://example.com/doc.pdf', labels)
            ```
        """
        # No client-side PDF validation - let server handle it
        result = (
            await self.workflow()
            .add_file_part(pdf)
            .output_pdf(cast("PDFOutputOptions", {"labels": labels}))
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def password_protect(
        self,
        file: FileInput,
        user_password: str,
        owner_password: str,
        permissions: list[PDFUserPermission] | None = None,
    ) -> BufferOutput:
        """Password protect a PDF document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            file: The file to protect (URLs supported)
            user_password: Password required to open the document
            owner_password: Password required to modify the document
            permissions: Optional array of permissions granted when opened with user password

        Returns:
            The password-protected document

        Example:
            ```python
            result = await client.password_protect('document.pdf', 'user123', 'owner456')

            # Or with specific permissions:
            result = await client.password_protect(
                'document.pdf',
                'user123',
                'owner456',
                ['printing', 'extract_accessibility']
            )
            ```
        """
        pdf_options: PDFOutputOptions = {
            "user_password": user_password,
            "owner_password": owner_password,
        }

        if permissions:
            pdf_options["user_permissions"] = permissions

        result = (
            await self.workflow().add_file_part(file).output_pdf(pdf_options).execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def set_metadata(
        self,
        pdf: FileInput,
        metadata: Metadata,
    ) -> BufferOutput:
        """Set metadata for a PDF document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        PDF validation is performed server-side.

        Args:
            pdf: The PDF file to modify (URLs supported)
            metadata: The metadata to set (title and/or author)

        Returns:
            The document with updated metadata

        Example:
            ```python
            result = await client.set_metadata('document.pdf', {
                'title': 'My Document',
                'author': 'John Doe'
            })

            # Works with URLs
            result = await client.set_metadata('https://example.com/doc.pdf', metadata)
            ```
        """
        # No client-side PDF validation - let server handle it
        result = (
            await self.workflow()
            .add_file_part(pdf)
            .output_pdf(cast("PDFOutputOptions", {"metadata": metadata}))
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def apply_instant_json(
        self,
        pdf: FileInput,
        instant_json_file: FileInput,
    ) -> BufferOutput:
        """Apply Instant JSON to a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        PDF validation is performed server-side.

        Args:
            pdf: The PDF file to modify (URLs supported)
            instant_json_file: The Instant JSON file to apply (URLs supported)

        Returns:
            The modified document

        Example:
            ```python
            result = await client.apply_instant_json('document.pdf', 'annotations.json')

            # Works with URLs
            result = await client.apply_instant_json(
                'https://example.com/doc.pdf',
                'https://example.com/annotations.json'
            )
            ```
        """
        # No client-side PDF validation - let server handle it
        apply_json_action = BuildActions.apply_instant_json(instant_json_file)

        result = (
            await self.workflow()
            .add_file_part(pdf, None, [apply_json_action])
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def apply_xfdf(
        self,
        pdf: FileInput,
        xfdf_file: FileInput,
        options: ApplyXfdfActionOptions | None = None,
    ) -> BufferOutput:
        """Apply XFDF to a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        PDF validation is performed server-side.

        Args:
            pdf: The PDF file to modify (URLs supported)
            xfdf_file: The XFDF file to apply (URLs supported)
            options: Optional settings for applying XFDF

        Returns:
            The modified document

        Example:
            ```python
            result = await client.apply_xfdf('document.pdf', 'annotations.xfdf')

            # With options:
            result = await client.apply_xfdf(
                'document.pdf', 'annotations.xfdf',
                {'ignorePageRotation': True, 'richTextEnabled': False}
            )

            # Works with URLs
            result = await client.apply_xfdf(
                'https://example.com/doc.pdf',
                'https://example.com/annotations.xfdf'
            )
            ```
        """
        # No client-side PDF validation - let server handle it
        apply_xfdf_action = BuildActions.apply_xfdf(xfdf_file, options)

        result = (
            await self.workflow()
            .add_file_part(pdf, None, [apply_xfdf_action])
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def merge(self, files: list[FileInput]) -> BufferOutput:
        """Merge multiple documents into a single document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            files: The files to merge (URLs supported)

        Returns:
            The merged document

        Example:
            ```python
            result = await client.merge(['doc1.pdf', 'doc2.pdf', 'doc3.pdf'])

            # Works with URLs
            result = await client.merge([
                'https://example.com/doc1.pdf',
                'doc2.pdf',
                'https://example.com/doc3.pdf'
            ])

            # Access the merged PDF buffer
            pdf_buffer = result['buffer']
            ```
        """
        if not files or len(files) < 2:
            raise ValidationError("At least 2 files are required for merge operation")

        builder = self.workflow()

        # Add first file
        workflow_builder = builder.add_file_part(files[0])

        # Add remaining files
        for file in files[1:]:
            workflow_builder = workflow_builder.add_file_part(file)

        result = await workflow_builder.output_pdf().execute()
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def flatten(
        self,
        pdf: FileInput,
        annotation_ids: list[str | int] | None = None,
    ) -> BufferOutput:
        """Flatten annotations in a PDF document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        PDF validation is performed server-side.

        Args:
            pdf: The PDF file to flatten
            annotation_ids: Optional list of specific annotation IDs to flatten.
                If not provided, all annotations are flattened. IDs can be
                strings or integers.

        Returns:
            The flattened document

        Example:
            ```python
            # Flatten all annotations
            result = await client.flatten('annotated-document.pdf')

            # Flatten specific annotations by string ID
            result = await client.flatten('annotated-document.pdf', ['annotation1', 'annotation2'])

            # Flatten specific annotations by integer ID
            result = await client.flatten('annotated-document.pdf', [1, 2, 3])

            # Mix of string and integer IDs
            result = await client.flatten('annotated-document.pdf', ['note1', 2, 'highlight3'])
            ```
        """
        # No client-side PDF validation - let server handle it
        flatten_action = BuildActions.flatten(annotation_ids)

        result = (
            await self.workflow()
            .add_file_part(pdf, None, [flatten_action])
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def create_redactions_ai(
        self,
        pdf: LocalFileInput,
        criteria: str,
        redaction_state: Literal["stage", "apply"] = "stage",
        pages: PageRange | None = None,
        options: RedactOptions | None = None,
    ) -> BufferOutput:
        """Use AI to redact sensitive information in a document.

        **Security Note**: This method only accepts local files (direct API call).
        For remote files, fetch them first with proper validation.

        Args:
            pdf: The PDF file to redact (local files only, no URLs)
            criteria: AI redaction criteria
            redaction_state: Whether to stage or apply redactions (default: 'stage')
            pages: Optional pages to redact
            options: Optional redaction options

        Returns:
            The redacted document

        Example:
            ```python
            # Stage redactions
            result = await client.create_redactions_ai(
                'document.pdf',
                'Remove all emails'
            )

            # Apply redactions immediately
            result = await client.create_redactions_ai(
                'document.pdf',
                'Remove all PII',
                'apply'
            )
            ```
        """
        # Process local files only
        normalized_file = await process_file_input(pdf)

        # Use pages directly - no page count computation needed
        normalized_pages = normalize_page_params(pages) if pages else None

        document_data: dict[str, Any] = {
            "file": "file",
        }

        if normalized_pages:
            document_data["pages"] = normalized_pages

        documents = [document_data]

        request_data = {
            "data": {
                "documents": documents,
                "criteria": criteria,
                "redaction_state": redaction_state,
            },
            "file": normalized_file,
            "fileKey": "file",
        }

        if options:
            request_data["data"]["options"] = options  # type: ignore

        config = RequestConfig(
            method="POST",
            data=cast("RedactRequestData", request_data),
            endpoint="/ai/redact",
            headers=None,
        )

        response: Any = await send_request(
            config,
            self.options,
        )

        buffer = response["data"]

        return {
            "mimeType": "application/pdf",
            "filename": "output.pdf",
            "buffer": buffer,
        }

    async def create_redactions_preset(
        self,
        pdf: FileInput,
        preset: SearchPreset,
        redaction_state: Literal["stage", "apply"] = "stage",
        pages: PageRange | None = None,
        preset_options: CreateRedactionsStrategyOptionsPreset | None = None,
        options: BaseCreateRedactionsOptions | None = None,
    ) -> BufferOutput:
        """Create redaction annotations based on a preset pattern.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Supports negative page indices (-1 = last page).

        Args:
            pdf: The PDF file to create redactions in (URLs supported)
            preset: The preset pattern to search for (e.g., 'email-address', 'social-security-number')
            redaction_state: Whether to stage or apply redactions (default: 'stage')
            pages: Optional page range to create redactions in (supports negative indices)
            preset_options: Optional settings for the preset strategy
            options: Optional settings for creating redactions

        Returns:
            The document with redaction annotations

        Example:
            ```python
            result = await client.create_redactions_preset('document.pdf', 'email-address')

            # Works with URLs
            result = await client.create_redactions_preset(
                'https://example.com/doc.pdf',
                'social-security-number'
            )
            ```
        """
        # No client-side PDF validation - let server handle it
        # Use negative indices: -1 means "to end", calculate limit accordingly
        start = pages.get("start", 0) if pages else 0
        end = pages.get("end", -1) if pages else -1

        # Prepare strategy options with pages
        strategy_options = preset_options.copy() if preset_options else {}
        strategy_options["start"] = start
        # If end is -1, omit limit (search to end); otherwise calculate count
        if end != -1:
            strategy_options["limit"] = end - start + 1

        create_redactions_action = BuildActions.create_redactions_preset(
            preset, options, strategy_options
        )
        actions: list[ApplicableAction] = [create_redactions_action]

        if redaction_state == "apply":
            actions.append(BuildActions.apply_redactions())

        result = (
            await self.workflow()
            .add_file_part(pdf, None, actions)
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def create_redactions_regex(
        self,
        pdf: FileInput,
        regex: str,
        redaction_state: Literal["stage", "apply"] = "stage",
        pages: PageRange | None = None,
        regex_options: CreateRedactionsStrategyOptionsRegex | None = None,
        options: BaseCreateRedactionsOptions | None = None,
    ) -> BufferOutput:
        r"""Create redaction annotations based on a regular expression.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Supports negative page indices (-1 = last page).

        Args:
            pdf: The PDF file to create redactions in (URLs supported)
            regex: The regular expression to search for
            redaction_state: Whether to stage or apply redactions (default: 'stage')
            pages: Optional page range to create redactions in (supports negative indices)
            regex_options: Optional settings for the regex strategy
            options: Optional settings for creating redactions

        Returns:
            The document with redaction annotations

        Example:
            ```python
            result = await client.create_redactions_regex('document.pdf', r'Account:\s*\d{8,12}')

            # Works with URLs
            result = await client.create_redactions_regex(
                'https://example.com/doc.pdf',
                r'\b\d{3}-\d{2}-\d{4}\b'
            )
            ```
        """
        # No client-side PDF validation - let server handle it
        # Use negative indices: -1 means "to end", calculate limit accordingly
        start = pages.get("start", 0) if pages else 0
        end = pages.get("end", -1) if pages else -1

        # Prepare strategy options with pages
        strategy_options = regex_options.copy() if regex_options else {}
        strategy_options["start"] = start
        # If end is -1, omit limit (search to end); otherwise calculate count
        if end != -1:
            strategy_options["limit"] = end - start + 1

        create_redactions_action = BuildActions.create_redactions_regex(
            regex, options, strategy_options
        )
        actions: list[ApplicableAction] = [create_redactions_action]

        if redaction_state == "apply":
            actions.append(BuildActions.apply_redactions())

        result = (
            await self.workflow()
            .add_file_part(pdf, None, actions)
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def create_redactions_text(
        self,
        pdf: FileInput,
        text: str,
        redaction_state: Literal["stage", "apply"] = "stage",
        pages: PageRange | None = None,
        text_options: CreateRedactionsStrategyOptionsText | None = None,
        options: BaseCreateRedactionsOptions | None = None,
    ) -> BufferOutput:
        """Create redaction annotations based on text.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Supports negative page indices (-1 = last page).

        Args:
            pdf: The PDF file to create redactions in (URLs supported)
            text: The text to search for
            redaction_state: Whether to stage or apply redactions (default: 'stage')
            pages: Optional page range to create redactions in (supports negative indices)
            text_options: Optional settings for the text strategy
            options: Optional settings for creating redactions

        Returns:
            The document with redaction annotations

        Example:
            ```python
            result = await client.create_redactions_text('document.pdf', 'email@example.com')

            # Works with URLs
            result = await client.create_redactions_text(
                'https://example.com/doc.pdf',
                'CONFIDENTIAL'
            )
            ```
        """
        # No client-side PDF validation - let server handle it
        # Use negative indices: -1 means "to end", calculate limit accordingly
        start = pages.get("start", 0) if pages else 0
        end = pages.get("end", -1) if pages else -1

        # Prepare strategy options with pages
        strategy_options = text_options.copy() if text_options else {}
        strategy_options["start"] = start
        # If end is -1, omit limit (search to end); otherwise calculate count
        if end != -1:
            strategy_options["limit"] = end - start + 1

        create_redactions_action = BuildActions.create_redactions_text(
            text, options, strategy_options
        )
        actions: list[ApplicableAction] = [create_redactions_action]

        if redaction_state == "apply":
            actions.append(BuildActions.apply_redactions())

        result = (
            await self.workflow()
            .add_file_part(pdf, None, actions)
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def apply_redactions(self, pdf: FileInput) -> BufferOutput:
        """Apply staged redaction into the PDF.

        **Note**: URLs are passed to the server for secure server-side fetching.

        Args:
            pdf: The PDF file with redaction annotations to apply (URLs supported)

        Returns:
            The document with applied redactions

        Example:
            ```python
            # Stage redactions from a createRedaction Method:
            staged_result = await client.create_redactions_text(
                'document.pdf',
                'email@example.com',
                'stage'
            )

            result = await client.apply_redactions(staged_result['buffer'])
            ```
        """
        apply_redactions_action = BuildActions.apply_redactions()

        # No client-side PDF validation - let server handle it
        result = (
            await self.workflow()
            .add_file_part(pdf, None, [apply_redactions_action])
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def rotate(
        self,
        pdf: FileInput,
        angle: Literal[90, 180, 270],
        pages: PageRange | None = None,
    ) -> BufferOutput:
        """Rotate pages in a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Supports negative page indices (-1 = last page, -2 = second-to-last, etc.).

        Args:
            pdf: The PDF file to rotate (URLs supported)
            angle: Rotation angle (90, 180, or 270 degrees)
            pages: Optional page range to rotate (supports negative indices)

        Returns:
            The entire document with specified pages rotated

        Example:
            ```python
            # Rotate entire document
            result = await client.rotate('document.pdf', 90)

            # Rotate specific pages
            result = await client.rotate('document.pdf', 90, {'start': 1, 'end': 3})

            # Rotate with URL
            result = await client.rotate('https://example.com/doc.pdf', 90)

            # Rotate last 3 pages using negative indices
            result = await client.rotate('document.pdf', 90, {'start': -3, 'end': -1})
            ```
        """
        rotate_action = BuildActions.rotate(angle)
        workflow = self.workflow()

        if pages:
            # Use negative index support (-1 = last page)
            # No need for client-side PDF parsing
            start = pages.get("start", 0)
            end = pages.get("end", -1)

            # Add pages before the rotation range
            if start != 0:
                part_options = cast(
                    "FilePartOptions",
                    {"pages": {"start": 0, "end": start - 1}},
                )
                workflow = workflow.add_file_part(pdf, part_options)

            # Add the rotation range
            part_options = cast(
                "FilePartOptions", {"pages": {"start": start, "end": end}}
            )
            workflow = workflow.add_file_part(pdf, part_options, [rotate_action])

            # Add pages after the rotation range (unless end is -1)
            if end != -1:
                part_options = cast(
                    "FilePartOptions",
                    {"pages": {"start": end + 1, "end": -1}},
                )
                workflow = workflow.add_file_part(pdf, part_options)
        else:
            # If no pages specified, rotate the entire document
            workflow = workflow.add_file_part(pdf, None, [rotate_action])

        result = await workflow.output_pdf().execute()
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def add_page(
        self, pdf: FileInput, count: int = 1, index: int | None = None
    ) -> BufferOutput:
        """Add blank pages to a document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Index must be non-negative. If the index exceeds the document's page count,
        the server will return an error.

        Args:
            pdf: The PDF file to add pages to (URLs supported)
            count: The number of blank pages to add
            index: Optional index where to add the blank pages (0-based). If not provided, pages are added at the end.
                   Must be non-negative.

        Returns:
            The document with added pages

        Example:
            ```python
            # Add 2 blank pages at the end
            result = await client.add_page('document.pdf', 2)

            # Add 1 blank page after the first page (at index 1)
            result = await client.add_page('document.pdf', 1, 1)

            # Works with URLs
            result = await client.add_page('https://example.com/doc.pdf', 3)
            ```
        """
        # No client-side PDF validation - let server handle it
        # If no index is provided, simply add pages at the end
        if index is None:
            builder = self.workflow()
            builder.add_file_part(pdf)
            builder = builder.add_new_page({"pageCount": count})
            result = await builder.output_pdf().execute()
        else:
            # Validate index is non-negative
            if index < 0:
                raise ValidationError(f"Index must be non-negative, got: {index}")

            builder = self.workflow()

            # Add pages before the specified index
            if index > 0:
                before_pages = normalize_page_params({"start": 0, "end": index - 1})
                part_options = cast("FilePartOptions", {"pages": before_pages})
                builder = builder.add_file_part(pdf, part_options)

            # Add the blank pages
            builder = builder.add_new_page({"pageCount": count})

            # Add pages after the specified index (use -1 for "to end")
            after_pages = normalize_page_params({"start": index, "end": -1})
            part_options = cast("FilePartOptions", {"pages": after_pages})
            builder = builder.add_file_part(pdf, part_options)

            result = await builder.output_pdf().execute()

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def split(
        self, pdf: FileInput, page_ranges: list[PageRange]
    ) -> list[BufferOutput]:
        """Split a PDF document into multiple parts based on page ranges.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Supports negative page indices (-1 = last page).

        Args:
            pdf: The PDF file to split (URLs supported)
            page_ranges: Array of page ranges to extract (supports negative indices)

        Returns:
            An array of PDF documents, one for each page range

        Example:
            ```python
            results = await client.split('document.pdf', [
                {'start': 0, 'end': 2},  # Pages 0, 1, 2
                {'start': 3, 'end': 5}   # Pages 3, 4, 5
            ])

            # Works with URLs and negative indices
            results = await client.split('https://example.com/doc.pdf', [
                {'start': 0, 'end': 4},    # First 5 pages
                {'start': 5, 'end': -1}    # Remaining pages to end
            ])
            ```
        """
        if not page_ranges or len(page_ranges) == 0:
            raise ValidationError("At least one page range is required for splitting")

        # No client-side PDF validation - server handles it
        # Use negative indices directly - no page count needed
        import asyncio
        from typing import cast as typing_cast

        async def create_split_pdf(page_range: PageRange) -> BufferOutput:
            builder = self.workflow()
            # Normalize pages to ensure we have start/end
            normalized = normalize_page_params(page_range)
            part_options = cast("FilePartOptions", {"pages": normalized})
            builder = builder.add_file_part(pdf, part_options)
            result = await builder.output_pdf().execute()
            return typing_cast(
                "BufferOutput", self._process_typed_workflow_result(result)
            )

        # Execute all workflows in parallel and process the results
        tasks = [create_split_pdf(page_range) for page_range in page_ranges]
        results = await asyncio.gather(*tasks)

        return results

    async def duplicate_pages(
        self, pdf: FileInput, page_indices: list[int]
    ) -> BufferOutput:
        """Create a new PDF containing only the specified pages in the order provided.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Supports negative page indices (-1 = last page, -2 = second-to-last, etc.).

        Args:
            pdf: The PDF file to extract pages from (URLs supported)
            page_indices: Array of page indices to include in the new PDF (0-based)
                         Negative indices count from the end of the document (e.g., -1 is the last page)

        Returns:
            A new document with only the specified pages

        Example:
            ```python
            # Create a new PDF with only the first and third pages
            result = await client.duplicate_pages('document.pdf', [0, 2])

            # Create a new PDF with pages in a different order
            result = await client.duplicate_pages('document.pdf', [2, 0, 1])

            # Create a new PDF with duplicated pages
            result = await client.duplicate_pages('document.pdf', [0, 0, 1, 1, 0])

            # Create a new PDF with the first and last pages
            result = await client.duplicate_pages('document.pdf', [0, -1])

            # Works with URLs
            result = await client.duplicate_pages('https://example.com/doc.pdf', [0, -1])
            ```
        """
        if not page_indices or len(page_indices) == 0:
            raise ValidationError("At least one page index is required for duplication")

        # No client-side PDF validation - let server handle it
        # Use negative indices directly - server interprets them
        builder = self.workflow()

        # Add each page in the order specified
        for page_index in page_indices:
            page_range = normalize_page_params({"start": page_index, "end": page_index})
            part_options = cast("FilePartOptions", {"pages": page_range})
            builder = builder.add_file_part(pdf, part_options)

        result = await cast("WorkflowWithPartsStage", builder).output_pdf().execute()
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def delete_pages(
        self, pdf: FileInput, page_indices: list[int]
    ) -> BufferOutput:
        """Delete pages from a PDF document.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        Supports negative page indices (-1 = last page, -2 = second-to-last, etc.).

        Args:
            pdf: The PDF file to modify (URLs supported)
            page_indices: Array of page indices to delete (0-based)
                         Negative indices count from the end of the document (e.g., -1 is the last page)

        Returns:
            The document with deleted pages

        Example:
            ```python
            # Delete second and fourth pages
            result = await client.delete_pages('document.pdf', [1, 3])

            # Delete the last page
            result = await client.delete_pages('document.pdf', [-1])

            # Delete the first and last two pages
            result = await client.delete_pages('document.pdf', [0, -1, -2])

            # Works with URLs
            result = await client.delete_pages('https://example.com/doc.pdf', [0, -1])
            ```
        """
        if not page_indices or len(page_indices) == 0:
            raise ValidationError("At least one page index is required for deletion")

        # No client-side PDF validation or page count computation
        # Use negative indices directly - server interprets them
        # Remove duplicates and sort the delete indices
        delete_indices = sorted(set(page_indices))

        builder = self.workflow()

        positive_deletes = [i for i in delete_indices if i >= 0]
        negative_deletes = [i for i in delete_indices if i < 0]

        page_ranges = []
        current_page = 0

        # Build keep ranges for positive delete indices
        for delete_index in positive_deletes:
            if current_page < delete_index:
                page_ranges.append(
                    normalize_page_params(
                        {"start": current_page, "end": delete_index - 1}
                    )
                )
            current_page = delete_index + 1

        if negative_deletes:
            # Add keep range from current position up to just before the first negative delete
            trailing_end = negative_deletes[0] - 1  # e.g. -1 -> -2, -2 -> -3
            page_ranges.append(
                normalize_page_params({"start": current_page, "end": trailing_end})
            )
            # Add keep ranges between consecutive negative delete indices
            for i in range(len(negative_deletes) - 1):
                between_start = negative_deletes[i] + 1
                between_end = negative_deletes[i + 1] - 1
                if between_start <= between_end:
                    page_ranges.append(
                        normalize_page_params(
                            {"start": between_start, "end": between_end}
                        )
                    )
            # Add keep range after the last negative delete, if it isn't the last page
            if negative_deletes[-1] != -1:
                page_ranges.append(
                    normalize_page_params(
                        {"start": negative_deletes[-1] + 1, "end": -1}
                    )
                )
        else:
            # All deletes are positive: keep remaining pages to end of document
            page_ranges.append(
                normalize_page_params({"start": current_page, "end": -1})
            )

        if len(page_ranges) == 0:
            raise ValidationError("You cannot delete all pages from a document")

        for page_range in page_ranges:
            part_options = cast("FilePartOptions", {"pages": page_range})
            builder = builder.add_file_part(pdf, part_options)

        result = await cast("WorkflowWithPartsStage", builder).output_pdf().execute()
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def optimize(
        self,
        pdf: FileInput,
        options: OptimizePdf | None = None,
    ) -> BufferOutput:
        """Optimize a PDF document for size reduction.
        This is a convenience method that uses the workflow builder.

        **Note**: URLs are passed to the server for secure server-side fetching.
        PDF validation is performed server-side.

        Args:
            pdf: The PDF file to optimize (URLs supported)
            options: Optimization options

        Returns:
            The optimized document

        Example:
            ```python
            result = await client.optimize('large-document.pdf', {
                'grayscaleImages': True,
                'mrcCompression': True,
                'imageOptimizationQuality': 2
            })

            # Works with URLs
            result = await client.optimize('https://example.com/large.pdf')
            ```
        """
        # No client-side PDF validation - let server handle it
        if options is None:
            options = {"imageOptimizationQuality": 2}

        result = (
            await self.workflow()
            .add_file_part(pdf)
            .output_pdf(cast("PDFOutputOptions", {"optimize": options}))
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))
