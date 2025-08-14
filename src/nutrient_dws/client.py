"""Main client for interacting with the Nutrient Document Web Services API."""
from typing import Any, Literal, Optional, Union, Dict, List, cast

from nutrient_dws.builder.builder import StagedWorkflowBuilder
from nutrient_dws.builder.constant import BuildActions
from nutrient_dws.builder.staged_builders import (
    BufferOutput,
    ContentOutput,
    JsonContentOutput,
    OutputFormat,
    TypedWorkflowResult,
    WorkflowInitialStage,
)
from nutrient_dws.errors import NutrientError, ValidationError
from nutrient_dws.http import NutrientClientOptions, send_request
from nutrient_dws.inputs import (
    FileInput,
    get_pdf_page_count,
    is_remote_file_input,
    is_valid_pdf,
    process_file_input,
    process_remote_file_input,
)
from nutrient_dws.types.build_output import PDFUserPermission, Metadata
from nutrient_dws.types.create_auth_token import CreateAuthTokenParameters, CreateAuthTokenResponse
from nutrient_dws.types.misc import Pages, PageRange, OcrLanguage
from nutrient_dws.types.sign_request import CreateDigitalSignature


def normalize_page_params(
    pages: Optional[PageRange] = None,
    page_count: Optional[int] = None,
) -> Pages:
    """Normalize page parameters according to the requirements:
    - start and end are inclusive
    - start defaults to 0 (first page)
    - end defaults to -1 (last page)
    - negative end values loop from the end of the document

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
        Server-side usage with API key:

        ```python
        client = NutrientClient({
            'apiKey': 'your-secret-api-key'
        })
        ```

        Client-side usage with token provider:

        ```python
        async def get_token():
            # Your token retrieval logic here
            return 'your-token'

        client = NutrientClient({
            'apiKey': get_token
        })
        ```
    """

    def __init__(self, options: NutrientClientOptions) -> None:
        """Create a new NutrientClient instance.

        Args:
            options: Configuration options for the client

        Raises:
            ValidationError: If options are invalid
        """
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
        if not isinstance(api_key, (str, type(lambda: None))):
            raise ValidationError("API key must be a string or a function that returns a string")

        base_url = options.get("baseUrl")
        if base_url is not None and not isinstance(base_url, str):
            raise ValidationError("Base URL must be a string")

    async def get_account_info(self) -> dict[str, Any]:
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

        return cast(dict[str, Any], response["data"])

    async def create_token(self, params: CreateAuthTokenParameters) -> CreateAuthTokenResponse:
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

        return cast(CreateAuthTokenResponse, response["data"])

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
                "data": cast(Any, {"id": token_id}),
                "headers": None,
            },
            self.options,
        )

    def workflow(self, override_timeout: Optional[int] = None) -> WorkflowInitialStage:
        """Create a new WorkflowBuilder for chaining multiple operations.

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
    ) -> Union[BufferOutput, ContentOutput, JsonContentOutput]:
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
        pdf: FileInput,
        data: Optional[CreateDigitalSignature] = None,
        options: Optional[Dict[str, FileInput]] = None,
    ) -> BufferOutput:
        """Sign a PDF document.

        Args:
            pdf: The PDF file to sign
            data: Signature data
            options: Additional options (image, graphicImage)

        Returns:
            The signed PDF file output

        Example:
            ```python
            result = await client.sign('document.pdf', {
                'signatureType': 'cms',
                'flatten': False,
                'cadesLevel': 'b-lt'
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
        # Normalize the file input
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Prepare optional files
        normalized_image = None
        normalized_graphic_image = None

        if options:
            if "image" in options:
                image = options["image"]
                if is_remote_file_input(image):
                    normalized_image = await process_remote_file_input(str(image))
                else:
                    normalized_image = await process_file_input(image)

            if "graphicImage" in options:
                graphic_image = options["graphicImage"]
                if is_remote_file_input(graphic_image):
                    normalized_graphic_image = await process_remote_file_input(str(graphic_image))
                else:
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
                "data": cast(Any, request_data),
                "headers": None,
            },
            self.options,
        )

        buffer = response["data"]

        return {"mimeType": "application/pdf", "filename": "output.pdf", "buffer": buffer}

    async def watermark_text(
        self,
        file: FileInput,
        text: str,
        options: Optional[dict[str, Any]] = None,
    ) -> BufferOutput:
        """Add a text watermark to a document.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The input file to watermark
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

            # Access the watermarked PDF buffer
            pdf_buffer = result['buffer']

            # Save the buffer to a file
            with open('watermarked-document.pdf', 'wb') as f:
                f.write(pdf_buffer)
            ```
        """
        watermark_action = BuildActions.watermarkText(text, cast(Any, options))

        builder = self.workflow().add_file_part(file, None, [watermark_action])

        result = await builder.output_pdf().execute()
        return cast(BufferOutput, self._process_typed_workflow_result(result))

    async def watermark_image(
        self,
        file: FileInput,
        image: FileInput,
        options: Optional[dict[str, Any]] = None,
    ) -> BufferOutput:
        """Add an image watermark to a document.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The input file to watermark
            image: The watermark image
            options: Watermark options

        Returns:
            The watermarked document

        Example:
            ```python
            result = await client.watermark_image('document.pdf', 'watermark.jpg', {
                'opacity': 0.5
            })

            # Access the watermarked PDF buffer
            pdf_buffer = result['buffer']
            ```
        """
        watermark_action = BuildActions.watermarkImage(image, cast(Any, options))

        builder = self.workflow().add_file_part(file, None, [watermark_action])

        result = await builder.output_pdf().execute()
        return cast(BufferOutput, self._process_typed_workflow_result(result))

    async def convert(
        self,
        file: FileInput,
        target_format: OutputFormat,
    ) -> Union[BufferOutput, ContentOutput, JsonContentOutput]:
        """Convert a document to a different format.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The input file to convert
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
            result = await builder.output_image(cast(Literal["png", "jpeg", "jpg", "webp"], target_format), {"dpi": 300}).execute()
        else:
            raise ValidationError(f"Unsupported target format: {target_format}")

        return self._process_typed_workflow_result(result)

    async def ocr(
        self,
        file: FileInput,
        language: Union[OcrLanguage, list[OcrLanguage]],
    ) -> BufferOutput:
        """Perform OCR (Optical Character Recognition) on a document.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The input file to perform OCR on
            language: The language(s) to use for OCR

        Returns:
            The OCR result

        Example:
            ```python
            result = await client.ocr('scanned-document.pdf', 'english')

            # Access the OCR-processed PDF buffer
            pdf_buffer = result['buffer']
            ```
        """
        ocr_action = BuildActions.ocr(language)

        builder = self.workflow().add_file_part(file, None, [ocr_action])

        result = await builder.output_pdf().execute()
        return cast(BufferOutput, self._process_typed_workflow_result(result))

    async def extract_text(
        self,
        file: FileInput,
        pages: Optional[PageRange] = None,
    ) -> JsonContentOutput:
        """Extract text content from a document.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The file to extract text from
            pages: Optional page range to extract text from

        Returns:
            The extracted text data

        Example:
            ```python
            result = await client.extract_text('document.pdf')
            print(result['data'])

            # Extract text from specific pages
            result = await client.extract_text('document.pdf', {'start': 0, 'end': 2})

            # Access the extracted text content
            text_content = result['data']['pages'][0]['plainText']
            ```
        """
        normalized_pages = normalize_page_params(pages) if pages else None

        part_options = cast(Any, {"pages": normalized_pages}) if normalized_pages else None

        result = (
            await self.workflow()
            .add_file_part(file, part_options)
            .output_json({"plainText": True, "tables": False})
            .execute()
        )

        return cast(JsonContentOutput, self._process_typed_workflow_result(result))

    async def extract_table(
        self,
        file: FileInput,
        pages: Optional[PageRange] = None,
    ) -> JsonContentOutput:
        """Extract table content from a document.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The file to extract table from
            pages: Optional page range to extract tables from

        Returns:
            The extracted table data

        Example:
            ```python
            result = await client.extract_table('document.pdf')

            # Access the extracted tables
            tables = result['data']['pages'][0]['tables']

            # Process the first table if available
            if tables and len(tables) > 0:
                first_table = tables[0]
                print(f"Table has {len(first_table['rows'])} rows")
            ```
        """
        normalized_pages = normalize_page_params(pages) if pages else None

        part_options = cast(Any, {"pages": normalized_pages}) if normalized_pages else None

        result = (
            await self.workflow()
            .add_file_part(file, part_options)
            .output_json({"plainText": False, "tables": True})
            .execute()
        )

        return cast(JsonContentOutput, self._process_typed_workflow_result(result))

    async def extract_key_value_pairs(
        self,
        file: FileInput,
        pages: Optional[PageRange] = None,
    ) -> JsonContentOutput:
        """Extract key value pair content from a document.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The file to extract KVPs from
            pages: Optional page range to extract KVPs from

        Returns:
            The extracted KVPs data

        Example:
            ```python
            result = await client.extract_key_value_pairs('document.pdf')

            # Access the extracted key-value pairs
            kvps = result['data']['pages'][0]['keyValuePairs']

            # Process the key-value pairs
            if kvps and len(kvps) > 0:
                for kvp in kvps:
                    print(f"Key: {kvp['key']}, Value: {kvp['value']}")
            ```
        """
        normalized_pages = normalize_page_params(pages) if pages else None

        part_options = cast(Any, {"pages": normalized_pages}) if normalized_pages else None

        result = (
            await self.workflow()
            .add_file_part(file, part_options)
            .output_json({"plainText": False, "tables": False, "keyValuePairs": True})
            .execute()
        )

        return cast(JsonContentOutput, self._process_typed_workflow_result(result))

    async def password_protect(
        self,
        file: FileInput,
        user_password: str,
        owner_password: str,
        permissions: Optional[list[PDFUserPermission]] = None,
    ) -> BufferOutput:
        """Password protect a PDF document.
        This is a convenience method that uses the workflow builder.

        Args:
            file: The file to protect
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
        pdf_options: dict[str, Any] = {
            "userPassword": user_password,
            "ownerPassword": owner_password,
        }

        if permissions:
            pdf_options["userPermissions"] = permissions

        result = await self.workflow().add_file_part(file).output_pdf(cast(Any, pdf_options)).execute()

        return cast(BufferOutput, self._process_typed_workflow_result(result))

    async def set_metadata(
        self,
        pdf: FileInput,
        metadata: Metadata,
    ) -> BufferOutput:
        """Set metadata for a PDF document.
        This is a convenience method that uses the workflow builder.

        Args:
            pdf: The PDF file to modify
            metadata: The metadata to set (title and/or author)

        Returns:
            The document with updated metadata

        Example:
            ```python
            result = await client.set_metadata('document.pdf', {
                'title': 'My Document',
                'author': 'John Doe'
            })
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        result = (
            await self.workflow().add_file_part(pdf).output_pdf(cast(Any, {"metadata": metadata})).execute()
        )

        return cast(BufferOutput, self._process_typed_workflow_result(result))

    async def merge(self, files: List[FileInput]) -> BufferOutput:
        """Merge multiple documents into a single document.
        This is a convenience method that uses the workflow builder.

        Args:
            files: The files to merge

        Returns:
            The merged document

        Example:
            ```python
            result = await client.merge(['doc1.pdf', 'doc2.pdf', 'doc3.pdf'])

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
        return cast(BufferOutput, self._process_typed_workflow_result(result))

    async def flatten(
        self,
        pdf: FileInput,
        annotation_ids: Optional[list[Union[str, int]]] = None,
    ) -> BufferOutput:
        """Flatten annotations in a PDF document.
        This is a convenience method that uses the workflow builder.

        Args:
            pdf: The PDF file to flatten
            annotation_ids: Optional specific annotation IDs to flatten

        Returns:
            The flattened document

        Example:
            ```python
            # Flatten all annotations
            result = await client.flatten('annotated-document.pdf')

            # Flatten specific annotations by ID
            result = await client.flatten('annotated-document.pdf', ['annotation1', 'annotation2'])
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        flatten_action = BuildActions.flatten(annotation_ids)

        result = (
            await self.workflow().add_file_part(pdf, None, [flatten_action]).output_pdf().execute()
        )

        return cast(BufferOutput, self._process_typed_workflow_result(result))

    async def create_redactions_ai(
        self,
        pdf: FileInput,
        criteria: str,
        redaction_state: Literal["stage", "apply"] = "stage",
        pages: Optional[PageRange] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> BufferOutput:
        """Use AI to redact sensitive information in a document.

        Args:
            pdf: The PDF file to redact
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
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        page_count = get_pdf_page_count(normalized_file[0])
        normalized_pages = normalize_page_params(pages, page_count) if pages else None

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

        response: Any = await send_request(
            {
                "method": "POST",
                "endpoint": "/ai/redact",
                "data": cast(Any, request_data),
                "headers": None,
            },
            self.options,
        )

        buffer = response["data"]

        return {"mimeType": "application/pdf", "filename": "output.pdf", "buffer": buffer}
