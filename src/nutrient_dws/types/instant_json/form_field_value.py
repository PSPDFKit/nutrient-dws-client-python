from typing import Literal, TypedDict

from typing_extensions import NotRequired


class FormFieldValue(TypedDict):
    name: str
    value: NotRequired[str | None | list[str]]
    type: Literal["pspdfkit/form-field-value"]
    v: Literal[1]
    optionIndexes: NotRequired[list[int]]
    isFitting: NotRequired[bool]
