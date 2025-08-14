from typing import TypedDict, Union

from typing_extensions import NotRequired


class RemoteFileHandle(TypedDict):
    url: str
    sha256: NotRequired[str]


FileHandle = Union[RemoteFileHandle, str]
