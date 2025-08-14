from __future__ import annotations

from typing import TypedDict, Union, Literal
from typing_extensions import NotRequired

from nutrient_dws.types.misc import AnnotationPlainText, IsCommentThreadRoot
from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2

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
