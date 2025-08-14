from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2

if TYPE_CHECKING:
    from nutrient_dws.types.misc import AnnotationNote, BorderStyle


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
