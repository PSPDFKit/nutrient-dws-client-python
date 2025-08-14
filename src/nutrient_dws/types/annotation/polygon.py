from __future__ import annotations

from typing import Literal, TypedDict, Union
from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2, BaseShapeAnnotation
from nutrient_dws.types.misc import FillColor, CloudyBorderIntensity, Point


class PolygonBase(TypedDict):
    type: Literal["pspdfkit/shape/polygon"]
    fillColor: NotRequired[FillColor]
    points: list[Point]
    cloudyBorderIntensity: NotRequired[CloudyBorderIntensity]

class V1(BaseV1, BaseShapeAnnotation, PolygonBase):
    ...

class V2(BaseV2, BaseShapeAnnotation, PolygonBase):
    ...

PolygonAnnotation = Union[V1, V2]