from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2

if TYPE_CHECKING:
    from nutrient_dws.types.misc import (
        AnnotationPlainText,
        AnnotationRotation,
        BorderStyle,
        CloudyBorderInset,
        CloudyBorderIntensity,
        Font,
        FontColor,
        FontSizeInt,
        HorizontalAlign,
        LineCap,
        Point,
        VerticalAlign,
    )


class Callout(TypedDict):
    start: Point
    end: Point
    innerRectInset: list[float]
    cap: NotRequired[LineCap]
    knee: NotRequired[Point]


class TextBase(TypedDict):
    type: Literal["pspdfkit/text"]
    text: AnnotationPlainText
    fontSize: FontSizeInt
    fontStyle: NotRequired[list[Literal["bold", "italic"]]]
    fontColor: NotRequired[FontColor]
    font: NotRequired[Font]
    backgroundColor: NotRequired[str]
    horizontalAlign: NotRequired[HorizontalAlign]
    verticalAlign: NotRequired[VerticalAlign]
    rotation: NotRequired[AnnotationRotation]
    isFitting: NotRequired[bool]
    callout: NotRequired[Callout]
    borderStyle: NotRequired[BorderStyle]
    borderWidth: NotRequired[int]
    cloudyBorderIntensity: NotRequired[CloudyBorderIntensity]
    cloudyBorderInset: NotRequired[CloudyBorderInset]


class V1(BaseV1, TextBase):
    pass


class V2(BaseV2, TextBase):
    pass


TextAnnotation = Union[V1, V2]
