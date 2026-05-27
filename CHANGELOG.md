# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-05-27

### Added

- `client.parse()` — first-class support for the Data Extraction API
  (`/extraction/parse`). Supports all four processing modes (`text`,
  `structure`, `understand`, `agentic`) and both output shapes (spatial
  elements and whole-document Markdown). Typed response model with
  discriminated element variants (paragraph, table, formula, picture,
  keyValueRegion, handwriting). Billed against **extraction credits**, a
  separate billing bucket from the **processor API credits** used by the
  other endpoints.
- `NutrientClient(extract_api_key=...)` — optional constructor parameter
  for the DWS Extract API key. `parse()` uses it for `/extraction/parse`
  requests; every other method continues to use `api_key`. Falls back to
  `api_key` when omitted (the path that becomes the default once global
  DWS API keys roll out). Passing only a Processor `api_key` against
  `/extraction/parse` is rejected by the server with `403`.
- New types exported from `nutrient_dws`: `ExtractionCredits`,
  `ParseResponse`, `ParseInstructions`, `ParseMode`, `ParseOutputFormat`,
  `ParseElement`, `ParseOutputBody`, `ParseOutputElements`,
  `ParseOutputMarkdown`, `ParagraphElement`, `TableElement`, `TableCell`,
  `FormulaElement`, `PictureElement`, `KeyValueRegionElement`,
  `KeyValuePair`, `HandwritingElement`.

## [3.0.0] - 2026-01-30

### Security

- **CRITICAL**: Removed client-side URL fetching to prevent SSRF vulnerabilities
- URLs are now passed to the server for secure server-side fetching
- Restricted `sign()` method to local files only (API limitation)

### Changed

- **BREAKING**: `sign()` only accepts local files (paths, bytes, file objects) - no URLs
- **BREAKING**: Most methods now accept `FileInputWithUrl` - URLs passed to server
- **BREAKING**: Removed client-side PDF parsing - leverage API's negative index support
- Methods like `rotate()`, `split()`, `deletePages()` now support negative indices (-1 = last page)
- All methods except `sign()` accept URLs that are passed securely to the server

### Removed

- **BREAKING**: Removed `process_remote_file_input()` from public API (security risk)
- **BREAKING**: Removed `get_pdf_page_count()` from public API (client-side PDF parsing)
- **BREAKING**: Removed `is_valid_pdf()` from public API (internal use only)
- Removed ~200 lines of client-side PDF parsing code

### Added

- SSRF protection documentation in README
- Migration guide (docs/MIGRATION.md)
- Security best practices for handling remote files
- Support for negative page indices in all page-based methods

## [2.0.0] - 2025-01-09

- Initial stable release with full API coverage
- Async-first design with httpx and aiofiles
- Comprehensive type hints and mypy strict mode
- Workflow builder with staged pattern
- Error hierarchy with typed exceptions
