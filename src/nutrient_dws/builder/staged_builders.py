"""Staged builder interfaces for workflow pattern implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, TypedDict

from nutrient_dws.builder.constant import ActionWithFileInput
from nutrient_dws.types.build_actions import BuildAction

if TYPE_CHECKING:
    from nutrient_dws.inputs import FileInput
    from nutrient_dws.types.analyze_response import AnalyzeBuildResponse
    from nutrient_dws.types.build_output import (
        ImageOutputOptions,
        JSONContentOutputOptions,
        PDFAOutputOptions,
        PDFOutputOptions,
        PDFUAOutputOptions,
    )
    from nutrient_dws.types.build_response_json import BuildResponseJsonContents
    from nutrient_dws.types.input_parts import (
        DocumentPartOptions,
        FilePartOptions,
        HTMLPartOptions,
        NewPagePartOptions,
    )

# Type aliases for output types
OutputFormat = Literal[
    "pdf",
    "pdfa",
    "pdfua",
    "png",
    "jpeg",
    "jpg",
    "webp",
    "docx",
    "xlsx",
    "pptx",
    "html",
    "markdown",
    "json-content",
]


# Output type mappings
class BufferOutput(TypedDict):
    buffer: bytes
    mimeType: str
    filename: str | None


class ContentOutput(TypedDict):
    content: str
    mimeType: str
    filename: str | None


class JsonContentOutput(TypedDict):
    data: BuildResponseJsonContents


# Applicable actions type - actions that can be applied to workflows
ApplicableAction = BuildAction | ActionWithFileInput


class WorkflowError(TypedDict):
    """Workflow execution error details."""

    step: int
    error: Exception


class WorkflowOutput(TypedDict):
    """Represents an output file with its content and metadata."""

    buffer: bytes
    mimeType: str
    filename: str | None


class WorkflowResult(TypedDict):
    """Result of a workflow execution."""

    success: bool
    output: WorkflowOutput | None
    errors: list[WorkflowError] | None


class TypedWorkflowResult(TypedDict):
    """Typed result of a workflow execution based on output configuration."""

    success: bool
    output: BufferOutput | ContentOutput | JsonContentOutput | None
    errors: list[WorkflowError] | None


class WorkflowDryRunResult(TypedDict):
    """Result of a workflow dry run."""

    success: bool
    analysis: AnalyzeBuildResponse | None
    errors: list[WorkflowError] | None


WorkflowExecuteCallback = Callable[[int, int], None]


class WorkflowInitialStage(ABC):
    """Stage 1: Initial workflow - only part methods available."""

    @abstractmethod
    def add_file_part(
        self,
        file: FileInput,
        options: FilePartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add a file part to the workflow."""
        pass

    @abstractmethod
    def add_html_part(
        self,
        html: FileInput,
        assets: list[FileInput] | None = None,
        options: HTMLPartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add an HTML part to the workflow."""
        pass

    @abstractmethod
    def add_new_page(
        self,
        options: NewPagePartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add a new page part to the workflow."""
        pass

    @abstractmethod
    def add_document_part(
        self,
        document_id: str,
        options: DocumentPartOptions | None = None,
        actions: list[ApplicableAction] | None = None,
    ) -> WorkflowWithPartsStage:
        """Add a document part to the workflow."""
        pass


class WorkflowWithPartsStage(WorkflowInitialStage):
    """Stage 2: After parts added - parts, actions, and output methods available."""

    # Action methods
    @abstractmethod
    def apply_actions(self, actions: list[ApplicableAction]) -> WorkflowWithPartsStage:
        """Apply multiple actions to the workflow."""
        pass

    @abstractmethod
    def apply_action(self, action: ApplicableAction) -> WorkflowWithPartsStage:
        """Apply a single action to the workflow."""
        pass

    # Output methods
    @abstractmethod
    def output_pdf(
        self,
        options: PDFOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set PDF output for the workflow."""
        pass

    @abstractmethod
    def output_pdfa(
        self,
        options: PDFAOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set PDF/A output for the workflow."""
        pass

    @abstractmethod
    def output_pdfua(
        self,
        options: PDFUAOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set PDF/UA output for the workflow."""
        pass

    @abstractmethod
    def output_image(
        self,
        format: Literal["png", "jpeg", "jpg", "webp"],
        options: ImageOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set image output for the workflow."""
        pass

    @abstractmethod
    def output_office(
        self,
        format: Literal["docx", "xlsx", "pptx"],
    ) -> WorkflowWithOutputStage:
        """Set Office format output for the workflow."""
        pass

    @abstractmethod
    def output_html(
        self,
        layout: Literal["page", "reflow"] | None = None,
    ) -> WorkflowWithOutputStage:
        """Set HTML output for the workflow."""
        pass

    @abstractmethod
    def output_markdown(
        self,
    ) -> WorkflowWithOutputStage:
        """Set Markdown output for the workflow."""
        pass

    @abstractmethod
    def output_json(
        self,
        options: JSONContentOutputOptions | None = None,
    ) -> WorkflowWithOutputStage:
        """Set JSON content output for the workflow."""
        pass


# Stage 3: After actions added - type alias since functionality is the same
WorkflowWithActionsStage = WorkflowWithPartsStage


class WorkflowWithOutputStage(ABC):
    """Stage 4: After output set - only execute and dryRun available."""

    @abstractmethod
    async def execute(
        self,
        on_progress: WorkflowExecuteCallback | None = None,
    ) -> TypedWorkflowResult:
        """Execute the workflow and return the result."""
        pass

    @abstractmethod
    async def dry_run(self) -> WorkflowDryRunResult:
        """Perform a dry run of the workflow without executing."""
        pass
