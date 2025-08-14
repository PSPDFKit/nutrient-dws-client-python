from __future__ import annotations

from typing import Literal, Union, TypedDict
from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2
from nutrient_dws.types.misc import Rect, BlendMode, AnnotationNote, IsCommentThreadRoot


class MarkupBase(TypedDict):
    type: Literal[
        "pspdfkit/markup/highlight",
        "pspdfkit/markup/squiggly",
        "pspdfkit/markup/strikeout",
        "pspdfkit/markup/underline",
    ]
    rects: list[Rect]
    blendMode: NotRequired[BlendMode]
    color: str
    note: NotRequired[AnnotationNote]
    isCommentThreadRoot: NotRequired[IsCommentThreadRoot]

class V1(BaseV1, MarkupBase):
    ...


class V2(BaseV2, MarkupBase):
    ...

MarkupAnnotation = Union[V1, V2]
