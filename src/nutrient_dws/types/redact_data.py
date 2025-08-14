from typing import TypedDict, Union, Literal
from typing_extensions import NotRequired

from nutrient_dws.types.misc import Pages


class RemoteFile(TypedDict):
    url: str

class Document(TypedDict):
    file: NotRequired[Union[str, RemoteFile]]
    pages: NotRequired[Union[list[int], Pages]]

class Confidence(TypedDict):
    threshold: float


class Options(TypedDict):
    confidence: NotRequired[Confidence]

class RedactData(TypedDict):
    documents: list[Document]
    criteria: str
    redaction_state: NotRequired[Literal["stage", "apply"]]
    options: NotRequired[Options]