from typing import Literal, TypedDict

from typing_extensions import NotRequired


class APIKeys(TypedDict):
    live: NotRequired[str]


SubscriptionType = Literal["free", "paid", "enterprise"]


class Usage(TypedDict):
    totalCredits: NotRequired[int]
    usedCredits: NotRequired[int]


class AccountInfo(TypedDict):
    apiKeys: NotRequired[APIKeys]
    signedIn: NotRequired[bool]
    subscriptionType: NotRequired[SubscriptionType]
    usage: NotRequired[Usage]
