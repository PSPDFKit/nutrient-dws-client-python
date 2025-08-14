"""Base builder class that all builders extend from."""
from abc import ABC, abstractmethod
from typing import Any, Generic, Literal, TypeVar, Union

from nutrient_dws.builder.staged_builders import TypedWorkflowResult
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
        path: Union[Literal["/build"], Literal["/analyze_build"]],
        options: Union[BuildRequestData, AnalyzeBuildRequestData],
        response_type: str = "json",
    ) -> Any:
        """Sends a request to the API."""
        config: RequestConfig[Union[BuildRequestData, AnalyzeBuildRequestData]] = {
            "endpoint": path,
            "method": "POST",
            "data": options,
            "headers": None
        }

        response = await send_request(config, self.client_options, response_type)
        return response["data"]

    @abstractmethod
    async def execute(self) -> TypedWorkflowResult:
        """Abstract method that child classes must implement for execution."""
        pass
