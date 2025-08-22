from typing import Literal, TypedDict

from typing_extensions import NotRequired

from nutrient_dws.types.instant_json.actions import Action


class Bookmark(TypedDict):
    name: NotRequired[str]
    type: Literal["pspdfkit/bookmark"]
    v: Literal[1]
    action: Action
    pdfBookmarkId: NotRequired[str]
