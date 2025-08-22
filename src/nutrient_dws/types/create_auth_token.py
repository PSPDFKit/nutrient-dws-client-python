from typing import Literal, TypedDict

from typing_extensions import NotRequired


class CreateAuthTokenParameters(TypedDict):
    allowedOperations: NotRequired[
        list[
            Literal[
                "annotations_api",
                "compression_api",
                "data_extraction_api",
                "digital_signatures_api",
                "document_editor_api",
                "html_conversion_api",
                "image_conversion_api",
                "image_rendering_api",
                "email_conversion_api",
                "linearization_api",
                "ocr_api",
                "office_conversion_api",
                "pdfa_api",
                "pdf_to_office_conversion_api",
                "redaction_api",
            ]
        ]
    ]
    allowedOrigins: NotRequired[list[str]]
    expirationTime: NotRequired[int]


class CreateAuthTokenResponse(TypedDict):
    id: NotRequired[str]
    accessToken: NotRequired[str]
