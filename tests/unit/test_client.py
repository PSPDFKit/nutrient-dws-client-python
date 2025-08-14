"""Simple working tests that cover core functionality."""

import pytest

from nutrient_dws import NutrientClient
from nutrient_dws.builder.constant import BuildActions, BuildOutputs
from nutrient_dws.errors import ValidationError


class TestBasicFunctionality:
    """Test basic functionality that should work."""

    def test_client_creation(self):
        """Test client can be created."""
        client = NutrientClient({"apiKey": "test-key"})
        assert client is not None

    def test_client_validation(self):
        """Test client validates options."""
        with pytest.raises(ValidationError):
            NutrientClient(None)

        with pytest.raises(ValidationError):
            NutrientClient({})

    def test_workflow_builder_creation(self):
        """Test workflow builder can be created."""
        client = NutrientClient({"apiKey": "test-key"})
        workflow = client.workflow()
        assert workflow is not None

    def test_build_actions_ocr(self):
        """Test OCR action creation."""
        action = BuildActions.ocr("english")
        assert action["type"] == "ocr"
        assert action["language"] == "english"

    def test_build_actions_watermark(self):
        """Test watermark action creation."""
        action = BuildActions.watermarkText("CONFIDENTIAL", {"opacity": 0.5})
        assert action["type"] == "watermark"
        assert action["text"] == "CONFIDENTIAL"

    def test_build_actions_flatten(self):
        """Test flatten action creation."""
        action = BuildActions.flatten()
        assert action["type"] == "flatten"

    def test_build_actions_rotate(self):
        """Test rotate action creation."""
        action = BuildActions.rotate(90)
        assert action["type"] == "rotate"
        assert action["rotateBy"] == 90

    def test_build_outputs_pdf(self):
        """Test PDF output creation."""
        output = BuildOutputs.pdf()
        assert output["type"] == "pdf"

    def test_build_outputs_image(self):
        """Test image output creation."""
        output = BuildOutputs.image("png")
        assert output["type"] == "image"
        assert output["format"] == "png"

    def test_build_outputs_office(self):
        """Test office output creation."""
        output = BuildOutputs.office("docx")
        assert output["type"] == "docx"

    def test_build_outputs_json(self):
        """Test JSON output creation."""
        output = BuildOutputs.jsonContent()
        assert output["type"] == "json-content"

    def test_mime_type_utility(self):
        """Test MIME type utility function."""
        output = BuildOutputs.pdf()
        result = BuildOutputs.getMimeTypeForOutput(output)
        assert result["mimeType"] == "application/pdf"
        assert "filename" in result

    def test_client_methods_exist(self):
        """Test that expected client methods exist."""
        client = NutrientClient({"apiKey": "test-key"})

        # Check account methods
        assert hasattr(client, "get_account_info")
        assert hasattr(client, "create_token")
        assert hasattr(client, "delete_token")

        # Check workflow method
        assert hasattr(client, "workflow")

        # Check convenience methods
        assert hasattr(client, "sign")
        assert hasattr(client, "watermark_text")
        assert hasattr(client, "watermark_image")
        assert hasattr(client, "convert")
        assert hasattr(client, "ocr")
        assert hasattr(client, "extract_text")
        assert hasattr(client, "extract_table")
        assert hasattr(client, "extract_key_value_pairs")
        assert hasattr(client, "password_protect")
        assert hasattr(client, "set_metadata")
        assert hasattr(client, "merge")
        assert hasattr(client, "flatten")
        assert hasattr(client, "create_redactions_ai")

    def test_workflow_builder_methods_exist(self):
        """Test that workflow builder has expected methods."""
        client = NutrientClient({"apiKey": "test-key"})
        builder = client.workflow()

        assert hasattr(builder, "add_file_part")
        assert hasattr(builder, "add_html_part")
        assert hasattr(builder, "add_new_page")
        assert hasattr(builder, "add_document_part")

    def test_merge_validation(self):
        """Test merge validation."""
        client = NutrientClient({"apiKey": "test-key"})

        with pytest.raises(ValidationError) as exc_info:
            import asyncio

            asyncio.run(client.merge(["single_file.pdf"]))

        assert "At least 2 files are required" in str(exc_info.value)


class TestErrorHierarchy:
    """Test error class hierarchy."""

    def test_validation_error_creation(self):
        """Test ValidationError can be created."""
        error = ValidationError("Test message")
        assert isinstance(error, Exception)
        assert "Test message" in str(error)

    def test_error_imports_work(self):
        """Test that error imports work correctly."""
        from nutrient_dws.errors import (
            APIError,
            AuthenticationError,
            NetworkError,
            NutrientError,
            ValidationError,
        )

        # Test that they can be instantiated
        validation_error = ValidationError("Test")
        api_error = APIError("Test", 400)
        auth_error = AuthenticationError("Test")
        network_error = NetworkError("Test")

        # Test inheritance
        assert isinstance(validation_error, NutrientError)
        assert isinstance(api_error, NutrientError)
        assert isinstance(auth_error, NutrientError)
        assert isinstance(network_error, NutrientError)
