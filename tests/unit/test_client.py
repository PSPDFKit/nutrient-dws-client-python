"""Tests for NutrientClient functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nutrient_dws import NutrientClient
from nutrient_dws.errors import ValidationError, NutrientError


class TestNutrientClientConstructor:
    """Tests for NutrientClient constructor."""

    def test_create_client_with_valid_options(self, valid_client_options, unit_client):
        assert unit_client is not None
        assert unit_client.options == valid_client_options

    def test_create_client_with_minimal_options(self):
        client = NutrientClient(api_key="test-key")
        assert client is not None
        assert client.options["apiKey"] == "test-key"

    def test_create_client_with_async_api_key_function(self):
        async def get_api_key():
            return "async-key"

        client = NutrientClient(api_key=get_api_key)
        assert client is not None
        assert callable(client.options["apiKey"])

    def test_throw_validation_error_for_missing_options(self):
        with pytest.raises(ValidationError, match="API key is required"):
            NutrientClient(None)

    def test_throw_validation_error_for_missing_api_key(self):
        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            NutrientClient()

    def test_throw_validation_error_for_invalid_api_key_type(self):
        with pytest.raises(
            ValidationError,
            match="API key must be a string or a function that returns a string",
        ):
            NutrientClient(api_key=123)

    def test_throw_validation_error_for_invalid_base_url_type(self):
        with pytest.raises(ValidationError, match="Base URL must be a string"):
            NutrientClient(api_key="test-key", base_url=123)


class TestNutrientClientWorkflow:
    """Tests for NutrientClient workflow method."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    def test_create_workflow_instance(
        self, mock_staged_workflow_builder, valid_client_options, unit_client
    ):
        mock_workflow_instance = MagicMock()
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        workflow = unit_client.workflow()

        mock_staged_workflow_builder.assert_called_once_with(valid_client_options)
        assert workflow == mock_workflow_instance

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    def test_pass_client_options_to_workflow(self, mock_staged_workflow_builder):
        custom_options = {"apiKey": "custom-key", "baseUrl": "https://custom.api.com", "timeout": None}
        client = NutrientClient(api_key=custom_options["apiKey"], base_url=custom_options["baseUrl"])

        client.workflow()

        mock_staged_workflow_builder.assert_called_once_with(custom_options)

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    def test_workflow_with_timeout_override(
        self, mock_staged_workflow_builder, valid_client_options, unit_client
    ):
        override_timeout = 5000

        unit_client.workflow(override_timeout)

        expected_options = valid_client_options.copy()
        expected_options["timeout"] = override_timeout
        mock_staged_workflow_builder.assert_called_once_with(expected_options)


class TestNutrientClientOcr:
    """Tests for NutrientClient OCR functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_perform_ocr_with_single_language_and_default_pdf_output(
        self, mock_staged_workflow_builder, unit_client
    ):

        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"test-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"
        language = "english"

        result = await unit_client.ocr(file, language)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(
            file, None, [{"type": "ocr", "language": "english"}]
        )
        mock_workflow_instance.output_pdf.assert_called_once()
        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert result["buffer"] == b"test-buffer"
        assert result["mimeType"] == "application/pdf"

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_perform_ocr_with_multiple_languages(
        self, mock_staged_workflow_builder, unit_client
    ):

        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"test-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"
        languages = ["english", "spanish"]

        await unit_client.ocr(file, languages)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(
            file, None, [{"type": "ocr", "language": ["english", "spanish"]}]
        )
        mock_workflow_instance.output_pdf.assert_called_once()
        mock_output_stage.execute.assert_called_once()


class TestNutrientClientWatermarkText:
    """Tests for NutrientClient text watermark functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_add_text_watermark_with_default_options(
        self, mock_staged_workflow_builder, unit_client
    ):

        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"test-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"
        text = "CONFIDENTIAL"

        await unit_client.watermark_text(file, text)

        # Check that add_file_part was called with the watermark action
        call_args = mock_workflow_instance.add_file_part.call_args
        assert call_args[0][0] == file  # First positional arg (file)
        assert call_args[0][1] is None  # Second positional arg (options)

        # Check the watermark action structure
        actions = call_args[0][2]  # Third positional arg (actions)
        assert len(actions) == 1
        watermark_action = actions[0]
        assert watermark_action["type"] == "watermark"
        assert watermark_action["text"] == "CONFIDENTIAL"
        assert watermark_action["width"] == {"value": 100, "unit": "%"}
        assert watermark_action["height"] == {"value": 100, "unit": "%"}

        mock_workflow_instance.output_pdf.assert_called_once()

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_add_text_watermark_with_custom_options(
        self, mock_staged_workflow_builder, unit_client
    ):

        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"test-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"
        text = "DRAFT"
        options = {
            "opacity": 0.5,
            "fontSize": 24,
            "fontColor": "#ff0000",
            "rotation": 45,
        }

        await unit_client.watermark_text(file, text, options)

        # Check that add_file_part was called with the correct watermark action
        call_args = mock_workflow_instance.add_file_part.call_args
        actions = call_args[0][2]
        watermark_action = actions[0]

        assert watermark_action["type"] == "watermark"
        assert watermark_action["text"] == "DRAFT"
        assert watermark_action["opacity"] == 0.5
        assert watermark_action["fontSize"] == 24
        assert watermark_action["fontColor"] == "#ff0000"
        assert watermark_action["rotation"] == 45


class TestNutrientClientWatermarkImage:
    """Tests for NutrientClient image watermark functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_add_image_watermark_with_default_options(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"test-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"
        image = "watermark.png"

        await unit_client.watermark_image(file, image)

        # Check that add_file_part was called with the watermark action
        call_args = mock_workflow_instance.add_file_part.call_args
        assert call_args[0][0] == file
        assert call_args[0][1] is None

        # Check the watermark action has the right properties (file input needs registration)
        actions = call_args[0][2]
        assert len(actions) == 1
        watermark_action = actions[0]

        # Check that it's an action that needs file registration
        assert hasattr(watermark_action, "fileInput")
        assert hasattr(watermark_action, "createAction")
        assert watermark_action.fileInput == "watermark.png"

        mock_workflow_instance.output_pdf.assert_called_once()

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_add_image_watermark_with_custom_options(
        self, mock_staged_workflow_builder, unit_client
    ):

        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"test-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"
        image = "watermark.png"
        options = {"opacity": 0.5, "rotation": 45}

        await unit_client.watermark_image(file, image, options)

        # Check that add_file_part was called with the watermark action
        call_args = mock_workflow_instance.add_file_part.call_args
        actions = call_args[0][2]
        watermark_action = actions[0]

        # Check that it's an action that needs file registration with the right file input
        assert hasattr(watermark_action, "fileInput")
        assert hasattr(watermark_action, "createAction")
        assert watermark_action.fileInput == "watermark.png"


class TestNutrientClientMerge:
    """Tests for NutrientClient merge functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_merge_multiple_files(
        self, mock_staged_workflow_builder, unit_client
    ):

        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"test-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        files = ["file1.pdf", "file2.pdf", "file3.pdf"]

        result = await unit_client.merge(files)

        # Check that add_file_part was called for each file
        assert mock_workflow_instance.add_file_part.call_count == 3
        mock_workflow_instance.add_file_part.assert_any_call("file1.pdf")
        mock_workflow_instance.add_file_part.assert_any_call("file2.pdf")
        mock_workflow_instance.add_file_part.assert_any_call("file3.pdf")

        mock_workflow_instance.output_pdf.assert_called_once()
        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert result["buffer"] == b"test-buffer"

    @pytest.mark.asyncio
    async def test_throw_validation_error_when_less_than_2_files_provided(
        self, valid_client_options, unit_client
    ):
        files = ["file1.pdf"]

        with pytest.raises(
            ValidationError, match="At least 2 files are required for merge operation"
        ):
            await unit_client.merge(files)

    @pytest.mark.asyncio
    async def test_throw_validation_error_when_empty_array_provided(
        self, unit_client
    ):
        files = []

        with pytest.raises(
            ValidationError, match="At least 2 files are required for merge operation"
        ):
            await unit_client.merge(files)


class TestNutrientClientExtractText:
    """Tests for NutrientClient extract text functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_extract_text_from_document(
        self, mock_staged_workflow_builder, unit_client
    ):

        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "data": {"pages": [{"plainText": "Extracted text content"}]},
                    "mimeType": "application/json",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_json.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"

        result = await unit_client.extract_text(file)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(file, None)
        mock_workflow_instance.output_json.assert_called_once_with(
            {"plainText": True, "tables": False}
        )
        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert result["data"] == {"pages": [{"plainText": "Extracted text content"}]}

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_extract_text_with_page_range(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "data": {"pages": [{"plainText": "Extracted text content"}]},
                    "mimeType": "application/json",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_json.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"
        pages = {"start": 0, "end": 2}

        await unit_client.extract_text(file, pages)

        # Verify the workflow was called with page options
        call_args = mock_workflow_instance.add_file_part.call_args
        assert call_args[0][0] == file  # First positional arg (file)
        assert call_args[0][1] == {
            "pages": {"start": 0, "end": 2}
        }  # Second positional arg (part options)


class TestNutrientClientExtractTable:
    """Tests for NutrientClient extract table functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_extract_table_from_document(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "data": {"pages": [{"tables": [{"rows": [["cell1", "cell2"]]}]}]},
                    "mimeType": "application/json",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_json.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"

        result = await unit_client.extract_table(file)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(file, None)
        mock_workflow_instance.output_json.assert_called_once_with(
            {"plainText": False, "tables": True}
        )
        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert "tables" in result["data"]["pages"][0]


class TestNutrientClientExtractKeyValuePairs:
    """Tests for NutrientClient extract key-value pairs functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_extract_key_value_pairs_from_document(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "data": {
                        "pages": [
                            {"keyValuePairs": [{"key": "Name", "value": "John Doe"}]}
                        ]
                    },
                    "mimeType": "application/json",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_json.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "test-file.pdf"

        result = await unit_client.extract_key_value_pairs(file)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(file, None)
        mock_workflow_instance.output_json.assert_called_once_with(
            {"plainText": False, "tables": False, "keyValuePairs": True}
        )
        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert "keyValuePairs" in result["data"]["pages"][0]


class TestNutrientClientConvert:
    """Tests for NutrientClient convert functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_convert_docx_to_pdf(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"pdf-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "document.docx"
        target_format = "pdf"

        result = await unit_client.convert(file, target_format)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(file)
        mock_workflow_instance.output_pdf.assert_called_once()
        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert result["buffer"] == b"pdf-buffer"
        assert result["mimeType"] == "application/pdf"

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_convert_pdf_to_image(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"png-buffer",
                    "mimeType": "image/png",
                    "filename": "output.png",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_image.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "document.pdf"
        target_format = "png"

        result = await unit_client.convert(file, target_format)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(file)
        mock_workflow_instance.output_image.assert_called_once_with("png", {"dpi": 300})
        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert result["buffer"] == b"png-buffer"
        assert result["mimeType"] == "image/png"

    @pytest.mark.asyncio
    async def test_convert_unsupported_format_throws_error(self, unit_client):
        file = "document.pdf"
        target_format = "unsupported"

        with pytest.raises(
            ValidationError, match="Unsupported target format: unsupported"
        ):
            await unit_client.convert(file, target_format)


class TestNutrientClientPasswordProtect:
    """Tests for NutrientClient password protection functionality."""

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_password_protect_pdf(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"protected-pdf-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "document.pdf"
        user_password = "user123"
        owner_password = "owner456"

        result = await unit_client.password_protect(file, user_password, owner_password)

        # Verify the workflow was called correctly
        mock_workflow_instance.add_file_part.assert_called_once_with(file)

        # Check the PDF output options
        call_args = mock_workflow_instance.output_pdf.call_args
        pdf_options = call_args[0][0]  # First positional argument
        assert pdf_options["user_password"] == user_password
        assert pdf_options["owner_password"] == owner_password

        mock_output_stage.execute.assert_called_once()

        # Verify the result
        assert result["buffer"] == b"protected-pdf-buffer"

    @patch("nutrient_dws.client.StagedWorkflowBuilder")
    @pytest.mark.asyncio
    async def test_password_protect_pdf_with_permissions(
        self, mock_staged_workflow_builder, unit_client
    ):
        # Setup mock workflow
        mock_workflow_instance = MagicMock()
        mock_output_stage = MagicMock()
        mock_output_stage.execute = AsyncMock(
            return_value={
                "success": True,
                "output": {
                    "buffer": b"protected-pdf-buffer",
                    "mimeType": "application/pdf",
                    "filename": "output.pdf",
                },
            }
        )

        mock_workflow_instance.add_file_part.return_value = mock_workflow_instance
        mock_workflow_instance.output_pdf.return_value = mock_output_stage
        mock_staged_workflow_builder.return_value = mock_workflow_instance

        file = "document.pdf"
        user_password = "user123"
        owner_password = "owner456"
        permissions = ["printing", "extract_accessibility"]

        result = await unit_client.password_protect(
            file, user_password, owner_password, permissions
        )

        # Check the PDF output options include permissions
        call_args = mock_workflow_instance.output_pdf.call_args
        pdf_options = call_args[0][0]
        assert pdf_options["user_permissions"] == permissions


class TestNutrientClientProcessTypedWorkflowResult:
    """Tests for NutrientClient _process_typed_workflow_result method."""

    def test_process_successful_workflow_result(self, unit_client):

        result = {
            "success": True,
            "output": {"buffer": b"test-buffer", "mimeType": "application/pdf"},
        }

        processed_result = unit_client._process_typed_workflow_result(result)
        assert processed_result == result["output"]

    def test_process_failed_workflow_result_with_errors(self, unit_client):
        test_error = NutrientError("Test error", "TEST_ERROR")
        result = {"success": False, "errors": [{"error": test_error}], "output": None}

        with pytest.raises(NutrientError, match="Test error"):
            unit_client._process_typed_workflow_result(result)

    def test_process_failed_workflow_result_without_errors(self, unit_client):
        result = {"success": False, "errors": [], "output": None}

        with pytest.raises(
            NutrientError,
            match="Workflow operation failed without specific error details",
        ):
            unit_client._process_typed_workflow_result(result)

    def test_process_successful_workflow_result_without_output(self, unit_client):
        result = {"success": True, "output": None}

        with pytest.raises(
            NutrientError,
            match="Workflow completed successfully but no output was returned",
        ):
            unit_client._process_typed_workflow_result(result)


class TestNutrientClientAccountInfo:
    """Tests for NutrientClient account info functionality."""

    @patch("nutrient_dws.client.send_request")
    @pytest.mark.asyncio
    async def test_get_account_info(self, mock_send_request, valid_client_options, unit_client):
        expected_account_info = {
            "subscriptionType": "premium",
            "remainingCredits": 1000,
        }

        mock_send_request.return_value = {"data": expected_account_info, "status": 200}

        result = await unit_client.get_account_info()

        # Verify the request was made correctly
        mock_send_request.assert_called_once_with(
            {
                "method": "GET",
                "endpoint": "/account/info",
                "data": None,
                "headers": None,
            },
            valid_client_options,
        )

        # Verify the result
        assert result == expected_account_info


class TestNutrientClientCreateToken:
    """Tests for NutrientClient create token functionality."""

    @patch("nutrient_dws.client.send_request")
    @pytest.mark.asyncio
    async def test_create_token(self, mock_send_request, valid_client_options, unit_client):
        params = {"allowedOperations": ["annotations_api"], "expirationTime": 3600}

        expected_token_response = {"id": "token-123", "token": "jwt-token-string"}

        mock_send_request.return_value = {
            "data": expected_token_response,
            "status": 200,
        }

        result = await unit_client.create_token(params)

        # Verify the request was made correctly
        mock_send_request.assert_called_once_with(
            {"method": "POST", "endpoint": "/tokens", "data": params, "headers": None},
            valid_client_options,
        )

        # Verify the result
        assert result == expected_token_response


class TestNutrientClientDeleteToken:
    """Tests for NutrientClient delete token functionality."""

    @patch("nutrient_dws.client.send_request")
    @pytest.mark.asyncio
    async def test_delete_token(self, mock_send_request, valid_client_options, unit_client):

        token_id = "token-123"

        mock_send_request.return_value = {"data": None, "status": 204}

        await unit_client.delete_token(token_id)

        # Verify the request was made correctly
        mock_send_request.assert_called_once_with(
            {
                "method": "DELETE",
                "endpoint": "/tokens",
                "data": {"id": token_id},
                "headers": None,
            },
            valid_client_options,
        )
