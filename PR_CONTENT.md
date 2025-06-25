# Pull Request: Add Missing Direct API Tools

## Summary
This PR adds 8 new direct API methods that were missing from the Python client, bringing it to feature parity with the Nutrient DWS API capabilities.

## New Tools Added

### 1. Create Redactions (3 methods for different strategies)
- `create_redactions_preset()` - Use built-in patterns for common sensitive data
  - Presets: social-security-number, credit-card-number, email, phone-number, date, currency
- `create_redactions_regex()` - Custom regex patterns for flexible redaction
- `create_redactions_text()` - Exact text matches with case sensitivity options

### 2. PDF Optimization
- `optimize_pdf()` - Reduce file size with multiple optimization options:
  - Grayscale conversion (text, graphics, images)
  - Image quality reduction (1-100)
  - Linearization for web viewing
  - Option to disable images entirely

### 3. Security Features
- `password_protect_pdf()` - Add password protection and permissions
  - User password (for opening)
  - Owner password (for permissions)
  - Granular permissions: print, modification, extract, annotations, fill, etc.
- `set_pdf_metadata()` - Update document properties
  - Title, author, subject, keywords, creator, producer

### 4. Annotation Import
- `apply_instant_json()` - Import Nutrient Instant JSON annotations
  - Supports file, bytes, or URL input
- `apply_xfdf()` - Import standard XFDF annotations
  - Supports file, bytes, or URL input

## Implementation Details

### Code Quality
- ✅ All methods have comprehensive docstrings with examples
- ✅ Type hints are complete and pass mypy checks
- ✅ Code follows project conventions and passes ruff linting
- ✅ All existing unit tests continue to pass (167 tests)

### Architecture
- Methods that require file uploads (apply_instant_json, apply_xfdf) handle them directly
- Methods that use output options (password_protect_pdf, set_pdf_metadata) use the Builder API
- All methods maintain consistency with existing Direct API patterns

### Testing
- Comprehensive integration tests added for all new methods (28 new tests)
- Tests cover success cases, error cases, and edge cases
- Tests are properly skipped when API key is not configured

## Files Changed
- `src/nutrient_dws/api/direct.py` - Added 8 new methods (565 lines)
- `tests/integration/test_new_tools_integration.py` - New test file (481 lines)

## Usage Examples

### Redact Sensitive Data
```python
# Redact social security numbers
client.create_redactions_preset(
    "document.pdf",
    preset="social-security-number",
    output_path="redacted.pdf"
)

# Custom regex redaction
client.create_redactions_regex(
    "document.pdf",
    pattern=r"\b\d{3}-\d{2}-\d{4}\b",
    appearance_fill_color="#000000"
)

# Then apply the redactions
client.apply_redactions("redacted.pdf", output_path="final.pdf")
```

### Optimize PDF Size
```python
# Aggressive optimization
client.optimize_pdf(
    "large_document.pdf",
    grayscale_images=True,
    reduce_image_quality=50,
    linearize=True,
    output_path="optimized.pdf"
)
```

### Secure PDFs
```python
# Password protect with restricted permissions
client.password_protect_pdf(
    "sensitive.pdf",
    user_password="view123",
    owner_password="admin456",
    permissions={
        "print": False,
        "modification": False,
        "extract": True
    }
)
```

## Breaking Changes
None - all changes are additive.

## Migration Guide
No migration needed - existing code continues to work as before.

## Checklist
- [x] Code follows project style guidelines
- [x] Self-review of code completed
- [x] Comments added for complex code sections
- [x] Documentation/docstrings updated
- [x] No warnings generated
- [x] Tests added for new functionality
- [x] All tests pass locally
- [ ] Integration tests pass with live API (requires API key)

## Next Steps
After merging:
1. Update README with examples of new methods
2. Consider adding more tools: HTML to PDF, digital signatures, etc.
3. Create a cookbook/examples directory with common use cases