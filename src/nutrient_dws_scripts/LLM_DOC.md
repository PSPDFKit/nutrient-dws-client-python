# Nutrient DWS Python Client Documentation

> Nutrient DWS is a document processing service which provides document processing operations including conversion, merging, compression, watermarking, signage, and text extraction.

## Authentication

### Direct API Key

Provide your API key directly:

```python
from nutrient_dws import NutrientClient

client = NutrientClient(api_key='your_api_key')
```

### Token Provider

Use an async token provider to fetch tokens from a secure source:

```python
import httpx
from nutrient_dws import NutrientClient

async def get_token():
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get('/api/get-nutrient-token')
        data = response.json()
        return data['token']

client = NutrientClient(api_key=get_token)
```

## NutrientClient

The main client for interacting with the Nutrient DWS Processor API.

### Constructor

```python
NutrientClient(api_key: str | Callable[[], Awaitable[str] | str], base_url: str | None = None, timeout: int | None = None)
```

Parameters:
- `api_key` (required): Your API key string or async function returning a token
- `base_url` (optional): Custom API base URL (defaults to `https://api.nutrient.io`)
- `timeout` (optional): Request timeout in milliseconds

## Direct Methods

The client provides numerous async methods for document processing:

### Account Methods

#### get_account_info()
Gets account information for the current API key.

**Returns**: `AccountInfo` - Account information dictionary

```python
account_info = await client.get_account_info()

# Access subscription information
print(account_info['subscriptionType'])
```

#### create_token(params)
Creates a new authentication token.

**Parameters**:
- `params: CreateAuthTokenParameters` - Parameters for creating the token

**Returns**: `CreateAuthTokenResponse` - The created token information

```python
token = await client.create_token({
    'expirationTime': 3600
})
print(token['id'])

# Store the token for future use
token_id = token['id']
token_value = token['accessToken']
```

#### delete_token(id)
Deletes an authentication token.

**Parameters**:
- `id: str` - ID of the token to delete

**Returns**: `None`

```python
await client.delete_token('token-id-123')

# Example in a token management function
async def revoke_user_token(token_id: str) -> bool:
    try:
        await client.delete_token(token_id)
        print(f'Token {token_id} successfully revoked')
        return True
    except Exception as error:
        print(f'Failed to revoke token: {error}')
        return False
```

### Document Processing Methods

#### sign(file, data?, options?)
Signs a PDF document.

**Parameters**:
- `file: FileInput` - The PDF file to sign
- `data: CreateDigitalSignature | None` - Signature data (optional)
- `options: SignRequestOptions | None` - Additional options (image, graphicImage) (optional)

**Returns**: `BufferOutput` - The signed PDF file output

```python
result = await client.sign('document.pdf', {
    'signatureType': 'cms',
    'flatten': False,
    'cadesLevel': 'b-lt'
})

# Access the signed PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('signed-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### create_redactions_ai(file, criteria, redaction_state?, pages?, options?)
Uses AI to redact sensitive information in a document.

**Parameters**:
- `file: FileInput` - The PDF file to redact
- `criteria: str` - AI redaction criteria
- `redaction_state: Literal['stage', 'apply']` - Whether to stage or apply redactions (default: 'stage')
- `pages: PageRange | None` - Optional pages to redact
- `options: RedactOptions | None` - Optional redaction options

**Returns**: `BufferOutput` - The redacted document

```python
# Stage redactions
result = await client.create_redactions_ai(
    'document.pdf',
    'Remove all emails'
)

# Apply redactions immediately
result = await client.create_redactions_ai(
    'document.pdf',
    'Remove all PII',
    'apply'
)

# Redact only specific pages
result = await client.create_redactions_ai(
    'document.pdf',
    'Remove all emails',
    'stage',
    {'start': 0, 'end': 4}  # Pages 0, 1, 2, 3, 4
)

# Redact only the last 3 pages
result = await client.create_redactions_ai(
    'document.pdf',
    'Remove all PII',
    'stage',
    {'start': -3, 'end': -1}  # Last three pages
)

# Access the redacted PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('redacted-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### ocr(file, language)
Performs OCR (Optical Character Recognition) on a document.

**Parameters**:
- `file: FileInput` - The input file to perform OCR on
- `language: OcrLanguage | list[OcrLanguage]` - The language(s) to use for OCR

**Returns**: `BufferOutput` - The OCR result

```python
result = await client.ocr('scanned-document.pdf', 'english')

# Access the OCR-processed PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('ocr-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### watermark_text(file, text, options?)
Adds a text watermark to a document.

**Parameters**:
- `file: FileInput` - The input file to watermark
- `text: str` - The watermark text
- `options: dict[str, Any] | None` - Watermark options (optional)

**Returns**: `BufferOutput` - The watermarked document

```python
result = await client.watermark_text('document.pdf', 'CONFIDENTIAL', {
    'opacity': 0.5,
    'fontSize': 24
})

# Access the watermarked PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('watermarked-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### watermark_image(file, image, options?)
Adds an image watermark to a document.

**Parameters**:
- `file: FileInput` - The input file to watermark
- `image: FileInput` - The watermark image
- `options: ImageWatermarkActionOptions | None` - Watermark options (optional)

**Returns**: `BufferOutput` - The watermarked document

```python
result = await client.watermark_image('document.pdf', 'watermark.jpg', {
    'opacity': 0.5,
    'width': {'value': 50, 'unit': "%"},
    'height': {'value': 50, 'unit': "%"}
})

# Access the watermarked PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('image-watermarked-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### convert(file, target_format)
Converts a document to a different format.

**Parameters**:
- `file: FileInput` - The input file to convert
- `target_format: OutputFormat` - The target format to convert to

**Returns**: `BufferOutput | ContentOutput | JsonContentOutput` - The specific output type based on the target format

```python
# Convert DOCX to PDF
pdf_result = await client.convert('document.docx', 'pdf')
# Supports formats: pdf, pdfa, pdfua, docx, xlsx, pptx, png, jpeg, jpg, webp, html, markdown

# Access the PDF buffer
pdf_buffer = pdf_result['buffer']
print(pdf_result['mimeType'])  # 'application/pdf'

# Save the PDF
with open('converted-document.pdf', 'wb') as f:
    f.write(pdf_buffer)

# Convert PDF to image
image_result = await client.convert('document.pdf', 'png')

# Access the PNG buffer
png_buffer = image_result['buffer']
print(image_result['mimeType'])  # 'image/png'

# Save the image
with open('document-page.png', 'wb') as f:
    f.write(png_buffer)
```

#### merge(files)
Merges multiple documents into one.

**Parameters**:
- `files: list[FileInput]` - The files to merge

**Returns**: `BufferOutput` - The merged document

```python
result = await client.merge([
    'doc1.pdf',
    'doc2.pdf',
    'doc3.pdf'
])

# Access the merged PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('merged-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### extract_text(file, pages?)
Extracts text content from a document.

**Parameters**:
- `file: FileInput` - The file to extract text from
- `pages: PageRange | None` - Optional page range to extract text from

**Returns**: `JsonContentOutput` - The extracted text data

```python
result = await client.extract_text('document.pdf')

# Extract text from specific pages
result = await client.extract_text('document.pdf', {'start': 0, 'end': 2})  # Pages 0, 1, 2

# Extract text from the last page
result = await client.extract_text('document.pdf', {'end': -1})  # Last page

# Extract text from the second-to-last page to the end
result = await client.extract_text('document.pdf', {'start': -2})  # Second-to-last and last page

# Access the extracted text content
text_content = result['data']['pages'][0]['plainText']

# Process the extracted text
word_count = len(text_content.split())
print(f'Document contains {word_count} words')

# Search for specific content
if 'confidential' in text_content:
    print('Document contains confidential information')
```

#### extract_table(file, pages?)
Extracts table content from a document.

**Parameters**:
- `file: FileInput` - The file to extract tables from
- `pages: PageRange | None` - Optional page range to extract tables from

**Returns**: `JsonContentOutput` - The extracted table data

```python
result = await client.extract_table('document.pdf')

# Extract tables from specific pages
result = await client.extract_table('document.pdf', {'start': 0, 'end': 2})  # Pages 0, 1, 2

# Extract tables from the last page
result = await client.extract_table('document.pdf', {'end': -1})  # Last page

# Extract tables from the second-to-last page to the end
result = await client.extract_table('document.pdf', {'start': -2})  # Second-to-last and last page

# Access the extracted tables
tables = result['data']['pages'][0]['tables']

# Process the first table if available
if tables and len(tables) > 0:
    first_table = tables[0]

    # Get table dimensions
    print(f"Table has {len(first_table['rows'])} rows and {len(first_table['columns'])} columns")

    # Access table cells
    for i in range(len(first_table['rows'])):
        for j in range(len(first_table['columns'])):
            cell = next((cell for cell in first_table['cells']
                        if cell['rowIndex'] == i and cell['columnIndex'] == j), None)
            cell_content = cell['text'] if cell else ''
            print(f"Cell [{i}][{j}]: {cell_content}")

    # Convert table to CSV
    csv_content = ''
    for i in range(len(first_table['rows'])):
        row_data = []
        for j in range(len(first_table['columns'])):
            cell = next((cell for cell in first_table['cells']
                        if cell['rowIndex'] == i and cell['columnIndex'] == j), None)
            row_data.append(cell['text'] if cell else '')
        csv_content += ','.join(row_data) + '\n'
    print(csv_content)
```

#### extract_key_value_pairs(file, pages?)
Extracts key value pair content from a document.

**Parameters**:
- `file: FileInput` - The file to extract KVPs from
- `pages: PageRange | None` - Optional page range to extract KVPs from

**Returns**: `JsonContentOutput` - The extracted KVPs data

```python
result = await client.extract_key_value_pairs('document.pdf')

# Extract KVPs from specific pages
result = await client.extract_key_value_pairs('document.pdf', {'start': 0, 'end': 2})  # Pages 0, 1, 2

# Extract KVPs from the last page
result = await client.extract_key_value_pairs('document.pdf', {'end': -1})  # Last page

# Extract KVPs from the second-to-last page to the end
result = await client.extract_key_value_pairs('document.pdf', {'start': -2})  # Second-to-last and last page

# Access the extracted key-value pairs
kvps = result['data']['pages'][0]['keyValuePairs']

# Process the key-value pairs
if kvps and len(kvps) > 0:
    # Iterate through all key-value pairs
    for index, kvp in enumerate(kvps):
        print(f'KVP {index + 1}:')
        print(f'  Key: {kvp["key"]}')
        print(f'  Value: {kvp["value"]}')
        print(f'  Confidence: {kvp["confidence"]}')

    # Create a dictionary from the key-value pairs
    dictionary = {}
    for kvp in kvps:
        dictionary[kvp['key']] = kvp['value']

    # Look up specific values
    print(f'Invoice Number: {dictionary.get("Invoice Number")}')
    print(f'Date: {dictionary.get("Date")}')
    print(f'Total Amount: {dictionary.get("Total")}')
```

#### flatten(file, annotation_ids?)
Flattens annotations in a PDF document.

**Parameters**:
- `file: FileInput` - The PDF file to flatten
- `annotation_ids: list[str | int] | None` - Optional specific annotation IDs to flatten

**Returns**: `BufferOutput` - The flattened document

```python
# Flatten all annotations
result = await client.flatten('annotated-document.pdf')

# Flatten specific annotations by ID
result = await client.flatten('annotated-document.pdf', ['annotation1', 'annotation2'])
```

#### password_protect(file, user_password, owner_password, permissions?)
Password protects a PDF document.

**Parameters**:
- `file: FileInput` - The file to protect
- `user_password: str` - Password required to open the document
- `owner_password: str` - Password required to modify the document
- `permissions: list[PDFUserPermission] | None` - Optional list of permissions granted when opened with user password

**Returns**: `BufferOutput` - The password-protected document

```python
result = await client.password_protect('document.pdf', 'user123', 'owner456')

# Or with specific permissions:
result = await client.password_protect('document.pdf', 'user123', 'owner456',
    ['printing', 'extract_accessibility'])

# Access the password-protected PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('protected-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### set_metadata(file, metadata)
Sets metadata for a PDF document.

**Parameters**:
- `file: FileInput` - The PDF file to modify
- `metadata: Metadata` - The metadata to set (title and/or author)

**Returns**: `BufferOutput` - The document with updated metadata

```python
result = await client.set_metadata('document.pdf', {
    'title': 'My Document',
    'author': 'John Doe'
})
```

#### set_page_labels(file, labels)
Sets page labels for a PDF document.

**Parameters**:
- `file: FileInput` - The PDF file to modify
- `labels: list[Label]` - List of label objects with pages and label properties

**Returns**: `BufferOutput` - The document with updated page labels

```python
result = await client.set_page_labels('document.pdf', [
    {'pages': [0, 1, 2], 'label': 'Cover'},
    {'pages': [3, 4, 5], 'label': 'Chapter 1'}
])

# Access the updated PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('labeled-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### apply_instant_json(file, instant_json_file)
Applies Instant JSON to a document.

**Parameters**:
- `file: FileInput` - The PDF file to modify
- `instant_json_file: FileInput` - The Instant JSON file to apply

**Returns**: `BufferOutput` - The modified document

```python
result = await client.apply_instant_json('document.pdf', 'annotations.json')

# Access the modified PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('annotated-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### apply_xfdf(file, xfdf_file, options?)
Applies XFDF to a document.

**Parameters**:
- `file: FileInput` - The PDF file to modify
- `xfdf_file: FileInput` - The XFDF file to apply
- `options: ApplyXfdfActionOptions | None` - Optional settings for applying XFDF

**Returns**: `BufferOutput` - The modified document

```python
result = await client.apply_xfdf('document.pdf', 'annotations.xfdf')

# Or with options:
result = await client.apply_xfdf(
    'document.pdf', 'annotations.xfdf',
    {'ignorePageRotation': True, 'richTextEnabled': False}
)

# Access the modified PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('xfdf-applied-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### create_redactions_preset(file, preset, redaction_state?, pages?, preset_options?, options?)
Creates redaction annotations based on a preset pattern.

**Parameters**:
- `file: FileInput` - The PDF file to create redactions in
- `preset: SearchPreset` - The preset pattern to search for (e.g., 'email-address', 'social-security-number')
- `redaction_state: Literal['stage', 'apply']` - Whether to stage or apply redactions (default: 'stage')
- `pages: PageRange | None` - Optional page range to create redactions in
- `preset_options: CreateRedactionsStrategyOptionsPreset | None` - Optional settings for the preset strategy
- `options: BaseCreateRedactionsOptions | None` - Optional settings for creating redactions

**Returns**: `BufferOutput` - The document with redaction annotations

```python
result = await client.create_redactions_preset('document.pdf', 'email-address')

# With specific pages
result = await client.create_redactions_preset(
    'document.pdf',
    'email-address',
    'stage',
    {'start': 0, 'end': 4}  # Pages 0, 1, 2, 3, 4
)

# With the last 3 pages
result = await client.create_redactions_preset(
    'document.pdf',
    'email-address',
    'stage',
    {'start': -3, 'end': -1}  # Last three pages
)

# Access the document with redactions
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('redacted-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### create_redactions_regex(file, regex, redaction_state?, pages?, regex_options?, options?)
Creates redaction annotations based on a regular expression.

**Parameters**:
- `file: FileInput` - The PDF file to create redactions in
- `regex: str` - The regular expression to search for
- `redaction_state: Literal['stage', 'apply']` - Whether to stage or apply redactions (default: 'stage')
- `pages: PageRange | None` - Optional page range to create redactions in
- `regex_options: CreateRedactionsStrategyOptionsRegex | None` - Optional settings for the regex strategy
- `options: BaseCreateRedactionsOptions | None` - Optional settings for creating redactions

**Returns**: `BufferOutput` - The document with redaction annotations

```python
result = await client.create_redactions_regex('document.pdf', r'Account:\s*\d{8,12}')

# With specific pages
result = await client.create_redactions_regex(
    'document.pdf',
    r'Account:\s*\d{8,12}',
    'stage',
    {'start': 0, 'end': 4}  # Pages 0, 1, 2, 3, 4
)

# With the last 3 pages
result = await client.create_redactions_regex(
    'document.pdf',
    r'Account:\s*\d{8,12}',
    'stage',
    {'start': -3, 'end': -1}  # Last three pages
)

# Access the document with redactions
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('regex-redacted-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### create_redactions_text(file, text, redaction_state?, pages?, text_options?, options?)
Creates redaction annotations based on text.

**Parameters**:
- `file: FileInput` - The PDF file to create redactions in
- `text: str` - The text to search for
- `redaction_state: Literal['stage', 'apply']` - Whether to stage or apply redactions (default: 'stage')
- `pages: PageRange | None` - Optional page range to create redactions in
- `text_options: CreateRedactionsStrategyOptionsText | None` - Optional settings for the text strategy
- `options: BaseCreateRedactionsOptions | None` - Optional settings for creating redactions

**Returns**: `BufferOutput` - The document with redaction annotations

```python
result = await client.create_redactions_text('document.pdf', 'email@example.com')

# With specific pages and options
result = await client.create_redactions_text(
    'document.pdf',
    'email@example.com',
    'stage',
    {'start': 0, 'end': 4},  # Pages 0, 1, 2, 3, 4
    {'caseSensitive': False, 'includeAnnotations': True}
)

# Create redactions on the last 3 pages
result = await client.create_redactions_text(
    'document.pdf',
    'email@example.com',
    'stage',
    {'start': -3, 'end': -1}  # Last three pages
)

# Access the document with redactions
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('text-redacted-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### apply_redactions(file)
Applies redaction annotations in a document.

**Parameters**:
- `file: FileInput` - The PDF file with redaction annotations to apply

**Returns**: `BufferOutput` - The document with applied redactions

```python
# Stage redactions from a createRedaction Method:
staged_result = await client.create_redactions_text(
    'document.pdf',
    'email@example.com',
    'stage'
)

result = await client.apply_redactions(staged_result['buffer'])

# Access the final redacted document
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('final-redacted-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### rotate(file, angle, pages?)
Rotates pages in a document.

**Parameters**:
- `file: FileInput` - The PDF file to rotate
- `angle: Literal[90, 180, 270]` - Rotation angle (90, 180, or 270 degrees)
- `pages: PageRange | None` - Optional page range to rotate

**Returns**: `BufferOutput` - The entire document with specified pages rotated

```python
result = await client.rotate('document.pdf', 90)

# Rotate specific pages:
result = await client.rotate('document.pdf', 90, {'start': 1, 'end': 3})  # Pages 1, 2, 3

# Rotate the last page:
result = await client.rotate('document.pdf', 90, {'end': -1})  # Last page

# Rotate from page 2 to the second-to-last page:
result = await client.rotate('document.pdf', 90, {'start': 2, 'end': -2})

# Access the rotated PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('rotated-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### add_page(file, count?, index?)
Adds blank pages to a document.

**Parameters**:
- `file: FileInput` - The PDF file to add pages to
- `count: int` - The number of blank pages to add (default: 1)
- `index: int | None` - Optional index where to add the blank pages (0-based). If not provided, pages are added at the end.

**Returns**: `BufferOutput` - The document with added pages

```python
# Add 2 blank pages at the end
result = await client.add_page('document.pdf', 2)

# Add 1 blank page after the first page (at index 1)
result = await client.add_page('document.pdf', 1, 1)

# Access the document with added pages
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('document-with-pages.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### optimize(file, options?)
Optimizes a PDF document for size reduction.

**Parameters**:
- `file: FileInput` - The PDF file to optimize
- `options: OptimizePdf | None` - Optimization options

**Returns**: `BufferOutput` - The optimized document

```python
result = await client.optimize('large-document.pdf', {
    'grayscaleImages': True,
    'mrcCompression': True,
    'imageOptimizationQuality': 2
})

# Access the optimized PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('optimized-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### split(file, page_ranges)
Splits a PDF document into multiple parts based on page ranges.

**Parameters**:
- `file: FileInput` - The PDF file to split
- `page_ranges: list[PageRange]` - List of page ranges to extract

**Returns**: `list[BufferOutput]` - A list of PDF documents, one for each page range

```python
results = await client.split('document.pdf', [
    {'start': 0, 'end': 2},  # Pages 0, 1, 2
    {'start': 3, 'end': 5}   # Pages 3, 4, 5
])

# Split using negative indices
results = await client.split('document.pdf', [
    {'start': 0, 'end': 2},     # First three pages
    {'start': 3, 'end': -3},    # Middle pages
    {'start': -2, 'end': -1}    # Last two pages
])

# Process each resulting PDF
for i, result in enumerate(results):
    # Access the PDF buffer
    pdf_buffer = result['buffer']

    # Get the MIME type of the output
    print(result['mimeType'])  # 'application/pdf'

    # Save the buffer to a file
    with open(f'split-part-{i}.pdf', 'wb') as f:
        f.write(pdf_buffer)
```

#### duplicate_pages(file, page_indices)
Creates a new PDF containing only the specified pages in the order provided.

**Parameters**:
- `file: FileInput` - The PDF file to extract pages from
- `page_indices: list[int]` - List of page indices to include in the new PDF (0-based)
                             Negative indices count from the end of the document (e.g., -1 is the last page)

**Returns**: `BufferOutput` - A new document with only the specified pages

```python
# Create a new PDF with only the first and third pages
result = await client.duplicate_pages('document.pdf', [0, 2])

# Create a new PDF with pages in a different order
result = await client.duplicate_pages('document.pdf', [2, 0, 1])

# Create a new PDF with duplicated pages
result = await client.duplicate_pages('document.pdf', [0, 0, 1, 1, 0])

# Create a new PDF with the first and last pages
result = await client.duplicate_pages('document.pdf', [0, -1])

# Create a new PDF with the last three pages in reverse order
result = await client.duplicate_pages('document.pdf', [-1, -2, -3])

# Access the PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('duplicated-pages.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

#### delete_pages(file, page_indices)
Deletes pages from a PDF document.

**Parameters**:
- `file: FileInput` - The PDF file to modify
- `page_indices: list[int]` - List of page indices to delete (0-based)
                             Negative indices count from the end of the document (e.g., -1 is the last page)

**Returns**: `BufferOutput` - The document with deleted pages

```python
# Delete second and fourth pages
result = await client.delete_pages('document.pdf', [1, 3])

# Delete the last page
result = await client.delete_pages('document.pdf', [-1])

# Delete the first and last two pages
result = await client.delete_pages('document.pdf', [0, -1, -2])

# Access the modified PDF buffer
pdf_buffer = result['buffer']

# Get the MIME type of the output
print(result['mimeType'])  # 'application/pdf'

# Save the buffer to a file
with open('modified-document.pdf', 'wb') as f:
    f.write(pdf_buffer)
```

### Error Handling

The library provides a comprehensive error hierarchy:

```python
from nutrient_dws import (
    NutrientError,
    ValidationError,
    APIError,
    AuthenticationError,
    NetworkError
)

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
```

## Workflow Methods

The Nutrient DWS Python Client uses a fluent builder pattern with staged interfaces to create document processing workflows. This architecture provides several benefits:

1. **Type Safety**: The staged interface ensures that methods are only available at appropriate stages
2. **Readability**: Method chaining creates readable, declarative code
3. **Discoverability**: IDE auto-completion guides you through the workflow stages
4. **Flexibility**: Complex workflows can be built with simple, composable pieces

### Stage 0: Create Workflow

You have several ways of creating a workflow

```python
# Creating Workflow from a client
workflow = client.workflow()

# Override the client timeout
workflow = client.workflow(60000)

# Create a workflow without a client
from nutrient_dws.builder.builder import StagedWorkflowBuilder
workflow = StagedWorkflowBuilder({
    'apiKey': 'your-api-key'
})
```

### Stage 1: Add Parts

In this stage, you add document parts to the workflow:

```python
workflow = (client.workflow()
    .add_file_part('document.pdf')
    .add_file_part('appendix.pdf'))
```

Available methods:

#### `add_file_part(file, options?, actions?)`
Adds a file part to the workflow.

**Parameters:**
- `file: FileInput` - The file to add to the workflow. Can be a local file path, bytes, or file-like object.
- `options: FilePartOptions | None` - Additional options for the file part (optional)
- `actions: list[BuildAction] | None` - Actions to apply to the file part (optional)

**Returns:** `WorkflowWithPartsStage` - The workflow builder instance for method chaining.

**Example:**

```python
# Add a PDF file from a local path
workflow.add_file_part('/path/to/document.pdf')

# Add a file with options and actions
workflow.add_file_part(
  '/path/to/document.pdf',
  {'pages': {'start': 1, 'end': 3}},
  [BuildActions.watermark_text('CONFIDENTIAL')]
)
```

#### `add_html_part(html, assets?, options?, actions?)`
Adds an HTML part to the workflow.

**Parameters:**
- `html: FileInput` - The HTML content to add. Can be a file path, bytes, or file-like object.
- `assets: list[FileInput] | None` - Optional list of assets (CSS, images, etc.) to include with the HTML. Only local files or bytes are supported (optional)
- `options: HTMLPartOptions | None` - Additional options for the HTML part (optional)
- `actions: list[BuildAction] | None` - Actions to apply to the HTML part (optional)

**Returns:** `WorkflowWithPartsStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Add HTML content from a file
workflow.add_html_part('/path/to/content.html')

# Add HTML with assets and options
workflow.add_html_part(
    '/path/to/content.html',
    ['/path/to/style.css', '/path/to/image.png'],
    {'layout': {'size': 'A4'}}
)
```

#### `add_new_page(options?, actions?)`
Adds a new blank page to the workflow.

**Parameters:**
- `options: NewPagePartOptions | None` - Additional options for the new page, such as page size, orientation, etc. (optional)
- `actions: list[BuildAction] | None` - Actions to apply to the new page (optional)

**Returns:** `WorkflowWithPartsStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Add a simple blank page
workflow.add_new_page()

# Add a new page with specific options
workflow.add_new_page({
    'layout': {'size': 'A4', 'orientation': 'portrait'}
})
```

#### `add_document_part(document_id, options?, actions?)`
Adds a document part to the workflow by referencing an existing document by ID.

**Parameters:**
- `document_id: str` - The ID of the document to add to the workflow.
- `options: DocumentPartOptions | None` - Additional options for the document part (optional)
  - `options['layer']: str` - Optional layer name to select a specific layer from the document.
- `actions: list[BuildAction] | None` - Actions to apply to the document part (optional)

**Returns:** `WorkflowWithPartsStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Add a document by ID
workflow.add_document_part('doc_12345abcde')

# Add a document with a specific layer and options
workflow.add_document_part(
    'doc_12345abcde',
    {
        'layer': 'content',
        'pages': {'start': 0, 'end': 3}
    }
)
```

### Stage 2: Apply Actions (Optional)

In this stage, you can apply actions to the document:

```python
workflow.apply_action(BuildActions.watermark_text('CONFIDENTIAL', {
  'opacity': 0.5,
  'fontSize': 48
}))
```

Available methods:

#### `apply_action(action)`
Applies a single action to the workflow.

**Parameters:**
- `action: BuildAction` - The action to apply to the workflow.

**Returns:** `WorkflowWithActionsStage` - The workflow builder instance for method chaining.

**Example:**

```python
# Apply a watermark action
workflow.apply_action(
  BuildActions.watermark_text('CONFIDENTIAL', {
    'opacity': 0.3,
    'rotation': 45
  })
)

# Apply an OCR action
workflow.apply_action(BuildActions.ocr('english'))
```

#### `apply_actions(actions)`
Applies multiple actions to the workflow.

**Parameters:**
- `actions: list[BuildAction]` - A list of actions to apply to the workflow.

**Returns:** `WorkflowWithActionsStage` - The workflow builder instance for method chaining.

**Example:**

```python
# Apply multiple actions to the workflow
workflow.apply_actions([
  BuildActions.watermark_text('DRAFT', {'opacity': 0.5}),
  BuildActions.ocr('english'),
  BuildActions.flatten()
])
```

#### Action Types:

#### Document Processing

##### `BuildActions.ocr(language)`
Creates an OCR (Optical Character Recognition) action to extract text from images or scanned documents.

**Parameters:**
- `language: str | list[str]` - Language(s) for OCR. Can be a single language or a list of languages.

**Example:**
```python
# Basic OCR with English language
workflow.apply_action(BuildActions.ocr('english'))

# OCR with multiple languages
workflow.apply_action(BuildActions.ocr(['english', 'french', 'german']))

# OCR with options (via dict syntax)
workflow.apply_action(BuildActions.ocr({
    'language': 'english',
    'enhanceResolution': True
}))
```

##### `BuildActions.rotate(rotate_by)`
Creates an action to rotate pages in the document.

**Parameters:**
- `rotate_by: Literal[90, 180, 270]` - Rotation angle in degrees (must be 90, 180, or 270).

**Example:**
```python
# Rotate pages by 90 degrees
workflow.apply_action(BuildActions.rotate(90))

# Rotate pages by 180 degrees
workflow.apply_action(BuildActions.rotate(180))
```

##### `BuildActions.flatten(annotation_ids?)`
Creates an action to flatten annotations into the document content, making them non-interactive but permanently visible.

**Parameters:**
- `annotation_ids: list[str | int] | None` - Optional list of annotation IDs to flatten. If not specified, all annotations will be flattened (optional)

**Example:**
```python
# Flatten all annotations
workflow.apply_action(BuildActions.flatten())

# Flatten specific annotations
workflow.apply_action(BuildActions.flatten(['annotation1', 'annotation2']))
```

#### Watermarking

##### `BuildActions.watermark_text(text, options?)`
Creates an action to add a text watermark to the document.

**Parameters:**
- `text: str` - Watermark text content.
- `options: TextWatermarkActionOptions | None` - Watermark options (optional):
  - `width`: Width dimension of the watermark (dict with 'value' and 'unit', e.g. `{'value': 100, 'unit': '%'}`)
  - `height`: Height dimension of the watermark (dict with 'value' and 'unit')
  - `top`, `right`, `bottom`, `left`: Position of the watermark (dict with 'value' and 'unit')
  - `rotation`: Rotation of the watermark in counterclockwise degrees (default: 0)
  - `opacity`: Watermark opacity (0 is fully transparent, 1 is fully opaque)
  - `fontFamily`: Font family for the text (e.g. 'Helvetica')
  - `fontSize`: Size of the text in points
  - `fontColor`: Foreground color of the text (e.g. '#ffffff')
  - `fontStyle`: Text style list (['bold'], ['italic'], or ['bold', 'italic'])

**Example:**

```python
# Simple text watermark
workflow.apply_action(BuildActions.watermark_text('CONFIDENTIAL'))

# Customized text watermark
workflow.apply_action(BuildActions.watermark_text('DRAFT', {
  'opacity': 0.5,
  'rotation': 45,
  'fontSize': 36,
  'fontColor': '#FF0000',
  'fontStyle': ['bold', 'italic']
}))
```

##### `BuildActions.watermark_image(image, options?)`
Creates an action to add an image watermark to the document.

**Parameters:**
- `image: FileInput` - Watermark image (file path, bytes, or file-like object).
- `options: ImageWatermarkActionOptions | None` - Watermark options (optional):
  - `width`: Width dimension of the watermark (dict with 'value' and 'unit', e.g. `{'value': 100, 'unit': '%'}`)
  - `height`: Height dimension of the watermark (dict with 'value' and 'unit')
  - `top`, `right`, `bottom`, `left`: Position of the watermark (dict with 'value' and 'unit')
  - `rotation`: Rotation of the watermark in counterclockwise degrees (default: 0)
  - `opacity`: Watermark opacity (0 is fully transparent, 1 is fully opaque)

**Example:**

```python
# Simple image watermark
workflow.apply_action(BuildActions.watermark_image('/path/to/logo.png'))

# Customized image watermark
workflow.apply_action(BuildActions.watermark_image('/path/to/logo.png', {
  'opacity': 0.3,
  'width': {'value': 50, 'unit': '%'},
  'height': {'value': 50, 'unit': '%'},
  'top': {'value': 10, 'unit': 'px'},
  'left': {'value': 10, 'unit': 'px'},
  'rotation': 0
}))
```

#### Annotations

##### `BuildActions.apply_instant_json(file)`
Creates an action to apply annotations from an Instant JSON file to the document.

**Parameters:**
- `file: FileInput` - Instant JSON file input (file path, bytes, or file-like object).

**Example:**

```python
# Apply annotations from Instant JSON file
workflow.apply_action(BuildActions.apply_instant_json('/path/to/annotations.json'))
```

##### `BuildActions.apply_xfdf(file, options?)`
Creates an action to apply annotations from an XFDF file to the document.

**Parameters:**
- `file: FileInput` - XFDF file input (file path, bytes, or file-like object).
- `options: ApplyXfdfActionOptions | None` - Apply XFDF options (optional):
  - `ignorePageRotation: bool` - If True, ignores page rotation when applying XFDF data (default: False)
  - `richTextEnabled: bool` - If True, plain text annotations will be converted to rich text annotations. If False, all text annotations will be plain text annotations (default: True)

**Example:**

```python
# Apply annotations from XFDF file with default options
workflow.apply_action(BuildActions.apply_xfdf('/path/to/annotations.xfdf'))

# Apply annotations with specific options
workflow.apply_action(BuildActions.apply_xfdf('/path/to/annotations.xfdf', {
  'ignorePageRotation': True,
  'richTextEnabled': False
}))
```

#### Redactions

##### `BuildActions.create_redactions_text(text, options?, strategy_options?)`
Creates an action to add redaction annotations based on text search.

**Parameters:**
- `text: str` - Text to search and redact.
- `options: BaseCreateRedactionsOptions | None` - Redaction options (optional):
  - `content: RedactionAnnotation` - Visual aspects of the redaction annotation (background color, overlay text, etc.)
- `strategy_options: CreateRedactionsStrategyOptionsText | None` - Redaction strategy options (optional):
  - `includeAnnotations: bool` - If True, redaction annotations are created on top of annotations whose content match the provided text (default: True)
  - `caseSensitive: bool` - If True, the search will be case sensitive (default: False)
  - `start: int` - The index of the page from where to start the search (default: 0)
  - `limit: int` - Starting from start, the number of pages to search (default: to the end of the document)

**Example:**

```python
# Create redactions for all occurrences of "Confidential"
workflow.apply_action(BuildActions.create_redactions_text('Confidential'))

# Create redactions with custom appearance and search options
workflow.apply_action(BuildActions.create_redactions_text('Confidential',
                                                          {
                                                            'content': {
                                                              'backgroundColor': '#000000',
                                                              'overlayText': 'REDACTED',
                                                              'textColor': '#FFFFFF'
                                                            }
                                                          },
                                                          {
                                                            'caseSensitive': True,
                                                            'start': 2,
                                                            'limit': 5
                                                          }
                                                          ))
```

##### `BuildActions.create_redactions_regex(regex, options?, strategy_options?)`
Creates an action to add redaction annotations based on regex pattern matching.

**Parameters:**
- `regex: str` - Regex pattern to search and redact.
- `options: BaseCreateRedactionsOptions | None` - Redaction options (optional):
  - `content: RedactionAnnotation` - Visual aspects of the redaction annotation (background color, overlay text, etc.)
- `strategy_options: CreateRedactionsStrategyOptionsRegex | None` - Redaction strategy options (optional):
  - `includeAnnotations: bool` - If True, redaction annotations are created on top of annotations whose content match the provided regex (default: True)
  - `caseSensitive: bool` - If True, the search will be case sensitive (default: True)
  - `start: int` - The index of the page from where to start the search (default: 0)
  - `limit: int` - Starting from start, the number of pages to search (default: to the end of the document)

**Example:**

```python
# Create redactions for email addresses
workflow.apply_action(BuildActions.create_redactions_regex(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'))

# Create redactions with custom appearance and search options
workflow.apply_action(BuildActions.create_redactions_regex(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                                                           {
                                                             'content': {
                                                               'backgroundColor': '#FF0000',
                                                               'overlayText': 'EMAIL REDACTED'
                                                             }
                                                           },
                                                           {
                                                             'caseSensitive': False,
                                                             'start': 0,
                                                             'limit': 10
                                                           }
                                                           ))
```

##### `BuildActions.create_redactions_preset(preset, options?, strategy_options?)`
Creates an action to add redaction annotations based on a preset pattern.

**Parameters:**
- `preset: str` - Preset pattern to search and redact (e.g. 'email-address', 'credit-card-number', 'social-security-number', etc.)
- `options: BaseCreateRedactionsOptions | None` - Redaction options (optional):
  - `content: RedactionAnnotation` - Visual aspects of the redaction annotation (background color, overlay text, etc.)
- `strategy_options: CreateRedactionsStrategyOptionsPreset | None` - Redaction strategy options (optional):
  - `includeAnnotations: bool` - If True, redaction annotations are created on top of annotations whose content match the provided preset (default: True)
  - `start: int` - The index of the page from where to start the search (default: 0)
  - `limit: int` - Starting from start, the number of pages to search (default: to the end of the document)

**Example:**

```python
# Create redactions for email addresses using preset
workflow.apply_action(BuildActions.create_redactions_preset('email-address'))

# Create redactions for credit card numbers with custom appearance
workflow.apply_action(BuildActions.create_redactions_preset('credit-card-number',
                                                            {
                                                              'content': {
                                                                'backgroundColor': '#000000',
                                                                'overlayText': 'FINANCIAL DATA'
                                                              }
                                                            },
                                                            {
                                                              'start': 0,
                                                              'limit': 5
                                                            }
                                                            ))
```

##### `BuildActions.apply_redactions()`
Creates an action to apply previously created redaction annotations, permanently removing the redacted content.

**Example:**

```python
# First create redactions
workflow.apply_action(BuildActions.create_redactions_preset('email-address'))

# Then apply them
workflow.apply_action(BuildActions.apply_redactions())
```

### Stage 3: Set Output Format

In this stage, you specify the desired output format:

```python
workflow.output_pdf({
    'optimize': {
        'mrcCompression': True,
        'imageOptimizationQuality': 2
    }
})
```

Available methods:

#### `output_pdf(options?)`
Sets the output format to PDF.

**Parameters:**
- `options: dict[str, Any] | None` - Additional options for PDF output, such as compression, encryption, etc. (optional)
  - `options['metadata']: dict[str, Any]` - Document metadata properties like title, author.
  - `options['labels']: list[dict[str, Any]]` - Custom labels to add to the document for organization and categorization.
  - `options['user_password']: str` - Password required to open the document. When set, the PDF will be encrypted.
  - `options['owner_password']: str` - Password required to modify the document. Provides additional security beyond the user password.
  - `options['user_permissions']: list[str]` - List of permissions granted to users who open the document with the user password.
    Options include: "printing", "modification", "content-copying", "annotation", "form-filling", etc.
  - `options['optimize']: dict[str, Any]` - PDF optimization settings to reduce file size and improve performance.
    - `options['optimize']['mrcCompression']: bool` - When True, applies Mixed Raster Content compression to reduce file size.
    - `options['optimize']['imageOptimizationQuality']: int` - Controls the quality of image optimization (1-5, where 1 is highest quality).

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to PDF with default options
workflow.output_pdf()

# Set output format to PDF with specific options
workflow.output_pdf({
    'user_password': 'secret',
    'user_permissions': ["printing"],
    'metadata': {
        'title': 'Important Document',
        'author': 'Document System'
    },
    'optimize': {
        'mrcCompression': True,
        'imageOptimizationQuality': 3
    }
})
```

#### `output_pdfa(options?)`
Sets the output format to PDF/A (archival PDF).

**Parameters:**
- `options: dict[str, Any] | None` - Additional options for PDF/A output (optional):
  - `options['conformance']: str` - The PDF/A conformance level to target. Options include 'pdfa-1b', 'pdfa-1a', 'pdfa-2b', 'pdfa-2a', 'pdfa-3b', 'pdfa-3a'.
    Different levels have different requirements for long-term archiving.
  - `options['vectorization']: bool` - When True, attempts to convert raster content to vector graphics where possible, improving quality and reducing file size.
  - `options['rasterization']: bool` - When True, converts vector graphics to raster images, which can help with compatibility in some cases.
  - `options['metadata']: dict[str, Any]` - Document metadata properties like title, author.
  - `options['labels']: list[dict[str, Any]]` - Custom labels to add to the document for organization and categorization.
  - `options['user_password']: str` - Password required to open the document. When set, the PDF will be encrypted.
  - `options['owner_password']: str` - Password required to modify the document. Provides additional security beyond the user password.
  - `options['user_permissions']: list[str]` - List of permissions granted to users who open the document with the user password.
    Options include: "printing", "modification", "content-copying", "annotation", "form-filling", etc.
  - `options['optimize']: dict[str, Any]` - PDF optimization settings to reduce file size and improve performance.
    - `options['optimize']['mrcCompression']: bool` - When True, applies Mixed Raster Content compression to reduce file size.
    - `options['optimize']['imageOptimizationQuality']: int` - Controls the quality of image optimization (1-5, where 1 is highest quality).

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to PDF/A with default options
workflow.output_pdfa()

# Set output format to PDF/A with specific options
workflow.output_pdfa({
    'conformance': 'pdfa-2b',
    'vectorization': True,
    'metadata': {
        'title': 'Archive Document',
        'author': 'Document System'
    },
    'optimize': {
        'mrcCompression': True
    }
})
```

#### `output_pdfua(options?)`
Sets the output format to PDF/UA (Universal Accessibility).

**Parameters:**
- `options: dict[str, Any] | None` - Additional options for PDF/UA output (optional):
  - `options['metadata']: dict[str, Any]` - Document metadata properties like title, author.
  - `options['labels']: list[dict[str, Any]]` - Custom labels to add to the document for organization and categorization.
  - `options['user_password']: str` - Password required to open the document. When set, the PDF will be encrypted.
  - `options['owner_password']: str` - Password required to modify the document. Provides additional security beyond the user password.
  - `options['user_permissions']: list[str]` - List of permissions granted to users who open the document with the user password.
    Options include: "printing", "modification", "content-copying", "annotation", "form-filling", etc.
  - `options['optimize']: dict[str, Any]` - PDF optimization settings to reduce file size and improve performance.
    - `options['optimize']['mrcCompression']: bool` - When True, applies Mixed Raster Content compression to reduce file size.
    - `options['optimize']['imageOptimizationQuality']: int` - Controls the quality of image optimization (1-5, where 1 is highest quality).

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to PDF/UA with default options
workflow.output_pdfua()

# Set output format to PDF/UA with specific options
workflow.output_pdfua({
    'metadata': {
        'title': 'Accessible Document',
        'author': 'Document System'
    },
    'optimize': {
        'mrcCompression': True,
        'imageOptimizationQuality': 3
    }
})
```

#### `output_image(format, options?)`
Sets the output format to an image format (PNG, JPEG, WEBP).

**Parameters:**
- `format: Literal['png', 'jpeg', 'jpg', 'webp']` - The image format to output.
  - PNG: Lossless compression, supports transparency, best for graphics and screenshots
  - JPEG/JPG: Lossy compression, smaller file size, best for photographs
  - WEBP: Modern format with both lossy and lossless compression, good for web use
- `options: dict[str, Any] | None` - Additional options for image output, such as resolution, quality, etc. (optional)
  **Note: At least one of options['width'], options['height'], or options['dpi'] must be specified.**
  - `options['pages']: dict[str, int]` - Specifies which pages to convert to images. If omitted, all pages are converted.
    - `options['pages']['start']: int` - The first page to convert (0-based index).
    - `options['pages']['end']: int` - The last page to convert (0-based index).
  - `options['width']: int` - The width of the output image in pixels. If specified without height, aspect ratio is maintained.
  - `options['height']: int` - The height of the output image in pixels. If specified without width, aspect ratio is maintained.
  - `options['dpi']: int` - The resolution in dots per inch. Higher values create larger, more detailed images.
    Common values: 72 (web), 150 (standard), 300 (print quality), 600 (high quality).

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to PNG with dpi specified
workflow.output_image('png', {'dpi': 300})

# Set output format to JPEG with specific options
workflow.output_image('jpeg', {
    'dpi': 300,
    'pages': {'start': 1, 'end': 3}
})

# Set output format to WEBP with specific dimensions
workflow.output_image('webp', {
    'width': 1200,
    'height': 800,
    'dpi': 150
})
```

#### `output_office(format)`
Sets the output format to an Office document format (DOCX, XLSX, PPTX).

**Parameters:**
- `format: Literal['docx', 'xlsx', 'pptx']` - The Office format to output ('docx' for Word, 'xlsx' for Excel, or 'pptx' for PowerPoint).

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to Word document (DOCX)
workflow.output_office('docx')

# Set output format to Excel spreadsheet (XLSX)
workflow.output_office('xlsx')

# Set output format to PowerPoint presentation (PPTX)
workflow.output_office('pptx')
```

#### `output_html(layout)`
Sets the output format to HTML.

**Parameters:**
- `layout: Literal['page', 'reflow']` - The layout type to use for conversion to HTML:
  - 'page' layout keeps the original structure of the document, segmented by page.
  - 'reflow' layout converts the document into a continuous flow of text, without page breaks.

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to HTML
workflow.output_html('page')
```

#### `output_markdown()`
Sets the output format to Markdown.

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to Markdown with default options
workflow.output_markdown()
```

#### `output_json(options?)`
Sets the output format to JSON content.

**Parameters:**
- `options: dict[str, Any] | None` - Additional options for JSON output (optional):
  - `options['plainText']: bool` - When True, extracts plain text content from the document and includes it in the JSON output.
    This provides the raw text without structural information.
  - `options['structuredText']: bool` - When True, extracts text with structural information (paragraphs, headings, etc.)
    and includes it in the JSON output.
  - `options['keyValuePairs']: bool` - When True, attempts to identify and extract key-value pairs from the document
    (like form fields, labeled data, etc.) and includes them in the JSON output.
  - `options['tables']: bool` - When True, attempts to identify and extract tabular data from the document
    and includes it in the JSON output as structured table objects.
  - `options['language']: str | list[str]` - Specifies the language(s) of the document content for better text extraction.
    Can be a single language code or a list of language codes for multi-language documents.
    Examples: "english", "french", "german", or ["english", "spanish"].

**Returns:** `WorkflowWithOutputStage` - The workflow builder instance for method chaining.

**Example:**
```python
# Set output format to JSON with default options
workflow.output_json()

# Set output format to JSON with specific options
workflow.output_json({
    'plainText': True,
    'structuredText': True,
    'keyValuePairs': True,
    'tables': True,
    'language': "english"
})

# Set output format to JSON with multiple languages
workflow.output_json({
    'plainText': True,
    'tables': True,
    'language': ["english", "french", "german"]
})
```

### Stage 4: Execute or Dry Run

In this final stage, you execute the workflow or perform a dry run:

```python
result = await workflow.execute()
```

Available methods:

#### `execute(options?)`
Executes the workflow and returns the result.

**Parameters:**
- `on_progress: Callable[[int, int], None] | None` - Callback for progress updates (optional).

**Returns:** `TypedWorkflowResult` - The workflow result.

**Example:**
```python
# Execute the workflow with default options
result = await workflow.execute()

# Execute with progress tracking
def progress_callback(current: int, total: int) -> None:
    print(f'Processing step {current} of {total}')

result = await workflow.execute(on_progress=progress_callback)
```

#### `dry_run(options?)`
Performs a dry run of the workflow without generating the final output. This is useful for validating the workflow configuration and estimating processing time.

**Returns:** `WorkflowDryRunResult` - The dry run result, containing validation information and estimated processing time.

**Example:**
```python
# Perform a dry run with default options
dry_run_result = await (workflow
    .add_file_part('/path/to/document.pdf')
    .output_pdf()
    .dry_run())
```

### Workflow Examples

#### Basic Document Conversion

```python
result = await (client
    .workflow()
    .add_file_part('document.docx')
    .output_pdf()
    .execute())
```

#### Document Merging with Watermark

```python
result = await (client
                .workflow()
                .add_file_part('document1.pdf')
                .add_file_part('document2.pdf')
                .apply_action(BuildActions.watermark_text('CONFIDENTIAL', {
  'opacity': 0.5,
  'fontSize': 48
}))
                .output_pdf()
                .execute())
```

#### OCR with Language Selection

```python
result = await (client
    .workflow()
    .add_file_part('scanned-document.pdf')
    .apply_action(BuildActions.ocr({
        'language': 'english',
        'enhanceResolution': True
    }))
    .output_pdf()
    .execute())
```

#### HTML to PDF Conversion

```python
result = await (client
    .workflow()
    .add_html_part('index.html', None, {
        'layout': {
            'size': 'A4',
            'margin': {
                'top': 50,
                'bottom': 50,
                'left': 50,
                'right': 50
            }
        }
    })
    .output_pdf()
    .execute())
```

#### Complex Multi-step Workflow

```python
def progress_callback(current: int, total: int) -> None:
  print(f'Processing step {current} of {total}')


result = await (client
                .workflow()
                .add_file_part('document.pdf', {'pages': {'start': 0, 'end': 5}})
                .add_file_part('appendix.pdf')
                .apply_actions([
  BuildActions.ocr({'language': 'english'}),
  BuildActions.watermark_text('CONFIDENTIAL'),
  BuildActions.create_redactions_preset('email-address', 'apply')
])
                .output_pdfa({
  'level': 'pdfa-2b',
  'optimize': {
    'mrcCompression': True
  }
})
                .execute(on_progress=progress_callback))
```

### Staged Workflow Builder

For more complex scenarios where you need to build workflows dynamically, you can use the staged workflow builder:

```python
# Create a staged workflow
workflow = client.workflow()

# Add parts
workflow.add_file_part('document.pdf')

# Conditionally add more parts
if include_appendix:
  workflow.add_file_part('appendix.pdf')

# Conditionally apply actions
if needs_watermark:
  workflow.apply_action(BuildActions.watermark_text('CONFIDENTIAL'))

# Set output format based on user preference
if output_format == 'pdf':
  workflow.output_pdf()
elif output_format == 'docx':
  workflow.output_office('docx')
else:
  workflow.output_image('png')

# Execute the workflow
result = await workflow.execute()
```

### Error Handling in Workflows

Workflows provide detailed error information:

```python
try:
    result = await (client
        .workflow()
        .add_file_part('document.pdf')
        .output_pdf()
        .execute())

    if not result['success']:
        # Handle workflow errors
        for error in result.get('errors', []):
            print(f"Step {error['step']}: {error['error']['message']}")
except Exception as error:
    # Handle unexpected errors
    print(f'Workflow execution failed: {error}')
```

### Workflow Result Structure

The result of a workflow execution includes:

```python
from typing import TypedDict, Any, List, Optional, Union

class WorkflowError(TypedDict):
    step: str
    error: dict[str, Any]

class BufferOutput(TypedDict):
    mimeType: str
    filename: str
    buffer: bytes

class ContentOutput(TypedDict):
    mimeType: str
    filename: str
    content: str

class JsonContentOutput(TypedDict):
    mimeType: str
    filename: str
    data: Any

class WorkflowResult(TypedDict):
    # Overall success status
    success: bool

    # Output data (if successful)
    output: Optional[Union[BufferOutput, ContentOutput, JsonContentOutput]]

    # Error information (if failed)
    errors: Optional[List[WorkflowError]]
```

### Performance Considerations

For optimal performance with workflows:

1. **Minimize the number of parts**: Combine related files when possible
2. **Use appropriate output formats**: Choose formats based on your needs
3. **Consider dry runs**: Use `dry_run()` to estimate resource usage
4. **Monitor progress**: Use the `on_progress` callback for long-running workflows
5. **Handle large files**: For very large files, consider splitting into smaller workflows
