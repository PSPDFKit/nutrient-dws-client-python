from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2

if TYPE_CHECKING:
    from nutrient_dws.types.misc import AnnotationNote, AnnotationRotation


class ImageBase(TypedDict):
    type: Literal["pspdfkit/image"]
    description: NotRequired[str]
    fileName: NotRequired[str]
    contentType: NotRequired[Literal["image/jpeg", "image/png", "application/pdf"]]
    imageAttachmentId: NotRequired[str]
    rotation: NotRequired[AnnotationRotation]
    isSignature: NotRequired[bool]
    note: NotRequired[AnnotationNote]


class V1(BaseV1, ImageBase):
    pass


class V2(BaseV2, ImageBase):
    pass


ImageAnnotation = Union[V1, V2]
