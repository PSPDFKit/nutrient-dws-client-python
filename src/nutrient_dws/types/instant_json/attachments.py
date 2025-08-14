from typing import TypedDict, Optional
from typing_extensions import NotRequired


class Attachment(TypedDict):
    binary: NotRequired[str]
    contentType: NotRequired[str]


Attachments = Optional[dict[str, Attachment]]