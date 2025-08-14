"""Base builder class that all builders extend from."""

from abc import ABC, abstractmethod
from typing import Any, Literal

from nutrient_dws.builder.staged_builders import (
    TypedWorkflowResult,
)
from nutrient_dws.http import (
    AnalyzeBuildRequestData,
    BuildRequestData,
    NutrientClientOptions,
    RequestConfig,
    send_request,
)


class BaseBuilder(ABC):
    """Base builder class that all builders extend from.
    Provides common functionality for API interaction.
    """

    def __init__(self, client_options: NutrientClientOptions) -> None:
        self.client_options = client_options

    async def _send_request(
        self,
        path: Literal["/build"] | Literal["/analyze_build"],
        options: BuildRequestData | AnalyzeBuildRequestData,
    ) -> Any:
        """Sends a request to the API."""
        config: RequestConfig[BuildRequestData | AnalyzeBuildRequestData] = {
            "endpoint": path,
            "method": "POST",
            "data": options,
            "headers": None,
        }

        response: Any = await send_request(config, self.client_options)
        return response["data"]

    @abstractmethod
    async def execute(self) -> TypedWorkflowResult:
        """Abstract method that child classes must implement for execution."""
        pass
