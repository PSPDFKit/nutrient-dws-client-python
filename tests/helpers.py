"""Test utilities and helpers for Nutrient DWS Python Client tests."""

import json
import os
from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestDocumentGenerator:
    """Generate test documents and content for testing purposes."""

    @staticmethod
    def generate_simple_pdf_content() -> bytes:
        """Generate a simple PDF-like content for testing.

        Note: This is not a real PDF, just bytes that can be used for testing file handling.
        """
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"

    @staticmethod
    def generate_pdf_with_sensitive_data() -> bytes:
        """Generate PDF-like content with sensitive data patterns for redaction testing."""
        content = b"%PDF-1.4\n"
        content += b"Email: test@example.com\n"
        content += b"SSN: 123-45-6789\n"
        content += b"Credit Card: 4111-1111-1111-1111\n"
        content += b"%%EOF"
        return content

    @staticmethod
    def generate_html_content(options: Optional[dict[str, Any]] = None) -> bytes:
        """Generate HTML content for testing."""
        options = options or {}
        title = options.get("title", "Test Document")
        body = options.get("body", "<p>This is test content.</p>")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
</head>
<body>
    {body}
</body>
</html>"""
        return html.encode("utf-8")

    @staticmethod
    def generate_xfdf_content(annotations: Optional[list] = None) -> bytes:
        """Generate XFDF annotation content."""
        annotations = annotations or []
        xfdf = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xfdf += '<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">\n'
        xfdf += "<annots>\n"

        for i, annotation in enumerate(annotations):
            xfdf += f'<text rect="100,100,200,150" contents="{annotation}" name="annotation_{i}"/>\n'

        xfdf += "</annots>\n"
        xfdf += "</xfdf>"
        return xfdf.encode("utf-8")

    @staticmethod
    def generate_instant_json_content(annotations: Optional[list] = None) -> bytes:
        """Generate Instant JSON annotation content."""
        annotations = annotations or []
        instant_data = {
            "format": "https://pspdfkit.com/instant-json/v1",
            "annotations": [],
        }

        for i, annotation in enumerate(annotations):
            instant_data["annotations"].append(
                {
                    "type": "pspdfkit/text",
                    "id": f"annotation_{i}",
                    "pageIndex": 0,
                    "boundingBox": {"minX": 100, "minY": 100, "maxX": 200, "maxY": 150},
                    "text": {"format": "plain", "value": annotation},
                }
            )

        return json.dumps(instant_data).encode("utf-8")


class ResultValidator:
    """Validate test results and outputs."""

    @staticmethod
    def validate_buffer_output(
        result: Any, expected_mime_type: str = "application/pdf"
    ) -> None:
        """Validate BufferOutput structure and content."""
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert "buffer" in result, "Result missing 'buffer' key"
        assert "mimeType" in result, "Result missing 'mimeType' key"
        assert "filename" in result, "Result missing 'filename' key"

        assert isinstance(result["buffer"], bytes), (
            f"Expected bytes, got {type(result['buffer'])}"
        )
        assert result["mimeType"] == expected_mime_type, (
            f"Expected {expected_mime_type}, got {result['mimeType']}"
        )
        assert isinstance(result["filename"], str), (
            f"Expected str, got {type(result['filename'])}"
        )
        assert len(result["buffer"]) > 0, "Buffer is empty"

    @staticmethod
    def validate_content_output(
        result: Any, expected_mime_type: str = "text/html"
    ) -> None:
        """Validate ContentOutput structure and content."""
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert "content" in result, "Result missing 'content' key"
        assert "mimeType" in result, "Result missing 'mimeType' key"
        assert "filename" in result, "Result missing 'filename' key"

        assert isinstance(result["content"], str), (
            f"Expected str, got {type(result['content'])}"
        )
        assert result["mimeType"] == expected_mime_type, (
            f"Expected {expected_mime_type}, got {result['mimeType']}"
        )
        assert isinstance(result["filename"], str), (
            f"Expected str, got {type(result['filename'])}"
        )
        assert len(result["content"]) > 0, "Content is empty"

    @staticmethod
    def validate_json_content_output(result: Any) -> None:
        """Validate JsonContentOutput structure and content."""
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert "data" in result, "Result missing 'data' key"
        assert "mimeType" in result, "Result missing 'mimeType' key"
        assert "filename" in result, "Result missing 'filename' key"

        assert result["mimeType"] == "application/json", (
            f"Expected application/json, got {result['mimeType']}"
        )
        assert isinstance(result["filename"], str), (
            f"Expected str, got {type(result['filename'])}"
        )
        assert result["data"] is not None, "Data is None"

    @staticmethod
    def validate_office_output(result: Any, format_type: str) -> None:
        """Validate Office document outputs."""
        expected_mime_types = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
        expected_mime_type = expected_mime_types.get(format_type)
        assert expected_mime_type, f"Unknown format type: {format_type}"

        ResultValidator.validate_buffer_output(result, expected_mime_type)

    @staticmethod
    def validate_image_output(result: Any, format_type: Optional[str] = None) -> None:
        """Validate image outputs."""
        expected_mime_types = {
            "png": "image/png",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "webp": "image/webp",
        }

        if format_type:
            expected_mime_type = expected_mime_types.get(format_type, "image/png")
        else:
            expected_mime_type = "image/png"  # Default

        ResultValidator.validate_buffer_output(result, expected_mime_type)

    @staticmethod
    def validate_error_response(
        error: Exception, expected_error_type: str, expected_code: Optional[str] = None
    ) -> None:
        """Validate error responses."""
        from nutrient_dws.errors import (
            APIError,
            AuthenticationError,
            NetworkError,
            NutrientError,
            ValidationError,
        )

        error_types = {
            "NutrientError": NutrientError,
            "ValidationError": ValidationError,
            "APIError": APIError,
            "AuthenticationError": AuthenticationError,
            "NetworkError": NetworkError,
        }

        expected_class = error_types.get(expected_error_type)
        assert expected_class, f"Unknown error type: {expected_error_type}"
        assert isinstance(error, expected_class), (
            f"Expected {expected_class}, got {type(error)}"
        )

        if expected_code:
            assert hasattr(error, "code"), "Error missing 'code' attribute"
            assert error.code == expected_code, (
                f"Expected code {expected_code}, got {error.code}"
            )


class MockFactory:
    """Factory for creating various mock objects used in tests."""

    @staticmethod
    def create_mock_workflow_result(
        success: bool = True,
        output: Optional[dict[str, Any]] = None,
        errors: Optional[list] = None,
    ):
        """Create a mock workflow result."""
        if output is None:
            output = {
                "buffer": b"mock_pdf_content",
                "mimeType": "application/pdf",
                "filename": "output.pdf",
            }

        return {
            "success": success,
            "output": output if success else None,
            "errors": errors if not success else None,
        }

    @staticmethod
    def create_mock_workflow_instance():
        """Create a complete mock workflow instance."""
        mock_workflow = MagicMock()

        # Chain all the methods to return self for fluent interface
        mock_workflow.add_file_part.return_value = mock_workflow
        mock_workflow.add_html_part.return_value = mock_workflow
        mock_workflow.add_new_page.return_value = mock_workflow
        mock_workflow.add_document_part.return_value = mock_workflow
        mock_workflow.apply_action.return_value = mock_workflow
        mock_workflow.apply_actions.return_value = mock_workflow
        mock_workflow.output_pdf.return_value = mock_workflow
        mock_workflow.output_pdfa.return_value = mock_workflow
        mock_workflow.output_pdfua.return_value = mock_workflow
        mock_workflow.output_image.return_value = mock_workflow
        mock_workflow.output_office.return_value = mock_workflow
        mock_workflow.output_html.return_value = mock_workflow
        mock_workflow.output_markdown.return_value = mock_workflow
        mock_workflow.output_json.return_value = mock_workflow

        # Set up the execute method to return a successful result
        mock_workflow.execute = AsyncMock(
            return_value=MockFactory.create_mock_workflow_result()
        )
        mock_workflow.dry_run = AsyncMock(
            return_value={"valid": True, "estimatedTime": 1000}
        )

        return mock_workflow

    @staticmethod
    def create_mock_http_response(data: Any, status_code: int = 200):
        """Create a mock HTTP response."""
        return {"data": data, "status": status_code}


class TestDataManager:
    """Manage test data files and sample documents."""

    @staticmethod
    def get_test_data_dir() -> Path:
        """Get the path to the test data directory."""
        return Path(__file__).parent / "data"

    @staticmethod
    def get_sample_pdf() -> bytes:
        """Get sample PDF content."""
        data_dir = TestDataManager.get_test_data_dir()
        pdf_path = data_dir / "sample.pdf"

        if pdf_path.exists():
            return pdf_path.read_bytes()
        else:
            # Return generated content if file doesn't exist
            return TestDocumentGenerator.generate_simple_pdf_content()

    @staticmethod
    def get_sample_docx() -> bytes:
        """Get sample DOCX content."""
        data_dir = TestDataManager.get_test_data_dir()
        docx_path = data_dir / "sample.docx"

        if docx_path.exists():
            return docx_path.read_bytes()
        else:
            # Return minimal DOCX-like content
            return b"PK\x03\x04mock_docx_content"

    @staticmethod
    def get_sample_png() -> bytes:
        """Get sample PNG content."""
        data_dir = TestDataManager.get_test_data_dir()
        png_path = data_dir / "sample.png"

        if png_path.exists():
            return png_path.read_bytes()
        else:
            # Return minimal PNG-like content (PNG signature + minimal data)
            return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"


class ConfigHelper:
    """Helper for test configuration and environment setup."""

    @staticmethod
    def should_run_integration_tests() -> bool:
        """Check if integration tests should run based on environment."""
        api_key = os.getenv("NUTRIENT_API_KEY")
        return bool(api_key and api_key != "fake_key" and len(api_key) > 10)

    @staticmethod
    def get_test_api_key() -> Optional[str]:
        """Get the API key for testing."""
        return os.getenv("NUTRIENT_API_KEY")

    @staticmethod
    def skip_integration_if_no_api_key():
        """Pytest skip decorator for integration tests without API key."""
        return pytest.mark.skipif(
            not ConfigHelper.should_run_integration_tests(),
            reason="NUTRIENT_API_KEY not available for integration tests",
        )


# Convenient aliases and constants
skip_integration_if_no_api_key = ConfigHelper.skip_integration_if_no_api_key()

# Sample data constants
SAMPLE_PDF = TestDataManager.get_sample_pdf()
SAMPLE_DOCX = TestDataManager.get_sample_docx()
SAMPLE_PNG = TestDataManager.get_sample_png()

# Common test parameters for parametrized tests
CONVERSION_TEST_CASES = [
    pytest.param("pdf", "pdfa", "application/pdf", id="pdf_to_pdfa"),
    pytest.param("pdf", "pdfua", "application/pdf", id="pdf_to_pdfua"),
    pytest.param(
        "pdf",
        "docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        id="pdf_to_docx",
    ),
    pytest.param("pdf", "png", "image/png", id="pdf_to_png"),
    pytest.param("pdf", "html", "text/html", id="pdf_to_html"),
    pytest.param("pdf", "markdown", "text/markdown", id="pdf_to_markdown"),
]

FILE_INPUT_TEST_CASES = [
    pytest.param("https://example.com/test.pdf", True, id="url_string"),
    pytest.param("test.pdf", False, id="file_path_string"),
    pytest.param(b"test content", False, id="bytes"),
    pytest.param(SAMPLE_PDF, False, id="sample_pdf_bytes"),
]

# TypeScript compatibility aliases
samplePDF = SAMPLE_PDF
samplePNG = SAMPLE_PNG
sampleDOCX = SAMPLE_DOCX
