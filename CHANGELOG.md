# Changelog

All notable changes to the nutrient-dws Python client library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-01-03

### Added

#### Direct API Methods
- `create_redactions_preset()` - Create redactions using predefined patterns (SSN, email, phone, etc.)
- `create_redactions_regex()` - Create redactions using custom regex patterns
- `create_redactions_text()` - Create redactions for specific text strings
- `optimize_pdf()` - Optimize PDF file size and performance
- `password_protect_pdf()` - Add password protection to PDFs
- `set_pdf_metadata()` - Update PDF metadata (title, author, subject, keywords)
- `split_pdf()` - Split PDFs into multiple files based on page ranges
- `duplicate_pdf_pages()` - Duplicate specific pages within a PDF
- `delete_pdf_pages()` - Remove specific pages from a PDF
- `add_page()` - Insert blank pages at specific positions
- `apply_instant_json()` - Apply PSPDFKit Instant JSON annotations
- `apply_xfdf()` - Apply XFDF annotations to PDFs
- `set_page_label()` - Set custom page labels (Roman numerals, letters, etc.)

#### Enhancements
- Image file support for `watermark_pdf()` method - now accepts PNG/JPEG images as watermarks
- Improved CI/CD integration test strategy with better error reporting
- Enhanced test coverage for all new Direct API methods

### Fixed
- Critical API compatibility issues in Direct API integration
- Python 3.9 and 3.10 syntax compatibility across the codebase
- Comprehensive CI failure resolution based on multi-model analysis
- Integration test fixes to match actual API behavior patterns
- Ruff linting and formatting issues throughout the project
- MyPy type checking errors and improved type annotations
- Removed unsupported parameters (stroke_width, base_url) from API calls
- Corrected API parameter formats for various operations
- Fixed page range handling in split_pdf with proper defaults
- Resolved runtime errors with isinstance union syntax
- Updated test fixtures to use valid PNG images

### Changed
- Minimum Python version maintained at 3.10+ as per project design
- Improved error messages for better debugging experience
- Standardized code formatting with ruff across entire codebase

## [1.0.1] - 2025-06-20

### Fixed

#### Critical Bug Fixes
- Fix README.md documentation to use `NutrientTimeoutError` instead of `TimeoutError`
- Resolve inconsistency where code exported `NutrientTimeoutError` but docs referenced `TimeoutError`

#### Testing Improvements
- Added comprehensive unit tests (31 tests total)
- Added integration test framework for CI
- Improved test stability and coverage

## [1.0.0] - 2024-06-17

### Added

#### Core Features
- **NutrientClient**: Main client class with support for both Direct API and Builder API patterns
- **Direct API Methods**: Convenient methods for single operations:
  - `convert_to_pdf()` - Convert Office documents to PDF (uses implicit conversion)
  - `flatten_annotations()` - Flatten PDF annotations and form fields
  - `rotate_pages()` - Rotate specific or all pages
  - `ocr_pdf()` - Apply OCR to make PDFs searchable
  - `watermark_pdf()` - Add text or image watermarks
  - `apply_redactions()` - Apply existing redaction annotations
  - `merge_pdfs()` - Merge multiple PDFs and Office documents

- **Builder API**: Fluent interface for chaining multiple operations:
  ```python
  client.build(input_file="document.docx") \
      .add_step("rotate-pages", {"degrees": 90}) \
      .add_step("ocr-pdf", {"language": "english"}) \
      .execute(output_path="processed.pdf")
  ```

#### Infrastructure
- **HTTP Client**: 
  - Connection pooling for performance
  - Automatic retry logic with exponential backoff
  - Bearer token authentication
  - Comprehensive error handling

- **File Handling**:
  - Support for multiple input types (paths, Path objects, bytes, file-like objects)
  - Automatic streaming for large files (>10MB)
  - Memory-efficient processing

- **Exception Hierarchy**:
  - `NutrientError` - Base exception
  - `AuthenticationError` - API key issues
  - `APIError` - General API errors with status codes
  - `ValidationError` - Request validation failures
  - `TimeoutError` - Request timeouts
  - `FileProcessingError` - File operation failures

#### Development Tools
- **Testing**: 82 unit tests with 92.46% code coverage
- **Type Safety**: Full mypy type checking support
- **Linting**: Configured with ruff
- **Pre-commit Hooks**: Automated code quality checks
- **CI/CD**: GitHub Actions for testing, linting, and releases
- **Documentation**: Comprehensive README with examples

### Changed
- Package name updated from `nutrient` to `nutrient-dws` for PyPI
- Source directory renamed from `src/nutrient` to `src/nutrient_dws`
- API endpoint updated to https://api.pspdfkit.com
- Authentication changed from X-Api-Key header to Bearer token

### Discovered
- **Implicit Document Conversion**: The API automatically converts Office documents (DOCX, XLSX, PPTX) to PDF when processing, eliminating the need for explicit conversion steps

### Fixed
- Watermark operation now correctly requires width/height parameters
- OCR language codes properly mapped (e.g., "en" → "english")
- All API operations updated to use the Build API endpoint
- Type annotations corrected throughout the codebase

### Security
- API keys are never logged or exposed
- Support for environment variable configuration
- Secure handling of authentication tokens

[1.0.2]: https://github.com/PSPDFKit/nutrient-dws-client-python/releases/tag/v1.0.2
[1.0.1]: https://github.com/PSPDFKit/nutrient-dws-client-python/releases/tag/v1.0.1
[1.0.0]: https://github.com/PSPDFKit/nutrient-dws-client-python/releases/tag/v1.0.0