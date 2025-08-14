from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

if TYPE_CHECKING:
    from nutrient_dws.types.misc import PageIndex, PdfObjectId


class AnnotationText(TypedDict):
    format: NotRequired[Literal["xhtml", "plain"]]
    value: NotRequired[str]


IsoDateTime = str


CustomData = Optional[dict[str, Any]]


class V2(TypedDict):
    type: Literal["pspdfkit/comment"]
    pageIndex: PageIndex
    rootId: str
    text: AnnotationText
    v: Literal[2]
    createdAt: NotRequired[IsoDateTime]
    creatorName: NotRequired[str]
    customData: NotRequired[CustomData | None]
    pdfObjectId: NotRequired[PdfObjectId]
    updatedAt: NotRequired[IsoDateTime]


class V1(TypedDict):
    type: Literal["pspdfkit/comment"]
    pageIndex: PageIndex
    rootId: str
    text: str
    v: Literal[1]
    createdAt: NotRequired[IsoDateTime]
    creatorName: NotRequired[str]
    customData: NotRequired[CustomData | None]
    pdfObjectId: NotRequired[PdfObjectId]
    updatedAt: NotRequired[IsoDateTime]


CommentContent = Union[V2, V1]
