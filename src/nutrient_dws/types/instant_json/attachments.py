from typing import Optional, TypedDict

from typing_extensions import NotRequired


class Attachment(TypedDict):
    binary: NotRequired[str]
    contentType: NotRequired[str]


Attachments = Optional[dict[str, Attachment]]
