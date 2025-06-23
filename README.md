# Nutrient DWS Python Client

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](https://github.com/jdrhyne/nutrient-dws-client-python/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI version](https://img.shields.io/pypi/v/nutrient-dws.svg)](https://pypi.org/project/nutrient-dws/)

A Python client library for the [Nutrient Document Web Services (DWS) API](https://www.nutrient.io/). This library provides a Pythonic interface to interact with Nutrient's document processing services, supporting both Direct API calls and Builder API workflows.

## Features

- 🚀 **Two API styles**: Direct API for single operations, Builder API for complex workflows
- 📄 **Comprehensive document tools**: Convert, merge, rotate, OCR, watermark, and more
- 🔄 **Automatic retries**: Built-in retry logic for transient failures
- 📁 **Flexible file handling**: Support for file paths, bytes, and file-like objects
- 🔒 **Type-safe**: Full type hints for better IDE support
- ⚡ **Streaming support**: Memory-efficient processing of large files
- 🧪 **Well-tested**: Comprehensive test suite with high coverage

## Installation

```bash
pip install nutrient-dws
```

## Quick Start

```python
from nutrient_dws import NutrientClient

# Initialize the client
client = NutrientClient(api_key="your-api-key")

# Direct API - Flatten PDF annotations
client.flatten_annotations(
    input_file="document.pdf",
    output_path="flattened.pdf"
)

# Builder API - Chain multiple operations
client.build(input_file="document.pdf") \
    .add_step("rotate-pages", {"degrees": 90}) \
    .add_step("ocr-pdf", {"language": "en"}) \
    .add_step("watermark-pdf", {"text": "CONFIDENTIAL"}) \
    .execute(output_path="processed.pdf")
```

## Authentication

The client supports API key authentication through multiple methods:

```python
# 1. Pass directly to client
client = NutrientClient(api_key="your-api-key")

# 2. Set environment variable
# export NUTRIENT_API_KEY=your-api-key
client = NutrientClient()  # Will use env variable

# 3. Use context manager for automatic cleanup
with NutrientClient(api_key="your-api-key") as client:
    client.convert_to_pdf("document.docx")
```

## Direct API Examples

### Flatten Annotations

```python
# Flatten all annotations and form fields
client.flatten_annotations(
    input_file="form.pdf",
    output_path="flattened.pdf"
)
```

### Merge PDFs

```python
# Merge multiple PDFs
client.merge_pdfs(
    input_files=["doc1.pdf", "doc2.pdf", "doc3.pdf"],
    output_path="merged.pdf"
)
```

### OCR PDF

```python
# Add OCR layer to scanned PDF
client.ocr_pdf(
    input_file="scanned.pdf",
    output_path="searchable.pdf",
    language="en"
)
```

### Rotate Pages

```python
# Rotate all pages
client.rotate_pages(
    input_file="document.pdf",
    output_path="rotated.pdf",
    degrees=180
)

# Rotate specific pages
client.rotate_pages(
    input_file="document.pdf",
    output_path="rotated.pdf",
    degrees=90,
    page_indexes=[0, 2, 4]  # Pages 1, 3, and 5
)
```

### Watermark PDF

```python
# Add text watermark (width/height required)
client.watermark_pdf(
    input_file="document.pdf",
    output_path="watermarked.pdf",
    text="DRAFT",
    width=200,
    height=100,
    opacity=0.5,
    position="center"
)

# Add image watermark from URL
client.watermark_pdf(
    input_file="document.pdf",
    output_path="watermarked.pdf",
    image_url="https://example.com/logo.png",
    width=150,
    height=75,
    opacity=0.8,
    position="bottom-right"
)

# Add image watermark from local file (NEW!)
client.watermark_pdf(
    input_file="document.pdf",
    output_path="watermarked.pdf",
    image_file="logo.png",  # Can be path, bytes, or file-like object
    width=150,
    height=75,
    opacity=0.8,
    position="bottom-right"
)
```

## Builder API Examples

The Builder API allows you to chain multiple operations in a single workflow:

```python
# Complex document processing pipeline
result = client.build(input_file="raw-scan.pdf") \
    .add_step("ocr-pdf", {"language": "en"}) \
    .add_step("rotate-pages", {"degrees": -90, "page_indexes": [0]}) \
    .add_step("watermark-pdf", {
        "text": "PROCESSED",
        "opacity": 0.3,
        "position": "top-right"
    }) \
    .add_step("flatten-annotations") \
    .set_output_options(
        metadata={"title": "Processed Document", "author": "DWS Client"},
        optimize=True
    ) \
    .execute(output_path="final.pdf")

# Using image file in builder API
result = client.build(input_file="document.pdf") \
    .add_step("watermark-pdf", {
        "image_file": "company-logo.png",  # Local file
        "width": 100,
        "height": 50,
        "opacity": 0.5,
        "position": "bottom-left"
    }) \
    .execute()
```

## File Input Options

The library supports multiple ways to provide input files:

```python
# File path (string or Path object)
client.convert_to_pdf("document.docx")
client.convert_to_pdf(Path("document.docx"))

# Bytes
with open("document.docx", "rb") as f:
    file_bytes = f.read()
client.convert_to_pdf(file_bytes)

# File-like object
with open("document.docx", "rb") as f:
    client.convert_to_pdf(f)

# URL (for supported operations)
client.import_from_url("https://example.com/document.pdf")
```

## Error Handling

The library provides specific exceptions for different error scenarios:

```python
from nutrient_dws import (
    NutrientError,
    AuthenticationError,
    APIError,
    ValidationError,
    TimeoutError,
    FileProcessingError
)

try:
    client.convert_to_pdf("document.docx")
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Invalid parameters: {e.errors}")
except APIError as e:
    print(f"API error: {e.status_code} - {e.message}")
except TimeoutError:
    print("Request timed out")
except FileProcessingError as e:
    print(f"File processing failed: {e}")
```

## Advanced Configuration

### Custom Timeout

```python
# Set timeout to 10 minutes for large files
client = NutrientClient(api_key="your-api-key", timeout=600)
```

### Streaming Large Files

Files larger than 10MB are automatically streamed to avoid memory issues:

```python
# This will stream the file instead of loading it into memory
client.flatten_annotations("large-document.pdf")
```

## Available Operations

### PDF Manipulation
- `merge_pdfs` - Merge multiple PDFs into one
- `rotate_pages` - Rotate PDF pages (all or specific pages)
- `flatten_annotations` - Flatten form fields and annotations

### PDF Enhancement
- `ocr_pdf` - Add searchable text layer (English and German)
- `watermark_pdf` - Add text or image watermarks

### PDF Security
- `apply_redactions` - Apply existing redaction annotations

### Builder API
The Builder API allows chaining multiple operations:
```python
client.build(input_file="document.pdf") \
    .add_step("rotate-pages", {"degrees": 90}) \
    .add_step("ocr-pdf", {"language": "english"}) \
    .add_step("watermark-pdf", {"text": "DRAFT", "width": 200, "height": 100}) \
    .execute(output_path="processed.pdf")
```

Note: See [SUPPORTED_OPERATIONS.md](SUPPORTED_OPERATIONS.md) for detailed documentation of all supported operations and their parameters.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/jdrhyne/nutrient-dws-client-python.git
cd nutrient-dws-client-python

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy src tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nutrient --cov-report=html

# Run specific test file
pytest tests/unit/test_client.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@nutrient.io
- 📚 Documentation: https://www.nutrient.io/docs/
- 🐛 Issues: https://github.com/jdrhyne/nutrient-dws-client-python/issues