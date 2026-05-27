# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-05-27

- Added `client.parse()` for the Data Extraction API (`/extraction/parse`)
- Added `extract_api_key` constructor parameter — DWS Extract is a separate product with its own API key

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
