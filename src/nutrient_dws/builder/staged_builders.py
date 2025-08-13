"""Staged builder interfaces for workflow pattern implementation."""
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import (
    Generic,
    TypeVar,
)

from nutrient_dws.generated import *
from nutrient_dws.inputs import FileInput

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
    filename: Optional[str]


class ContentOutput(TypedDict):
    content: str
    mimeType: str
    filename: Optional[str]


class JsonContentOutput(TypedDict):
    data: BuildResponseJsonContents


# Type variable for output type
TOutput = TypeVar("TOutput", bound=OutputFormat)

# Applicable actions type - actions that can be applied to workflows
ApplicableAction = BuildAction


class WorkflowError(TypedDict):
    """Workflow execution error details."""

    step: int
    error: Exception


class WorkflowOutput(TypedDict):
    """Represents an output file with its content and metadata."""

    buffer: bytes
    mimeType: str
    filename: Optional[str]


class WorkflowResult(TypedDict):
    """Result of a workflow execution."""

    success: bool
    output: Optional[WorkflowOutput]
    errors: Optional[List[WorkflowError]]


class TypedWorkflowResult(TypedDict, Generic[TOutput]):
    """Typed result of a workflow execution based on output configuration."""

    success: bool
    output: Optional[Union[BufferOutput, ContentOutput, JsonContentOutput]]
    errors: Optional[List[WorkflowError]]


class WorkflowDryRunResult(TypedDict):
    """Result of a workflow dry run."""

    success: bool
    analysis: Optional[AnalyzeBuildResponse]
    errors: Optional[List[WorkflowError]]


class WorkflowExecuteOptions(TypedDict, total=False):
    """Options for workflow execution."""

    onProgress: Optional[Callable[[int, int], None]]


class WorkflowInitialStage(ABC):
    """Stage 1: Initial workflow - only part methods available."""

    @abstractmethod
    def add_file_part(
        self,
        file: FileInput,
        options: Optional[Dict[str, Any]] = None,
        actions: Optional[List[ApplicableAction]] = None,
    ) -> "WorkflowWithPartsStage":
        """Add a file part to the workflow."""
        pass

    @abstractmethod
    def add_html_part(
        self,
        html: FileInput,
        assets: Optional[List[FileInput]] = None,
        options: Optional[Dict[str, Any]] = None,
        actions: Optional[List[ApplicableAction]] = None,
    ) -> "WorkflowWithPartsStage":
        """Add an HTML part to the workflow."""
        pass

    @abstractmethod
    def add_new_page(
        self,
        options: Optional[Dict[str, Any]] = None,
        actions: Optional[List[ApplicableAction]] = None,
    ) -> "WorkflowWithPartsStage":
        """Add a new page part to the workflow."""
        pass

    @abstractmethod
    def add_document_part(
        self,
        document_id: str,
        options: Optional[Dict[str, Any]] = None,
        actions: Optional[List[ApplicableAction]] = None,
    ) -> "WorkflowWithPartsStage":
        """Add a document part to the workflow."""
        pass


class WorkflowWithPartsStage(ABC, WorkflowInitialStage):
    """Stage 2: After parts added - parts, actions, and output methods available."""

    # Action methods
    @abstractmethod
    def apply_actions(self, actions: List[ApplicableAction]) -> "WorkflowWithActionsStage":
        """Apply multiple actions to the workflow."""
        pass

    @abstractmethod
    def apply_action(self, action: ApplicableAction) -> "WorkflowWithActionsStage":
        """Apply a single action to the workflow."""
        pass

    # Output methods
    @abstractmethod
    def output_pdf(
        self,
        options: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowWithOutputStage[Literal["pdf"]]':
        """Set PDF output for the workflow."""
        pass

    @abstractmethod
    def output_pdfa(
        self,
        options: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowWithOutputStage[Literal["pdfa"]]':
        """Set PDF/A output for the workflow."""
        pass

    @abstractmethod
    def output_pdfua(
        self,
        options: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowWithOutputStage[Literal["pdfua"]]':
        """Set PDF/UA output for the workflow."""
        pass

    @abstractmethod
    def output_image(
        self,
        format: Literal["png", "jpeg", "jpg", "webp"],
        options: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowWithOutputStage[Literal["png"]]':
        """Set image output for the workflow."""
        pass

    @abstractmethod
    def output_office(
        self,
        format: Literal["docx", "xlsx", "pptx"],
    ) -> 'WorkflowWithOutputStage[Literal["docx"]]':
        """Set Office format output for the workflow."""
        pass

    @abstractmethod
    def output_html(
        self,
        layout: Optional[Literal["page", "reflow"]] = None,
    ) -> 'WorkflowWithOutputStage[Literal["html"]]':
        """Set HTML output for the workflow."""
        pass

    @abstractmethod
    def output_markdown(
        self,
        options: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowWithOutputStage[Literal["markdown"]]':
        """Set Markdown output for the workflow."""
        pass

    @abstractmethod
    def output_json(
        self,
        options: Optional[Dict[str, Any]] = None,
    ) -> 'WorkflowWithOutputStage[Literal["json-content"]]':
        """Set JSON content output for the workflow."""
        pass


# Stage 3: After actions added - type alias since functionality is the same
WorkflowWithActionsStage = WorkflowWithPartsStage


class WorkflowWithOutputStage(ABC, Generic[TOutput]):
    """Stage 4: After output set - only execute and dryRun available."""

    @abstractmethod
    async def execute(
        self,
        options: Optional[WorkflowExecuteOptions] = None,
    ) -> TypedWorkflowResult[TOutput]:
        """Execute the workflow and return the result."""
        pass

    @abstractmethod
    async def dry_run(self) -> WorkflowDryRunResult:
        """Perform a dry run of the workflow without executing."""
        pass
