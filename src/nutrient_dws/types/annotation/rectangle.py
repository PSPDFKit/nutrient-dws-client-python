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
    )


class RectangleBase(TypedDict):
    type: Literal["pspdfkit/shape/rectangle"]
    fillColor: NotRequired[FillColor]
    cloudyBorderIntensity: NotRequired[CloudyBorderIntensity]
    cloudyBorderInset: NotRequired[CloudyBorderInset]


class V1(BaseV1, BaseShapeAnnotation, RectangleBase): ...


class V2(BaseV2, BaseShapeAnnotation, RectangleBase): ...


RectangleAnnotation = Union[V1, V2]
