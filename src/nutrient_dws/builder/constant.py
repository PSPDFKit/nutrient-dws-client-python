from collections.abc import Callable
from typing import Any, Literal, Protocol, TypeVar, cast

from nutrient_dws.inputs import FileInput
from nutrient_dws.types.build_actions import (
    ApplyInstantJsonAction,
    ApplyRedactionsAction,
    ApplyXfdfAction,
    ApplyXfdfActionOptions,
    BaseCreateRedactionsOptions,
    BuildAction,
    CreateRedactionsActionPreset,
    CreateRedactionsActionRegex,
    CreateRedactionsActionText,
    CreateRedactionsStrategyOptionsPreset,
    CreateRedactionsStrategyOptionsRegex,
    CreateRedactionsStrategyOptionsText,
    FlattenAction,
    ImageWatermarkAction,
    ImageWatermarkActionOptions,
    OcrAction,
    RotateAction,
    SearchPreset,
    TextWatermarkAction,
    TextWatermarkActionOptions,
)
from nutrient_dws.types.build_output import (
    HTMLOutput,
    ImageOutput,
    ImageOutputOptions,
    JSONContentOutput,
    JSONContentOutputOptions,
    MarkdownOutput,
    OfficeOutput,
    PDFAOutput,
    PDFAOutputOptions,
    PDFOutput,
    PDFOutputOptions,
    PDFUAOutput,
    PDFUAOutputOptions,
)
from nutrient_dws.types.file_handle import FileHandle
from nutrient_dws.types.misc import OcrLanguage, WatermarkDimension

# Default dimension for watermarks
DEFAULT_DIMENSION: WatermarkDimension = {"value": 100, "unit": "%"}


T = TypeVar("T")


class ActionWithFileInput(Protocol):
    """Internal action type that holds FileInput for deferred registration."""

    __needsFileRegistration: bool
    fileInput: FileInput
    createAction: Callable[[FileHandle], BuildAction]


class BuildActions:
    """Factory functions for creating common build actions."""

    @staticmethod
    def ocr(language: OcrLanguage | list[OcrLanguage]) -> OcrAction:
        """Create an OCR action.

        Args:
            language: Language(s) for OCR

        Returns:
            OcrAction object
        """
        return {
            "type": "ocr",
            "language": language,
        }

    @staticmethod
    def rotate(rotateBy: Literal[90, 180, 270]) -> RotateAction:
        """Create a rotation action.

        Args:
            rotateBy: Rotation angle (90, 180, or 270)

        Returns:
            RotateAction object
        """
        return {
            "type": "rotate",
            "rotateBy": rotateBy,
        }

    @staticmethod
    def watermark_text(
        text: str, options: TextWatermarkActionOptions | None = None
    ) -> TextWatermarkAction:
        """Create a text watermark action.

        Args:
            text: Watermark text
            options: Watermark options
                width: Width dimension of the watermark (value and unit, e.g. {value: 100, unit: '%'})
                height: Height dimension of the watermark (value and unit, e.g. {value: 100, unit: '%'})
                top: Top position of the watermark (value and unit)
                right: Right position of the watermark (value and unit)
                bottom: Bottom position of the watermark (value and unit)
                left: Left position of the watermark (value and unit)
                rotation: Rotation of the watermark in counterclockwise degrees (default: 0)
                opacity: Watermark opacity (0 is fully transparent, 1 is fully opaque)
                fontFamily: Font family for the text (e.g. 'Helvetica')
                fontSize: Size of the text in points
                fontColor: Foreground color of the text (e.g. '#ffffff')
                fontStyle: Text style array ('bold', 'italic', or both)

        Returns:
            TextWatermarkAction object
        """
        if options is None:
            options = {
                "width": DEFAULT_DIMENSION,
                "height": DEFAULT_DIMENSION,
                "rotation": 0,
            }

        return {
            "type": "watermark",
            "text": text,
            **options,
            "rotation": options.get("rotation", 0),
            "width": options.get("width", DEFAULT_DIMENSION),
            "height": options.get("height", DEFAULT_DIMENSION),
        }

    @staticmethod
    def watermark_image(
        image: FileInput, options: ImageWatermarkActionOptions | None = None
    ) -> ActionWithFileInput:
        """Create an image watermark action.

        Args:
            image: Watermark image
            options: Watermark options
                width: Width dimension of the watermark (value and unit, e.g. {value: 100, unit: '%'})
                height: Height dimension of the watermark (value and unit, e.g. {value: 100, unit: '%'})
                top: Top position of the watermark (value and unit)
                right: Right position of the watermark (value and unit)
                bottom: Bottom position of the watermark (value and unit)
                left: Left position of the watermark (value and unit)
                rotation: Rotation of the watermark in counterclockwise degrees (default: 0)
                opacity: Watermark opacity (0 is fully transparent, 1 is fully opaque)

        Returns:
            ActionWithFileInput object
        """
        if options is None:
            options = {
                "width": DEFAULT_DIMENSION,
                "height": DEFAULT_DIMENSION,
                "rotation": 0,
            }

        class ImageWatermarkActionWithFileInput(ActionWithFileInput):
            __needsFileRegistration = True

            def __init__(
                self, file_input: FileInput, opts: ImageWatermarkActionOptions
            ):
                self.fileInput = file_input
                self.options = opts

            def createAction(self, fileHandle: FileHandle) -> ImageWatermarkAction:
                return {
                    "type": "watermark",
                    "image": fileHandle,
                    **self.options,
                    "rotation": self.options.get("rotation", 0),
                    "width": self.options.get("width", DEFAULT_DIMENSION),
                    "height": self.options.get("height", DEFAULT_DIMENSION),
                }

        return ImageWatermarkActionWithFileInput(image, options)

    @staticmethod
    def flatten(annotation_ids: list[str | int] | None = None) -> FlattenAction:
        """Create a flatten action.

        Args:
            annotation_ids: Optional annotation IDs to flatten (all if not specified)

        Returns:
            FlattenAction object
        """
        result: FlattenAction = {"type": "flatten"}
        if annotation_ids is not None:
            result["annotationIds"] = annotation_ids
        return result

    @staticmethod
    def apply_instant_json(file: FileInput) -> ActionWithFileInput:
        """Create an apply Instant JSON action.

        Args:
            file: Instant JSON file input

        Returns:
            ActionWithFileInput object
        """

        class ApplyInstantJsonActionWithFileInput(ActionWithFileInput):
            __needsFileRegistration = True

            def __init__(self, file_input: FileInput):
                self.fileInput = file_input

            def createAction(self, fileHandle: FileHandle) -> ApplyInstantJsonAction:
                return {
                    "type": "applyInstantJson",
                    "file": fileHandle,
                }

        return ApplyInstantJsonActionWithFileInput(file)

    @staticmethod
    def apply_xfdf(
        file: FileInput, options: ApplyXfdfActionOptions | None = None
    ) -> ActionWithFileInput:
        """Create an apply XFDF action.

        Args:
            file: XFDF file input
            options: Apply Xfdf options
                ignorePageRotation: If true, ignores page rotation when applying XFDF data (default: false)
                richTextEnabled: If true, plain text annotations will be converted to rich text annotations. If false, all text annotations will be plain text annotations (default: true)

        Returns:
            ActionWithFileInput object
        """

        class ApplyXfdfActionWithFileInput(ActionWithFileInput):
            __needsFileRegistration = True

            def __init__(
                self, file_input: FileInput, opts: ApplyXfdfActionOptions | None
            ):
                self.fileInput = file_input
                self.options = opts or {}

            def createAction(self, fileHandle: FileHandle) -> ApplyXfdfAction:
                return {
                    "type": "applyXfdf",
                    "file": fileHandle,
                    **self.options,
                }

        return ApplyXfdfActionWithFileInput(file, options)

    @staticmethod
    def create_redactions_text(
        text: str,
        options: BaseCreateRedactionsOptions | None = None,
        strategy_options: CreateRedactionsStrategyOptionsText | None = None,
    ) -> CreateRedactionsActionText:
        """Create redactions with text search.

        Args:
            text: Text to search and redact
            options: Redaction options
                content: Visual aspects of the redaction annotation (background color, overlay text, etc.)
            strategy_options: Redaction strategy options
                includeAnnotations: If true, redaction annotations are created on top of annotations whose content match the provided text (default: true)
                caseSensitive: If true, the search will be case sensitive (default: false)
                start: The index of the page from where to start the search (default: 0)
                limit: Starting from start, the number of pages to search (default: to the end of the document)

        Returns:
            CreateRedactionsAction object
        """
        result: dict[str, Any] = {
            "type": "createRedactions",
            "strategy": "text",
            "strategyOptions": {
                "text": text,
                **(strategy_options or {}),
            },
            **(options or {}),
        }
        return cast("CreateRedactionsActionText", result)

    @staticmethod
    def create_redactions_regex(
        regex: str,
        options: BaseCreateRedactionsOptions | None = None,
        strategy_options: CreateRedactionsStrategyOptionsRegex | None = None,
    ) -> CreateRedactionsActionRegex:
        """Create redactions with regex pattern.

        Args:
            regex: Regex pattern to search and redact
            options: Redaction options
                content: Visual aspects of the redaction annotation (background color, overlay text, etc.)
            strategy_options: Redaction strategy options
                includeAnnotations: If true, redaction annotations are created on top of annotations whose content match the provided regex (default: true)
                caseSensitive: If true, the search will be case sensitive (default: true)
                start: The index of the page from where to start the search (default: 0)
                limit: Starting from start, the number of pages to search (default: to the end of the document)

        Returns:
            CreateRedactionsAction object
        """
        result: dict[str, Any] = {
            "type": "createRedactions",
            "strategy": "regex",
            "strategyOptions": {
                "regex": regex,
                **(strategy_options or {}),
            },
            **(options or {}),
        }
        return cast("CreateRedactionsActionRegex", result)

    @staticmethod
    def create_redactions_preset(
        preset: SearchPreset,
        options: BaseCreateRedactionsOptions | None = None,
        strategy_options: CreateRedactionsStrategyOptionsPreset | None = None,
    ) -> CreateRedactionsActionPreset:
        """Create redactions with preset pattern.

        Args:
            preset: Preset pattern to search and redact (e.g. 'email-address', 'credit-card-number', 'social-security-number', etc.)
            options: Redaction options
                content: Visual aspects of the redaction annotation (background color, overlay text, etc.)
            strategy_options: Redaction strategy options
                includeAnnotations: If true, redaction annotations are created on top of annotations whose content match the provided preset (default: true)
                start: The index of the page from where to start the search (default: 0)
                limit: Starting from start, the number of pages to search (default: to the end of the document)

        Returns:
            CreateRedactionsAction object
        """
        result: dict[str, Any] = {
            "type": "createRedactions",
            "strategy": "preset",
            "strategyOptions": {
                "preset": preset,
                **(strategy_options or {}),
            },
            **(options or {}),
        }
        return cast("CreateRedactionsActionPreset", result)

    @staticmethod
    def apply_redactions() -> ApplyRedactionsAction:
        """Apply previously created redactions.

        Returns:
            ApplyRedactionsAction object
        """
        return {
            "type": "applyRedactions",
        }


class BuildOutputs:
    """Factory functions for creating output configurations."""

    @staticmethod
    def pdf(options: PDFOutputOptions | None = None) -> PDFOutput:
        """PDF output configuration.

        Args:
            options: PDF output options
                metadata: Document metadata
                labels: Page labels
                user_password: User password for the PDF
                owner_password: Owner password for the PDF
                user_permissions: User permissions
                optimize: PDF optimization options

        Returns:
            PDFOutput object
        """
        result: dict[str, Any] = {"type": "pdf"}

        if options:
            if "metadata" in options:
                result["metadata"] = options["metadata"]
            if "labels" in options:
                result["labels"] = options["labels"]
            if "user_password" in options:
                result["user_password"] = options["user_password"]
            if "owner_password" in options:
                result["owner_password"] = options["owner_password"]
            if "user_permissions" in options:
                result["user_permissions"] = options["user_permissions"]
            if "optimize" in options:
                result["optimize"] = options["optimize"]

        return cast("PDFOutput", result)

    @staticmethod
    def pdfa(options: PDFAOutputOptions | None = None) -> PDFAOutput:
        """PDF/A output configuration.

        Args:
            options: PDF/A output options
                conformance: PDF/A conformance level
                vectorization: Enable vectorization
                rasterization: Enable rasterization
                metadata: Document metadata
                labels: Page labels
                user_password: User password for the PDF
                owner_password: Owner password for the PDF
                user_permissions: User permissions
                optimize: PDF optimization options

        Returns:
            PDFAOutput object
        """
        result: dict[str, Any] = {"type": "pdfa"}

        if options:
            if "conformance" in options:
                result["conformance"] = options["conformance"]
            if "vectorization" in options:
                result["vectorization"] = options["vectorization"]
            if "rasterization" in options:
                result["rasterization"] = options["rasterization"]
            if "metadata" in options:
                result["metadata"] = options["metadata"]
            if "labels" in options:
                result["labels"] = options["labels"]
            if "user_password" in options:
                result["user_password"] = options["user_password"]
            if "owner_password" in options:
                result["owner_password"] = options["owner_password"]
            if "user_permissions" in options:
                result["user_permissions"] = options["user_permissions"]
            if "optimize" in options:
                result["optimize"] = options["optimize"]

        return cast("PDFAOutput", result)

    @staticmethod
    def pdfua(options: PDFUAOutputOptions | None = None) -> PDFUAOutput:
        """PDF/UA output configuration.

        Args:
            options: PDF/UA output options
                metadata: Document metadata
                labels: Page labels
                user_password: User password for the PDF
                owner_password: Owner password for the PDF
                user_permissions: User permissions
                optimize: PDF optimization options

        Returns:
            PDFUAOutput object
        """
        result: dict[str, Any] = {"type": "pdfua"}

        if options:
            if "metadata" in options:
                result["metadata"] = options["metadata"]
            if "labels" in options:
                result["labels"] = options["labels"]
            if "user_password" in options:
                result["user_password"] = options["user_password"]
            if "owner_password" in options:
                result["owner_password"] = options["owner_password"]
            if "user_permissions" in options:
                result["user_permissions"] = options["user_permissions"]
            if "optimize" in options:
                result["optimize"] = options["optimize"]

        return cast("PDFUAOutput", result)

    @staticmethod
    def image(
        format: Literal["png", "jpeg", "jpg", "webp"],
        options: ImageOutputOptions | None = None,
    ) -> ImageOutput:
        """Image output configuration.

        Args:
            format: Image format type
            options: Image output options
                pages: Page range to convert
                width: Width of the output image
                height: Height of the output image
                dpi: DPI of the output image

        Returns:
            ImageOutput object
        """
        result: dict[str, Any] = {
            "type": "image",
            "format": format,
        }

        if options:
            if "pages" in options:
                result["pages"] = options["pages"]
            if "width" in options:
                result["width"] = options["width"]
            if "height" in options:
                result["height"] = options["height"]
            if "dpi" in options:
                result["dpi"] = options["dpi"]

        return cast("ImageOutput", result)

    @staticmethod
    def jsonContent(
        options: JSONContentOutputOptions | None = None,
    ) -> JSONContentOutput:
        """JSON content output configuration.

        Args:
            options: JSON content extraction options
                plainText: Extract plain text
                structuredText: Extract structured text
                keyValuePairs: Extract key-value pairs
                tables: Extract tables
                language: Language(s) for OCR

        Returns:
            JSONContentOutput object
        """
        result: dict[str, Any] = {"type": "json-content"}

        if options:
            if "plainText" in options:
                result["plainText"] = options["plainText"]
            if "structuredText" in options:
                result["structuredText"] = options["structuredText"]
            if "keyValuePairs" in options:
                result["keyValuePairs"] = options["keyValuePairs"]
            if "tables" in options:
                result["tables"] = options["tables"]
            if "language" in options:
                result["language"] = options["language"]

        return cast("JSONContentOutput", result)

    @staticmethod
    def office(type: Literal["docx", "xlsx", "pptx"]) -> OfficeOutput:
        """Office document output configuration.

        Args:
            type: Office document type

        Returns:
            OfficeOutput object
        """
        return {
            "type": type,
        }

    @staticmethod
    def html(layout: Literal["page", "reflow"]) -> HTMLOutput:
        """HTML output configuration.

        Args:
            layout: The layout type to use for conversion to HTML

        Returns:
            HTMLOutput object
        """
        return {
            "type": "html",
            "layout": layout,
        }

    @staticmethod
    def markdown() -> MarkdownOutput:
        """Markdown output configuration.

        Returns:
            MarkdownOutput object
        """
        return {
            "type": "markdown",
        }

    @staticmethod
    def getMimeTypeForOutput(
        output: PDFOutput
        | PDFAOutput
        | PDFUAOutput
        | ImageOutput
        | OfficeOutput
        | HTMLOutput
        | MarkdownOutput,
    ) -> dict[str, str]:
        """Get MIME type and filename for a given output configuration.

        Args:
            output: The output configuration

        Returns:
            Dictionary with mimeType and optional filename
        """
        output_type = output.get("type", "pdf")

        if output_type in ["pdf", "pdfa", "pdfua"]:
            return {"mimeType": "application/pdf", "filename": "output.pdf"}
        elif output_type == "image":
            format = output.get("format", "png")
            if format == "jpg":
                return {"mimeType": "image/jpeg", "filename": "output.jpg"}
            else:
                return {"mimeType": f"image/{format}", "filename": f"output.{format}"}
        elif output_type == "docx":
            return {
                "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "filename": "output.docx",
            }
        elif output_type == "xlsx":
            return {
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "filename": "output.xlsx",
            }
        elif output_type == "pptx":
            return {
                "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "filename": "output.pptx",
            }
        elif output_type == "html":
            return {
                "mimeType": "text/html",
                "filename": "output.html",
            }
        elif output_type == "markdown":
            return {
                "mimeType": "text/markdown",
                "filename": "output.md",
            }
        else:
            return {"mimeType": "application/octet-stream", "filename": "output"}
