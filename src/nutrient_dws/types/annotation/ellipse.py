from __future__ import annotations

from typing import Literal, TypedDict, Union
from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2, BaseShapeAnnotation
from nutrient_dws.types.misc import FillColor, CloudyBorderIntensity, CloudyBorderInset


class EllipseBase(TypedDict):
    type: Literal["pspdfkit/shape/ellipse"]
    fillColor: NotRequired[FillColor]
    cloudyBorderIntensity: NotRequired[CloudyBorderIntensity]
    cloudyBorderInset: NotRequired[CloudyBorderInset]

class V1(BaseV1, BaseShapeAnnotation, EllipseBase):
    ...

class V2(BaseV2, BaseShapeAnnotation, EllipseBase):
    ...

EllipseAnnotation = Union[V1, V2]
