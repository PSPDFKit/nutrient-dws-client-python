from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.misc import OcrLanguage, PageRange


class Metadata(TypedDict):
    title: NotRequired[str]
    author: NotRequired[str]


class Label(TypedDict):
    pages: list[int]
    label: str


PDFUserPermission = Literal[
    "printing",
    "modification",
    "extract",
    "annotations_and_forms",
    "fill_forms",
    "extract_accessibility",
    "assemble",
    "print_high_quality",
]


class OptimizePdf(TypedDict):
    grayscaleText: NotRequired[bool]
    grayscaleGraphics: NotRequired[bool]
    grayscaleImages: NotRequired[bool]
    grayscaleFormFields: NotRequired[bool]
    grayscaleAnnotations: NotRequired[bool]
    disableImages: NotRequired[bool]
    mrcCompression: NotRequired[bool]
    imageOptimizationQuality: NotRequired[int]
    linearize: NotRequired[bool]


class BasePDFOutput(TypedDict):
    metadata: NotRequired[Metadata]
    labels: NotRequired[list[Label]]
    user_password: NotRequired[str]
    owner_password: NotRequired[str]
    user_permissions: NotRequired[list[PDFUserPermission]]
    optimize: NotRequired[OptimizePdf]


PDFOutputOptions = BasePDFOutput


class PDFOutput(BasePDFOutput):
    type: NotRequired[Literal["pdf"]]


class PDFAOutputOptions(PDFOutputOptions):
    conformance: NotRequired[
        Literal[
            "pdfa-1a", "pdfa-1b", "pdfa-2a", "pdfa-2u", "pdfa-2b", "pdfa-3a", "pdfa-3u"
        ]
    ]
    vectorization: NotRequired[bool]
    rasterization: NotRequired[bool]


class PDFAOutput(PDFAOutputOptions):
    type: Literal["pdfa"]


PDFUAOutputOptions = BasePDFOutput


class PDFUAOutput(PDFUAOutputOptions):
    type: Literal["pdfua"]


class ImageOutputOptions(TypedDict):
    format: NotRequired[Literal["png", "jpeg", "jpg", "webp"]]
    pages: NotRequired[PageRange]
    width: NotRequired[float]
    height: NotRequired[float]
    dpi: NotRequired[float]


class ImageOutput(ImageOutputOptions):
    type: Literal["image"]


class JSONContentOutputOptions(TypedDict):
    plainText: NotRequired[bool]
    structuredText: NotRequired[bool]
    keyValuePairs: NotRequired[bool]
    tables: NotRequired[bool]
    language: NotRequired[OcrLanguage | list[OcrLanguage]]


class JSONContentOutput(JSONContentOutputOptions):
    type: Literal["json-content"]


class OfficeOutput(TypedDict):
    type: Literal["docx", "xlsx", "pptx"]


class HTMLOutput(TypedDict):
    type: Literal["html"]
    layout: NotRequired[Literal["page", "reflow"]]


class MarkdownOutput(TypedDict):
    type: Literal["markdown"]


BuildOutput = Union[
    PDFOutput,
    PDFAOutput,
    PDFUAOutput,
    ImageOutput,
    JSONContentOutput,
    OfficeOutput,
    HTMLOutput,
    MarkdownOutput,
]
