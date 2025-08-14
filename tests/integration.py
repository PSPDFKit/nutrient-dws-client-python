"""Integration tests for Nutrient DWS Python Client.

These tests require a valid API key and make real API calls.
Set NUTRIENT_API_KEY environment variable to run these tests.
"""

import pytest

from nutrient_dws import NutrientClient
from nutrient_dws.errors import APIError, AuthenticationError, ValidationError

from .helpers import (
    SAMPLE_PDF,
    ResultValidator,
    TestDocumentGenerator,
    skip_integration_if_no_api_key,
)


class TestIntegrationClientBasics:
    """Test basic client functionality with real API calls."""

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_client_account_info(self, integration_client):
        """Test getting account information."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        account_info = await integration_client.get_account_info()

        assert isinstance(account_info, dict)
        assert "organization" in account_info
        assert "subscriptionType" in account_info
        assert "credits" in account_info or "creditsRemaining" in account_info

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_client_with_invalid_api_key(self):
        """Test client with invalid API key."""
        invalid_client = NutrientClient({"apiKey": "invalid_key_12345"})

        with pytest.raises(AuthenticationError):
            await invalid_client.get_account_info()

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_token_management(self, integration_client):
        """Test creating and deleting tokens."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        # Create a token
        token_params = {
            "allowedOperations": ["annotations_api"],
            "expirationTime": 3600,
        }

        token_response = await integration_client.create_token(token_params)

        assert isinstance(token_response, dict)
        assert "id" in token_response
        assert "accessToken" in token_response
        assert "expirationTime" in token_response

        token_id = token_response["id"]

        # Delete the token
        await integration_client.delete_token(token_id)

        # Should succeed without errors


class TestIntegrationDocumentOperations:
    """Test document operations with real API calls."""

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_simple_pdf_conversion(self, integration_client):
        """Test converting PDF to DOCX."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        result = await integration_client.convert(SAMPLE_PDF, "docx")

        ResultValidator.validate_office_output(result, "docx")
        assert len(result["buffer"]) > 0
        assert result["filename"].endswith(".docx")

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_ocr_operation(self, integration_client):
        """Test OCR operation on PDF."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        # Create a PDF with text that needs OCR
        scanned_pdf = TestDocumentGenerator.generate_simple_pdf_content()

        result = await integration_client.ocr(scanned_pdf, "english")

        ResultValidator.validate_buffer_output(result, "application/pdf")
        assert len(result["buffer"]) > 0

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_text_extraction(self, integration_client):
        """Test extracting text from PDF."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        result = await integration_client.extract_text(SAMPLE_PDF)

        ResultValidator.validate_json_content_output(result)
        assert "pages" in result["data"]
        assert isinstance(result["data"]["pages"], list)

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_watermark_text(self, integration_client):
        """Test adding text watermark."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        result = await integration_client.watermark_text(
            SAMPLE_PDF, "CONFIDENTIAL", {"opacity": 0.5, "fontSize": 24}
        )

        ResultValidator.validate_buffer_output(result, "application/pdf")
        assert len(result["buffer"]) > 0
        # Watermarked PDF should be different from original
        assert result["buffer"] != SAMPLE_PDF

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_merge_documents(self, integration_client):
        """Test merging multiple documents."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        # Create two similar PDFs to merge
        pdf1 = TestDocumentGenerator.generate_simple_pdf_content()
        pdf2 = TestDocumentGenerator.generate_simple_pdf_content()

        result = await integration_client.merge([pdf1, pdf2])

        ResultValidator.validate_buffer_output(result, "application/pdf")
        assert len(result["buffer"]) > 0
        # Merged PDF should be larger than individual PDFs
        assert len(result["buffer"]) > len(pdf1)

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_password_protection(self, integration_client):
        """Test password protecting a PDF."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        result = await integration_client.password_protect(
            SAMPLE_PDF,
            "user_password_123",
            "owner_password_456",
            ["printing", "extract_accessibility"],
        )

        ResultValidator.validate_buffer_output(result, "application/pdf")
        assert len(result["buffer"]) > 0
        # Password-protected PDF should be different from original
        assert result["buffer"] != SAMPLE_PDF


class TestIntegrationWorkflowBuilder:
    """Test workflow builder with real API calls."""

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_simple_workflow(self, integration_client):
        """Test building and executing a simple workflow."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        result = await (
            integration_client.workflow()
            .add_file_part(SAMPLE_PDF)
            .output_pdf()
            .execute()
        )

        assert result["success"] is True
        assert "output" in result
        ResultValidator.validate_buffer_output(result["output"], "application/pdf")

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_complex_workflow(self, integration_client):
        """Test building and executing a complex workflow."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        from nutrient_dws.builder.constant import BuildActions

        result = await (
            integration_client.workflow()
            .add_file_part(SAMPLE_PDF)
            .apply_action(BuildActions.watermark_text("DRAFT", {"opacity": 0.3}))
            .apply_action(BuildActions.flatten())
            .output_pdf({"flatten": True})
            .execute()
        )

        assert result["success"] is True
        assert "output" in result
        ResultValidator.validate_buffer_output(result["output"], "application/pdf")

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_workflow_dry_run(self, integration_client):
        """Test workflow dry run functionality."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        from nutrient_dws.builder.constant import BuildActions

        workflow = (
            integration_client.workflow()
            .add_file_part(SAMPLE_PDF)
            .apply_action(BuildActions.ocr("english"))
            .output_pdf()
        )

        dry_run_result = await workflow.dry_run()

        assert isinstance(dry_run_result, dict)
        assert "valid" in dry_run_result
        assert dry_run_result["valid"] is True
        assert "estimated_time" in dry_run_result
        assert "estimated_credits" in dry_run_result
        assert isinstance(dry_run_result["estimated_time"], int)
        assert dry_run_result["estimated_time"] > 0

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_html_to_pdf_workflow(self, integration_client):
        """Test HTML to PDF conversion workflow."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        html_content = """
        <html>
        <head><title>Test Document</title></head>
        <body>
            <h1>Integration Test Document</h1>
            <p>This document was generated during integration testing.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
            </ul>
        </body>
        </html>
        """

        result = await (
            integration_client.workflow()
            .add_html_part(html_content)
            .output_pdf()
            .execute()
        )

        assert result["success"] is True
        ResultValidator.validate_buffer_output(result["output"], "application/pdf")
        assert len(result["output"]["buffer"]) > 0


class TestIntegrationErrorHandling:
    """Test error handling in integration scenarios."""

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_invalid_file_format(self, integration_client):
        """Test handling of invalid file format."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        invalid_content = b"This is not a valid PDF file content"

        with pytest.raises((ValidationError, APIError)) as exc_info:
            await integration_client.convert(invalid_content, "docx")

        # Should get an error about invalid file format
        error_message = str(exc_info.value).lower()
        assert any(
            keyword in error_message for keyword in ["invalid", "pdf", "format", "file"]
        )

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_unsupported_conversion(self, integration_client):
        """Test handling of unsupported conversion format."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        with pytest.raises(ValidationError) as exc_info:
            await integration_client.convert(SAMPLE_PDF, "unsupported_format")

        assert "unsupported" in str(exc_info.value).lower()

    @skip_integration_if_no_api_key
    @pytest.mark.asyncio
    async def test_workflow_validation_error(self, integration_client):
        """Test workflow validation errors."""
        if not integration_client:
            pytest.skip("No API key available for integration tests")

        # Try to execute workflow without adding any parts
        workflow = integration_client.workflow().output_pdf()

        with pytest.raises(ValidationError) as exc_info:
            await workflow.execute()

        error_message = str(exc_info.value).lower()
        assert any(keyword in error_message for keyword in ["parts", "input", "empty"])


# Custom markers for different test types
pytestmark = [
    pytest.mark.integration,  # Mark all tests in this file as integration tests
]


# Fixtures specific to integration tests
@pytest.fixture(scope="module")
def integration_test_config():
    """Configuration for integration tests."""
    return {
        "timeout": 30,  # 30 second timeout for API calls
        "retry_attempts": 2,
        "max_file_size": 10 * 1024 * 1024,  # 10MB max file size
    }
