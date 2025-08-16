"""Tests for StagedWorkflowBuilder functionality."""

from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest

from nutrient_dws.builder.builder import StagedWorkflowBuilder
from nutrient_dws.builder.constant import BuildActions, BuildOutputs
from nutrient_dws.errors import ValidationError, NutrientError





@pytest.fixture
def mock_send_request():
    """Mock the send request method."""

    async def mock_request(endpoint, data):
        if endpoint == "/build":
            return b"mock-response"
        elif endpoint == "/analyze_build":
            return {"cost": 1.0, "required_features": {}}
        return b"mock-response"

    with patch(
        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
        side_effect=mock_request,
    ) as mock:
        yield mock


@pytest.fixture
def mock_validate_file_input():
    """Mock file input validation."""
    with patch("nutrient_dws.inputs.validate_file_input") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_is_remote_file_input():
    """Mock remote file input check."""
    with patch("nutrient_dws.inputs.is_remote_file_input") as mock:
        mock.return_value = False
        yield mock


@pytest.fixture
def mock_process_file_input():
    """Mock file input processing."""

    async def mock_process(file_input):
        return ("test-content", "application/pdf")

    with patch(
        "nutrient_dws.inputs.process_file_input", side_effect=mock_process
    ) as mock:
        yield mock


class TestStagedWorkflowBuilderConstructor:
    """Tests for StagedWorkflowBuilder constructor."""

    def test_create_workflow_builder_with_valid_options(self, valid_client_options):
        """Test creating a workflow builder with valid options."""
        builder = StagedWorkflowBuilder(valid_client_options)
        assert builder is not None
        assert builder.build_instructions == {"parts": []}
        assert builder.assets == {}
        assert builder.asset_index == 0
        assert builder.current_step == 0
        assert builder.is_executed is False


class TestStagedWorkflowBuilderPrivateMethods:
    """Tests for StagedWorkflowBuilder private methods."""

    def test_register_asset_with_valid_file(self, valid_client_options):
        """Test registering a valid file asset."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ) as mock_validate:
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ) as mock_is_remote:
                builder = StagedWorkflowBuilder(valid_client_options)
                test_file = "test.pdf"

                asset_key = builder._register_asset(test_file)

                assert asset_key == "asset_0"
                assert builder.assets["asset_0"] == test_file
                assert builder.asset_index == 1
                mock_validate.assert_called_once_with(test_file)
                mock_is_remote.assert_called_once_with(test_file)

    def test_register_asset_with_invalid_file(self, valid_client_options):
        """Test registering an invalid file asset throws ValidationError."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=False
        ):
            builder = StagedWorkflowBuilder(valid_client_options)

            with pytest.raises(
                ValidationError, match="Invalid file input provided to workflow"
            ):
                builder._register_asset("invalid-file")

    def test_register_asset_with_remote_file(self, valid_client_options):
        """Test registering a remote file throws ValidationError."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=True
            ):
                builder = StagedWorkflowBuilder(valid_client_options)

                with pytest.raises(
                    ValidationError,
                    match="Remote file input doesn't need to be registered",
                ):
                    builder._register_asset("https://example.com/file.pdf")

    def test_register_multiple_assets_increments_counter(self, valid_client_options):
        """Test that registering multiple assets increments the counter."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                builder = StagedWorkflowBuilder(valid_client_options)

                first_key = builder._register_asset("file1.pdf")
                second_key = builder._register_asset("file2.pdf")

                assert first_key == "asset_0"
                assert second_key == "asset_1"
                assert builder.asset_index == 2

    def test_ensure_not_executed_with_fresh_workflow(self, valid_client_options):
        """Test ensure_not_executed passes with fresh workflow."""
        builder = StagedWorkflowBuilder(valid_client_options)
        # Should not raise exception
        builder._ensure_not_executed()

    def test_ensure_not_executed_with_executed_workflow(self, valid_client_options):
        """Test ensure_not_executed throws error when workflow is executed."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.is_executed = True

        with pytest.raises(
            ValidationError, match="This workflow has already been executed"
        ):
            builder._ensure_not_executed()

    def test_validate_with_no_parts(self, valid_client_options):
        """Test validate throws error when workflow has no parts."""
        builder = StagedWorkflowBuilder(valid_client_options)

        with pytest.raises(ValidationError, match="Workflow has no parts to execute"):
            builder._validate()

    def test_validate_with_parts_but_no_output(self, valid_client_options):
        """Test validate adds default PDF output when no output is specified."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.build_instructions["parts"] = [{"file": "asset_0"}]

        builder._validate()

        assert builder.build_instructions["output"] == {"type": "pdf"}

    def test_validate_with_parts_and_output(self, valid_client_options):
        """Test validate passes when workflow has parts and output."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.build_instructions["parts"] = [{"file": "asset_0"}]
        builder.build_instructions["output"] = {"type": "png", "format": "png"}

        # Should not raise exception
        builder._validate()

    def test_process_action_with_regular_action(self, valid_client_options):
        """Test processing a regular action without file input."""
        builder = StagedWorkflowBuilder(valid_client_options)
        action = {"type": "ocr", "language": "english"}

        result = builder._process_action(action)

        assert result == action

    def test_process_action_with_file_input_action(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test processing an action that requires file registration."""
        builder = StagedWorkflowBuilder(valid_client_options)

        # Create a mock action with file input
        mock_action = MagicMock()
        mock_action.__needsFileRegistration = True
        mock_action.fileInput = "watermark.png"
        mock_action.createAction.return_value = {
            "type": "watermark",
            "image": "asset_0",
        }

        result = builder._process_action(mock_action)

        assert result == {"type": "watermark", "image": "asset_0"}
        mock_action.createAction.assert_called_once_with("asset_0")

    def test_process_action_with_remote_file_input_action(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test processing an action with remote file input."""
        mock_is_remote_file_input.return_value = True
        builder = StagedWorkflowBuilder(valid_client_options)

        # Create a mock action with remote file input
        mock_action = MagicMock()
        mock_action.__needsFileRegistration = True
        mock_action.fileInput = "https://example.com/watermark.png"
        mock_action.createAction.return_value = {
            "type": "watermark",
            "image": {"url": "https://example.com/watermark.png"},
        }

        result = builder._process_action(mock_action)

        expected_file_handle = {"url": "https://example.com/watermark.png"}
        assert result == {"type": "watermark", "image": expected_file_handle}
        mock_action.createAction.assert_called_once_with(expected_file_handle)

    def test_is_action_with_file_input_returns_true_for_file_action(
        self, valid_client_options
    ):
        """Test is_action_with_file_input returns True for actions with file input."""
        builder = StagedWorkflowBuilder(valid_client_options)

        # Create a mock action that needs file registration
        mock_action = MagicMock()
        mock_action.__needsFileRegistration = True
        mock_action.fileInput = "test.png"
        mock_action.createAction = MagicMock()

        result = builder._is_action_with_file_input(mock_action)

        assert result is True

    def test_is_action_with_file_input_returns_false_for_regular_action(
        self, valid_client_options
    ):
        """Test is_action_with_file_input returns False for regular actions."""
        builder = StagedWorkflowBuilder(valid_client_options)
        action = {"type": "ocr", "language": "english"}

        result = builder._is_action_with_file_input(action)

        assert result is False

    @pytest.mark.asyncio
    async def test_prepare_files_processes_assets_concurrently(
        self, valid_client_options
    ):
        """Test prepare_files processes all assets concurrently."""

        async def mock_process(file_input):
            if file_input == "file1.pdf":
                return ("content1", "application/pdf")
            elif file_input == "file2.pdf":
                return ("content2", "application/pdf")
            return ("test-content", "application/pdf")

        with patch(
            "nutrient_dws.builder.builder.process_file_input", side_effect=mock_process
        ) as mock_process_file:
            builder = StagedWorkflowBuilder(valid_client_options)
            builder.assets = {"asset_0": "file1.pdf", "asset_1": "file2.pdf"}

            result = await builder._prepare_files()

            assert result == {
                "asset_0": ("content1", "application/pdf"),
                "asset_1": ("content2", "application/pdf"),
            }
            assert mock_process_file.call_count == 2

    def test_cleanup_resets_builder_state(self, valid_client_options):
        """Test cleanup resets the builder to initial state."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.assets = {"asset_0": "test.pdf"}
        builder.asset_index = 5
        builder.current_step = 2

        builder._cleanup()

        assert builder.assets == {}
        assert builder.asset_index == 0
        assert builder.current_step == 0
        assert builder.is_executed is True


class TestStagedWorkflowBuilderPartMethods:
    """Tests for StagedWorkflowBuilder part methods."""

    def test_add_file_part_with_local_file(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test adding a file part with local file."""
        builder = StagedWorkflowBuilder(valid_client_options)
        test_file = "test.pdf"

        result = builder.add_file_part(test_file)

        assert result is builder
        assert len(builder.build_instructions["parts"]) == 1

        file_part = builder.build_instructions["parts"][0]
        assert file_part["file"] == "asset_0"
        assert builder.assets["asset_0"] == test_file

    def test_add_file_part_with_remote_file(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test adding a file part with remote file URL."""
        mock_is_remote_file_input.return_value = True
        builder = StagedWorkflowBuilder(valid_client_options)
        test_url = "https://example.com/document.pdf"

        result = builder.add_file_part(test_url)

        assert result is builder
        assert len(builder.build_instructions["parts"]) == 1

        file_part = builder.build_instructions["parts"][0]
        assert file_part["file"] == {"url": test_url}
        assert len(builder.assets) == 0  # Remote files are not registered

    def test_add_file_part_with_options_and_actions(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test adding a file part with options and actions."""
        builder = StagedWorkflowBuilder(valid_client_options)
        test_file = "test.pdf"
        options = {"pages": {"start": 0, "end": 5}}
        actions = [{"type": "ocr", "language": "english"}]

        result = builder.add_file_part(test_file, options, actions)

        assert result is builder
        file_part = builder.build_instructions["parts"][0]
        assert file_part["pages"] == {"start": 0, "end": 5}
        assert file_part["actions"] == [{"type": "ocr", "language": "english"}]

    def test_add_file_part_throws_error_when_executed(self, valid_client_options):
        """Test add_file_part throws error when workflow is already executed."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.is_executed = True

        with pytest.raises(
            ValidationError, match="This workflow has already been executed"
        ):
            builder.add_file_part("test.pdf")

    def test_add_html_part_with_local_file(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test adding an HTML part with local file."""
        builder = StagedWorkflowBuilder(valid_client_options)
        html_content = b"<html><body>Test</body></html>"

        result = builder.add_html_part(html_content)

        assert result is builder
        assert len(builder.build_instructions["parts"]) == 1

        html_part = builder.build_instructions["parts"][0]
        assert html_part["html"] == "asset_0"
        assert builder.assets["asset_0"] == html_content

    def test_add_html_part_with_remote_url(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test adding an HTML part with remote URL."""
        mock_is_remote_file_input.return_value = True
        builder = StagedWorkflowBuilder(valid_client_options)
        html_url = "https://example.com/page.html"

        result = builder.add_html_part(html_url)

        assert result is builder
        html_part = builder.build_instructions["parts"][0]
        assert html_part["html"] == {"url": html_url}
        assert len(builder.assets) == 0

    def test_add_html_part_with_assets_and_actions(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test adding HTML part with assets and actions."""
        builder = StagedWorkflowBuilder(valid_client_options)
        html_content = b"<html><body>Test</body></html>"
        assets = [b"p {color: red;}", b"img {width: 100px;}"]
        options = {"layout": "page"}
        actions = [{"type": "ocr", "language": "english"}]

        result = builder.add_html_part(html_content, assets, options, actions)

        assert result is builder
        html_part = builder.build_instructions["parts"][0]
        assert html_part["html"] == "asset_0"
        assert html_part["layout"] == "page"
        assert html_part["assets"] == ["asset_1", "asset_2"]
        assert html_part["actions"] == [{"type": "ocr", "language": "english"}]
        assert len(builder.assets) == 3  # HTML + 2 assets

    def test_add_html_part_with_remote_assets_throws_error(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test adding HTML part with remote assets throws ValidationError."""

        def is_remote_side_effect(input_file):
            return input_file.startswith("https://")

        mock_is_remote_file_input.side_effect = is_remote_side_effect
        builder = StagedWorkflowBuilder(valid_client_options)
        html_content = b"<html><body>Test</body></html>"
        assets = ["https://example.com/style.css"]

        with pytest.raises(ValidationError, match="Assets file input cannot be a URL"):
            builder.add_html_part(html_content, assets)

    def test_add_new_page_with_no_options(self, valid_client_options):
        """Test adding a new page with no options."""
        builder = StagedWorkflowBuilder(valid_client_options)

        result = builder.add_new_page()

        assert result is builder
        assert len(builder.build_instructions["parts"]) == 1

        page_part = builder.build_instructions["parts"][0]
        assert page_part["page"] == "new"

    def test_add_new_page_with_options_and_actions(self, valid_client_options):
        """Test adding a new page with options and actions."""
        builder = StagedWorkflowBuilder(valid_client_options)
        options = {"pageCount": 3, "layout": "A4"}
        actions = [{"type": "ocr", "language": "english"}]

        result = builder.add_new_page(options, actions)

        assert result is builder
        page_part = builder.build_instructions["parts"][0]
        assert page_part["page"] == "new"
        assert page_part["pageCount"] == 3
        assert page_part["layout"] == "A4"
        assert page_part["actions"] == [{"type": "ocr", "language": "english"}]

    def test_add_document_part_with_basic_options(self, valid_client_options):
        """Test adding a document part with basic options."""
        builder = StagedWorkflowBuilder(valid_client_options)
        document_id = "doc-123"

        result = builder.add_document_part(document_id)

        assert result is builder
        assert len(builder.build_instructions["parts"]) == 1

        doc_part = builder.build_instructions["parts"][0]
        assert doc_part["document"] == {"id": "doc-123"}

    def test_add_document_part_with_options_and_actions(self, valid_client_options):
        """Test adding a document part with options and actions."""
        builder = StagedWorkflowBuilder(valid_client_options)
        document_id = "doc-123"
        options = {
            "layer": "layer1",
            "password": "secret",
            "pages": {"start": 0, "end": 10},
        }
        actions = [{"type": "ocr", "language": "english"}]

        result = builder.add_document_part(document_id, options, actions)

        assert result is builder
        doc_part = builder.build_instructions["parts"][0]
        assert doc_part["document"] == {"id": "doc-123", "layer": "layer1"}
        assert doc_part["password"] == "secret"
        assert doc_part["pages"] == {"start": 0, "end": 10}
        assert doc_part["actions"] == [{"type": "ocr", "language": "english"}]


class TestStagedWorkflowBuilderActionMethods:
    """Tests for StagedWorkflowBuilder action methods."""

    def test_apply_actions_with_multiple_actions(self, valid_client_options):
        """Test applying multiple actions to workflow."""
        builder = StagedWorkflowBuilder(valid_client_options)
        actions = [{"type": "ocr", "language": "english"}, {"type": "flatten"}]

        result = builder.apply_actions(actions)

        assert result is builder
        assert builder.build_instructions["actions"] == actions

    def test_apply_actions_extends_existing_actions(self, valid_client_options):
        """Test that apply_actions extends existing actions."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.build_instructions["actions"] = [{"type": "rotate", "rotateBy": 90}]

        new_actions = [{"type": "ocr", "language": "english"}]
        result = builder.apply_actions(new_actions)

        assert result is builder
        expected_actions = [
            {"type": "rotate", "rotateBy": 90},
            {"type": "ocr", "language": "english"},
        ]
        assert builder.build_instructions["actions"] == expected_actions

    def test_apply_action_with_single_action(self, valid_client_options):
        """Test applying a single action to workflow."""
        builder = StagedWorkflowBuilder(valid_client_options)
        action = {"type": "ocr", "language": "english"}

        result = builder.apply_action(action)

        assert result is builder
        assert builder.build_instructions["actions"] == [action]

    def test_apply_actions_with_file_input_action(
        self, valid_client_options, mock_validate_file_input, mock_is_remote_file_input
    ):
        """Test applying actions that require file registration."""
        builder = StagedWorkflowBuilder(valid_client_options)

        # Create a mock action with file input
        mock_action = MagicMock()
        mock_action.__needsFileRegistration = True
        mock_action.fileInput = "watermark.png"
        mock_action.createAction.return_value = {
            "type": "watermark",
            "image": "asset_0",
        }

        result = builder.apply_actions([mock_action])

        assert result is builder
        assert builder.build_instructions["actions"] == [
            {"type": "watermark", "image": "asset_0"}
        ]

    def test_apply_actions_throws_error_when_executed(self, valid_client_options):
        """Test apply_actions throws error when workflow is already executed."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.is_executed = True

        with pytest.raises(
            ValidationError, match="This workflow has already been executed"
        ):
            builder.apply_actions([{"type": "ocr", "language": "english"}])


class TestStagedWorkflowBuilderOutputMethods:
    """Tests for StagedWorkflowBuilder output methods."""

    def test_output_pdf_with_no_options(self, valid_client_options):
        """Test setting PDF output with no options."""
        builder = StagedWorkflowBuilder(valid_client_options)

        result = builder.output_pdf()

        assert result is builder
        assert builder.build_instructions["output"] == {"type": "pdf"}

    def test_output_pdf_with_options(self, valid_client_options):
        """Test setting PDF output with options."""
        builder = StagedWorkflowBuilder(valid_client_options)
        options = {"user_password": "secret", "owner_password": "owner"}

        result = builder.output_pdf(options)

        assert result is builder
        expected_output = {
            "type": "pdf",
            "user_password": "secret",
            "owner_password": "owner",
        }
        assert builder.build_instructions["output"] == expected_output

    def test_output_pdfa_with_options(self, valid_client_options):
        """Test setting PDF/A output with options."""
        builder = StagedWorkflowBuilder(valid_client_options)
        options = {"conformance": "pdfa-2b", "vectorization": True}

        result = builder.output_pdfa(options)

        assert result is builder
        expected_output = {
            "type": "pdfa",
            "conformance": "pdfa-2b",
            "vectorization": True,
        }
        assert builder.build_instructions["output"] == expected_output

    def test_output_pdfua_with_options(self, valid_client_options):
        """Test setting PDF/UA output with options."""
        builder = StagedWorkflowBuilder(valid_client_options)
        options = {"metadata": {"title": "Accessible Document"}}

        result = builder.output_pdfua(options)

        assert result is builder
        expected_output = {
            "type": "pdfua",
            "metadata": {"title": "Accessible Document"},
        }
        assert builder.build_instructions["output"] == expected_output

    def test_output_image_with_dpi(self, valid_client_options):
        """Test setting image output with DPI option."""
        builder = StagedWorkflowBuilder(valid_client_options)
        options = {"dpi": 300}

        result = builder.output_image("png", options)

        assert result is builder
        expected_output = {"type": "image", "format": "png", "dpi": 300}
        assert builder.build_instructions["output"] == expected_output

    def test_output_image_with_dimensions(self, valid_client_options):
        """Test setting image output with width and height."""
        builder = StagedWorkflowBuilder(valid_client_options)
        options = {"width": 800, "height": 600}

        result = builder.output_image("jpeg", options)

        assert result is builder
        expected_output = {
            "type": "image",
            "format": "jpeg",
            "width": 800,
            "height": 600,
        }
        assert builder.build_instructions["output"] == expected_output

    def test_output_image_without_required_options_throws_error(
        self, valid_client_options
    ):
        """Test that image output without required options throws ValidationError."""
        builder = StagedWorkflowBuilder(valid_client_options)

        with pytest.raises(
            ValidationError,
            match="Image output requires at least one of the following options: dpi, height, width",
        ):
            builder.output_image("png")

        with pytest.raises(
            ValidationError,
            match="Image output requires at least one of the following options: dpi, height, width",
        ):
            builder.output_image("png", {})

    def test_output_office_formats(self, valid_client_options):
        """Test setting office output formats."""
        builder = StagedWorkflowBuilder(valid_client_options)

        # Test DOCX
        result_docx = builder.output_office("docx")
        assert result_docx is builder
        assert builder.build_instructions["output"] == {"type": "docx"}

        # Test XLSX
        builder2 = StagedWorkflowBuilder(valid_client_options)
        result_xlsx = builder2.output_office("xlsx")
        assert result_xlsx is builder2
        assert builder2.build_instructions["output"] == {"type": "xlsx"}

        # Test PPTX
        builder3 = StagedWorkflowBuilder(valid_client_options)
        result_pptx = builder3.output_office("pptx")
        assert result_pptx is builder3
        assert builder3.build_instructions["output"] == {"type": "pptx"}

    def test_output_html_with_default_layout(self, valid_client_options):
        """Test setting HTML output with default layout."""
        builder = StagedWorkflowBuilder(valid_client_options)

        result = builder.output_html()

        assert result is builder
        assert builder.build_instructions["output"] == {
            "type": "html",
            "layout": "page",
        }

    def test_output_html_with_reflow_layout(self, valid_client_options):
        """Test setting HTML output with reflow layout."""
        builder = StagedWorkflowBuilder(valid_client_options)

        result = builder.output_html("reflow")

        assert result is builder
        assert builder.build_instructions["output"] == {
            "type": "html",
            "layout": "reflow",
        }

    def test_output_markdown(self, valid_client_options):
        """Test setting Markdown output."""
        builder = StagedWorkflowBuilder(valid_client_options)

        result = builder.output_markdown()

        assert result is builder
        assert builder.build_instructions["output"] == {"type": "markdown"}

    def test_output_json_with_options(self, valid_client_options):
        """Test setting JSON content output with options."""
        builder = StagedWorkflowBuilder(valid_client_options)
        options = {"plainText": True, "tables": False}

        result = builder.output_json(options)

        assert result is builder
        expected_output = {"type": "json-content", "plainText": True, "tables": False}
        assert builder.build_instructions["output"] == expected_output

    def test_output_methods_throw_error_when_executed(self, valid_client_options):
        """Test output methods throw error when workflow is already executed."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.is_executed = True

        with pytest.raises(
            ValidationError, match="This workflow has already been executed"
        ):
            builder.output_pdf()


class TestStagedWorkflowBuilderExecutionMethods:
    """Tests for StagedWorkflowBuilder execution methods."""

    @pytest.mark.asyncio
    async def test_execute_with_pdf_output(self, valid_client_options):
        """Test executing workflow with PDF output."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        return b"pdf-content"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ) as mock_send:
                        builder = StagedWorkflowBuilder(valid_client_options)
                        builder.add_file_part("test.pdf")
                        builder.output_pdf()

                        result = await builder.execute()

                        assert result["success"] is True
                        assert result["errors"] == []
                        assert result["output"]["buffer"] == b"pdf-content"
                        assert result["output"]["mimeType"] == "application/pdf"
                        assert result["output"]["filename"] == "output.pdf"
                        assert builder.is_executed is True
                        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_json_output(self, valid_client_options):
        """Test executing workflow with JSON content output."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    mock_response_data = {"pages": [{"plainText": "Some text"}]}

                    async def mock_request(endpoint, data):
                        return mock_response_data

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)
                        builder.add_file_part("test.pdf")
                        builder.output_json({"plainText": True})

                        result = await builder.execute()

                        assert result["success"] is True
                        assert result["output"]["data"] == mock_response_data

    @pytest.mark.asyncio
    async def test_execute_with_html_output(self, valid_client_options):
        """Test executing workflow with HTML output."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        return b"<html><body>Content</body></html>"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)
                        builder.add_file_part("test.pdf")
                        builder.output_html("page")

                        result = await builder.execute()

                        assert result["success"] is True
                        assert (
                            result["output"]["content"]
                            == b"<html><body>Content</body></html>"
                        )
                        assert result["output"]["mimeType"] == "text/html"
                        assert result["output"]["filename"] == "output.html"

    @pytest.mark.asyncio
    async def test_execute_with_markdown_output(self, valid_client_options):
        """Test executing workflow with Markdown output."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        return b"# Header\n\nContent"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)
                        builder.add_file_part("test.pdf")
                        builder.output_markdown()

                        result = await builder.execute()

                        assert result["success"] is True
                        assert result["output"]["content"] == b"# Header\n\nContent"
                        assert result["output"]["mimeType"] == "text/markdown"
                        assert result["output"]["filename"] == "output.md"

    @pytest.mark.asyncio
    async def test_execute_with_progress_callback(self, valid_client_options):
        """Test executing workflow with progress callback."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    progress_calls = []

                    def on_progress(current: int, total: int) -> None:
                        progress_calls.append((current, total))

                    async def mock_request(endpoint, data):
                        return b"pdf-content"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)
                        builder.add_file_part("test.pdf")
                        builder.output_pdf()

                        await builder.execute(on_progress=on_progress)

                        assert progress_calls == [(1, 3), (2, 3), (3, 3)]

    @pytest.mark.asyncio
    async def test_execute_handles_validation_error(self, valid_client_options):
        """Test execute handles validation errors properly."""
        builder = StagedWorkflowBuilder(valid_client_options)
        # Don't add any parts - should trigger validation error

        result = await builder.execute()

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["step"] == 1
        assert isinstance(result["errors"][0]["error"], ValidationError)
        assert builder.is_executed is True

    @pytest.mark.asyncio
    async def test_execute_handles_request_error(self, valid_client_options):
        """Test execute handles request errors properly."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        raise Exception("Network error")

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)
                        builder.add_file_part("test.pdf")
                        builder.output_pdf()

                        result = await builder.execute()

                        assert result["success"] is False
                        assert len(result["errors"]) == 1
                        assert result["errors"][0]["step"] == 2
                        assert str(result["errors"][0]["error"]) == "Network error"

    @pytest.mark.asyncio
    async def test_execute_throws_error_when_already_executed(
        self, valid_client_options
    ):
        """Test execute throws error when workflow is already executed."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.is_executed = True

        with pytest.raises(
            ValidationError, match="This workflow has already been executed"
        ):
            await builder.execute()

    @pytest.mark.asyncio
    async def test_dry_run_success(self, valid_client_options):
        """Test successful dry run execution."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                mock_analysis_data = {"estimatedTime": 5.2, "cost": 0.10}

                async def mock_request(endpoint, data):
                    return mock_analysis_data

                with patch(
                    "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                    side_effect=mock_request,
                ) as mock_send:
                    builder = StagedWorkflowBuilder(valid_client_options)
                    builder.add_file_part("test.pdf")

                    result = await builder.dry_run()

                    assert result["success"] is True
                    assert result["errors"] == []
                    assert result["analysis"] == mock_analysis_data
                    mock_send.assert_called_once()
                    # Verify it called the analyze_build endpoint
                    call_args = mock_send.call_args
                    assert call_args[0][0] == "/analyze_build"

    @pytest.mark.asyncio
    async def test_dry_run_handles_validation_error(self, valid_client_options):
        """Test dry run handles validation errors properly."""
        builder = StagedWorkflowBuilder(valid_client_options)
        # Don't add any parts - should trigger validation error

        result = await builder.dry_run()

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["step"] == 0
        assert isinstance(result["errors"][0]["error"], ValidationError)

    @pytest.mark.asyncio
    async def test_dry_run_handles_request_error(
        self,
        valid_client_options,
        mock_send_request,
        mock_validate_file_input,
        mock_is_remote_file_input,
    ):
        """Test dry run handles request errors properly."""
        mock_send_request.side_effect = Exception("Analysis failed")
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.add_file_part("test.pdf")

        result = await builder.dry_run()

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["step"] == 0
        assert str(result["errors"][0]["error"]) == "Analysis failed"

    @pytest.mark.asyncio
    async def test_dry_run_throws_error_when_already_executed(
        self, valid_client_options
    ):
        """Test dry run throws error when workflow is already executed."""
        builder = StagedWorkflowBuilder(valid_client_options)
        builder.is_executed = True

        with pytest.raises(
            ValidationError, match="This workflow has already been executed"
        ):
            await builder.dry_run()


class TestStagedWorkflowBuilderChaining:
    """Tests for StagedWorkflowBuilder method chaining and type safety."""

    @pytest.mark.asyncio
    async def test_complete_workflow_chaining(self, valid_client_options):
        """Test complete workflow with method chaining."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        return b"pdf-content"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)

                        result = await (
                            builder.add_file_part("test.pdf")
                            .apply_action({"type": "ocr", "language": "english"})
                            .output_pdf({"user_password": "secret"})
                            .execute()
                        )

                        assert result["success"] is True
                        assert result["output"]["buffer"] == b"pdf-content"

                        # Verify the build instructions were set correctly
                        assert len(builder.build_instructions["parts"]) == 1
                        assert builder.build_instructions["actions"] == [
                            {"type": "ocr", "language": "english"}
                        ]
                        assert (
                            builder.build_instructions["output"]["user_password"]
                            == "secret"
                        )

    @pytest.mark.asyncio
    async def test_complex_workflow_with_multiple_parts_and_actions(
        self, valid_client_options
    ):
        """Test complex workflow with multiple parts and actions."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        return b"merged-pdf-content"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)

                        result = await (
                            builder.add_file_part(
                                "doc1.pdf", {"pages": {"start": 0, "end": 5}}
                            )
                            .add_file_part(
                                "doc2.pdf", {"pages": {"start": 2, "end": 8}}
                            )
                            .add_new_page({"pageCount": 1})
                            .apply_actions(
                                [
                                    {"type": "ocr", "language": "english"},
                                    {"type": "flatten"},
                                ]
                            )
                            .output_pdf({"metadata": {"title": "Merged Document"}})
                            .execute()
                        )

        assert result["success"] is True
        assert len(builder.build_instructions["parts"]) == 3
        assert len(builder.build_instructions["actions"]) == 2


class TestStagedWorkflowBuilderIntegration:
    """Integration tests for StagedWorkflowBuilder with real BuildActions."""

    @pytest.mark.asyncio
    async def test_workflow_with_watermark_action(self, valid_client_options):
        """Test workflow with watermark action that requires file registration."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        return b"watermarked-pdf"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)

                        # Create a watermark action that needs file registration
                        watermark_action = BuildActions.watermark_image("logo.png")

                        result = await (
                            builder.add_file_part("document.pdf")
                            .apply_action(watermark_action)
                            .output_pdf()
                            .execute()
                        )

                        assert result["success"] is True

                        # Verify that actions were applied (the specific structure depends on implementation)
                        # Note: assets are cleaned up after execution, but the build instructions remain
                        assert len(builder.build_instructions["actions"]) == 1

    @pytest.mark.asyncio
    async def test_workflow_with_mixed_actions(self, valid_client_options):
        """Test workflow with mix of regular actions and file-input actions."""
        with patch(
            "nutrient_dws.builder.builder.validate_file_input", return_value=True
        ):
            with patch(
                "nutrient_dws.builder.builder.is_remote_file_input", return_value=False
            ):
                with patch(
                    "nutrient_dws.builder.builder.process_file_input"
                ) as mock_process:
                    mock_process.return_value = ("test-content", "application/pdf")

                    async def mock_request(endpoint, data):
                        return b"processed-pdf"

                    with patch(
                        "nutrient_dws.builder.base_builder.BaseBuilder._send_request",
                        side_effect=mock_request,
                    ):
                        builder = StagedWorkflowBuilder(valid_client_options)

                        # Mix of regular actions and actions requiring file registration
                        actions = [
                            BuildActions.ocr("english"),  # Regular action
                            BuildActions.watermark_image(
                                "watermark.png"
                            ),  # File input action
                            BuildActions.flatten(),  # Regular action
                            BuildActions.apply_instant_json(
                                "annotations.json"
                            ),  # File input action
                        ]

                        result = await (
                            builder.add_file_part("document.pdf")
                            .apply_actions(actions)
                            .output_pdf()
                            .execute()
                        )

                        assert result["success"] is True

                        # Verify actions were applied (the specific structure depends on implementation)
                        # Note: assets are cleaned up after execution, but the build instructions remain
                        processed_actions = builder.build_instructions["actions"]
                        assert len(processed_actions) == 4
