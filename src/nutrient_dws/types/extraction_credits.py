"""Shared types for the DWS **extraction credits** billing bucket.

Extraction credits are billed separately from the processor API credits
consumed by `/build`, `/sign`, OCR, etc. The types in this module are
intentionally endpoint-agnostic so they can be reused by any future
endpoint that surfaces extraction-credit accounting in its response.
"""

from typing import TypedDict


class ExtractionCredits(TypedDict, total=False):
    """Credit accounting for one request against the extraction-credits bucket.

    `cost` is the number of **extraction credits** debited by the request
    (NOT processor API credits). `remainingCredits` is the post-debit
    balance in the same bucket.
    """

    cost: float
    remainingCredits: float
