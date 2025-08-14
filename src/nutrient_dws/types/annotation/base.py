from __future__ import annotations

from typing import Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired

from nutrient_dws.types.misc import AnnotationBbox, AnnotationCustomData, PageIndex, AnnotationOpacity, PdfObjectId, \
    AnnotationNote, MeasurementPrecision, MeasurementScale
from nutrient_dws.types.instant_json.actions import Action

class V1(TypedDict):
    v: Literal[1]
    pageIndex: int
    bbox: AnnotationBbox
    action: NotRequired[Action]
    opacity: NotRequired[float]
    pdfObjectId: NotRequired[int]
    id: NotRequired[str]
    flags: NotRequired[
        list[
            Literal[
                "noPrint",
                "noZoom",
                "noRotate",
                "noView",
                "hidden",
                "invisible",
                "readOnly",
                "locked",
                "toggleNoView",
                "lockedContents",
            ]
        ]
    ]
    createdAt: NotRequired[str]
    updatedAt: NotRequired[str]
    name: NotRequired[str]
    creatorName: NotRequired[str]
    customData: NotRequired[Optional[AnnotationCustomData]]


class V2(TypedDict):
    v: Literal[2]
    pageIndex: PageIndex
    bbox: AnnotationBbox
    action: NotRequired[Action]
    opacity: NotRequired[AnnotationOpacity]
    pdfObjectId: NotRequired[PdfObjectId]
    id: NotRequired[str]
    flags: NotRequired[
        list[
            Literal[
                "noPrint",
                "noZoom",
                "noRotate",
                "noView",
                "hidden",
                "invisible",
                "readOnly",
                "locked",
                "toggleNoView",
                "lockedContents",
            ]
        ]
    ]
    createdAt: NotRequired[str]
    updatedAt: NotRequired[str]
    name: NotRequired[str]
    creatorName: NotRequired[str]
    customData: NotRequired[Optional[AnnotationCustomData]]


class BaseShapeAnnotation(TypedDict):
    strokeDashArray: NotRequired[list[float]]
    strokeWidth: NotRequired[float]
    strokeColor: NotRequired[str]
    note: NotRequired[AnnotationNote]
    measurementScale: NotRequired[MeasurementScale]
    measurementPrecision: NotRequired[MeasurementPrecision]


BaseAnnotation = Union[V1, V2]
