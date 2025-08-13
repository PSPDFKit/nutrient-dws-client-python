"""Factory function to create a new workflow builder with staged interface."""
from nutrient_dws.builder.builder import StagedWorkflowBuilder
from nutrient_dws.builder.staged_builders import WorkflowInitialStage
from nutrient_dws.http import NutrientClientOptions


def workflow(client_options: NutrientClientOptions) -> WorkflowInitialStage:
    """Factory function to create a new workflow builder with staged interface.

    Args:
        client_options: Client configuration options

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
    return StagedWorkflowBuilder(client_options)
