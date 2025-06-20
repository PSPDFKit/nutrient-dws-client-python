# Feature: Convert to PDF/A Method

## Summary
Implement `convert_to_pdfa()` to convert PDFs to PDF/A archival format for long-term preservation and compliance.

## Proposed Implementation
```python
def convert_to_pdfa(
    self,
    input_file: FileInput,
    output_path: Optional[str] = None,
    conformance: Literal["pdfa-1a", "pdfa-1b", "pdfa-2a", "pdfa-2u", "pdfa-2b", "pdfa-3a", "pdfa-3u"] = "pdfa-2b",
    vectorization: bool = True,
    rasterization: bool = True,
) -> Optional[bytes]:
```

## Benefits
- Long-term archival compliance (ISO 19005)
- Legal and regulatory requirement fulfillment
- Guaranteed font embedding
- Self-contained documents
- Multiple conformance levels for different needs

## Implementation Details
- Use Build API with output type: `pdfa`
- Support all PDF/A conformance levels
- Provide sensible defaults (PDF/A-2b most common)
- Handle vectorization/rasterization options
- Clear error messages for conversion failures

## Testing Requirements
- [ ] Test each conformance level
- [ ] Test vectorization on/off
- [ ] Test rasterization on/off
- [ ] Test with complex PDFs (forms, multimedia)
- [ ] Verify output is valid PDF/A
- [ ] Test conversion failures gracefully

## OpenAPI Reference
- Output type: `pdfa`
- Conformance levels: pdfa-1a, pdfa-1b, pdfa-2a, pdfa-2u, pdfa-2b, pdfa-3a, pdfa-3u
- Options: vectorization (default: true), rasterization (default: true)

## Use Case Example
```python
# Convert for long-term archival (most permissive)
archived_pdf = client.convert_to_pdfa(
    "document.pdf",
    conformance="pdfa-2b"
)

# Convert for accessibility compliance (strictest)
accessible_pdf = client.convert_to_pdfa(
    "document.pdf",
    conformance="pdfa-2a",
    output_path="archived_accessible.pdf"
)
```

## Conformance Level Guide
- **PDF/A-1a**: Level A compliance, accessibility features required
- **PDF/A-1b**: Level B compliance, visual appearance preservation
- **PDF/A-2a/2b**: Based on PDF 1.7, more features allowed
- **PDF/A-2u**: Unicode mapping required
- **PDF/A-3a/3u**: Allows embedded files

## Priority
🟡 Priority 3 - Format conversion method

## Labels
- feature
- conversion
- compliance
- archival
- openapi-compliance