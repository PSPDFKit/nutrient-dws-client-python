# Nutrient DWS Python Client Methods

This document provides detailed information about all the methods available in the Nutrient DWS Python Client.

## Client Methods

### NutrientClient

The main client for interacting with the Nutrient DWS Processor API.

#### Constructor

```python
NutrientClient(options: NutrientClientOptions)
```

Options:
- `apiKey` (required): Your API key string or async function returning a token
- `baseUrl` (optional): Custom API base URL (defaults to `https://api.nutrient.io`)
- `timeout` (optional): Request timeout in milliseconds

#### Account Methods

##### get_account_info()
Gets account information for the current API key.

**Returns**: `AccountInfo` - Account information dictionary

```python
account_info = await client.get_account_info()

# Access subscription information
print(account_info['subscriptionType'])
```

##### create_token(params)
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

##### delete_token(id)
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

#### Document Processing Methods

##### sign(file, data?, options?)
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

##### create_redactions_ai(file, criteria, redaction_state?, pages?, options?)
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

##### ocr(file, language)
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

##### watermark_text(file, text, options?)
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

##### watermark_image(file, image, options?)
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

##### convert(file, target_format)
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

##### merge(files)
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

##### extract_text(file, pages?)
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

##### extract_table(file, pages?)
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

##### extract_key_value_pairs(file, pages?)
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

##### flatten(file, annotation_ids?)
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

##### password_protect(file, user_password, owner_password, permissions?)
Password protects a PDF document.

**Parameters**:
- `file: FileInput` - The file to protect
- `user_password: str` - Password required to open the document
- `owner_password: str` - Password required to modify the document
- `permissions: list[PDFUserPermission] | None` - Optional array of permissions granted when opened with user password

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

##### set_metadata(file, metadata)
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

## Workflow Builder Methods

The workflow builder provides a fluent interface for chaining multiple operations. See [WORKFLOW.md](./WORKFLOW.md) for detailed information about workflow methods including:

- `workflow()` - Create a new workflow builder
- `add_file_part()` - Add file parts to the workflow
- `add_html_part()` - Add HTML content
- `apply_action()` - Apply processing actions
- `output_pdf()`, `output_image()`, `output_json()` - Set output formats
- `execute()` - Execute the workflow

## Error Handling

All methods can raise the following exceptions:

- `ValidationError` - Invalid input parameters
- `AuthenticationError` - Authentication failed
- `APIError` - API returned an error
- `NetworkError` - Network request failed
- `NutrientError` - Base error class

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
    print(f'Invalid input: {error.message} - Details: {error.details}')
except AuthenticationError as error:
    print(f'Auth error: {error.message} - Status: {error.status_code}')
except APIError as error:
    print(f'API error: {error.message} - Status: {error.status_code} - Details: {error.details}')
except NetworkError as error:
    print(f'Network error: {error.message} - Details: {error.details}')
```
