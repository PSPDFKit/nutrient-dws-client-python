# v1.0.2 - Major Feature Release

## What's Changed

This release adds significant new functionality with 13 new Direct API methods and numerous stability improvements.

### ✨ New Features

#### Direct API Methods
- `create_redactions_preset()` - Create redactions using predefined patterns (SSN, email, phone, etc.)
- `create_redactions_regex()` - Create redactions using custom regex patterns
- `create_redactions_text()` - Create redactions for specific text strings
- `optimize_pdf()` - Optimize PDF file size and performance
- `password_protect_pdf()` - Add password protection to PDFs
- `set_pdf_metadata()` - Update PDF metadata (title, author)
- `split_pdf()` - Split PDFs into multiple files based on page ranges
- `duplicate_pdf_pages()` - Duplicate specific pages within a PDF
- `delete_pdf_pages()` - Remove specific pages from a PDF
- `add_page()` - Insert blank pages at specific positions
- `apply_instant_json()` - Apply PSPDFKit Instant JSON annotations
- `apply_xfdf()` - Apply XFDF annotations to PDFs
- `set_page_label()` - Set custom page labels (Roman numerals, letters, etc.)

#### Enhancements
- 🖼️ Image file support for `watermark_pdf()` method - now accepts PNG/JPEG images as watermarks
- 🧪 Improved CI/CD integration test strategy with better error reporting
- 📈 Enhanced test coverage for all new Direct API methods

### 🐛 Bug Fixes
- Critical API compatibility issues in Direct API integration
- Python 3.9 and 3.10 syntax compatibility across the codebase
- Comprehensive CI failure resolution
- Integration test fixes to match actual API behavior patterns
- Ruff linting and formatting issues throughout the project
- MyPy type checking errors and improved type annotations
- Removed unsupported parameters from API calls
- Fixed page range handling in split_pdf with proper defaults
- Resolved runtime errors with isinstance union syntax
- Updated test fixtures to use valid PNG images

### 📋 Requirements
- Python 3.10+ (maintained as per project design)
- requests>=2.25.0,<3.0.0

### 📦 Installation
```bash
pip install nutrient-dws==1.0.2
```

### 📚 Documentation
See the [README](https://github.com/PSPDFKit/nutrient-dws-client-python#readme) for usage examples of the new features.

**Full Changelog**: https://github.com/PSPDFKit/nutrient-dws-client-python/compare/v1.0.1...v1.0.2