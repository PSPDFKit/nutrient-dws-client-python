"""Test configuration and fixtures for Nutrient DWS Python Client tests.

Following TypeScript test patterns and pytest best practices.
"""

from unittest.mock import AsyncMock, patch

import pytest

from nutrient_dws import NutrientClient

from .helpers import (
    ConfigHelper,
    MockFactory,
    TestDataManager,
    sampleDOCX,
    samplePDF,
    samplePNG,
)

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for tests."""
    import asyncio

    return asyncio.get_event_loop_policy()


@pytest.fixture
def valid_client_options():
    """Valid client options for testing."""
    return {"apiKey": "test-api-key"}


@pytest.fixture
def client_with_function_api_key():
    """Client options with API key function."""

    def get_api_key():
        return "function-api-key"

    return {"apiKey": get_api_key}


@pytest.fixture
def client_with_base_url():
    """Client options with custom base URL."""
    return {"apiKey": "test-api-key", "baseUrl": "https://custom-api.nutrient.io"}


@pytest.fixture
def client_with_timeout():
    """Client options with custom timeout."""
    return {"apiKey": "test-api-key", "timeout": 60000}


@pytest.fixture
def invalid_client_options_cases():
    """Invalid client options for testing error scenarios."""
    return [
        (None, "Client options are required"),
        ({}, "API key is required"),
        ({"apiKey": None}, "API key is required"),
        ({"apiKey": ""}, "API key is required"),
        ({"apiKey": 123}, "API key must be a string or function"),
        ({"apiKey": "valid", "baseUrl": 123}, "Base URL must be a string"),
    ]


@pytest.fixture
def nutrient_client(valid_client_options):
    """Create a NutrientClient instance for testing."""
    return NutrientClient(valid_client_options)


# HTTP mocking fixtures
@pytest.fixture
def mock_http_send():
    """Mock the HTTP send function."""
    with patch("nutrient_dws.http.send") as mock:
        mock.return_value = AsyncMock(
            return_value={"success": True, "data": {"message": "success"}}
        )
        yield mock


@pytest.fixture
def mock_successful_http_response():
    """Mock successful HTTP response data."""
    return {
        "success": True,
        "data": {
            "organization": "Test Organization",
            "subscriptionType": "premium",
            "credits": 1000,
        },
    }


@pytest.fixture
def mock_error_http_response():
    """Mock error HTTP response data."""
    return {
        "success": False,
        "error": {
            "code": "API_ERROR",
            "message": "API request failed",
            "details": {"statusCode": 400},
        },
    }


# File processing mocking
@pytest.fixture
def mock_file_processing():
    """Mock file processing functions."""
    with (
        patch("nutrient_dws.inputs.process_file_input") as mock_process,
        patch("nutrient_dws.inputs.process_remote_file_input") as mock_remote,
        patch("nutrient_dws.inputs.is_remote_file_input") as mock_is_remote,
        patch("nutrient_dws.inputs.is_valid_pdf") as mock_valid_pdf,
        patch("nutrient_dws.inputs.get_pdf_page_count") as mock_page_count,
    ):
        # Set up default mock behaviors
        mock_process.return_value = (samplePDF, "sample.pdf")
        mock_remote.return_value = (samplePDF, "remote.pdf")
        mock_is_remote.return_value = False
        mock_valid_pdf.return_value = True
        mock_page_count.return_value = 6  # Same as TypeScript tests

        yield {
            "process_file_input": mock_process,
            "process_remote_file_input": mock_remote,
            "is_remote_file_input": mock_is_remote,
            "is_valid_pdf": mock_valid_pdf,
            "get_pdf_page_count": mock_page_count,
        }


# Workflow builder mocking
@pytest.fixture
def mock_workflow_builder():
    """Mock the StagedWorkflowBuilder."""
    with patch("nutrient_dws.client.StagedWorkflowBuilder") as mock_class:
        mock_instance = MockFactory.create_mock_workflow_instance()
        mock_class.return_value = mock_instance
        yield mock_class, mock_instance


@pytest.fixture
def mock_workflow_instance():
    """Create a standalone mock workflow instance."""
    return MockFactory.create_mock_workflow_instance()


# Sample file fixtures
@pytest.fixture
def sample_files():
    """Provide sample files for testing."""
    return {"pdf": samplePDF, "png": samplePNG, "docx": sampleDOCX}


@pytest.fixture
def sample_pdf_content():
    """Generate sample PDF content."""
    return TestDataManager.get_sample_pdf()


@pytest.fixture
def sample_html_content():
    """Generate sample HTML content."""
    return TestDataManager.generate_html_content(
        {
            "title": "Test Document",
            "body": "<h1>Test HTML Content</h1><p>This is a test document.</p>",
        }
    )


# Integration test fixtures
@pytest.fixture(scope="session")
def test_api_key():
    """Get test API key if available."""
    return ConfigHelper.get_test_api_key()


@pytest.fixture(scope="session")
def integration_client(test_api_key):
    """Create client for integration tests."""
    if test_api_key and ConfigHelper.should_run_integration_tests():
        return NutrientClient({"apiKey": test_api_key})
    return None


@pytest.fixture(scope="session")
def should_run_integration_tests():
    """Check if integration tests should run."""
    return ConfigHelper.should_run_integration_tests()


# Common test data fixtures
@pytest.fixture
def common_test_data():
    """Common test data used across multiple tests."""
    return {
        "api_key": "test-api-key-123",
        "base_url": "https://api.nutrient.io",
        "timeout": 30000,
        "languages": ["english", "french", "german"],
        "page_ranges": [
            {"start": 0, "end": 2},
            {"start": 1, "end": 3},
            {"start": -3, "end": -1},
        ],
        "supported_formats": [
            "pdf",
            "pdfa",
            "pdfua",
            "docx",
            "xlsx",
            "pptx",
            "png",
            "jpeg",
            "html",
            "markdown",
        ],
    }


# Parametrized test data fixtures
@pytest.fixture(
    params=[("english",), (["english", "french"],), (["english", "french", "german"],)]
)
def ocr_language_cases(request):
    """Parametrized OCR language test cases."""
    return request.param[0]


@pytest.fixture(
    params=[
        {"opacity": 0.5},
        {"opacity": 0.5, "fontSize": 24},
        {"opacity": 0.3, "rotation": 45, "fontSize": 36},
    ]
)
def watermark_option_cases(request):
    """Parametrized watermark options test cases."""
    return request.param


@pytest.fixture(
    params=[
        "pdf",
        "pdfa",
        "pdfua",
        "docx",
        "xlsx",
        "pptx",
        "png",
        "jpeg",
        "html",
        "markdown",
    ]
)
def output_format_cases(request):
    """Parametrized output format test cases."""
    return request.param


@pytest.fixture(
    params=[
        ({"start": 0, "end": 2}, 3),  # (page_range, expected_page_count)
        ({"start": 1, "end": 3}, 3),
        ({"start": -3, "end": -1}, 3),
        (None, None),  # No page range specified
    ]
)
def page_range_test_cases(request):
    """Parametrized page range test cases."""
    return request.param


# Error test fixtures
@pytest.fixture
def api_error_response_cases():
    """Mock API error responses for testing."""
    return [
        (400, {"error": "Bad Request", "message": "Invalid parameters"}),
        (401, {"error": "Unauthorized", "message": "Invalid API key"}),
        (403, {"error": "Forbidden", "message": "Access denied"}),
        (404, {"error": "Not Found", "message": "Resource not found"}),
        (422, {"error": "Validation Error", "message": "Invalid input data"}),
        (500, {"error": "Internal Server Error", "message": "Server error"}),
    ]


# Performance and configuration fixtures
@pytest.fixture(scope="session")
def performance_test_config():
    """Configuration for performance tests."""
    return {
        "timeout_seconds": 30,
        "max_file_size_mb": 10,
        "concurrent_requests": 3,
        "retry_attempts": 2,
    }


@pytest.fixture
def extended_timeout():
    """Extended timeout for integration tests."""
    return 120  # 2 minutes for API calls


@pytest.fixture(autouse=True)
def clear_mocks():
    """Clear all mocks before each test."""
    # This ensures clean state between tests
    yield
    # Cleanup happens automatically with patch context managers


# Utility fixtures for TypeScript-like test structure
@pytest.fixture
def describe():
    """Provide TypeScript-like describe functionality through pytest classes."""

    class DescribeHelper:
        @staticmethod
        def skip_if_no_api_key():
            return pytest.mark.skipif(
                not ConfigHelper.should_run_integration_tests(),
                reason="NUTRIENT_API_KEY not available for integration tests",
            )

    return DescribeHelper


# Mark configuration for conditional test execution
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring API key"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration test skipping."""
    if not ConfigHelper.should_run_integration_tests():
        skip_integration = pytest.mark.skip(reason="NUTRIENT_API_KEY not available")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
