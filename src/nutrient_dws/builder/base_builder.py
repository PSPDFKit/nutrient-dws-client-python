"""Base builder class that all builders extend from."""

from abc import ABC, abstractmethod
from typing import Literal, Union, overload

from nutrient_dws.builder.staged_builders import (
    TypedWorkflowResult,
)
from nutrient_dws.errors import ValidationError
from nutrient_dws.http import (
    AnalyzeBuildRequestData,
    BuildRequestData,
    NutrientClientOptions,
    RequestConfig,
    is_post_analyse_build_request_config,
    is_post_build_request_config,
    send_request,
)
from nutrient_dws.types.analyze_response import AnalyzeBuildResponse
from nutrient_dws.types.build_response_json import BuildResponseJsonContents


class BaseBuilder(ABC):
    """Base builder class that all builders extend from.
    Provides common functionality for API interaction.
    """

    def __init__(self, client_options: NutrientClientOptions) -> None:
        self.client_options = client_options

    @overload
    async def _send_request(
        self, path: Literal["/build"], options: BuildRequestData
    ) -> Union[BuildResponseJsonContents, bytes, str]: ...

    @overload
    async def _send_request(
        self, path: Literal["/analyze_build"], options: AnalyzeBuildRequestData
    ) -> AnalyzeBuildResponse: ...

    async def _send_request(
        self,
        path: Literal["/build", "/analyze_build"],
        options: BuildRequestData | AnalyzeBuildRequestData,
    ) -> Union[BuildResponseJsonContents, bytes, str, AnalyzeBuildResponse]:
        """Sends a request to the API."""
        config = RequestConfig(endpoint=path, method="POST", data=options, headers=None)

        if is_post_build_request_config(config):
            response = await send_request(config, self.client_options)
            return response["data"]

        if is_post_analyse_build_request_config(config):
            analyze_response = await send_request(config, self.client_options)
            return analyze_response["data"]

        raise ValidationError(
            "Invalid _send_request args", {"path": path, "options": options}
        )

    @abstractmethod
    async def execute(self) -> TypedWorkflowResult:
        """Abstract method that child classes must implement for execution."""
        pass
