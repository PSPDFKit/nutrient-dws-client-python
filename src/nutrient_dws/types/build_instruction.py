from typing import TypedDict

from typing_extensions import NotRequired

from nutrient_dws.types.build_actions import BuildAction
from nutrient_dws.types.build_output import BuildOutput
from nutrient_dws.types.input_parts import Part


class BuildInstructions(TypedDict):
    parts: list[Part]
    actions: NotRequired[list[BuildAction]]
    output: NotRequired[BuildOutput]
