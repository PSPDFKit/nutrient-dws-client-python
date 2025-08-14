from typing import TypedDict

from typing_extensions import NotRequired

PlainText = str


class JsonContentsBbox(TypedDict):
    """Represents a rectangular region on the page."""

    left: float
    top: float
    width: float
    height: float


class Character(TypedDict):
    """Character in structured text."""

    bbox: JsonContentsBbox
    char: str


class Line(TypedDict):
    """Line in structured text."""

    bbox: JsonContentsBbox
    text: str


class Word(TypedDict):
    """Word in structured text."""

    bbox: JsonContentsBbox
    text: str


class Paragraph(TypedDict):
    """Paragraph in structured text."""

    bbox: JsonContentsBbox
    text: str


class StructuredText(TypedDict):
    """Structured text content."""

    characters: NotRequired[list[Character]]
    lines: NotRequired[list[Line]]
    paragraphs: NotRequired[list[Paragraph]]
    words: NotRequired[list[Word]]


class KVPKey(TypedDict):
    """Key-value pair key."""

    bbox: JsonContentsBbox
    confidence: float
    text: str


class KVPValue(TypedDict):
    """Key-value pair value."""

    bbox: JsonContentsBbox
    confidence: float
    text: str


class KeyValuePair(TypedDict):
    """Detected key-value pair."""

    confidence: float
    key: KVPKey
    value: KVPValue


class TableCell(TypedDict):
    """Table cell."""

    bbox: JsonContentsBbox
    rowIndex: int
    colIndex: int
    text: str


class TableColumn(TypedDict):
    """Table column."""

    bbox: JsonContentsBbox


class TableLine(TypedDict):
    """Table line."""

    bbox: JsonContentsBbox


class TableRow(TypedDict):
    """Table row."""

    bbox: JsonContentsBbox


class Table(TypedDict):
    """Detected table."""

    confidence: float
    bbox: JsonContentsBbox
    cells: list[TableCell]
    columns: list[TableColumn]
    lines: list[TableLine]
    rows: list[TableRow]


class PageJsonContents(TypedDict):
    """JSON content for a single page."""

    pageIndex: int
    plainText: NotRequired[PlainText]
    structuredText: NotRequired[StructuredText]
    keyValuePairs: NotRequired[list[KeyValuePair]]
    tables: NotRequired[list[Table]]


class BuildResponseJsonContents(TypedDict):
    """Build response JSON contents."""

    pages: NotRequired[list[PageJsonContents]]
