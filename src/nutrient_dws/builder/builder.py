"""Staged workflow builder that provides compile-time safety through Python's type system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeGuard, cast

from nutrient_dws.builder.base_builder import BaseBuilder
from nutrient_dws.builder.constant import ActionWithFileInput, BuildOutputs
from nutrient_dws.builder.staged_builders import (
    ApplicableAction,
    BufferOutput,
    ContentOutput,
    JsonContentOutput,
    TypedWorkflowResult,
    WorkflowDryRunResult,
    WorkflowError,
    WorkflowExecuteCallback,
    WorkflowWithActionsStage,
    WorkflowWithOutputStage,
    WorkflowWithPartsStage,
)
from nutrient_dws.errors import ValidationError
from nutrient_dws.http import (
    AnalyzeBuildRequestData,
    BuildRequestData,
    NutrientClientOptions,
)
from nutrient_dws.inputs import (
    FileInput,
    NormalizedFileData,
    is_remote_file_input,
    process_file_input,
    validate_file_input,
)
from nutrient_dws.types.file_handle import FileHandle, RemoteFileHandle

if TYPE_CHECKING:
    from nutrient_dws.types.build_actions import BuildAction
    from nutrient_dws.types.build_instruction import BuildInstructions
    from nutrient_dws.types.build_output import (
        BuildOutput,
        ImageOutputOptions,
        JSONContentOutputOptions,
        PDFAOutputOptions,
        PDFOutput,
        PDFOutputOptions,
        PDFUAOutputOptions,
    )
    from nutrient_dws.types.build_response_json import BuildResponseJsonContents
    from nutrient_dws.types.input_parts import (
        DocumentPart,
        DocumentPartOptions,
        FilePart,
        FilePartOptions,
        HTMLPart,
        HTMLPartOptions,
        NewPagePart,
        NewPagePartOptions,
    )


class StagedWorkflowBuilder(
    BaseBuilder,
    WorkflowWithPartsStage,
    WorkflowWithOutputStage,
):
    """Staged workflow builder that provides compile-time safety through Python's type system.
    This builder ensures methods are only available at appropriate stages of the workflow.
    """

    def __init__(self, client_options: NutrientClientOptions) -> None:
        """Initialize the staged workflow builder.

        Args:
            client_options: Client configuration options
        """
        super().__init__(client_options)
        self.build_instructions: BuildInstructions = {"parts": []}
        self.assets: dict[str, FileInput] = {}
        self.asset_index = 0
        self.current_step = 0
        self.is_executed = False

    def _register_asset(self, asset: FileInput) -> str:
        """Register an asset in the workflow and return its key for use in actions.

        Args:
            asset: The asset to register

        Returns:
            The asset key that can be used in BuildActions
        """
        if not validate_file_input(asset):
            raise ValidationError(
                "Invalid file input provided to workflow", {"asset": asset}
            )

        if is_remote_file_input(asset):
            raise ValidationError(
                "Remote file input doesn't need to be registered", {"asset": asset}
            )

        asset_key = f"asset_{self.asset_index}"
        self.asset_index += 1
        self.assets[asset_key] = asset
        return asset_key

    def _ensure_not_executed(self) -> None:
        """Ensure the workflow hasn't been executed yet."""
        if self.is_executed:
            raise ValidationError(
                "This workflow has already been executed. Create a new workflow builder for additional operations."
            )

    def _validate(self) -> None:
        """Validate the workflow before execution."""
        if not self.build_instructions["parts"]:
            raise ValidationError("Workflow has no parts to execute")

        if "output" not in self.build_instructions:
            self.build_instructions["output"] = cast("PDFOutput", {"type": "pdf"})

    def _process_action(self, action: ApplicableAction) -> BuildAction:
        """Process an action, registering files if needed.

        Args:
            action: The action to process

        Returns:
            The processed action
        """
        if self._is_action_with_file_input(action):
            # Register the file and create the actual action
            if is_remote_file_input(action.fileInput):
                file_handle: FileHandle = RemoteFileHandle(url=action.fileInput)
            else:
                file_handle = self._register_asset(action.fileInput)
            return action.createAction(file_handle)
        else:
            return cast("BuildAction", action)

    def _is_action_with_file_input(
        self, action: ApplicableAction
    ) -> TypeGuard[ActionWithFileInput]:
        """Type guard to check if action needs file registration.

        Args:
            action: The action to check

        Returns:
            True if action needs file registration
        """
        return hasattr(action, "createAction")

    async def _prepare_files(self) -> dict[str, NormalizedFileData]:
        """Prepare files for the request concurrently.

        Returns:
            Dictionary mapping asset keys to normalized file data
        """
        import asyncio

        # Process all files concurrently
        tasks = []
        keys = []
        for key, file_input in self.assets.items():
            tasks.append(process_file_input(file_input))
            keys.append(key)

        # Wait for all file processing to complete
        normalized_files = await asyncio.gather(*tasks)

        # Build the result dictionary
        request_files = {}
        for key, normalized_data in zip(keys, normalized_files, strict=False):
            request_files[key] = normalized_data

        return request_files

    def _cleanup(self) -> None:
        """Clean up resources after execution."""
        self.assets.clear()
        self.asset_index = 0
        self.current_step = 0
        self.is_executed = True

    # Part methods (WorkflowInitialStage)

    def add_file_part(
        self,
        file: FileInput,
        options: FilePartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add a file part to the workflow.

        Args:
            file: The file to add to the workflow. Can be a local file path, bytes, or URL.
            options: Additional options for the file part.
            actions: Actions to apply to the file part.

        Returns:
            The workflow builder instance for method chaining.
        """
        self._ensure_not_executed()

        # Handle file field
        file_field: FileHandle
        if is_remote_file_input(file):
            file_field = RemoteFileHandle(url=file)
        else:
            file_field = self._register_asset(file)

        # Process actions
        processed_actions = None
        if actions:
            processed_actions = [self._process_action(action) for action in actions]

        file_part: FilePart = {
            "file": file_field,
            **(options or {}),
        }

        if processed_actions:
            file_part["actions"] = processed_actions

        self.build_instructions["parts"].append(file_part)
        return self

    def add_html_part(
        self,
        html: FileInput,
        assets: list[FileInput] | None = None,
        options: HTMLPartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add an HTML part to the workflow.

        Args:
            html: The HTML content to add. Can be a file path, bytes, or URL.
            assets: Optional array of assets (CSS, images, etc.) to include with the HTML.
            options: Additional options for the HTML part.
            actions: Actions to apply to the HTML part.

        Returns:
            The workflow builder instance for method chaining.
        """
        self._ensure_not_executed()

        # Handle HTML field
        html_field: FileHandle
        if is_remote_file_input(html):
            html_field = RemoteFileHandle(url=html)
        else:
            html_field = self._register_asset(html)

        # Handle assets
        assets_field = None
        if assets:
            assets_field = []
            for asset in assets:
                if is_remote_file_input(asset):
                    raise ValidationError(
                        "Assets file input cannot be a URL", {"input": asset}
                    )
                asset_key = self._register_asset(asset)
                assets_field.append(asset_key)

        # Process actions
        processed_actions = None
        if actions:
            processed_actions = [self._process_action(action) for action in actions]

        html_part: HTMLPart = {
            "html": html_field,
        }

        if options is not None and "layout" in options:
            html_part["layout"] = options["layout"]

        if assets_field:
            html_part["assets"] = assets_field

        if processed_actions:
            html_part["actions"] = processed_actions

        self.build_instructions["parts"].append(html_part)
        return self

    def add_new_page(
        self,
        options: NewPagePartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add a new blank page to the workflow.

        Args:
            options: Additional options for the new page, such as page size, orientation, etc.
            actions: Actions to apply to the new page.

        Returns:
            The workflow builder instance for method chaining.
        """
        self._ensure_not_executed()

        # Process actions
        processed_actions = None
        if actions:
            processed_actions = [self._process_action(action) for action in actions]

        new_page_part: NewPagePart = {
            "page": "new",
        }

        if options is not None:
            if "pageCount" in options:
                new_page_part["pageCount"] = options["pageCount"]

            if "layout" in options:
                new_page_part["layout"] = options["layout"]

        if processed_actions:
            new_page_part["actions"] = processed_actions

        self.build_instructions["parts"].append(new_page_part)
        return self

    def add_document_part(
        self,
        document_id: str,
        options: DocumentPartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add a document part to the workflow by referencing an existing document by ID.

        Args:
            document_id: The ID of the document to add to the workflow.
            options: Additional options for the document part.
            actions: Actions to apply to the document part.

        Returns:
            The workflow builder instance for method chaining.
        """
        self._ensure_not_executed()

        # Extract layer from options
        layer = None
        document_options = options or {}
        if "layer" in document_options:
            layer = document_options.pop("layer")

        # Process actions
        processed_actions = None
        if actions:
            processed_actions = [self._process_action(action) for action in actions]

        document_part: DocumentPart = {
            "document": {"id": document_id},
        }

        if "password" in document_options:
            document_part["password"] = document_options["password"]

        if "pages" in document_options:
            document_part["pages"] = document_options["pages"]

        if layer:
            document_part["document"]["layer"] = layer

        if processed_actions:
            document_part["actions"] = processed_actions

        self.build_instructions["parts"].append(document_part)
        return self

    # Action methods (WorkflowWithPartsStage)

    def apply_actions(
        self, actions: list[ApplicableAction]
    ) -> WorkflowWithActionsStage:
        """Apply multiple actions to the workflow.

        Args:
            actions: An array of actions to apply to the workflow.

        Returns:
            The workflow builder instance for method chaining.
        """
        self._ensure_not_executed()

        if "actions" not in self.build_instructions:
            self.build_instructions["actions"] = []

        processed_actions = [self._process_action(action) for action in actions]
        self.build_instructions["actions"].extend(processed_actions)
        return cast("WorkflowWithActionsStage", self)

    def apply_action(self, action: ApplicableAction) -> WorkflowWithActionsStage:
        """Apply a single action to the workflow.

        Args:
            action: The action to apply to the workflow.

        Returns:
            The workflow builder instance for method chaining.
        """
        return self.apply_actions([action])

    # Output methods (WorkflowWithPartsStage)

    def _output(self, output: BuildOutput) -> StagedWorkflowBuilder:
        """Set the output configuration."""
        self._ensure_not_executed()
        self.build_instructions["output"] = output
        return self

    def output_pdf(
        self,
        options: PDFOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set the output format to PDF."""
        self._output(BuildOutputs.pdf(options))
        return cast("WorkflowWithOutputStage", self)

    def output_pdfa(
        self,
        options: PDFAOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set the output format to PDF/A."""
        self._output(BuildOutputs.pdfa(options))
        return cast("WorkflowWithOutputStage", self)

    def output_pdfua(
        self,
        options: PDFUAOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set the output format to PDF/UA."""
        self._output(BuildOutputs.pdfua(options))
        return cast("WorkflowWithOutputStage", self)

    def output_image(
        self,
        format: Literal["png", "jpeg", "jpg", "webp"],
        options: ImageOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set the output format to an image format."""
        if not options or not any(k in options for k in ["dpi", "width", "height"]):
            raise ValidationError(
                "Image output requires at least one of the following options: dpi, height, width"
            )
        self._output(BuildOutputs.image(format, options))
        return cast("WorkflowWithOutputStage", self)

    def output_office(
        self,
        format: Literal["docx", "xlsx", "pptx"],
    ) -> WorkflowWithOutputStage:
        """Set the output format to an Office document format."""
        self._output(BuildOutputs.office(format))
        return cast("WorkflowWithOutputStage", self)

    def output_html(
        self, layout: Literal["page", "reflow"] | None = None
    ) -> WorkflowWithOutputStage:
        """Set the output format to HTML."""
        casted_layout: Literal["page", "reflow"] = "page"
        if layout is not None:
            casted_layout = layout
        self._output(BuildOutputs.html(casted_layout))
        return cast("WorkflowWithOutputStage", self)

    def output_markdown(
        self,
    ) -> WorkflowWithOutputStage:
        """Set the output format to Markdown."""
        self._output(BuildOutputs.markdown())
        return cast("WorkflowWithOutputStage", self)

    def output_json(
        self,
        options: JSONContentOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set the output format to JSON content."""
        self._output(BuildOutputs.jsonContent(options))
        return cast("WorkflowWithOutputStage", self)

    # Execution methods (WorkflowWithOutputStage)

    async def execute(
        self,
        on_progress: WorkflowExecuteCallback | None = None,
    ) -> TypedWorkflowResult:
        """Execute the workflow and return the result.

        Args:
            on_progress: Optional progress callback.

        Returns:
            The workflow execution result.
        """
        self._ensure_not_executed()
        self.current_step = 0

        result: TypedWorkflowResult = {
            "success": False,
            "errors": [],
            "output": None,
        }

        try:
            # Step 1: Validate
            self.current_step = 1
            if on_progress:
                on_progress(self.current_step, 3)
            self._validate()

            # Step 2: Prepare files
            self.current_step = 2
            if on_progress:
                on_progress(self.current_step, 3)

            output_config = self.build_instructions.get("output")
            if not output_config:
                raise ValueError("Output configuration is required")

            files = await self._prepare_files()

            # Make the request
            response = await self._send_request(
                "/build",
                BuildRequestData(instructions=self.build_instructions, files=files),
            )

            # Step 3: Process response
            self.current_step = 3
            if on_progress:
                on_progress(self.current_step, 3)

            if output_config["type"] == "json-content":
                result["success"] = True
                result["output"] = JsonContentOutput(
                    data=cast("BuildResponseJsonContents", response)
                )
            elif output_config["type"] in ["html", "markdown"]:
                mime_info = BuildOutputs.getMimeTypeForOutput(output_config)
                result["success"] = True
                result["output"] = ContentOutput(
                    content=cast("bytes", response).decode("utf-8"),
                    mimeType=mime_info["mimeType"],
                    filename=mime_info.get("filename"),
                )
            else:
                mime_info = BuildOutputs.getMimeTypeForOutput(output_config)
                result["success"] = True
                result["output"] = BufferOutput(
                    buffer=cast("bytes", response),
                    mimeType=mime_info["mimeType"],
                    filename=mime_info.get("filename"),
                )

        except Exception as error:
            if result["errors"] is None:
                result["errors"] = []

            workflow_error: WorkflowError = {
                "step": self.current_step,
                "error": error
                if isinstance(error, Exception)
                else Exception(str(error)),
            }
            cast("list[WorkflowError]", result["errors"]).append(workflow_error)

        finally:
            self._cleanup()

        return result

    async def dry_run(self) -> WorkflowDryRunResult:
        """Perform a dry run of the workflow without generating the final output.
        This is useful for validating the workflow configuration and estimating processing time.

        Returns:
            A dry run result containing validation information and estimated processing time.
        """
        self._ensure_not_executed()

        result: WorkflowDryRunResult = {
            "success": False,
            "errors": [],
            "analysis": None,
        }

        try:
            self._validate()

            response = await self._send_request(
                "/analyze_build",
                AnalyzeBuildRequestData(instructions=self.build_instructions),
            )

            result["success"] = True
            result["analysis"] = response

        except Exception as error:
            if result["errors"] is None:
                result["errors"] = []

            workflow_error: WorkflowError = {
                "step": 0,
                "error": error
                if isinstance(error, Exception)
                else Exception(str(error)),
            }
            cast("list[WorkflowError]", result["errors"]).append(workflow_error)

        return result
