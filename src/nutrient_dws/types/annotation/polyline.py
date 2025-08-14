from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2
from nutrient_dws.types.annotation.base import BaseShapeAnnotation

if TYPE_CHECKING:
    from nutrient_dws.types.misc import (
        CloudyBorderInset,
        CloudyBorderIntensity,
        FillColor,
        LineCaps,
        Point,
    )


class PolylineBase(TypedDict):
    type: Literal["pspdfkit/shape/polyline"]
    fillColor: NotRequired[FillColor]
    points: list[Point]
    lineCaps: NotRequired[LineCaps]
    cloudyBorderIntensity: NotRequired[CloudyBorderIntensity]
    cloudyBorderInset: NotRequired[CloudyBorderInset]


class V1(BaseV1, BaseShapeAnnotation, PolylineBase): ...


class V2(BaseV2, BaseShapeAnnotation, PolylineBase): ...


PolylineAnnotation = Union[V1, V2]
