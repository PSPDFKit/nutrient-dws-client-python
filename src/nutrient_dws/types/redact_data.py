from typing import Literal, TypedDict

from typing_extensions import NotRequired

from nutrient_dws.types.misc import Pages


class RemoteFile(TypedDict):
    url: str


class Document(TypedDict):
    file: NotRequired[str | RemoteFile]
    pages: NotRequired[list[int] | Pages]


class Confidence(TypedDict):
    threshold: float


class RedactOptions(TypedDict):
    confidence: NotRequired[Confidence]


class RedactData(TypedDict):
    documents: list[Document]
    criteria: str
    redaction_state: NotRequired[Literal["stage", "apply"]]
    options: NotRequired[RedactOptions]
