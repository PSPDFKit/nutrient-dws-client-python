from typing import TypedDict, Union, Optional, Literal
from typing_extensions import NotRequired


class FormFieldValue(TypedDict):
    name: str
    value: NotRequired[Union[Optional[str], list[str]]]
    type: Literal["pspdfkit/form-field-value"]
    v: Literal[1]
    optionIndexes: NotRequired[list[int]]
    isFitting: NotRequired[bool]