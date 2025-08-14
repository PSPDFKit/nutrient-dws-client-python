from typing import Literal, TypedDict

from typing_extensions import NotRequired


class FailingPath(TypedDict):
    path: NotRequired[str]
    details: NotRequired[str]


class HostedErrorResponse(TypedDict):
    details: NotRequired[str]
    status: NotRequired[Literal[400, 402, 408, 413, 422, 500]]
    requestId: NotRequired[str]
    failingPaths: NotRequired[list[FailingPath]]
