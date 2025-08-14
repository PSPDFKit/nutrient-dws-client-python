from __future__ import annotations

from typing import Literal, Union, TypedDict
from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2
from nutrient_dws.types.misc import Lines, BackgroundColor, BlendMode, AnnotationNote


class InkBase(TypedDict):
    type: Literal["pspdfkit/ink"]
    lines: Lines
    lineWidth: int
    isDrawnNaturally: NotRequired[bool]
    isSignature: NotRequired[bool]
    strokeColor: NotRequired[str]
    backgroundColor: NotRequired[BackgroundColor]
    blendMode: NotRequired[BlendMode]
    note: NotRequired[AnnotationNote]


class V1(BaseV1, InkBase):
    pass

class V2(BaseV2, InkBase):
    pass

InkAnnotation = Union[V1, V2]