from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.redaction import RedactionAnnotation
from nutrient_dws.types.file_handle import FileHandle
from nutrient_dws.types.misc import OcrLanguage, WatermarkDimension


class ApplyInstantJsonAction(TypedDict):
    type: Literal["applyInstantJson"]
    file: FileHandle


class ApplyXfdfActionOptions(TypedDict, total=False):
    ignorePageRotation: NotRequired[bool]
    richTextEnabled: NotRequired[bool]


class ApplyXfdfAction(TypedDict):
    type: Literal["applyXfdf"]
    file: FileHandle
    ignorePageRotation: NotRequired[bool]
    richTextEnabled: NotRequired[bool]


class FlattenAction(TypedDict):
    type: Literal["flatten"]
    annotationIds: NotRequired[list[str | int]]


class OcrAction(TypedDict):
    type: Literal["ocr"]
    language: OcrLanguage | list[OcrLanguage]


class RotateAction(TypedDict):
    type: Literal["rotate"]
    rotateBy: Literal[90, 180, 270]


class BaseWatermarkActionOptions(TypedDict):
    width: WatermarkDimension
    height: WatermarkDimension
    top: NotRequired[WatermarkDimension]
    right: NotRequired[WatermarkDimension]
    bottom: NotRequired[WatermarkDimension]
    left: NotRequired[WatermarkDimension]
    rotation: NotRequired[float]
    opacity: NotRequired[float]


class BaseWatermarkAction(BaseWatermarkActionOptions):
    type: Literal["watermark"]


class TextWatermarkActionOptions(BaseWatermarkActionOptions, total=False):
    fontFamily: NotRequired[str]
    fontSize: NotRequired[int]
    fontColor: NotRequired[str]
    fontStyle: NotRequired[list[Literal["bold", "italic"]]]


class TextWatermarkAction(BaseWatermarkAction):
    text: str
    fontFamily: NotRequired[str]
    fontSize: NotRequired[int]
    fontColor: NotRequired[str]
    fontStyle: NotRequired[list[Literal["bold", "italic"]]]


class ImageWatermarkActionOptions(BaseWatermarkActionOptions, total=False): ...


class ImageWatermarkAction(BaseWatermarkAction):
    image: FileHandle


WatermarkAction = Union[TextWatermarkAction, ImageWatermarkAction]

SearchPreset = Literal[
    "credit-card-number",
    "date",
    "email-address",
    "international-phone-number",
    "ipv4",
    "ipv6",
    "mac-address",
    "north-american-phone-number",
    "social-security-number",
    "time",
    "url",
    "us-zip-code",
    "vin",
]


class CreateRedactionsStrategyOptionsPreset(TypedDict):
    includeAnnotations: NotRequired[bool]
    start: NotRequired[int]
    limit: NotRequired[int]


class CreateRedactionsStrategyOptionsRegex(TypedDict):
    includeAnnotations: NotRequired[bool]
    caseSensitive: NotRequired[bool]
    start: NotRequired[int]
    limit: NotRequired[int]


class CreateRedactionsStrategyOptionsText(TypedDict):
    includeAnnotations: NotRequired[bool]
    caseSensitive: NotRequired[bool]
    start: NotRequired[int]
    limit: NotRequired[int]


class BaseCreateRedactionsOptions(TypedDict):
    content: NotRequired[RedactionAnnotation]


class BaseCreateRedactionsAction(BaseCreateRedactionsOptions):
    type: Literal["createRedactions"]


class CreateRedactionsActionPreset(TypedDict, BaseCreateRedactionsAction):
    strategy: Literal["preset"]
    strategyOptions: CreateRedactionsStrategyOptionsPreset


class CreateRedactionsActionRegex(TypedDict, BaseCreateRedactionsAction):
    strategy: Literal["regex"]
    strategyOptions: CreateRedactionsStrategyOptionsRegex


class CreateRedactionsActionText(TypedDict, BaseCreateRedactionsAction):
    strategy: Literal["text"]
    strategyOptions: CreateRedactionsStrategyOptionsText


CreateRedactionsAction = Union[
    CreateRedactionsActionPreset,
    CreateRedactionsActionRegex,
    CreateRedactionsActionText,
]


class ApplyRedactionsAction(TypedDict):
    type: Literal["applyRedactions"]


BuildAction = Union[
    ApplyInstantJsonAction,
    ApplyXfdfAction,
    FlattenAction,
    OcrAction,
    RotateAction,
    WatermarkAction,
    CreateRedactionsAction,
    ApplyRedactionsAction,
]
