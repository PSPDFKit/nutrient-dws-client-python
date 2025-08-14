from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2
from nutrient_dws.types.annotation.base import BaseShapeAnnotation

if TYPE_CHECKING:
    from nutrient_dws.types.misc import CloudyBorderIntensity, FillColor, Point


class PolygonBase(TypedDict):
    type: Literal["pspdfkit/shape/polygon"]
    fillColor: NotRequired[FillColor]
    points: list[Point]
    cloudyBorderIntensity: NotRequired[CloudyBorderIntensity]


class V1(BaseV1, BaseShapeAnnotation, PolygonBase): ...


class V2(BaseV2, BaseShapeAnnotation, PolygonBase): ...


PolygonAnnotation = Union[V1, V2]
