from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.annotation.base import V1 as BaseV1
from nutrient_dws.types.annotation.base import V2 as BaseV2

if TYPE_CHECKING:
    from nutrient_dws.types.misc import AnnotationNote, AnnotationRotation


class StampBase(TypedDict):
    type: Literal["pspdfkit/stamp"]
    stampType: Literal[
        "Accepted",
        "Approved",
        "AsIs",
        "Completed",
        "Confidential",
        "Departmental",
        "Draft",
        "Experimental",
        "Expired",
        "Final",
        "ForComment",
        "ForPublicRelease",
        "InformationOnly",
        "InitialHere",
        "NotApproved",
        "NotForPublicRelease",
        "PreliminaryResults",
        "Rejected",
        "Revised",
        "SignHere",
        "Sold",
        "TopSecret",
        "Void",
        "Witness",
        "Custom",
    ]
    title: NotRequired[str]
    subtitle: NotRequired[str]
    color: NotRequired[str]
    rotation: NotRequired[AnnotationRotation]
    note: NotRequired[AnnotationNote]


class V1(BaseV1, StampBase):
    pass


class V2(BaseV2, StampBase):
    pass


StampAnnotation = Union[V1, V2]
