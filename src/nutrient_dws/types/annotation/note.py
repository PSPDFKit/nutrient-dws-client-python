from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2

if TYPE_CHECKING:
    from nutrient_dws.types.misc import AnnotationPlainText, IsCommentThreadRoot

NoteIcon = Literal[
    "comment",
    "rightPointer",
    "rightArrow",
    "check",
    "circle",
    "cross",
    "insert",
    "newParagraph",
    "note",
    "paragraph",
    "help",
    "star",
    "key",
]


class NoteBase(TypedDict):
    text: AnnotationPlainText
    icon: NoteIcon
    color: NotRequired[str]
    isCommentThreadRoot: NotRequired[IsCommentThreadRoot]


class V1(BaseV1, NoteBase):
    pass


class V2(BaseV2, NoteBase):
    pass


NoteAnnotation = Union[V1, V2]
