from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2
from nutrient_dws.types.annotation.base import BaseShapeAnnotation

if TYPE_CHECKING:
    from nutrient_dws.types.misc import FillColor, LineCaps, Point


class LineBase(TypedDict):
    type: Literal["pspdfkit/shape/line"]
    startPoint: Point
    endPoint: Point
    fillColor: NotRequired[FillColor]
    lineCaps: NotRequired[LineCaps]


class V1(BaseV1, BaseShapeAnnotation, LineBase): ...


class V2(BaseV2, BaseShapeAnnotation, LineBase): ...


LineAnnotation = Union[V1, V2]
