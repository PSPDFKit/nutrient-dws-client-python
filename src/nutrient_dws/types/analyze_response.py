from typing import Literal, TypedDict

from typing_extensions import NotRequired


class RequiredFeatures(TypedDict):
    unit_cost: NotRequired[float]
    unit_type: NotRequired[Literal["per_use", "per_output_page"]]
    units: NotRequired[int]
    cost: NotRequired[float]
    usage: NotRequired[list[str]]


class AnalyzeBuildResponse(TypedDict):
    cost: NotRequired[float]
    required_features: NotRequired[dict[str, RequiredFeatures]]
