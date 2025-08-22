"""Factory function to create a new workflow builder with staged interface."""

from collections.abc import Callable

from nutrient_dws.builder.builder import StagedWorkflowBuilder
from nutrient_dws.builder.staged_builders import WorkflowInitialStage
from nutrient_dws.http import NutrientClientOptions


def workflow(
    api_key: str | Callable[[], str],
    base_url: str | None = None,
    timeout: int | None = None,
) -> WorkflowInitialStage:
    r"""Factory function to create a new workflow builder with staged interface.

    Args:
        api_key: API key or API key getter
        base_url: DWS Base url
        timeout: DWS request timeout

    Returns:
        A new staged workflow builder instance

    Example:
        ```python
        from nutrient_dws import workflow

        # Create a workflow
        result = await workflow({
            'apiKey': 'your-api-key'
        }) \\
        .add_file_part('document.pdf') \\
        .apply_action(BuildActions.ocr('english')) \\
        .output_pdf() \\
        .execute()
        ```
    """
    client_options = NutrientClientOptions(
        apiKey=api_key, baseUrl=base_url, timeout=timeout
    )
    return StagedWorkflowBuilder(client_options)
