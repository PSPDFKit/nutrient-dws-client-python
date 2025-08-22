from typing import Literal, TypedDict

from typing_extensions import NotRequired


class Appearance(TypedDict):
    mode: NotRequired[
        Literal["signatureOnly", "signatureAndDescription", "descriptionOnly"]
    ]
    contentType: NotRequired[str]
    showWatermark: NotRequired[bool]
    showSignDate: NotRequired[bool]
    showDateTimezone: NotRequired[bool]


class Position(TypedDict):
    pageIndex: int
    rect: list[float]


class CreateDigitalSignature(TypedDict):
    signatureType: Literal["cms", "cades"]
    flatten: NotRequired[bool]
    formFieldName: NotRequired[str]
    appearance: NotRequired[Appearance]
    position: NotRequired[Position]
    cadesLevel: NotRequired[Literal["b-lt", "b-t", "b-b"]]
