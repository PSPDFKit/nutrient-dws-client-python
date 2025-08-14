from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired

from nutrient_dws.types.build_actions import BuildAction
from nutrient_dws.types.file_handle import FileHandle
from nutrient_dws.types.misc import PageLayout, PageRange


class FilePartOptions(TypedDict):
    password: NotRequired[str]
    pages: NotRequired[PageRange]
    layout: NotRequired[PageLayout]
    content_type: NotRequired[str]
    actions: NotRequired[list[BuildAction]]


class FilePart(FilePartOptions):
    file: FileHandle


class HTMLPartOptions(TypedDict):
    layout: NotRequired[PageLayout]


class HTMLPart(HTMLPartOptions):
    html: FileHandle
    assets: NotRequired[list[str]]
    actions: NotRequired[list[BuildAction]]


class NewPagePartOptions(TypedDict):
    pageCount: NotRequired[int]
    layout: NotRequired[PageLayout]


class NewPagePart(NewPagePartOptions):
    page: Literal["new"]
    actions: NotRequired[list[BuildAction]]


DocumentId = str


class DocumentEngineID(TypedDict):
    id: DocumentId | Literal["#self"]
    layer: NotRequired[str]


class DocumentPartOptions(TypedDict):
    password: NotRequired[str]
    pages: NotRequired[PageRange]
    layer: NotRequired[str]


class DocumentPart(TypedDict):
    document: DocumentEngineID
    password: NotRequired[str]
    pages: NotRequired[PageRange]
    actions: NotRequired[list[BuildAction]]


Part = Union[FilePart, HTMLPart, NewPagePart, DocumentPart]
