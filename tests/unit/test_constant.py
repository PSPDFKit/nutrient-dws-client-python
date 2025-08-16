"""Tests for BuildActions and BuildOutputs factory functions."""

import pytest

from nutrient_dws.builder.constant import BuildActions, BuildOutputs
from nutrient_dws.inputs import FileInput


class TestBuildActions:
    """Tests for BuildActions factory functions."""

    def test_ocr_with_single_language(self):
        action = BuildActions.ocr("english")

        assert action == {"type": "ocr", "language": "english"}

    def test_ocr_with_multiple_languages(self):
        languages = ["english", "spanish"]
        action = BuildActions.ocr(languages)

        assert action == {"type": "ocr", "language": ["english", "spanish"]}

    def test_rotate_90_degrees(self):
        action = BuildActions.rotate(90)

        assert action == {"type": "rotate", "rotateBy": 90}

    def test_rotate_180_degrees(self):
        action = BuildActions.rotate(180)

        assert action == {"type": "rotate", "rotateBy": 180}

    def test_rotate_270_degrees(self):
        action = BuildActions.rotate(270)

        assert action == {"type": "rotate", "rotateBy": 270}

    def test_watermark_text_with_minimal_options(self):
        default_dimensions = {
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
        }

        action = BuildActions.watermark_text("CONFIDENTIAL", default_dimensions)

        assert action == {
            "type": "watermark",
            "text": "CONFIDENTIAL",
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
            "rotation": 0,
        }

    def test_watermark_text_with_all_options(self):
        options = {
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
            "opacity": 0.5,
            "rotation": 45,
            "fontSize": 24,
            "fontColor": "#ff0000",
            "fontFamily": "Arial",
            "fontStyle": ["bold", "italic"],
            "top": {"value": 10, "unit": "pt"},
            "left": {"value": 20, "unit": "pt"},
            "right": {"value": 30, "unit": "pt"},
            "bottom": {"value": 40, "unit": "pt"},
        }

        action = BuildActions.watermark_text("DRAFT", options)

        assert action == {
            "type": "watermark",
            "text": "DRAFT",
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
            "opacity": 0.5,
            "rotation": 45,
            "fontSize": 24,
            "fontColor": "#ff0000",
            "fontFamily": "Arial",
            "fontStyle": ["bold", "italic"],
            "top": {"value": 10, "unit": "pt"},
            "left": {"value": 20, "unit": "pt"},
            "right": {"value": 30, "unit": "pt"},
            "bottom": {"value": 40, "unit": "pt"},
        }

    def test_watermark_image_with_minimal_options(self):
        image = "logo.png"
        default_dimensions = {
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
        }

        action = BuildActions.watermark_image(image, default_dimensions)

        # Check that action requires file registration by having fileInput and createAction method
        assert hasattr(action, "fileInput")
        assert hasattr(action, "createAction")
        assert action.fileInput == "logo.png"

        result = action.createAction("asset_0")
        assert result == {
            "type": "watermark",
            "image": "asset_0",
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
            "rotation": 0,
        }

    def test_watermark_image_with_all_options(self):
        image = "watermark.png"
        options = {
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
            "opacity": 0.3,
            "rotation": 30,
            "top": {"value": 10, "unit": "pt"},
            "left": {"value": 20, "unit": "pt"},
            "right": {"value": 30, "unit": "pt"},
            "bottom": {"value": 40, "unit": "pt"},
        }

        action = BuildActions.watermark_image(image, options)

        # Check that action requires file registration by having fileInput and createAction method
        assert hasattr(action, "fileInput")
        assert hasattr(action, "createAction")
        assert action.fileInput == "watermark.png"

        result = action.createAction("asset_0")
        assert result == {
            "type": "watermark",
            "image": "asset_0",
            "width": {"value": 100, "unit": "%"},
            "height": {"value": 100, "unit": "%"},
            "opacity": 0.3,
            "rotation": 30,
            "top": {"value": 10, "unit": "pt"},
            "left": {"value": 20, "unit": "pt"},
            "right": {"value": 30, "unit": "pt"},
            "bottom": {"value": 40, "unit": "pt"},
        }

    def test_flatten_without_annotation_ids(self):
        action = BuildActions.flatten()

        assert action == {"type": "flatten"}

    def test_flatten_with_annotation_ids(self):
        annotation_ids = ["ann1", "ann2", 123]
        action = BuildActions.flatten(annotation_ids)

        assert action == {"type": "flatten", "annotationIds": ["ann1", "ann2", 123]}

    def test_apply_instant_json(self):
        file: FileInput = "annotations.json"
        action = BuildActions.apply_instant_json(file)

        # Check that action requires file registration by having fileInput and createAction method
        assert hasattr(action, "fileInput")
        assert hasattr(action, "createAction")
        assert action.fileInput == "annotations.json"

        result = action.createAction("asset_0")
        assert result == {"type": "applyInstantJson", "file": "asset_0"}

    def test_apply_xfdf(self):
        file: FileInput = "annotations.xfdf"
        action = BuildActions.apply_xfdf(file)

        # Check that action requires file registration by having fileInput and createAction method
        assert hasattr(action, "fileInput")
        assert hasattr(action, "createAction")
        assert action.fileInput == "annotations.xfdf"

        result = action.createAction("asset_1")
        assert result == {"type": "applyXfdf", "file": "asset_1"}

    def test_apply_redactions(self):
        action = BuildActions.apply_redactions()

        assert action == {"type": "applyRedactions"}

    def test_create_redactions_text_with_minimal_options(self):
        text = "confidential"
        action = BuildActions.create_redactions_text(text)

        assert action == {
            "type": "createRedactions",
            "strategy": "text",
            "strategyOptions": {"text": "confidential"},
        }

    def test_create_redactions_text_with_all_options(self):
        text = "secret"
        options = {}
        strategy_options = {"caseSensitive": True, "wholeWord": True}

        action = BuildActions.create_redactions_text(text, options, strategy_options)

        assert action == {
            "type": "createRedactions",
            "strategy": "text",
            "strategyOptions": {
                "text": "secret",
                "caseSensitive": True,
                "wholeWord": True,
            },
        }

    def test_create_redactions_regex_with_minimal_options(self):
        regex = r"\d{3}-\d{2}-\d{4}"
        action = BuildActions.create_redactions_regex(regex)

        assert action == {
            "type": "createRedactions",
            "strategy": "regex",
            "strategyOptions": {"regex": r"\d{3}-\d{2}-\d{4}"},
        }

    def test_create_redactions_regex_with_all_options(self):
        regex = r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"
        options = {}
        strategy_options = {"caseSensitive": False}

        action = BuildActions.create_redactions_regex(regex, options, strategy_options)

        assert action == {
            "type": "createRedactions",
            "strategy": "regex",
            "strategyOptions": {
                "regex": r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
                "caseSensitive": False,
            },
        }

    def test_create_redactions_preset_with_minimal_options(self):
        preset = "date"
        action = BuildActions.create_redactions_preset(preset)

        assert action == {
            "type": "createRedactions",
            "strategy": "preset",
            "strategyOptions": {"preset": "date"},
        }

    def test_create_redactions_preset_with_all_options(self):
        preset = "email-address"
        options = {}
        strategy_options = {"start": 1}

        action = BuildActions.create_redactions_preset(preset, options, strategy_options)

        assert action == {
            "type": "createRedactions",
            "strategy": "preset",
            "strategyOptions": {"preset": "email-address", "start": 1},
        }


class TestBuildOutputs:
    """Tests for BuildOutputs factory functions."""

    def test_pdf_with_no_options(self):
        output = BuildOutputs.pdf()

        assert output == {"type": "pdf"}

    def test_pdf_with_all_options(self):
        options = {
            "metadata": {"title": "Test Document"},
            "labels": [{"pages": [0], "label": "Page I-III"}],
            "user_password": "user123",
            "owner_password": "owner123",
            "user_permissions": ["print"],
            "optimize": {"print": True},
        }

        output = BuildOutputs.pdf(options)

        assert output == {
            "type": "pdf",
            "metadata": {"title": "Test Document"},
            "labels": [{"pages": [0], "label": "Page I-III"}],
            "user_password": "user123",
            "owner_password": "owner123",
            "user_permissions": ["print"],
            "optimize": {"print": True},
        }

    def test_pdfa_with_no_options(self):
        output = BuildOutputs.pdfa()

        assert output == {"type": "pdfa"}

    def test_pdfa_with_all_options(self):
        options = {
            "conformance": "pdfa-1b",
            "vectorization": True,
            "rasterization": False,
            "metadata": {"title": "Test Document"},
            "user_password": "user123",
            "owner_password": "owner123",
        }

        output = BuildOutputs.pdfa(options)

        assert output == {
            "type": "pdfa",
            "conformance": "pdfa-1b",
            "vectorization": True,
            "rasterization": False,
            "metadata": {"title": "Test Document"},
            "user_password": "user123",
            "owner_password": "owner123",
        }

    def test_image_with_default_options(self):
        output = BuildOutputs.image("png")

        assert output == {"type": "image", "format": "png"}

    def test_image_with_custom_options(self):
        options = {"dpi": 300, "pages": {"start": 1, "end": 5}}

        output = BuildOutputs.image("png", options)

        assert output == {
            "type": "image",
            "format": "png",
            "dpi": 300,
            "pages": {"start": 1, "end": 5},
        }

    def test_pdfua_with_no_options(self):
        output = BuildOutputs.pdfua()

        assert output == {"type": "pdfua"}

    def test_pdfua_with_all_options(self):
        options = {
            "metadata": {"title": "Accessible Document"},
            "labels": [{"pages": [0], "label": "Cover Page"}],
            "user_password": "user123",
            "owner_password": "owner123",
            "user_permissions": ["print"],
            "optimize": {"print": True},
        }

        output = BuildOutputs.pdfua(options)

        assert output == {
            "type": "pdfua",
            "metadata": {"title": "Accessible Document"},
            "labels": [{"pages": [0], "label": "Cover Page"}],
            "user_password": "user123",
            "owner_password": "owner123",
            "user_permissions": ["print"],
            "optimize": {"print": True},
        }

    def test_json_content_with_default_options(self):
        output = BuildOutputs.jsonContent()

        assert output == {"type": "json-content"}

    def test_json_content_with_custom_options(self):
        options = {
            "plainText": False,
            "structuredText": True,
            "keyValuePairs": True,
            "tables": False,
            "language": "english",
        }

        output = BuildOutputs.jsonContent(options)

        assert output == {
            "type": "json-content",
            "plainText": False,
            "structuredText": True,
            "keyValuePairs": True,
            "tables": False,
            "language": "english",
        }

    def test_office_docx(self):
        output = BuildOutputs.office("docx")

        assert output == {"type": "docx"}

    def test_office_xlsx(self):
        output = BuildOutputs.office("xlsx")

        assert output == {"type": "xlsx"}

    def test_office_pptx(self):
        output = BuildOutputs.office("pptx")

        assert output == {"type": "pptx"}

    def test_html_with_page_layout(self):
        output = BuildOutputs.html("page")

        assert output == {"type": "html", "layout": "page"}

    def test_html_with_reflow_layout(self):
        output = BuildOutputs.html("reflow")

        assert output == {"type": "html", "layout": "reflow"}

    def test_markdown(self):
        output = BuildOutputs.markdown()

        assert output == {"type": "markdown"}

    def test_get_mime_type_for_pdf_output(self):
        output = BuildOutputs.pdf()
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {"mimeType": "application/pdf", "filename": "output.pdf"}

    def test_get_mime_type_for_pdfa_output(self):
        output = BuildOutputs.pdfa()
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {"mimeType": "application/pdf", "filename": "output.pdf"}

    def test_get_mime_type_for_pdfua_output(self):
        output = BuildOutputs.pdfua()
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {"mimeType": "application/pdf", "filename": "output.pdf"}

    def test_get_mime_type_for_image_output_with_custom_format(self):
        output = BuildOutputs.image("jpeg")
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {"mimeType": "image/jpeg", "filename": "output.jpeg"}

    def test_get_mime_type_for_docx_output(self):
        output = BuildOutputs.office("docx")
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {
            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "filename": "output.docx",
        }

    def test_get_mime_type_for_xlsx_output(self):
        output = BuildOutputs.office("xlsx")
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {
            "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "filename": "output.xlsx",
        }

    def test_get_mime_type_for_pptx_output(self):
        output = BuildOutputs.office("pptx")
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {
            "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "filename": "output.pptx",
        }

    def test_get_mime_type_for_html_output(self):
        output = BuildOutputs.html("page")
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {"mimeType": "text/html", "filename": "output.html"}

    def test_get_mime_type_for_markdown_output(self):
        output = BuildOutputs.markdown()
        result = BuildOutputs.getMimeTypeForOutput(output)

        assert result == {"mimeType": "text/markdown", "filename": "output.md"}

    def test_get_mime_type_for_unknown_output(self):
        # Create an output with unknown type
        unknown_output = {"type": "unknown"}
        result = BuildOutputs.getMimeTypeForOutput(unknown_output)

        assert result == {"mimeType": "application/octet-stream", "filename": "output"}
