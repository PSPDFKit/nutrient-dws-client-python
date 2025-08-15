from typing import Any, Literal, Optional, TypedDict

from typing_extensions import NotRequired


class PageRange(TypedDict):
    start: NotRequired[int]
    end: NotRequired[int]


class Pages(TypedDict):
    start: int
    end: int


class Size(TypedDict):
    width: NotRequired[float]
    height: NotRequired[float]


class Margin(TypedDict):
    left: NotRequired[float]
    top: NotRequired[float]
    right: NotRequired[float]
    bottom: NotRequired[float]


class PageLayout(TypedDict):
    orientation: NotRequired[Literal["portrait", "landscape"]]
    size: NotRequired[
        Literal["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "Letter", "Legal"]
        | Size
    ]
    margin: NotRequired[Margin]


OcrLanguage = Literal[
    "afrikaans",
    "albanian",
    "arabic",
    "armenian",
    "azerbaijani",
    "basque",
    "belarusian",
    "bengali",
    "bosnian",
    "bulgarian",
    "catalan",
    "chinese",
    "croatian",
    "czech",
    "danish",
    "dutch",
    "english",
    "finnish",
    "french",
    "german",
    "indonesian",
    "italian",
    "malay",
    "norwegian",
    "polish",
    "portuguese",
    "serbian",
    "slovak",
    "slovenian",
    "spanish",
    "swedish",
    "turkish",
    "welsh",
    "afr",
    "amh",
    "ara",
    "asm",
    "aze",
    "bel",
    "ben",
    "bod",
    "bos",
    "bre",
    "bul",
    "cat",
    "ceb",
    "ces",
    "chr",
    "cos",
    "cym",
    "dan",
    "deu",
    "div",
    "dzo",
    "ell",
    "eng",
    "enm",
    "epo",
    "equ",
    "est",
    "eus",
    "fao",
    "fas",
    "fil",
    "fin",
    "fra",
    "frk",
    "frm",
    "fry",
    "gla",
    "gle",
    "glg",
    "grc",
    "guj",
    "hat",
    "heb",
    "hin",
    "hrv",
    "hun",
    "hye",
    "iku",
    "ind",
    "isl",
    "ita",
    "jav",
    "jpn",
    "kan",
    "kat",
    "kaz",
    "khm",
    "kir",
    "kmr",
    "kor",
    "kur",
    "lao",
    "lat",
    "lav",
    "lit",
    "ltz",
    "mal",
    "mar",
    "mkd",
    "mlt",
    "mon",
    "mri",
    "msa",
    "mya",
    "nep",
    "nld",
    "nor",
    "oci",
    "ori",
    "osd",
    "pan",
    "pol",
    "por",
    "pus",
    "que",
    "ron",
    "rus",
    "san",
    "sin",
    "slk",
    "slv",
    "snd",
    "sp1",
    "spa",
    "sqi",
    "srp",
    "sun",
    "swa",
    "swe",
    "syr",
    "tam",
    "tat",
    "tel",
    "tgk",
    "tgl",
    "tha",
    "tir",
    "ton",
    "tur",
    "uig",
    "ukr",
    "urd",
    "uzb",
    "vie",
    "yid",
    "yor",
]


class WatermarkDimension(TypedDict):
    value: float
    unit: Literal["pt", "%"]


PageIndex = int


AnnotationBbox = list[float]


AnnotationOpacity = float


PdfObjectId = int


AnnotationCustomData = Optional[dict[str, Any]]


Rect = list[float]


AnnotationRotation = Literal[0, 90, 180, 270]


AnnotationNote = str


BlendMode = Literal[
    "normal",
    "multiply",
    "screen",
    "overlay",
    "darken",
    "lighten",
    "colorDodge",
    "colorBurn",
    "hardLight",
    "softLight",
    "difference",
    "exclusion",
]


IsCommentThreadRoot = bool


CloudyBorderIntensity = float


CloudyBorderInset = list[float]


FillColor = str


MeasurementScale = TypedDict(
    "MeasurementScale",
    {
        "unitFrom": NotRequired[Literal["in", "mm", "cm", "pt"]],
        "unitTo": NotRequired[
            Literal["in", "mm", "cm", "pt", "ft", "m", "yd", "km", "mi"]
        ],
        "from": NotRequired[float],
        "to": NotRequired[float],
    },
)


MeasurementPrecision = Literal["whole", "oneDp", "twoDp", "threeDp", "fourDp"]


FontSizeInt = int


FontStyle = list[Literal["bold", "italic"]]


FontColor = str


Font = str


HorizontalAlign = Literal["left", "center", "right"]


VerticalAlign = Literal["top", "center", "bottom"]


Point = list[float]


LineCap = Literal[
    "square",
    "circle",
    "diamond",
    "openArrow",
    "closedArrow",
    "butt",
    "reverseOpenArrow",
    "reverseClosedArrow",
    "slash",
]


BorderStyle = Literal["solid", "dashed", "beveled", "inset", "underline"]


class LineCaps(TypedDict):
    start: NotRequired[LineCap]
    end: NotRequired[LineCap]


AnnotationPlainText = str

BackgroundColor = str

FontSizeAuto = Literal["auto"]


Intensity = float


class Lines(TypedDict):
    intensities: NotRequired[list[list[Intensity]]]
    points: NotRequired[list[list[Point]]]
