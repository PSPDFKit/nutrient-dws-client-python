"""Type definitions for the data-extraction `/extraction/parse` endpoint.

These TypedDicts describe the multipart request payload (`ParseInstructions`)
and the JSON response envelope (`ParseResponse`) returned by `POST
/extraction/parse`.

Billing note: `/extraction/parse` is billed against **extraction credits**,
which are a separate bucket from the **processor API credits** consumed by
endpoints such as `/build`, `/sign`, and OCR. The credit costs documented
below (1, 1.5, 9, 18 per page) are extraction credits.
"""

from typing import Literal

from typing_extensions import NotRequired, TypedDict

from nutrient_dws.types.extraction_credits import ExtractionCredits

# ---- Request types --------------------------------------------------------

ParseMode = Literal["text", "structure", "understand", "agentic"]
"""Processing mode for `/extraction/parse`.

| Mode        | Extraction credits / page | Notes                                                      |
|-------------|---------------------------|------------------------------------------------------------|
| `text`      | 1                         | Fast Markdown extraction from born-digital documents.      |
| `structure` | 1.5                       | OCR + spatial elements with bounding boxes.                |
| `understand`| 9                         | AI-augmented: tables, formulas, semantic classification.   |
| `agentic`   | 18                        | VLM-augmented; deepest visual understanding.               |
"""

ParseOutputFormat = Literal["markdown", "spatial"]
"""Output format requested from `/extraction/parse`.

- `markdown`: a whole-document Markdown string at `response.output.markdown`.
- `spatial`: a list of typed elements with bounds at `response.output.elements`.
"""


class ParseOutput(TypedDict, total=False):
    """The `output` sub-object of `ParseInstructions`."""

    format: ParseOutputFormat


class ParseInstructions(TypedDict, total=False):
    """Request body sent as the `instructions` multipart field.

    Both fields are optional on the wire; the server defaults are applied if
    omitted. The client surfaces these as keyword arguments on
    `NutrientClient.parse()` so the typical caller does not construct this
    dict directly.
    """

    mode: ParseMode
    output: ParseOutput


# ---- Response types -------------------------------------------------------


class ParseBounds(TypedDict):
    """Axis-aligned bounding box on the page.

    `(x, y)` is the **top-left corner** of the box. The page's coordinate
    origin is the top-left, with `x` increasing to the right and `y`
    increasing downward. Units are pixels in the same canvas described by
    `ParsePageRef.width` and `ParsePageRef.height` (i.e. element bounds and
    the page dimensions share one coordinate space).
    """

    x: float
    y: float
    width: float
    height: float


class ParsePageRef(TypedDict):
    """Reference to the page an element was extracted from.

    `pageIndex` and dimensions are always populated; `pageNumber` carries the
    page's visible label (e.g. `"1"`, `"iv"`) and may be absent if the
    document does not declare one.
    """

    pageIndex: int
    width: float
    height: float
    pageNumber: NotRequired[str]


class ParseWord(TypedDict, total=False):
    """A single OCR'd word from a `paragraph` or `handwriting` element."""

    text: str
    bounds: ParseBounds
    confidence: float


# Element variants (discriminated on `type`) -------------------------------

ParagraphRole = Literal[
    "Text",
    "Title",
    "SectionHeader",
    "Header",
    "Footer",
    "Caption",
    "Footnote",
    "ListItem",
    "PageNumber",
    "Code",
    "CheckboxSelected",
    "CheckboxUnselected",
]


class _ElementBase(TypedDict, total=False):
    """Fields shared by every element variant.

    Kept private; the public element types below extend the relevant subset
    explicitly so that `type` is a literal on each variant (enabling
    discriminated-union narrowing).
    """

    id: str
    bounds: ParseBounds
    confidence: float
    readingOrder: int
    page: ParsePageRef


class ParagraphElement(_ElementBase, total=False):
    """A paragraph (or other text-bearing block) of extracted text."""

    type: Literal["paragraph"]
    text: str
    role: ParagraphRole
    words: list[ParseWord] | None


class HandwritingElement(_ElementBase, total=False):
    """Handwritten text extracted by `understand` / `agentic` modes."""

    type: Literal["handwriting"]
    text: str
    words: list[ParseWord] | None


class FormulaElement(_ElementBase, total=False):
    """A mathematical formula, expressed in LaTeX."""

    type: Literal["formula"]
    latex: str


PictureClassification = Literal[
    "chart",
    "diagram",
    "logo",
    "photo",
    "screenshot",
    "signature",
    "other",
]


class PictureElement(_ElementBase, total=False):
    """An image, chart, diagram, or other non-text region."""

    type: Literal["picture"]
    classification: PictureClassification
    classificationConfidence: float
    altDescription: str
    captionIds: list[str]
    footnoteIds: list[str]


class TableCell(TypedDict, total=False):
    """One cell of a `TableElement`."""

    id: str
    bounds: ParseBounds
    confidence: float
    row: int
    column: int
    rowSpan: int
    colSpan: int
    text: str


class TableElement(_ElementBase, total=False):
    """A tabular region with cell-level extraction."""

    type: Literal["table"]
    rowCount: int
    columnCount: int
    cells: list[TableCell] | None
    captionIds: list[str]
    footnoteIds: list[str]


KeyValueEntityType = Literal["QUESTION", "ANSWER", "HEADER", "OTHER"]


class KeyValueEntity(TypedDict, total=False):
    """One side (key or value) of a `KeyValuePair`."""

    id: str
    bounds: ParseBounds
    confidence: float
    entityType: KeyValueEntityType
    value: str


class KeyValuePair(TypedDict, total=False):
    """A linked key/value pair within a `KeyValueRegionElement`."""

    id: str
    key: KeyValueEntity
    value: KeyValueEntity
    relationshipConfidence: float


class KeyValueRegionElement(_ElementBase, total=False):
    """A form-field region whose contents pair keys to values."""

    type: Literal["keyValueRegion"]
    pairs: list[KeyValuePair]


ParseElement = (
    ParagraphElement
    | HandwritingElement
    | FormulaElement
    | PictureElement
    | TableElement
    | KeyValueRegionElement
)
"""Discriminated union of every element variant the parse endpoint returns.

Narrow by reading the `type` literal, e.g.:

```python
for element in response["output"]["elements"]:
    if element["type"] == "table":
        # element is now narrowed to TableElement
        print(element["rowCount"])
```
"""


# Output shapes ------------------------------------------------------------


class ParseOutputMarkdown(TypedDict):
    """`response.output` when `output.format == "markdown"`."""

    markdown: str


class ParseOutputElements(TypedDict):
    """`response.output` when `output.format == "spatial"`."""

    elements: list[ParseElement]


ParseOutputBody = ParseOutputMarkdown | ParseOutputElements
"""Discriminated by the requested output format: markdown vs elements.

In practice callers know which format they requested, so the response can be
narrowed by inspecting which key is present.
"""


# Envelope sub-objects -----------------------------------------------------


class ParseMetrics(TypedDict, total=False):
    """Per-request processing metrics."""

    processingTimeMs: int
    pagesProcessed: int


class ParseConfiguration(TypedDict, total=False):
    """Server-reported configuration the request was executed under.

    `mode` echoes the requested `ParseMode`. `outputFormat` echoes the
    requested `ParseOutputFormat` ("markdown" or "spatial").
    """

    mode: ParseMode
    outputFormat: ParseOutputFormat


class ParseUsage(TypedDict, total=False):
    """Wraps the extraction-credit accounting under its wire key.

    The server uses the snake_case key `data_extraction_credits` here even
    though every other field in the response is camelCase; the TypedDict
    mirrors the wire format verbatim. The inner `ExtractionCredits` type
    lives in `nutrient_dws.types.extraction_credits` because the same
    credit-accounting shape will surface on future endpoints that bill
    against the extraction-credits bucket.
    """

    data_extraction_credits: ExtractionCredits


class ParseFailingPath(TypedDict, total=False):
    """One entry of `errorDetails.failingPaths` on a 4xx error response."""

    path: str
    details: str


class ParseErrorDetails(TypedDict, total=False):
    """Structured server-side error details, when present."""

    source: str
    code: str
    failingPaths: list[ParseFailingPath]


class ParseResponse(TypedDict, total=False):
    """Top-level response envelope from `POST /extraction/parse`.

    On a successful 200 response, `status == 200`, `output` is populated, and
    `metrics` / `usage` / `configuration` are present. Error responses (4xx
    / 5xx) reuse the same envelope but populate `errorMessage` +
    `errorDetails` instead of `output`; the client raises before returning
    them, so the response object the user sees is always a success.
    """

    status: int
    requestId: str
    output: ParseOutputBody
    metrics: ParseMetrics
    usage: ParseUsage
    configuration: ParseConfiguration
    errorMessage: str
    errorDetails: ParseErrorDetails
