from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2

if TYPE_CHECKING:
    from nutrient_dws.types.misc import (
        AnnotationRotation,
        BackgroundColor,
        BorderStyle,
        Font,
        FontColor,
        FontSizeAuto,
        FontSizeInt,
        HorizontalAlign,
        VerticalAlign,
    )


class WidgetBase(TypedDict):
    type: Literal["pspdfkit/widget"]
    formFieldName: NotRequired[str]
    borderColor: NotRequired[str]
    borderStyle: NotRequired[BorderStyle]
    borderWidth: NotRequired[int]
    font: NotRequired[Font]
    fontSize: NotRequired[FontSizeInt | FontSizeAuto]
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
