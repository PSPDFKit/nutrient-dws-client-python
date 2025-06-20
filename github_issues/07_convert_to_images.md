# Feature: Convert PDF to Images Method

## Summary
Implement `convert_to_images()` to extract PDF pages as image files in various formats.

## Proposed Implementation
```python
def convert_to_images(
    self,
    input_file: FileInput,
    output_dir: Optional[str] = None,  # Directory for multiple images
    format: Literal["png", "jpeg", "webp"] = "png",
    pages: Optional[List[int]] = None,  # None means all pages
    width: Optional[int] = None,
    height: Optional[int] = None,
    dpi: int = 150,
) -> Union[List[bytes], None]:  # Returns list of image bytes or None if saved
```

## Benefits
- Generate thumbnails and previews
- Web-friendly image formats
- Flexible resolution control
- Selective page extraction
- Batch image generation

## Implementation Details
- Use Build API with output type: `image`
- Support PNG, JPEG, and WebP formats
- Handle multi-page extraction (returns list)
- Automatic file naming when saving to directory
- Resolution control via width/height/DPI

## Testing Requirements
- [ ] Test PNG format extraction
- [ ] Test JPEG format extraction
- [ ] Test WebP format extraction
- [ ] Test single page extraction
- [ ] Test multi-page extraction
- [ ] Test resolution options (width, height, DPI)
- [ ] Test file saving vs bytes return

## OpenAPI Reference
- Output type: `image`
- Formats: png, jpeg, jpg, webp
- Parameters: width, height, dpi, pages (range)

## Use Case Example
```python
# Extract all pages as PNG thumbnails
thumbnails = client.convert_to_images(
    "document.pdf",
    format="png",
    width=200  # Fixed width, height auto-calculated
)

# Extract specific pages as high-res JPEGs
client.convert_to_images(
    "document.pdf",
    output_dir="./page_images",
    format="jpeg",
    pages=[0, 1, 2],  # First 3 pages
    dpi=300  # High resolution
)

# Generate web-optimized previews
web_images = client.convert_to_images(
    "document.pdf",
    format="webp",
    width=800,
    height=600
)
```

## File Naming Convention
When saving to directory:
- Single page: `{original_name}.{format}`
- Multiple pages: `{original_name}_page_{n}.{format}`

## Priority
🟡 Priority 3 - Format conversion method

## Labels
- feature
- conversion
- images
- thumbnails
- openapi-compliance