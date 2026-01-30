# Migration Guide: v2.x to v3.0

## Overview

Version 3.0.0 introduces SSRF protection and removes client-side PDF parsing.

## Key Changes

### 1. `sign()` No Longer Accepts URLs (API Limitation)

**Before (v2.x)**:
```python
result = await client.sign('https://example.com/document.pdf', {...})
```

**After (v3.0)** - Fetch file first:
```python
import httpx

async with httpx.AsyncClient() as http:
    url = 'https://example.com/document.pdf'

    # IMPORTANT: Validate URL
    if not url.startswith('https://trusted-domain.com/'):
        raise ValueError('URL not from trusted domain')

    response = await http.get(url, timeout=10.0)
    response.raise_for_status()
    pdf_bytes = response.content

result = await client.sign(pdf_bytes, {...})
```

### 2. Most Methods Now Accept URLs (Passed to Server)

Good news! These methods now support URLs passed securely to the server:
- `rotate()`, `split()`, `add_page()`, `duplicate_pages()`, `delete_pages()`
- `set_page_labels()`, `set_metadata()`, `optimize()`
- `flatten()`, `apply_instant_json()`, `apply_xfdf()`
- All redaction methods
- `convert()`, `ocr()`, `watermark_*()`, `extract_*()`, `merge()`, `password_protect()`

**Example**:
```python
# This now works!
result = await client.rotate('https://example.com/doc.pdf', 90, pages={'start': 0, 'end': 5})
```

### 3. Negative Page Indices Now Supported

Use negative indices for "from end" references:
- `-1` = last page
- `-2` = second-to-last page
- etc.

**Examples**:
```python
# Rotate last 3 pages
await client.rotate(pdf, 90, pages={'start': -3, 'end': -1})

# Delete first and last pages
await client.delete_pages(pdf, [0, -1])

# Split: keep middle pages, excluding first and last
await client.split(pdf, [{'start': 1, 'end': -2}])
```

### 4. Removed from Public API

- `process_remote_file_input()` - No longer needed (URLs passed to server)
- `get_pdf_page_count()` - Use negative indices instead
- `is_valid_pdf()` - Let server validate (internal use only)

**Still Available:**
- `is_remote_file_input()` - Helper to detect if input is a URL (still public)
