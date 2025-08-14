from __future__ import annotations

from typing import Literal, Union, TypedDict
from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2
from nutrient_dws.types.misc import AnnotationRotation, AnnotationNote


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
