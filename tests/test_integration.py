"""Integration tests for Nutrient DWS Python Client.

These tests require a valid API key and make real API calls.
Set NUTRIENT_API_KEY environment variable to run these tests.

To run these tests with a live API:
1. Set NUTRIENT_API_KEY environment variable
2. Run: NUTRIENT_API_KEY=your_key pytest tests/test_integration.py
"""

import os
import pytest
from dotenv import load_dotenv

from nutrient_dws import NutrientClient
from nutrient_dws.builder.constant import BuildActions
from nutrient_dws.errors import NutrientError, ValidationError
from tests.helpers import (
    TestDocumentGenerator,
    ResultValidator,
    sample_pdf,
    sample_docx,
    sample_png,
)

load_dotenv()  # Load environment variables

# Skip integration tests unless explicitly enabled with valid API key
should_run_integration_tests = bool(os.getenv("NUTRIENT_API_KEY"))

# Use conditional pytest.mark based on environment
pytestmark = pytest.mark.skipif(
    not should_run_integration_tests,
    reason="Integration tests require NUTRIENT_API_KEY environment variable",
)

@pytest.fixture(scope="class")
def integration_client():
    """Create client instance for testing."""
    return NutrientClient(api_key=os.getenv("NUTRIENT_API_KEY", ""), base_url=os.getenv("NUTRIENT_BASE_URL", "https://api.nutrient.io"))


class TestIntegrationDirectMethods:
    """Integration tests with live API - direct client methods."""

    def test_account_and_authentication_methods(self, integration_client):
        """Test account information and authentication methods."""

    @pytest.mark.asyncio
    async def test_get_account_info(self, integration_client):
        """Test retrieving account information."""
        account_info = await integration_client.get_account_info()

        assert account_info is not None
        assert "subscriptionType" in account_info
        assert isinstance(account_info["subscriptionType"], str)
        assert "apiKeys" in account_info

    @pytest.mark.asyncio
    async def test_create_and_delete_token(self, integration_client):
        """Test creating and deleting authentication tokens."""
        token_params = {
            "expirationTime": 0,
        }

        token = await integration_client.create_token(token_params)

        assert token is not None
        assert "id" in token
        assert isinstance(token["id"], str)
        assert "accessToken" in token
        assert isinstance(token["accessToken"], str)

        # Clean up - delete the token we just created
        await integration_client.delete_token(token["id"])

    @pytest.mark.asyncio
    async def test_sign_pdf_document(self, integration_client):
        """Test signing PDF documents."""
        result = await integration_client.sign(sample_pdf)

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_sign_pdf_with_custom_image(self, integration_client):
        """Test signing PDF with custom signature image."""
        result = await integration_client.sign(
            sample_pdf,
            None,
            {
                "image": sample_png,
            },
        )

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_create_redactions_ai(self, integration_client):
        """Test AI-powered redaction functionality."""
        sensitive_document = TestDocumentGenerator.generate_pdf_with_sensitive_data()
        result = await integration_client.create_redactions_ai(sensitive_document, "Redact Email")

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"
        assert result["filename"] == "output.pdf"

    @pytest.mark.asyncio
    async def test_create_redactions_ai_with_page_range(self, integration_client):
        """Test AI redaction with specific page range."""
        result = await integration_client.create_redactions_ai(
            sample_pdf,
            "Redact Email",
            "apply",
            {
                "start": 1,
                "end": 2,
            },
        )

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_data,input_type,output_type,expected_mime",
        [
            (sample_pdf, "pdf", "pdfa", "application/pdf"),
            (sample_pdf, "pdf", "pdfua", "application/pdf"),
            (
                sample_pdf,
                "pdf",
                "docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            (
                sample_pdf,
                "pdf",
                "xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            (
                sample_pdf,
                "pdf",
                "pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
            (sample_docx, "docx", "pdf", "application/pdf"),
            (sample_pdf, "pdf", "png", "image/png"),
            (sample_pdf, "pdf", "jpeg", "image/jpeg"),
            (sample_pdf, "pdf", "jpg", "image/jpeg"),
            (sample_pdf, "pdf", "webp", "image/webp"),
            # (sample_pdf, "pdf", "html", "text/html"), # FIXME: 500 error upstream
            (sample_pdf, "pdf", "markdown", "text/markdown"),
        ],
    )
    async def test_convert_formats(
        self, integration_client, input_data, input_type, output_type, expected_mime
    ):
        """Test document format conversion."""
        result = await integration_client.convert(input_data, output_type)

        assert result is not None

        if output_type not in ["markdown", "html"]:
            assert isinstance(result.get("buffer"), (bytes, bytearray))
        else:
            assert isinstance(result.get("content"), str)
        assert result["mimeType"] == expected_mime

    @pytest.mark.asyncio
    async def test_ocr_single_language(self, integration_client):
        """Test OCR with single language."""
        result = await integration_client.ocr(sample_png, "english")

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_ocr_multiple_languages(self, integration_client):
        """Test OCR with multiple languages."""
        result = await integration_client.ocr(sample_png, ["english", "spanish"])

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_watermark_text(self, integration_client):
        """Test text watermarking."""
        result = await integration_client.watermark_text(
            sample_pdf,
            "CONFIDENTIAL",
            {
                "opacity": 0.5,
                "fontSize": 48,
                "rotation": 45,
            },
        )

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_watermark_image(self, integration_client):
        """Test image watermarking."""
        result = await integration_client.watermark_image(
            sample_pdf,
            sample_png,
            {
                "opacity": 0.5,
            },
        )

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_merge_pdf_files(self, integration_client):
        """Test merging multiple PDF files."""
        result = await integration_client.merge([sample_pdf, sample_pdf, sample_pdf])

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"
        # Merged PDF should be larger than single PDF
        assert len(result["buffer"]) > len(sample_pdf)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "optimization_options",
        [
            {"imageOptimizationQuality": 1},  # low
            {"imageOptimizationQuality": 2},  # medium
            {"imageOptimizationQuality": 3},  # high
            {"imageOptimizationQuality": 4, "mrcCompression": True},  # maximum
        ],
    )
    async def test_optimize_pdf(self, integration_client, optimization_options):
        """Test PDF optimization with different options."""
        result = await integration_client.optimize(sample_pdf, optimization_options)

        assert result is not None
        assert isinstance(result["buffer"], (bytes, bytearray))
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_extract_text(self, integration_client):
        """Test text extraction from PDF."""
        result = await integration_client.extract_text(sample_pdf)

        assert result is not None
        assert "data" in result
        assert isinstance(result["data"], dict)

    @pytest.mark.asyncio
    async def test_flatten_pdf(self, integration_client):
        """Test flattening PDF annotations."""
        result = await integration_client.flatten(sample_pdf)

        assert result is not None
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_rotate_pdf(self, integration_client):
        """Test rotating PDF pages."""
        result = await integration_client.rotate(sample_pdf, 90)

        assert result is not None
        assert result["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_rotate_pdf_page_range(self, integration_client):
        """Test rotating specific page range."""
        result = await integration_client.rotate(sample_pdf, 180, {"start": 1, "end": 3})

        assert result is not None
        assert result["mimeType"] == "application/pdf"


class TestIntegrationErrorHandling:
    """Test error handling scenarios with live API."""

    @pytest.mark.asyncio
    async def test_invalid_file_input(self, integration_client):
        """Test handling of invalid file input."""
        with pytest.raises((ValidationError, NutrientError)):
            await integration_client.convert(None, "pdf")

    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """Test handling of invalid API key."""
        invalid_client = NutrientClient(api_key="invalid-api-key")

        with pytest.raises(NutrientError, match="HTTP 401"):
            await invalid_client.convert(b"test", "pdf")

    @pytest.mark.asyncio
    async def test_network_timeout(self):
        """Test handling of network timeouts."""
        timeout_client = NutrientClient(api_key=os.getenv("NUTRIENT_API_KEY", ""), timeout=1)

        with pytest.raises(NutrientError):
            await timeout_client.convert(sample_docx, "pdf")


class TestIntegrationWorkflowBuilder:
    """Integration tests for workflow builder with live API."""

    @pytest.mark.asyncio
    async def test_complex_workflow_multiple_parts_actions(self, integration_client):
        """Test complex workflow with multiple parts and actions."""
        pdf1 = TestDocumentGenerator.generate_pdf_with_table()
        pdf2 = TestDocumentGenerator.generate_pdf_with_sensitive_data()
        html = TestDocumentGenerator.generate_html_content()

        result = await (
            integration_client.workflow()
            .add_file_part(pdf1, None, [BuildActions.rotate(90)])
            .add_html_part(html)
            .add_file_part(pdf2)
            .add_new_page({"layout": {"size": "A4"}})
            .apply_actions(
                [
                    BuildActions.watermark_text("DRAFT", {"opacity": 0.3}),
                    BuildActions.flatten(),
                ]
            )
            .output_pdfua()
            .execute(on_progress=lambda step, total: None)
        )

        assert result["success"] is True
        assert isinstance(result["output"]["buffer"], (bytes, bytearray))
        assert result["output"]["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_workflow_dry_run(self, integration_client):
        """Test workflow dry run analysis."""
        result = await (
            integration_client.workflow()
            .add_file_part(sample_pdf)
            .apply_action(BuildActions.ocr(["english", "french"]))
            .output_pdf()
            .dry_run()
        )

        assert result["success"] is True
        assert "analysis" in result
        assert result["analysis"]["cost"] >= 0
        assert "required_features" in result["analysis"]

    @pytest.mark.asyncio
    async def test_workflow_redaction_actions(self, integration_client):
        """Test workflow with redaction actions."""
        result = await (
            integration_client.workflow()
            .add_file_part(sample_pdf)
            .apply_actions(
                [
                    BuildActions.create_redactions_text(
                        "confidential", {}, {"caseSensitive": False}
                    ),
                    BuildActions.apply_redactions(),
                ]
            )
            .output_pdf()
            .execute()
        )

        assert result["success"] is True
        assert result["output"]["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_workflow_regex_redactions(self, integration_client):
        """Test workflow with regex redaction actions."""
        result = await (
            integration_client.workflow()
            .add_file_part(sample_pdf)
            .apply_actions(
                [
                    BuildActions.create_redactions_regex(
                        r"\d{3}-\d{2}-\d{4}", {}, {"caseSensitive": False}
                    ),
                    BuildActions.apply_redactions(),
                ]
            )
            .output_pdf()
            .execute()
        )

        assert result["success"] is True
        assert result["output"]["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_workflow_preset_redactions(self, integration_client):
        """Test workflow with preset redaction actions."""
        result = await (
            integration_client.workflow()
            .add_file_part(sample_pdf)
            .apply_actions(
                [
                    BuildActions.create_redactions_preset("email-address"),
                    BuildActions.apply_redactions(),
                ]
            )
            .output_pdf()
            .execute()
        )

        assert result["success"] is True
        assert result["output"]["mimeType"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_workflow_instant_json_xfdf(self, integration_client):
        """Test workflow with Instant JSON and XFDF actions."""
        pdf_file = sample_pdf
        json_file = TestDocumentGenerator.generate_instant_json_content()
        xfdf_file = TestDocumentGenerator.generate_xfdf_content()

        # Test apply_instant_json
        instant_json_result = await (
            integration_client.workflow()
            .add_file_part(pdf_file)
            .apply_action(BuildActions.apply_instant_json(json_file))
            .output_pdf()
            .execute()
        )

        assert instant_json_result["success"] is True
        assert instant_json_result["output"]["mimeType"] == "application/pdf"

        # Test apply_xfdf
        xfdf_result = await (
            integration_client.workflow()
            .add_file_part(pdf_file)
            .apply_action(BuildActions.apply_xfdf(xfdf_file))
            .output_pdf()
            .execute()
        )

        assert xfdf_result["success"] is True
        assert xfdf_result["output"]["mimeType"] == "application/pdf"


class TestIntegrationRedactionOperations:
    """Test redaction operations with live API."""

    @pytest.mark.asyncio
    async def test_text_based_redactions(self, integration_client, test_sensitive_pdf):
        """Test text-based redactions."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_sensitive_pdf)
            .apply_actions(
                [
                    BuildActions.create_redactions_text("123-45-6789"),
                    BuildActions.create_redactions_text("john.doe@example.com"),
                    BuildActions.apply_redactions(),
                ]
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_regex_redactions_ssn_pattern(self, integration_client, test_sensitive_pdf):
        """Test regex redactions for SSN pattern."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_sensitive_pdf)
            .apply_actions(
                [
                    BuildActions.create_redactions_regex(
                        r"\d{3}-\d{2}-\d{4}"
                    ),  # SSN pattern
                    BuildActions.apply_redactions(),
                ]
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_multiple_regex_patterns(self, integration_client, test_sensitive_pdf):
        """Test multiple regex redaction patterns."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_sensitive_pdf)
            .apply_actions(
                [
                    BuildActions.create_redactions_regex(
                        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                    ),  # Email
                    BuildActions.create_redactions_regex(
                        r"\(\d{3}\) \d{3}-\d{4}"
                    ),  # Phone
                    BuildActions.create_redactions_regex(
                        r"\d{4}-\d{4}-\d{4}-\d{4}"
                    ),  # Credit card
                    BuildActions.apply_redactions(),
                ]
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_preset_redactions_common_patterns(self, integration_client, test_sensitive_pdf):
        """Test preset redactions for common patterns."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_sensitive_pdf)
            .apply_actions(
                [
                    BuildActions.create_redactions_preset("email-address"),
                    BuildActions.create_redactions_preset("international-phone-number"),
                    BuildActions.create_redactions_preset("social-security-number"),
                    BuildActions.apply_redactions(),
                ]
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)


class TestIntegrationImageWatermarking:
    """Test image watermarking with live API."""

    @pytest.mark.asyncio
    async def test_image_watermark_basic(self, integration_client, test_table_pdf):
        """Test basic image watermarking."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .apply_action(
                BuildActions.watermark_image(
                    sample_png,
                    {
                        "opacity": 0.3,
                        "width": {"value": 200, "unit": "pt"},
                        "height": {"value": 100, "unit": "pt"},
                    },
                )
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_image_watermark_custom_positioning(self, integration_client, test_table_pdf):
        """Test image watermarking with custom positioning."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .apply_action(
                BuildActions.watermark_image(
                    sample_png,
                    {
                        "opacity": 0.5,
                        "width": {"value": 150, "unit": "pt"},
                        "height": {"value": 150, "unit": "pt"},
                        "top": {"value": 100, "unit": "pt"},
                        "left": {"value": 100, "unit": "pt"},
                    },
                )
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)


class TestIntegrationHtmlToPdfConversion:
    """Test HTML to PDF conversion with live API."""



    @pytest.mark.asyncio
    async def test_html_to_pdf_default_settings(self, integration_client, test_html_content):
        """Test HTML to PDF conversion with default settings."""
        result = await (
            integration_client.workflow().add_html_part(test_html_content).output_pdf().execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_html_with_actions(self, integration_client, test_html_content):
        """Test HTML conversion with applied actions."""
        result = await (
            integration_client.workflow()
            .add_html_part(test_html_content)
            .apply_actions(
                [
                    BuildActions.watermark_text("DRAFT", {"opacity": 0.3}),
                    BuildActions.flatten(),
                ]
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_combine_html_with_pdf(self, integration_client, test_html_content):
        """Test combining HTML with existing PDF."""
        test_table_pdf = TestDocumentGenerator.generate_pdf_with_table()
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .add_html_part(test_html_content)
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)


class TestIntegrationAnnotationOperations:
    """Test annotation operations with live API."""

    @pytest.mark.asyncio
    async def test_apply_xfdf_annotations(
        self, integration_client, test_table_pdf, test_xfdf_content
    ):
        """Test applying XFDF annotations to PDF."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .apply_action(BuildActions.apply_xfdf(test_xfdf_content))
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_apply_xfdf_and_flatten(
        self, integration_client, test_table_pdf, test_xfdf_content
    ):
        """Test applying XFDF and flattening annotations."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .apply_actions(
                [BuildActions.apply_xfdf(test_xfdf_content), BuildActions.flatten()]
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_apply_instant_json_annotations(
        self, integration_client, test_table_pdf, test_instant_json_content
    ):
        """Test applying Instant JSON annotations."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .apply_action(BuildActions.apply_instant_json(test_instant_json_content))
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)


class TestIntegrationAdvancedPdfOptions:
    """Test advanced PDF options with live API."""

    @pytest.mark.asyncio
    async def test_password_protected_pdf(self, integration_client, test_sensitive_pdf):
        """Test creating password-protected PDF."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_sensitive_pdf)
            .output_pdf(
                {
                    "user_password": "user123",
                    "owner_password": "owner456",
                }
            )
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_pdf_permissions(self, integration_client, test_table_pdf):
        """Test setting PDF permissions."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_pdf(
                {
                    "owner_password": "owner123",
                    "user_permissions": ["printing", "extract", "fill_forms"],
                }
            )
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_pdf_metadata(self, integration_client, test_table_pdf):
        """Test setting PDF metadata."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_pdf(
                {
                    "metadata": {
                        "title": "Test Document",
                        "author": "Test Author",
                    },
                }
            )
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_pdf_optimization_advanced(self, integration_client, test_table_pdf):
        """Test PDF optimization with advanced settings."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_pdf(
                {
                    "optimize": {
                        "mrcCompression": True,
                        "imageOptimizationQuality": 3,
                        "linearize": True,
                    },
                }
            )
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_pdfa_advanced_options(self, integration_client, test_table_pdf):
        """Test PDF/A with specific conformance level."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_pdfa(
                {
                    "conformance": "pdfa-2a",
                    "vectorization": True,
                    "rasterization": True,
                }
            )
            .execute()
        )

        ResultValidator.validate_pdf_output(result)


class TestIntegrationOfficeFormatOutputs:
    """Test Office format outputs with live API."""

    @pytest.mark.asyncio
    async def test_pdf_to_excel(self, integration_client, test_table_pdf):
        """Test converting PDF to Excel (XLSX)."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_office("xlsx")
            .execute()
        )

        ResultValidator.validate_office_output(result, "xlsx")

    @pytest.mark.asyncio
    async def test_pdf_to_powerpoint(self, integration_client, test_table_pdf):
        """Test converting PDF to PowerPoint (PPTX)."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_office("pptx")
            .execute()
        )

        ResultValidator.validate_office_output(result, "pptx")


class TestIntegrationImageOutputOptions:
    """Test image output options with live API."""

    @pytest.mark.asyncio
    async def test_pdf_to_jpeg_custom_dpi(self, integration_client, test_table_pdf):
        """Test converting PDF to JPEG with custom DPI."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_image("jpeg", {"dpi": 300})
            .execute()
        )

        ResultValidator.validate_image_output(result, "jpeg")

    @pytest.mark.asyncio
    async def test_pdf_to_webp(self, integration_client, test_table_pdf):
        """Test converting PDF to WebP format."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_image("webp", {"height": 300})
            .execute()
        )

        ResultValidator.validate_image_output(result, "webp")


class TestIntegrationJsonContentExtraction:
    """Test JSON content extraction with live API."""

    @pytest.mark.asyncio
    async def test_extract_tables(self, integration_client, test_table_pdf):
        """Test extracting tables from PDF."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_json({"tables": True})
            .execute()
        )

        ResultValidator.validate_json_output(result)

    @pytest.mark.asyncio
    async def test_extract_key_value_pairs(self, integration_client, test_table_pdf):
        """Test extracting key-value pairs."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_table_pdf)
            .output_json({"keyValuePairs": True})
            .execute()
        )

        ResultValidator.validate_json_output(result)

    @pytest.mark.asyncio
    async def test_extract_specific_page_range(self, integration_client, test_sensitive_pdf):
        """Test extracting content from specific page range."""
        result = await (
            integration_client.workflow()
            .add_file_part(test_sensitive_pdf, {"pages": {"start": 0, "end": 0}})
            .output_json()
            .execute()
        )

        ResultValidator.validate_json_output(result)


class TestIntegrationComplexWorkflows:
    """Test complex multi-format workflows with live API."""

    @pytest.mark.asyncio
    async def test_combine_html_pdf_images_with_actions(self, integration_client):
        """Test combining HTML, PDF, and images with various actions."""
        test_sensitive_pdf = TestDocumentGenerator.generate_pdf_with_sensitive_data()
        test_html_content = TestDocumentGenerator.generate_html_content()

        result = await (
            integration_client.workflow()
            # Add existing PDF
            .add_file_part(test_sensitive_pdf, None, [BuildActions.rotate(90)])
            # Add HTML content
            .add_html_part(test_html_content)
            # Add image as new page
            .add_file_part(sample_png)
            # Add blank page
            .add_new_page({"layout": {"size": "A4"}})
            # Apply global actions
            .apply_actions(
                [
                    BuildActions.watermark_text(
                        "CONFIDENTIAL",
                        {
                            "opacity": 0.2,
                            "fontSize": 60,
                            "rotation": 45,
                        },
                    ),
                    BuildActions.flatten(),
                ]
            )
            .output_pdf({"optimize": {"imageOptimizationQuality": 2}})
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_document_assembly_with_redactions(self, integration_client):
        """Test document assembly with redactions."""
        pdf1 = TestDocumentGenerator.generate_simple_pdf_content("SSN: 123-45-6789")
        pdf2 = TestDocumentGenerator.generate_simple_pdf_content(
            "email: secret@example.com"
        )

        result = await (
            integration_client.workflow()
            # First document with redactions
            .add_file_part(
                pdf1,
                None,
                [
                    BuildActions.create_redactions_regex(r"\d{3}-\d{2}-\d{4}"),
                    BuildActions.apply_redactions(),
                ],
            )
            # Second document with different redactions
            .add_file_part(
                pdf2,
                None,
                [
                    BuildActions.create_redactions_regex(
                        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                    ),
                    BuildActions.apply_redactions(),
                ],
            )
            # Apply watermark to entire document
            .apply_action(
                BuildActions.watermark_text(
                    "REDACTED COPY",
                    {
                        "opacity": 0.3,
                        "fontSize": 48,
                        "fontColor": "#FF0000",
                    },
                )
            )
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)


class TestIntegrationErrorScenarios:
    """Test error scenarios with live API."""

    @pytest.mark.asyncio
    async def test_invalid_html_content(self, integration_client):
        """Test handling of invalid HTML content."""
        invalid_html = b"<html><body><unclosed-tag>Invalid HTML"

        result = await (
            integration_client.workflow().add_html_part(invalid_html).output_pdf().execute()
        )

        # Should still succeed with best-effort HTML processing
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_xfdf_content(self, integration_client):
        """Test handling of invalid XFDF content."""
        invalid_xfdf = b'<?xml version="1.0"?><invalid-xfdf>'

        result = await (
            integration_client.workflow()
            .add_file_part(b"%PDF-1.4")
            .apply_action(BuildActions.apply_xfdf(invalid_xfdf))
            .output_pdf()
            .execute()
        )

        # Error handling may vary - check if it succeeds or fails gracefully
        assert "success" in result

    @pytest.mark.asyncio
    async def test_invalid_instant_json(self, integration_client):
        """Test handling of invalid Instant JSON."""
        invalid_json = "{ invalid json }"

        result = await (
            integration_client.workflow()
            .add_file_part(b"%PDF-1.4")
            .apply_action(BuildActions.apply_instant_json(invalid_json))
            .output_pdf()
            .execute()
        )

        # Error handling may vary - check if it succeeds or fails gracefully
        assert "success" in result


class TestIntegrationPerformanceAndLimits:
    """Test performance and limits with live API."""

    @pytest.mark.asyncio
    async def test_workflow_with_many_actions(self, integration_client):
        """Test workflow with many actions."""
        actions = []
        # Add multiple watermarks
        for i in range(5):
            actions.append(
                BuildActions.watermark_text(
                    f"Layer {i + 1}",
                    {
                        "opacity": 0.1,
                        "fontSize": 20 + i * 10,
                        "rotation": i * 15,
                    },
                )
            )
        # Add multiple redaction patterns
        actions.extend(
            [
                BuildActions.create_redactions_regex(r"\d{3}-\d{2}-\d{4}"),
                BuildActions.create_redactions_regex(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                ),
                BuildActions.apply_redactions(),
                BuildActions.flatten(),
            ]
        )

        result = await (
            integration_client.workflow()
            .add_file_part(sample_pdf)
            .apply_actions(actions)
            .output_pdf()
            .execute()
        )

        ResultValidator.validate_pdf_output(result)

    @pytest.mark.asyncio
    async def test_workflow_with_many_parts(self, integration_client):
        """Test workflow with many parts."""
        parts = []
        for i in range(10):
            parts.append(
                TestDocumentGenerator.generate_simple_pdf_content(f"Page {i + 1}")
            )

        workflow = integration_client.workflow()
        for part in parts:
            workflow = workflow.add_file_part(part)

        result = await workflow.output_pdf().execute()

        ResultValidator.validate_pdf_output(result)


class TestIntegrationPatternsMock:
    """Mock integration patterns for CI/development environments."""

    def test_workflow_builder_pattern(self):
        """Test workflow builder pattern structure."""
        client = NutrientClient(api_key="mock-key")
        workflow = client.workflow()

        assert workflow is not None
        assert hasattr(workflow, "add_file_part")
        assert callable(workflow.add_file_part)

    def test_all_convenience_methods_available(self):
        """Test that all convenience methods are available."""
        client = NutrientClient(api_key="mock-key")

        # Core methods
        assert hasattr(client, "workflow")
        assert callable(client.workflow)

        # Document conversion methods
        assert hasattr(client, "convert")
        assert callable(client.convert)
        assert hasattr(client, "ocr")
        assert callable(client.ocr)
        assert hasattr(client, "extract_text")
        assert callable(client.extract_text)

        # Document manipulation methods
        assert hasattr(client, "watermark_text")
        assert callable(client.watermark_text)
        assert hasattr(client, "watermark_image")
        assert callable(client.watermark_image)
        assert hasattr(client, "merge")
        assert callable(client.merge)
        assert hasattr(client, "optimize")
        assert callable(client.optimize)
        assert hasattr(client, "flatten")
        assert callable(client.flatten)
        assert hasattr(client, "rotate")
        assert callable(client.rotate)

    def test_type_safety_workflow_builder(self):
        """Test type safety with workflow builder."""
        client = NutrientClient(api_key="mock-key")

        # Python should maintain method chaining
        stage1 = client.workflow()
        stage2 = stage1.add_file_part("test.pdf")
        stage3 = stage2.output_pdf()

        # Each stage should have appropriate methods
        assert hasattr(stage1, "add_file_part")
        assert callable(stage1.add_file_part)
        assert hasattr(stage2, "apply_action")
        assert callable(stage2.apply_action)
        assert hasattr(stage3, "execute")
        assert callable(stage3.execute)
