from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2

if TYPE_CHECKING:
    from nutrient_dws.types.misc import AnnotationNote, AnnotationRotation, Rect


class RedactionBase(TypedDict):
    type: Literal["pspdfkit/markup/redaction"]
    rects: NotRequired[list[Rect]]
    outlineColor: NotRequired[str]
    fillColor: NotRequired[str]
    overlayText: NotRequired[str]
    repeatOverlayText: NotRequired[bool]
    color: NotRequired[str]
    rotation: NotRequired[AnnotationRotation]
    note: NotRequired[AnnotationNote]


class V1(BaseV1, RedactionBase): ...


class V2(BaseV2, RedactionBase): ...


RedactionAnnotation = Union[V1, V2]
