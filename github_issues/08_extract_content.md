# Feature: Extract Content as JSON Method

## Summary
Implement `extract_content()` to extract text, tables, and metadata from PDFs as structured JSON data.

## Proposed Implementation
```python
def extract_content(
    self,
    input_file: FileInput,
    extract_text: bool = True,
    extract_tables: bool = True,
    extract_metadata: bool = True,
    extract_structure: bool = False,
    language: Union[str, List[str]] = "english",
    output_path: Optional[str] = None,
) -> Union[Dict[str, Any], None]:
```

## Benefits
- Structured data extraction for analysis
- Table detection and extraction
- Metadata parsing
- Search indexing support
- Machine learning data preparation
- Multi-language text extraction

## Implementation Details
- Use Build API with output type: `json-content`
- Map parameters to OpenAPI options:
  - `plainText`: extract_text
  - `tables`: extract_tables
  - `structuredText`: extract_structure
- Include document metadata in response
- Support OCR for scanned documents

## Testing Requirements
- [ ] Test plain text extraction
- [ ] Test table extraction
- [ ] Test metadata extraction
- [ ] Test structured text extraction
- [ ] Test with multi-language documents
- [ ] Test with scanned documents (OCR)
- [ ] Validate JSON structure

## OpenAPI Reference
- Output type: `json-content`
- Options: plainText, structuredText, tables, keyValuePairs
- Language support for OCR
- Returns structured JSON

## Use Case Example
```python
# Extract everything from a document
content = client.extract_content(
    "report.pdf",
    extract_text=True,
    extract_tables=True,
    extract_metadata=True
)

# Access extracted data
print(content["metadata"]["title"])
print(content["text"])
for table in content["tables"]:
    print(table["data"])

# Extract for multilingual search indexing
search_data = client.extract_content(
    "multilingual.pdf",
    language=["english", "spanish", "french"],
    extract_structure=True
)
```

## Expected JSON Structure
```json
{
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "created": "2024-01-01T00:00:00Z",
    "pages": 10
  },
  "text": "Extracted plain text...",
  "structured_text": {
    "paragraphs": [...],
    "headings": [...]
  },
  "tables": [
    {
      "page": 1,
      "data": [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]]
    }
  ]
}
```

## Priority
🟡 Priority 3 - Format conversion method

## Labels
- feature
- extraction
- data-processing
- json
- openapi-compliance