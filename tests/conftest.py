import os
from unittest.mock import AsyncMock

import pytest
from dotenv import load_dotenv
from nutrient_dws import NutrientClient
from tests.helpers import TestDocumentGenerator

load_dotenv()  # Load environment variables

@pytest.fixture
def mock_workflow_instance():
    """Create a mock workflow instance for testing."""
    mock_output_stage = AsyncMock()
    mock_output_stage.execute.return_value = {
        "success": True,
        "output": {
            "buffer": b"test-buffer",
            "mimeType": "application/pdf",
            "filename": "output.pdf",
        },
    }
    mock_output_stage.dry_run.return_value = {"success": True}

    mock_workflow = AsyncMock()
    mock_workflow.add_file_part.return_value = mock_workflow
    mock_workflow.add_html_part.return_value = mock_workflow
    mock_workflow.add_new_page.return_value = mock_workflow
    mock_workflow.add_document_part.return_value = mock_workflow
    mock_workflow.apply_actions.return_value = mock_workflow
    mock_workflow.apply_action.return_value = mock_workflow
    mock_workflow.output_pdf.return_value = mock_output_stage
    mock_workflow.output_pdfa.return_value = mock_output_stage
    mock_workflow.output_pdfua.return_value = mock_output_stage
    mock_workflow.output_image.return_value = mock_output_stage
    mock_workflow.output_office.return_value = mock_output_stage
    mock_workflow.output_html.return_value = mock_output_stage
    mock_workflow.output_markdown.return_value = mock_output_stage
    mock_workflow.output_json.return_value = mock_output_stage

    return mock_workflow


@pytest.fixture
def valid_client_options():
    """Valid client options for testing."""
    return {"apiKey": "test-api-key", "baseUrl": "https://api.test.com/v1"}

@pytest.fixture(scope="class")
def client():
    """Create client instance for testing."""
    options = {
        "apiKey": os.getenv("NUTRIENT_API_KEY", ""),
        "baseUrl": os.getenv("NUTRIENT_BASE_URL", "https://api.nutrient.io"),
    }
    return NutrientClient(options)


@pytest.fixture
def test_table_pdf():
    """Generate PDF with table for annotation tests."""
    return TestDocumentGenerator.generate_pdf_with_table()

@pytest.fixture
def test_xfdf_content():
    """Generate XFDF content for testing."""
    return TestDocumentGenerator.generate_xfdf_content()

@pytest.fixture
def test_instant_json_content():
    """Generate Instant JSON content for testing."""
    return TestDocumentGenerator.generate_instant_json_content()

@pytest.fixture
def test_sensitive_pdf():
    """Generate PDF with sensitive data for redaction testing."""
    return TestDocumentGenerator.generate_pdf_with_sensitive_data()

@pytest.fixture
def test_html_content():
    """Generate HTML content for testing."""
    return TestDocumentGenerator.generate_html_content()
