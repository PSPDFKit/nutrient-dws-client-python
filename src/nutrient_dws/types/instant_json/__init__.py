from typing import Literal, TypedDict

from typing_extensions import NotRequired

from nutrient_dws.types.annotation import Annotation
from nutrient_dws.types.instant_json.attachments import Attachments
from nutrient_dws.types.instant_json.bookmark import Bookmark
from nutrient_dws.types.instant_json.comment import CommentContent
from nutrient_dws.types.instant_json.form_field import FormField
from nutrient_dws.types.instant_json.form_field_value import FormFieldValue


class PdfId(TypedDict):
    permanent: NotRequired[str]
    changing: NotRequired[str]


class InstantJson(TypedDict):
    format: Literal["https://pspdfkit.com/instant-json/v1"]
    annotations: NotRequired[list[Annotation]]
    attachments: NotRequired[Attachments]
    formFields: NotRequired[list[FormField]]
    formFieldValues: NotRequired[list[FormFieldValue]]
    bookmarks: NotRequired[list[Bookmark]]
    comments: NotRequired[list[CommentContent]]
    skippedPdfObjectIds: NotRequired[list[int]]
    pdfId: NotRequired[PdfId]
