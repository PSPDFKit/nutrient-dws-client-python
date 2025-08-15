"""Test utilities and helpers for Nutrient DWS Python Client tests."""
from datetime import datetime, timezone
import json
from typing import Any, Optional, TypedDict, Literal, List
from pathlib import Path

class XfdfAnnotation(TypedDict):
    type: Literal['highlight', 'text', 'square', 'circle']
    page: int
    rect: List[int]
    content: Optional[str]
    color: Optional[str]

class TestDocumentGenerator:
    """Generate test documents and content for testing purposes."""

    @staticmethod
    def generate_simple_pdf_content(content: str = "Test PDF Document") -> bytes:
        """Generate a simple PDF-like content for testing.

        Note: This is not a real PDF, just bytes that can be used for testing file handling.
        """
        pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>/Contents 4 0 R>>endobj
4 0 obj<</Length {len(content) + 30}>>stream
BT /F1 12 Tf 100 700 Td ({content}) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000262 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
356
%%EOF"""
        return pdf.encode("utf-8")

    @staticmethod
    def generate_pdf_with_sensitive_data() -> bytes:
        """Generate PDF-like content with sensitive data patterns for redaction testing."""
        content = f"""Personal Information:
Name: John Doe
SSN: 123-45-6789
Email: john.doe@example.com
Phone: (555) 123-4567
Credit Card: 4111-1111-1111-1111
Medical Record: MR-2024-12345
License: DL-ABC-123456"""
        return TestDocumentGenerator.generate_simple_pdf_content(content)

    @staticmethod
    def generate_pdf_with_table() -> bytes:
        """Generate PDF-like content with table data patterns"""
        content = f"""Sales Report 2024
Product | Q1 | Q2 | Q3 | Q4
Widget A | 100 | 120 | 140 | 160
Widget B | 80 | 90 | 100 | 110
Widget C | 60 | 70 | 80 | 90"""
        return TestDocumentGenerator.generate_simple_pdf_content(content)

    @staticmethod
    def generate_html_content(title: str = "Test Document", include_styles: bool = True, include_table: bool = False, include_images: bool = False, include_form: bool = False) -> bytes:
        """Generate HTML content for testing."""

        styles = """<style>
body {
    font-family: Arial, sans-serif;
    margin: 40px;
    line-height: 1.6;
}
h1 {
    color: #333;
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
}
.highlight {
    background-color: #ffeb3b;
    padding: 2px 4px;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
th {
    background-color: #f4f4f4;
}
.form-group {
    margin-bottom: 15px;
}
label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}
input, select, textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}
</style>""" if include_styles else ""
        tables = """<h2>Data Table</h2>
<table>
    <thead>
        <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Quantity</th>
            <th>Total</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Widget A</td>
            <td>$10.00</td>
            <td>5</td>
            <td>$50.00</td>
        </tr>
        <tr>
            <td>Widget B</td>
            <td>$15.00</td>
            <td>3</td>
            <td>$45.00</td>
        </tr>
        <tr>
            <td>Widget C</td>
            <td>$20.00</td>
            <td>2</td>
            <td>$40.00</td>
        </tr>
    </tbody>
</table>""" if include_table else ""
        images = """<h2>Images</h2>
<p>Below is a placeholder for image content:</p>
<div style="width: 200px; height: 200px; background-color: #e0e0e0; display: flex; align-items: center; justify-content: center; margin: 20px 0;">
    <span style="color: #666;">Image Placeholder</span>
</div>""" if include_images else ""
        form = """<h2>Form Example</h2>
<form>
    <div class="form-group">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" placeholder="Enter your name">
    </div>
    <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" placeholder="Enter your email">
    </div>
    <div class="form-group">
        <label for="message">Message:</label>
        <textarea id="message" name="message" rows="4" placeholder="Enter your message"></textarea>
    </div>
</form>""" if include_form else ""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>{styles}
</head>
<body>
    <h1>{title}</h1>
    <p>This is a test document with <span class="highlight">highlighted text</span> for PDF conversion testing.</p>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
    {tables}{images}{form}
</body>
</html>"""
        return html.encode("utf-8")

    @staticmethod
    def generate_xfdf_content(annotations: Optional[list[XfdfAnnotation]] = None) -> bytes:
        """Generate XFDF annotation content."""

        if annotations is None:
            annotations = [
                {
                    "type": 'highlight',
                    "page": 0,
                    "rect": [100, 100, 200, 150],
                    "color": '#FFFF00',
                    "content": 'Important text',
                },
            ]

        inner_xfdf = ""

        for annot in annotations:
            rectStr = ",".join([str(x) for x in annot["rect"]])
            color = annot["color"] or "#FFFF00"
            if annot["type"] == "highlight":
                inner_xfdf = f"""<highlight page="${annot["page"]}" rect="${rectStr}" color="${color}">
                            <contents>${annot.get("content", 'Highlighted text')}</contents>
                        </highlight>"""
            elif annot["type"] == "text":
                inner_xfdf = f"""<text page="${annot["page"]}" rect="${rectStr}" color="${color}">
                            <contents>${annot.get("content", 'Note')}</contents>
                        </text>"""
            elif annot["type"] == "square":
                inner_xfdf = f"""<square page="{annot["page"]}" rect="{rectStr}" color="{color}" />"""
            elif annot["type"] == "circle":
                inner_xfdf = f"""<circle page="{annot["page"]}" rect="{rectStr}" color="{color}" />"""

        xfdf = f"""<?xml version="1.0" encoding="UTF-8"?>
<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
    <annots>
    {inner_xfdf}
    </annots>
</xfdf>"""

        return xfdf.encode("utf-8")

    @staticmethod
    def generate_instant_json_content(annotations: Optional[list] = None) -> bytes:
        """Generate Instant JSON annotation content."""
        annotations = annotations or [{
        "v": 2,
        "type": 'pspdfkit/text',
        "pageIndex": 0,
        "bbox": [100, 100, 200, 150],
        "content": 'Test annotation',
        "fontSize": 14,
        "opacity": 1,
        "horizontalAlign": 'left',
        "verticalAlign": 'top',
      }]
        instant_data = {
            "format": "https://pspdfkit.com/instant-json/v1",
            "annotations": [],
        }

        for i, annotation in enumerate(annotations):
            instant_data["annotations"].append(
                {
                    **annotation,
                    "id": f"annotation_{i}",
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                }
            )

        return json.dumps(instant_data).encode("utf-8")


class ResultValidator:
    """Validate test results and outputs."""

    @staticmethod
    def validate_pdf_output(result: Any) -> None:
        """Validates that the result contains a valid PDF"""
        if not isinstance(result, dict):
            raise ValueError("Result must be a dictionary")

        if "success" not in result:
            raise ValueError("Result must have success property")
        if not result.get("success") or "output" not in result:
            raise ValueError("Result must be successful with output")

        output = result["output"]
        if not isinstance(output.get("buffer"), (bytes, bytearray)):
            raise ValueError("Output buffer must be bytes or bytearray")
        if output.get("mimeType") != "application/pdf":
            raise ValueError("Output must be PDF")
        if len(output["buffer"]) == 0:
            raise ValueError("Output buffer cannot be empty")

        # Check PDF header
        header = output["buffer"][:5].decode(errors="ignore")
        if not header.startswith("%PDF-"):
            raise ValueError("Invalid PDF header")

    @staticmethod
    def validate_office_output(
            result: Any, format: Literal["docx", "xlsx", "pptx"]
    ) -> None:
        """Validates Office document output"""
        mime_types = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }

        if not isinstance(result, dict) or not result.get("success") or "output" not in result:
            raise ValueError("Result must be successful with output")

        output = result["output"]
        if not isinstance(output.get("buffer"), (bytes, bytearray)):
            raise ValueError("Output buffer must be bytes or bytearray")
        if len(output["buffer"]) == 0:
            raise ValueError("Output buffer cannot be empty")
        if output.get("mimeType") != mime_types[format]:
            raise ValueError(f"Expected {format} MIME type")

    @staticmethod
    def validate_image_output(
        result: Any, format: Literal["png", "jpeg", "jpg", "webp"] | None = None
    ) -> None:
        """Validates image output"""
        if not isinstance(result, dict) or not result.get("success") or "output" not in result:
            raise ValueError("Result must be successful with output")

        output = result["output"]
        if not isinstance(output.get("buffer"), (bytes, bytearray)):
            raise ValueError("Output buffer must be bytes or bytearray")
        if len(output["buffer"]) == 0:
            raise ValueError("Output buffer cannot be empty")

        if format:
            format_mime_types = {
                "png": ["image/png"],
                "jpg": ["image/jpeg"],
                "jpeg": ["image/jpeg"],
                "webp": ["image/webp"],
            }
            valid_mimes = format_mime_types.get(format, [f"image/{format}"])
            if output.get("mimeType") not in valid_mimes:
                raise ValueError(f"Expected format {format}, got {output.get('mimeType')}")
        else:
            if not isinstance(output.get("mimeType"), str) or not output["mimeType"].startswith("image/"):
                raise ValueError("Expected image MIME type")

    @staticmethod
    def validate_json_output(result: Any) -> None:
        """Validates JSON extraction output"""
        if not isinstance(result, dict) or not result.get("success") or "output" not in result:
            raise ValueError("Result must be successful with output")

        output = result["output"]
        if "data" not in output:
            raise ValueError("Output must have data property")
        if not isinstance(output["data"], dict):
            raise ValueError("Output data must be an object")

    @staticmethod
    def validate_error_response(result: Any, expected_error_type: str | None = None) -> None:
        """Validates error response"""
        if not isinstance(result, dict):
            raise ValueError("Result must be a dictionary")

        if result.get("success"):
            raise ValueError("Result should not be successful")
        if not isinstance(result.get("errors"), list):
            raise ValueError("Result must have errors array")
        if len(result["errors"]) == 0:
            raise ValueError("Errors array cannot be empty")

        if expected_error_type:
            has_expected_error = any(
                isinstance(e, dict)
                and "error" in e
                and (
                    e["error"].get("name") == expected_error_type
                    or e["error"].get("code") == expected_error_type
                )
                for e in result["errors"]
            )
            if not has_expected_error:
                raise ValueError(f"Expected error type {expected_error_type} not found")


sample_pdf = Path(__file__).parent.joinpath("data", "sample.pdf").read_bytes()

sample_docx = Path(__file__).parent.joinpath("data", "sample.docx").read_bytes()

sample_png = Path(__file__).parent.joinpath("data", "sample.png").read_bytes()
