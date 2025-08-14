from __future__ import annotations

from typing import Literal, Union, TypedDict
from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1, V2 as BaseV2
from nutrient_dws.types.misc import BorderStyle, Font, FontSizeInt, FontSizeAuto, FontColor, HorizontalAlign, \
    VerticalAlign, AnnotationRotation, BackgroundColor


class WidgetBase(TypedDict):
    type: Literal["pspdfkit/widget"]
    formFieldName: NotRequired[str]
    borderColor: NotRequired[str]
    borderStyle: NotRequired[BorderStyle]
    borderWidth: NotRequired[int]
    font: NotRequired[Font]
    fontSize: NotRequired[Union[FontSizeInt, FontSizeAuto]]
    fontColor: NotRequired[FontColor]
    horizontalAlign: NotRequired[HorizontalAlign]
    verticalAlign: NotRequired[VerticalAlign]
    rotation: NotRequired[AnnotationRotation]
    backgroundColor: NotRequired[BackgroundColor]


class V1(BaseV1, WidgetBase):
    pass

class V2(BaseV2, WidgetBase):
    pass


WidgetAnnotation = Union[V1, V2]