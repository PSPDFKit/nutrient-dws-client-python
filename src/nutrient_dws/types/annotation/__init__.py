from typing import Union

from nutrient_dws.types.annotation.ellipse import EllipseAnnotation
from nutrient_dws.types.annotation.image import ImageAnnotation
from nutrient_dws.types.annotation.ink import InkAnnotation
from nutrient_dws.types.annotation.line import LineAnnotation
from nutrient_dws.types.annotation.link import LinkAnnotation
from nutrient_dws.types.annotation.markup import MarkupAnnotation
from nutrient_dws.types.annotation.note import NoteAnnotation
from nutrient_dws.types.annotation.polygon import PolygonAnnotation
from nutrient_dws.types.annotation.polyline import PolylineAnnotation
from nutrient_dws.types.annotation.rectangle import RectangleAnnotation
from nutrient_dws.types.annotation.redaction import RedactionAnnotation
from nutrient_dws.types.annotation.stamp import StampAnnotation
from nutrient_dws.types.annotation.text import TextAnnotation
from nutrient_dws.types.annotation.widget import WidgetAnnotation

Annotation = Union[
    MarkupAnnotation,
    RedactionAnnotation,
    TextAnnotation,
    InkAnnotation,
    LinkAnnotation,
    NoteAnnotation,
    EllipseAnnotation,
    RectangleAnnotation,
    LineAnnotation,
    PolylineAnnotation,
    PolygonAnnotation,
    ImageAnnotation,
    StampAnnotation,
    WidgetAnnotation,
]
