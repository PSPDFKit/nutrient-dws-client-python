from __future__ import annotations

from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired


class BaseAction(TypedDict):
    subAction: NotRequired[Action]


class GoToAction(BaseAction):
    type: Literal["goTo"]
    pageIndex: int


class GoToRemoteAction(BaseAction):
    type: Literal["goToRemote"]
    relativePath: str
    namedDestination: NotRequired[str]


class GoToEmbeddedAction(BaseAction):
    type: Literal["goToEmbedded"]
    relativePath: str
    newWindow: NotRequired[bool]
    targetType: NotRequired[Literal["parent", "child"]]


class LaunchAction(BaseAction):
    type: Literal["launch"]
    filePath: str


class URIAction(BaseAction):
    type: Literal["uri"]
    uri: str


class AnnotationReference(TypedDict):
    fieldName: NotRequired[str]
    pdfObjectId: NotRequired[int]


class HideAction(BaseAction):
    type: Literal["hide"]
    hide: bool
    annotationReferences: list[AnnotationReference]


class JavaScriptAction(BaseAction):
    type: Literal["javascript"]
    script: str


class SubmitFormAction(BaseAction):
    type: Literal["submitForm"]
    uri: str
    flags: list[
        Literal[
            "includeExclude",
            "includeNoValueFields",
            "exportFormat",
            "getMethod",
            "submitCoordinated",
            "xfdf",
            "includeAppendSaves",
            "includeAnnotations",
            "submitPDF",
            "canonicalFormat",
            "excludeNonUserAnnotations",
            "excludeFKey",
            "embedForm",
        ]
    ]
    fields: NotRequired[list[AnnotationReference]]


class ResetFormAction(BaseAction):
    type: Literal["resetForm"]
    flags: NotRequired[Literal["includeExclude"]]
    fields: NotRequired[list[AnnotationReference]]


class NamedAction(BaseAction):
    type: Literal["named"]
    action: Literal[
        "nextPage",
        "prevPage",
        "firstPage",
        "lastPage",
        "goBack",
        "goForward",
        "goToPage",
        "find",
        "print",
        "outline",
        "search",
        "brightness",
        "zoomIn",
        "zoomOut",
        "saveAs",
        "info",
    ]


Action = Union[
    GoToAction,
    GoToRemoteAction,
    GoToEmbeddedAction,
    LaunchAction,
    URIAction,
    HideAction,
    JavaScriptAction,
    SubmitFormAction,
    ResetFormAction,
    NamedAction,
]
