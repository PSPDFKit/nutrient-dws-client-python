# Nutrient DWS Python Client

[![PyPI version](https://badge.fury.io/py/nutrient-dws.svg)](https://badge.fury.io/py/nutrient-dws)
[![CI](https://github.com/PSPDFKit/nutrient-dws-client-python/actions/workflows/ci.yml/badge.svg)](https://github.com/PSPDFKit/nutrient-dws-client-python/actions/workflows/ci.yml)
[![Integration Tests](https://github.com/PSPDFKit/nutrient-dws-client-python/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/PSPDFKit/nutrient-dws-client-python/actions/workflows/integration-tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client library for [Nutrient Document Web Services (DWS) API](https://nutrient.io/). This library provides a fully async, type-safe, and ergonomic interface for document processing operations including conversion, merging, compression, watermarking, OCR, and text extraction.

> **Note**: This package is published as `nutrient-dws` on PyPI. The package provides full type support and is designed for async Python environments (Python 3.10+).

## Features

- 📄 **Powerful document processing**: Convert, OCR, edit, compress, watermark, redact, and digitally sign documents
- 🤖 **LLM friendly**: Built-in support for popular Coding Agents (Claude Code, GitHub Copilot, JetBrains Junie, Cursor, Windsurf) with auto-generated rules
- 🔄 **100% mapping with DWS Processor API**: Complete coverage of all Nutrient DWS Processor API capabilities
- 🛠️ **Convenient functions with sane defaults**: Simple interfaces for common operations with smart default settings
- ⛓️ **Chainable operations**: Build complex document workflows with intuitive method chaining
- 🚀 **Fully async**: Built from the ground up with async/await support for optimal performance
- 🔐 **Flexible authentication and security**: Support for API keys and async token providers with secure handling
- ✅ **Highly tested**: Comprehensive test suite ensuring reliability and stability
- 🔒 **Type-safe**: Full type annotations with comprehensive type definitions
- 🐍 **Pythonic**: Follows Python conventions and best practices

## Installation

```bash
pip install nutrient-dws
```


## Integration with Coding Agents

This package has built-in support with popular coding agents like Claude Code, GitHub Copilot, Cursor, and Windsurf by exposing scripts that will inject rules instructing the coding agents on how to use the package. This ensures that the coding agent doesn't hallucinate documentation, as well as making full use of all the features offered in Nutrient DWS Python Client.

```bash
# Adding code rule to Claude Code
dws-add-claude-code-rule

# Adding code rule to GitHub Copilot
dws-add-github-copilot-rule

# Adding code rule to Junie (Jetbrains)
dws-add-junie-rule

# Adding code rule to Cursor
dws-add-cursor-rule

# Adding code rule to Windsurf
dws-add-windsurf-rule
```

The documentation for Nutrient DWS Python Client is also available on [Context7](https://context7.com/pspdfkit/nutrient-dws-client-python)

## Quick Start

```python
from nutrient_dws import NutrientClient

client = NutrientClient(api_key='your_api_key')
```

## Direct Methods

The client provides numerous async methods for document processing:

```python
import asyncio
from nutrient_dws import NutrientClient

async def main():
    client = NutrientClient(api_key='your_api_key')

    # Convert a document
    pdf_result = await client.convert('document.docx', 'pdf')

    # Extract text
    text_result = await client.extract_text('document.pdf')

    # Add a watermark
    watermarked_doc = await client.watermark_text('document.pdf', 'CONFIDENTIAL')

    # Merge multiple documents
    merged_pdf = await client.merge(['doc1.pdf', 'doc2.pdf', 'doc3.pdf'])

asyncio.run(main())
```

For a complete list of available methods with examples, see the [Methods Documentation](docs/METHODS.md).

## Data Extraction (`/extraction/parse`)

`client.parse()` exposes Nutrient's Data Extraction API. It's designed for
**content-extraction workflows** where you need to feed document content into a
downstream pipeline rather than render or transform the document itself:

> **Heads up — separate API key.** DWS Extract is a different product from
> DWS Processor and has its own API key. Pass it as
> `NutrientClient(api_key=..., extract_api_key=...)`; the Extract key is
> used only for `parse()`, while every other method continues to use the
> Processor key. Using the Processor key against `/extraction/parse`
> returns `403`. If `extract_api_key` is omitted, `parse()` falls back to
> the main `api_key` — that path works once your tenant moves to global
> DWS API keys.

- **RAG (retrieval-augmented generation) pipelines** — pull a clean Markdown
  representation of a document for chunking, embedding, and indexing in a
  vector store.
- **Search indexing and content migration** — convert documents into Markdown
  for full-text search or for migration into a new content management system.
- **Form and invoice extraction** — pull structured fields (key/value pairs,
  tables, semantic regions) out of business documents with bounding boxes and
  confidence scores attached to every element.
- **Layout-aware document understanding** — get a typed, page-anchored element
  list (paragraphs with semantic roles, tables with cell spans, formulas in
  LaTeX, pictures, handwriting) suitable for building document-comprehension
  tooling, including agentic workflows.

### Choosing an output format

| Format            | Best for                                                                   | Shape                                                                |
|-------------------|----------------------------------------------------------------------------|----------------------------------------------------------------------|
| `markdown`        | RAG, search indexing, content migration — anywhere structured text beats spatial data | One whole-document Markdown string at `response['output']['markdown']` |
| `spatial` (default) | Form/invoice extraction, layout reconstruction, flows that need per-element confidence | Flat list of typed elements at `response['output']['elements']`        |

Spatial output requires an OCR-capable mode (`structure`, `understand`, or
`agentic`); `mode='text'` is markdown-only and the client rejects the
`text` + `spatial` combination before the request goes out.

### Quick start

```python
import asyncio
from nutrient_dws import NutrientClient

async def main():
    client = NutrientClient(
        api_key='your_processor_key',
        extract_api_key='your_extract_key',
    )

    # Spatial elements (default) — paragraphs, tables, formulas, pictures, etc.
    response = await client.parse('contract.pdf', mode='understand')
    for element in response['output']['elements']:
        if element['type'] == 'table':
            print(element['rowCount'], element['columnCount'])

    # Whole-document Markdown from a born-digital PDF
    response = await client.parse(
        'report.pdf', mode='text', output_format='markdown',
    )
    print(response['output']['markdown'])

asyncio.run(main())
```

### Modes — when to use which

| Mode         | Credits / page | When to use                                                                                  |
|--------------|----------------|----------------------------------------------------------------------------------------------|
| `text`       | 1              | Born-digital documents only. No OCR, no AI. Fastest and cheapest path to Markdown.           |
| `structure`  | 1.5            | OCR-based segmentation with bounding boxes. Handles scanned documents, images, and any input requiring OCR. |
| `understand` | 9              | Full pipeline with AI augmentation on top of OCR. Most accurate for documents with tables, multi-column layouts, formulas, and form fields. |
| `agentic`    | 18             | Builds on `understand` and adds a vision-language model. Best for image descriptions, complex visual layouts, and deeper semantic understanding. |

### Recipes

**RAG ingestion** — PDF → Markdown → chunks → embeddings → vector store:

```python
response = await client.parse('whitepaper.pdf', mode='text', output_format='markdown')
markdown = response['output']['markdown']
# Then: chunk on headings, embed, push to your vector store of choice.
```

For born-digital PDFs, `mode='text'` is the cheapest path (1 credit/page).
For scanned PDFs or images, switch to `mode='structure'` so OCR runs.

**Form/invoice extraction** — PDF → spatial elements → structured dict:

```python
response = await client.parse('invoice.pdf', mode='understand')
elements = response['output']['elements']

# Pull key/value pairs from form regions
fields = {}
for element in elements:
    if element['type'] == 'keyValueRegion':
        for pair in element['pairs']:
            fields[pair['key']['value']] = pair['value']['value']

# Walk tables — each cell carries row/col indices and span counts
for element in elements:
    if element['type'] == 'table':
        print(f"Table: {element['rowCount']}×{element['columnCount']}")
        for cell in element['cells']:
            print(f"  [{cell['row']}][{cell['column']}] {cell['text']}")
```

For complex layouts that mix dense images with text, step up to
`mode='agentic'` so the VLM can produce image descriptions and semantic
classifications (18 credits/page).

### Billing — extraction credits vs processor credits

The Data Extraction API is billed against **extraction credits**, which are a
separate billing bucket from the **processor API credits** consumed by
`/build`, `/sign`, OCR, and the other Processor API endpoints used by this
client (`convert`, `watermark_text`, `merge`, etc.). The response surfaces the
extraction-credit accounting under `response['usage']['data_extraction_credits']`:

```python
usage = response['usage']['data_extraction_credits']
print(f"Cost: {usage['cost']} extraction credits, "
      f"remaining: {usage['remainingCredits']}")
```

## Workflow System

The client also provides a fluent builder pattern with staged interfaces to create document processing workflows:

```python
from nutrient_dws.builder.constant import BuildActions

async def main():
    client = NutrientClient(api_key='your_api_key')

    result = await (client
        .workflow()
        .add_file_part('document.pdf')
        .add_file_part('appendix.pdf')
        .apply_action(BuildActions.watermark_text('CONFIDENTIAL', {
            'opacity': 0.5,
            'fontSize': 48
        }))
        .output_pdf({
            'optimize': {
                'mrcCompression': True,
                'imageOptimizationQuality': 2
            }
        })
        .execute())

asyncio.run(main())
```

The workflow system follows a staged approach:
1. Add document parts (files, HTML, pages)
2. Apply actions (optional)
3. Set output format
4. Execute or perform a dry run

For detailed information about the workflow system, including examples and best practices, see the [Workflow Documentation](docs/WORKFLOW.md).

## Error Handling

The library provides a comprehensive error hierarchy:

```python
from nutrient_dws import (
    NutrientClient,
    NutrientError,
    ValidationError,
    APIError,
    AuthenticationError,
    NetworkError
)

async def main():
    client = NutrientClient(api_key='your_api_key')

    try:
        result = await client.convert('file.docx', 'pdf')
    except ValidationError as error:
        # Invalid input parameters
        print(f'Invalid input: {error.message} - Details: {error.details}')
    except AuthenticationError as error:
        # Authentication failed
        print(f'Auth error: {error.message} - Status: {error.status_code}')
    except APIError as error:
        # API returned an error
        print(f'API error: {error.message} - Status: {error.status_code} - Details: {error.details}')
    except NetworkError as error:
        # Network request failed
        print(f'Network error: {error.message} - Details: {error.details}')

asyncio.run(main())
```

## Testing

The library includes comprehensive unit and integration tests:

```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=nutrient_dws --cov-report=html

# Run only unit tests
python -m pytest tests/unit/

# Run integration tests (requires API key)
NUTRIENT_API_KEY=your_key python -m pytest tests/test_integration.py
```

The library maintains high test coverage across all API methods, including:
- Unit tests for all public methods
- Integration tests for real API interactions
- Type checking with mypy

## Development

For development, install the package in development mode:

```bash
# Clone the repository
git clone https://github.com/PSPDFKit/nutrient-dws-client-python.git
cd nutrient-dws-client-python

# Install in development mode
pip install -e ".[dev]"

# Run type checking
mypy src/

# Run linting
ruff check src/

# Run formatting
ruff format src/
```

## Contributing

We welcome contributions to improve the library! Please follow our development standards to ensure code quality and maintainability.

Quick start for contributors:

1. Clone and setup the repository
2. Make changes following atomic commit practices
3. Use conventional commits for clear change history
4. Include appropriate tests for new features
5. Ensure type checking passes with mypy
6. Follow Python code style with ruff

For detailed contribution guidelines, see the [Contributing Guide](docs/CONTRIBUTING.md).

## Project Structure

```
src/
├── nutrient_dws/
│   ├── builder/         # Builder classes and constants
│   ├── generated/       # Generated type definitions
│   ├── types/          # Type definitions
│   ├── client.py       # Main NutrientClient class
│   ├── errors.py       # Error classes
│   ├── http.py         # HTTP layer
│   ├── inputs.py       # Input handling
│   ├── workflow.py     # Workflow factory
│   └── __init__.py     # Public exports
├── nutrient_dws_scripts/            # CLI scripts for coding agents
└── tests/              # Test files
```

## Python Version Support

This library supports Python 3.10 and higher. The async-first design requires modern Python features for optimal performance and type safety.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/PSPDFKit/nutrient-dws-client-python/issues).

For questions about the Nutrient DWS Processor API, refer to the [official documentation](https://nutrient.io/docs/).
