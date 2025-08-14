from __future__ import annotations

from typing import Literal, Union, TypedDict
from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2
from nutrient_dws.types.misc import BorderStyle, AnnotationNote


class LinkBase(TypedDict):
    type: Literal["pspdfkit/link"]
    borderColor: NotRequired[str]
    borderStyle: NotRequired[BorderStyle]
    borderWidth: NotRequired[int]
    note: NotRequired[AnnotationNote]


class V1(BaseV1, LinkBase):
    pass

class V2(BaseV2, LinkBase):
    pass

LinkAnnotation = Union[V1, V2]