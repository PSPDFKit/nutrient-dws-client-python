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
    RedactRequestData,
    RequestConfig,
    SignRequestData,
    SignRequestOptions,
    send_request,
)
from nutrient_dws.inputs import (
    FileInput,
    get_pdf_page_count,
    is_remote_file_input,
    is_valid_pdf,
    process_file_input,
    process_remote_file_input,
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
        pdf: FileInput,
        data: CreateDigitalSignature | None = None,
        options: SignRequestOptions | None = None,
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
                    normalized_graphic_image = await process_remote_file_input(
                        str(graphic_image)
                    )
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
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def extract_text(
        self,
        file: FileInput,
        pages: PageRange | None = None,
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

    async def set_page_labels(
        self,
        pdf: FileInput,
        labels: list[Label],
    ) -> BufferOutput:
        """Set page labels for a PDF document.
        This is a convenience method that uses the workflow builder.

        Args:
            pdf: The PDF file to modify
            labels: Array of label objects with pages and label properties

        Returns:
            The document with updated page labels

        Example:
            ```python
            result = await client.set_page_labels('document.pdf', [
                {'pages': [0, 1, 2], 'label': 'Cover'},
                {'pages': [3, 4, 5], 'label': 'Chapter 1'}
            ])
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

        Args:
            pdf: The PDF file to modify
            instant_json_file: The Instant JSON file to apply

        Returns:
            The modified document

        Example:
            ```python
            result = await client.apply_instant_json('document.pdf', 'annotations.json')
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

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

        Args:
            pdf: The PDF file to modify
            xfdf_file: The XFDF file to apply
            options: Optional settings for applying XFDF

        Returns:
            The modified document

        Example:
            ```python
            result = await client.apply_xfdf('document.pdf', 'annotations.xfdf')
            # Or with options:
            result = await client.apply_xfdf(
                'document.pdf', 'annotations.xfdf',
                {'ignorePageRotation': True, 'richTextEnabled': False}
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
        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def flatten(
        self,
        pdf: FileInput,
        annotation_ids: list[str | int] | None = None,
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
            await self.workflow()
            .add_file_part(pdf, None, [flatten_action])
            .output_pdf()
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def create_redactions_ai(
        self,
        pdf: FileInput,
        criteria: str,
        redaction_state: Literal["stage", "apply"] = "stage",
        pages: PageRange | None = None,
        options: RedactOptions | None = None,
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

        Args:
            pdf: The PDF file to create redactions in
            preset: The preset pattern to search for (e.g., 'email-address', 'social-security-number')
            redaction_state: Whether to stage or apply redactions (default: 'stage')
            pages: Optional page range to create redactions in
            preset_options: Optional settings for the preset strategy
            options: Optional settings for creating redactions

        Returns:
            The document with redaction annotations

        Example:
            ```python
            result = await client.create_redactions_preset('document.pdf', 'email-address')
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Get page count for handling negative indices
        page_count = get_pdf_page_count(normalized_file[0])
        normalized_pages = normalize_page_params(pages, page_count) if pages else None

        # Prepare strategy options with pages
        strategy_options = preset_options.copy() if preset_options else {}
        if normalized_pages:
            strategy_options["start"] = normalized_pages["start"]
            if normalized_pages["end"] >= 0:
                strategy_options["limit"] = (
                    normalized_pages["end"] - normalized_pages["start"] + 1
                )

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

        Args:
            pdf: The PDF file to create redactions in
            regex: The regular expression to search for
            redaction_state: Whether to stage or apply redactions (default: 'stage')
            pages: Optional page range to create redactions in
            regex_options: Optional settings for the regex strategy
            options: Optional settings for creating redactions

        Returns:
            The document with redaction annotations

        Example:
            ```python
            result = await client.create_redactions_regex('document.pdf', r'Account:\s*\d{8,12}')
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Get page count for handling negative indices
        page_count = get_pdf_page_count(normalized_file[0])
        normalized_pages = normalize_page_params(pages, page_count) if pages else None

        # Prepare strategy options with pages
        strategy_options = regex_options.copy() if regex_options else {}
        if normalized_pages:
            strategy_options["start"] = normalized_pages["start"]
            if normalized_pages["end"] >= 0:
                strategy_options["limit"] = (
                    normalized_pages["end"] - normalized_pages["start"] + 1
                )

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

        Args:
            pdf: The PDF file to create redactions in
            text: The text to search for
            redaction_state: Whether to stage or apply redactions (default: 'stage')
            pages: Optional page range to create redactions in
            text_options: Optional settings for the text strategy
            options: Optional settings for creating redactions

        Returns:
            The document with redaction annotations

        Example:
            ```python
            result = await client.create_redactions_text('document.pdf', 'email@example.com')
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Get page count for handling negative indices
        page_count = get_pdf_page_count(normalized_file[0])
        normalized_pages = normalize_page_params(pages, page_count) if pages else None

        # Prepare strategy options with pages
        strategy_options = text_options.copy() if text_options else {}
        if normalized_pages:
            strategy_options["start"] = normalized_pages["start"]
            if normalized_pages["end"] >= 0:
                strategy_options["limit"] = (
                    normalized_pages["end"] - normalized_pages["start"] + 1
                )

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

        Args:
            pdf: The PDF file with redaction annotations to apply

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

        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

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

        Args:
            pdf: The PDF file to rotate
            angle: Rotation angle (90, 180, or 270 degrees)
            pages: Optional page range to rotate

        Returns:
            The entire document with specified pages rotated

        Example:
            ```python
            result = await client.rotate('document.pdf', 90)

            # Rotate specific pages:
            result = await client.rotate('document.pdf', 90, {'start': 1, 'end': 3})
            ```
        """
        rotate_action = BuildActions.rotate(angle)

        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        workflow = self.workflow()

        if pages:
            page_count = get_pdf_page_count(normalized_file[0])
            normalized_pages = normalize_page_params(pages, page_count)

            # Add pages before the range to rotate
            if normalized_pages["start"] > 0:
                part_options = cast(
                    "FilePartOptions",
                    {"pages": {"start": 0, "end": normalized_pages["start"] - 1}},
                )
                workflow = workflow.add_file_part(pdf, part_options)

            # Add the specific pages with rotation action
            part_options = cast("FilePartOptions", {"pages": normalized_pages})
            workflow = workflow.add_file_part(pdf, part_options, [rotate_action])

            # Add pages after the range to rotate
            if normalized_pages["end"] < page_count - 1:
                part_options = cast(
                    "FilePartOptions",
                    {
                        "pages": {
                            "start": normalized_pages["end"] + 1,
                            "end": page_count - 1,
                        }
                    },
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

        Args:
            pdf: The PDF file to add pages to
            count: The number of blank pages to add
            index: Optional index where to add the blank pages (0-based). If not provided, pages are added at the end.

        Returns:
            The document with added pages

        Example:
            ```python
            # Add 2 blank pages at the end
            result = await client.add_page('document.pdf', 2)

            # Add 1 blank page after the first page (at index 1)
            result = await client.add_page('document.pdf', 1, 1)
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # If no index is provided or it's the end of the document, simply add pages at the end
        if index is None:
            builder = self.workflow()

            builder.add_file_part(pdf)

            # Add the specified number of blank pages
            builder = builder.add_new_page({"pageCount": count})

            result = await builder.output_pdf().execute()
        else:
            # Get the actual page count of the PDF
            page_count = get_pdf_page_count(normalized_file[0])

            # Validate that the index is within range
            if index < 0 or index > page_count:
                raise ValidationError(
                    f"Index {index} is out of range (document has {page_count} pages)"
                )

            builder = self.workflow()

            # Add pages before the specified index
            if index > 0:
                before_pages = normalize_page_params(
                    {"start": 0, "end": index - 1}, page_count
                )
                part_options = cast("FilePartOptions", {"pages": before_pages})
                builder = builder.add_file_part(pdf, part_options)

            # Add the blank pages
            builder = builder.add_new_page({"pageCount": count})

            # Add pages after the specified index
            if index < page_count:
                after_pages = normalize_page_params(
                    {"start": index, "end": page_count - 1}, page_count
                )
                part_options = cast("FilePartOptions", {"pages": after_pages})
                builder = builder.add_file_part(pdf, part_options)

            result = await builder.output_pdf().execute()

        return cast("BufferOutput", self._process_typed_workflow_result(result))

    async def split(
        self, pdf: FileInput, page_ranges: list[PageRange]
    ) -> list[BufferOutput]:
        """Split a PDF document into multiple parts based on page ranges.
        This is a convenience method that uses the workflow builder.

        Args:
            pdf: The PDF file to split
            page_ranges: Array of page ranges to extract

        Returns:
            An array of PDF documents, one for each page range

        Example:
            ```python
            results = await client.split('document.pdf', [
                {'start': 0, 'end': 2},  # Pages 0, 1, 2
                {'start': 3, 'end': 5}   # Pages 3, 4, 5
            ])
            ```
        """
        if not page_ranges or len(page_ranges) == 0:
            raise ValidationError("At least one page range is required for splitting")

        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Get the actual page count of the PDF
        page_count = get_pdf_page_count(normalized_file[0])

        # Normalize and validate all page ranges
        normalized_ranges = [
            normalize_page_params(page_range, page_count) for page_range in page_ranges
        ]

        # Validate that all page ranges are within bounds
        for page_range in normalized_ranges:
            if page_range["start"] > page_range["end"]:
                raise ValidationError(
                    f"Page range {page_range} is invalid (start > end)"
                )

        # Create a separate workflow for each page range
        import asyncio
        from typing import cast as typing_cast

        async def create_split_pdf(page_range: Pages) -> BufferOutput:
            builder = self.workflow()
            part_options = cast("FilePartOptions", {"pages": page_range})
            builder = builder.add_file_part(pdf, part_options)
            result = await builder.output_pdf().execute()
            return typing_cast(
                "BufferOutput", self._process_typed_workflow_result(result)
            )

        # Execute all workflows in parallel and process the results
        tasks = [create_split_pdf(page_range) for page_range in normalized_ranges]
        results = await asyncio.gather(*tasks)

        return results

    async def duplicate_pages(
        self, pdf: FileInput, page_indices: list[int]
    ) -> BufferOutput:
        """Create a new PDF containing only the specified pages in the order provided.
        This is a convenience method that uses the workflow builder.

        Args:
            pdf: The PDF file to extract pages from
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
            ```
        """
        if not page_indices or len(page_indices) == 0:
            raise ValidationError("At least one page index is required for duplication")

        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Get the actual page count of the PDF
        page_count = get_pdf_page_count(normalized_file[0])

        # Normalize negative indices
        normalized_indices = []
        for index in page_indices:
            if index < 0:
                # Handle negative indices (e.g., -1 is the last page)
                normalized_indices.append(page_count + index)
            else:
                normalized_indices.append(index)

        # Validate that all page indices are within range
        for i, original_index in enumerate(page_indices):
            normalized_index = normalized_indices[i]
            if normalized_index < 0 or normalized_index >= page_count:
                raise ValidationError(
                    f"Page index {original_index} is out of range (document has {page_count} pages)"
                )

        builder = self.workflow()

        # Add each page in the order specified
        for page_index in normalized_indices:
            # Use normalize_page_params to ensure consistent handling
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

        Args:
            pdf: The PDF file to modify
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
            ```
        """
        if not page_indices or len(page_indices) == 0:
            raise ValidationError("At least one page index is required for deletion")

        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        # Get the actual page count of the PDF
        page_count = get_pdf_page_count(normalized_file[0])

        # Normalize negative indices
        normalized_indices = []
        for index in page_indices:
            if index < 0:
                # Handle negative indices (e.g., -1 is the last page)
                normalized_indices.append(page_count + index)
            else:
                normalized_indices.append(index)

        # Remove duplicates and sort the deleteIndices
        delete_indices = sorted(set(normalized_indices))

        # Validate that all page indices are within range
        for original_index in page_indices:
            if original_index >= 0:
                normalized_index = original_index
            else:
                normalized_index = page_count + original_index

            if normalized_index < 0 or normalized_index >= page_count:
                raise ValidationError(
                    f"Page index {original_index} is out of range (document has {page_count} pages)"
                )

        builder = self.workflow()

        # Group consecutive pages that should be kept into ranges
        current_page = 0
        page_ranges = []

        for delete_index in delete_indices:
            if current_page < delete_index:
                page_ranges.append(
                    normalize_page_params(
                        {"start": current_page, "end": delete_index - 1}
                    )
                )
            current_page = delete_index + 1

        if (
            current_page > 0 or (current_page == 0 and len(delete_indices) == 0)
        ) and current_page < page_count:
            page_ranges.append(
                normalize_page_params({"start": current_page, "end": page_count - 1})
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

        Args:
            pdf: The PDF file to optimize
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
            ```
        """
        # Validate PDF
        if is_remote_file_input(pdf):
            normalized_file = await process_remote_file_input(str(pdf))
        else:
            normalized_file = await process_file_input(pdf)

        if not is_valid_pdf(normalized_file[0]):
            raise ValidationError("Invalid pdf file", {"input": pdf})

        if options is None:
            options = {"imageOptimizationQuality": 2}

        result = (
            await self.workflow()
            .add_file_part(pdf)
            .output_pdf(cast("PDFOutputOptions", {"optimize": options}))
            .execute()
        )

        return cast("BufferOutput", self._process_typed_workflow_result(result))
