"""Comprehensive unit tests for Builder API."""

import io
from unittest.mock import Mock, patch

import pytest

from nutrient_dws.builder import BuildAPIWrapper


class TestBuilderInitialization:
    """Test suite for BuildAPIWrapper initialization."""

    def test_builder_init_with_string_path(self):
        """Test builder initialization with string file path."""
        builder = BuildAPIWrapper(None, "test.pdf")
        assert builder._input_file == "test.pdf"
        assert builder._actions == []
        assert builder._parts == [{"file": "file"}]
        assert "file" in builder._files

    def test_builder_init_with_bytes(self):
        """Test builder initialization with bytes input."""
        content = b"PDF content"
        builder = BuildAPIWrapper(None, content)
        assert builder._input_file == content
        assert builder._actions == []
        assert builder._parts == [{"file": "file"}]
        assert "file" in builder._files

    def test_builder_init_with_file_like_object(self):
        """Test builder initialization with file-like object."""
        file_obj = io.BytesIO(b"File content")
        file_obj.name = "test.pdf"

        builder = BuildAPIWrapper(None, file_obj)
        assert builder._input_file == file_obj
        assert builder._actions == []
        assert builder._parts == [{"file": "file"}]
        assert "file" in builder._files

    def test_builder_init_with_mock_client(self):
        """Test builder initialization with mock client."""
        mock_client = Mock()
        builder = BuildAPIWrapper(mock_client, "test.pdf")
        assert builder._client == mock_client


class TestBuilderAddStep:
    """Test suite for BuildAPIWrapper add_step method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = BuildAPIWrapper(None, "test.pdf")

    def test_add_step_basic(self):
        """Test adding basic step without options."""
        result = self.builder.add_step("convert-to-pdf")

        assert result is self.builder  # Should return self for chaining
        assert len(self.builder._actions) == 1
        assert self.builder._actions[0]["type"] == "convert-to-pdf"

    def test_add_step_with_options(self):
        """Test adding step with options."""
        result = self.builder.add_step("rotate-pages", options={"degrees": 90})

        assert result is self.builder
        assert len(self.builder._actions) == 1
        assert self.builder._actions[0]["type"] == "rotate"
        assert self.builder._actions[0]["rotateBy"] == 90

    def test_add_step_with_complex_options(self):
        """Test adding step with complex options."""
        options = {
            "text": "CONFIDENTIAL",
            "width": 200,
            "height": 100,
            "opacity": 0.5,
            "position": "center",
        }
        result = self.builder.add_step("watermark-pdf", options=options)

        assert result is self.builder
        assert len(self.builder._actions) == 1
        action = self.builder._actions[0]
        assert action["type"] == "watermark"
        assert action["text"] == "CONFIDENTIAL"
        assert action["width"] == 200
        assert action["height"] == 100
        assert action["opacity"] == 0.5
        assert action["position"] == "center"

    def test_add_multiple_steps(self):
        """Test adding multiple steps."""
        self.builder.add_step("convert-to-pdf")
        self.builder.add_step("rotate-pages", options={"degrees": 90})
        self.builder.add_step("watermark-pdf", options={"text": "DRAFT"})

        assert len(self.builder._actions) == 3
        assert self.builder._actions[0]["type"] == "convert-to-pdf"
        assert self.builder._actions[1]["type"] == "rotate"
        assert self.builder._actions[2]["type"] == "watermark"


class TestBuilderChaining:
    """Test suite for BuildAPIWrapper method chaining."""

    def test_basic_chaining(self):
        """Test basic method chaining."""
        builder = BuildAPIWrapper(None, "test.pdf")
        result = (
            builder.add_step("convert-to-pdf")
            .add_step("rotate-pages", options={"degrees": 90})
            .add_step("watermark-pdf", options={"text": "DRAFT"})
        )

        assert result is builder
        assert len(builder._actions) == 3
        assert all("type" in action for action in builder._actions)

    def test_chaining_with_output_options(self):
        """Test chaining with output options."""
        builder = BuildAPIWrapper(None, "test.pdf")
        result = (
            builder.add_step("convert-to-pdf")
            .set_output_options(metadata={"title": "Test"}, optimize=True)
            .add_step("watermark-pdf", options={"text": "FINAL"})
        )

        assert result is builder
        assert len(builder._actions) == 2
        assert builder._output_options["metadata"]["title"] == "Test"
        assert builder._output_options["optimize"] is True

    def test_complex_workflow_chaining(self):
        """Test complex workflow with multiple operations."""
        builder = BuildAPIWrapper(None, "document.docx")
        result = (
            builder.add_step("convert-to-pdf")
            .add_step("ocr-pdf", options={"language": "english"})
            .add_step("rotate-pages", options={"degrees": 90, "page_indexes": [0, 2]})
            .add_step("watermark-pdf", options={"text": "PROCESSED"})
            .add_step("flatten-annotations")
            .set_output_options(optimize=True, metadata={"title": "Processed Document"})
        )

        assert result is builder
        assert len(builder._actions) == 5
        assert builder._actions[0]["type"] == "convert-to-pdf"
        assert builder._actions[1]["type"] == "ocr"
        assert builder._actions[2]["type"] == "rotate"
        assert builder._actions[3]["type"] == "watermark"
        assert builder._actions[4]["type"] == "flatten"


class TestBuilderOutputOptions:
    """Test suite for BuildAPIWrapper output options."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = BuildAPIWrapper(None, "test.pdf")

    def test_set_output_options_basic(self):
        """Test setting basic output options."""
        result = self.builder.set_output_options(optimize=True)

        assert result is self.builder
        assert self.builder._output_options["optimize"] is True

    def test_set_output_options_metadata(self):
        """Test setting output options with metadata."""
        metadata = {"title": "Test Doc", "author": "Test Author"}
        result = self.builder.set_output_options(metadata=metadata)

        assert result is self.builder
        assert self.builder._output_options["metadata"]["title"] == "Test Doc"
        assert self.builder._output_options["metadata"]["author"] == "Test Author"

    def test_set_output_options_multiple_calls(self):
        """Test multiple calls to set_output_options merge properly."""
        self.builder.set_output_options(optimize=True)
        self.builder.set_output_options(metadata={"title": "Test"})
        self.builder.set_output_options(compress=True)

        assert self.builder._output_options["optimize"] is True
        assert self.builder._output_options["metadata"]["title"] == "Test"
        assert self.builder._output_options["compress"] is True

    def test_set_output_options_overwrites_same_key(self):
        """Test that setting same option key overwrites previous value."""
        self.builder.set_output_options(optimize=True)
        self.builder.set_output_options(optimize=False)

        assert self.builder._output_options["optimize"] is False

    def test_set_output_options_complex_metadata(self):
        """Test setting complex metadata structure."""
        metadata = {
            "title": "Complex Document",
            "author": "Test Author",
            "subject": "Test Subject",
            "keywords": ["test", "document", "processing"],
            "custom": {"version": "1.0", "department": "Engineering"},
        }
        result = self.builder.set_output_options(metadata=metadata)

        assert result is self.builder
        assert self.builder._output_options["metadata"] == metadata


class TestBuilderToolToActionMapping:
    """Test suite for BuildAPIWrapper tool to action mapping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = BuildAPIWrapper(None, "test.pdf")

    def test_map_tool_to_action_convert_to_pdf(self):
        """Test mapping convert-to-pdf tool."""
        self.builder.add_step("convert-to-pdf")
        action = self.builder._actions[0]
        assert action["type"] == "convert-to-pdf"

    def test_map_tool_to_action_flatten_annotations(self):
        """Test mapping flatten-annotations tool."""
        self.builder.add_step("flatten-annotations")
        action = self.builder._actions[0]
        assert action["type"] == "flatten"

    def test_map_tool_to_action_rotate_pages(self):
        """Test mapping rotate-pages tool with options."""
        self.builder.add_step("rotate-pages", options={"degrees": 180})
        action = self.builder._actions[0]
        assert action["type"] == "rotate"
        assert action["rotateBy"] == 180

    def test_map_tool_to_action_rotate_pages_with_page_indexes(self):
        """Test mapping rotate-pages tool with page indexes."""
        self.builder.add_step("rotate-pages", options={"degrees": 90, "page_indexes": [0, 2, 4]})
        action = self.builder._actions[0]
        assert action["type"] == "rotate"
        assert action["rotateBy"] == 90
        assert action["pageIndexes"] == [0, 2, 4]

    def test_map_tool_to_action_ocr_pdf(self):
        """Test mapping ocr-pdf tool with language."""
        self.builder.add_step("ocr-pdf", options={"language": "german"})
        action = self.builder._actions[0]
        assert action["type"] == "ocr"
        assert action["language"] == "deu"  # Maps to API format

    def test_map_tool_to_action_ocr_pdf_english(self):
        """Test mapping ocr-pdf tool with english language."""
        self.builder.add_step("ocr-pdf", options={"language": "english"})
        action = self.builder._actions[0]
        assert action["type"] == "ocr"
        assert action["language"] == "english"

    def test_map_tool_to_action_watermark_pdf(self):
        """Test mapping watermark-pdf tool with all options."""
        options = {
            "text": "CONFIDENTIAL",
            "width": 300,
            "height": 150,
            "opacity": 0.7,
            "position": "top-right",
        }
        self.builder.add_step("watermark-pdf", options=options)
        action = self.builder._actions[0]
        assert action["type"] == "watermark"
        assert action["text"] == "CONFIDENTIAL"
        assert action["width"] == 300
        assert action["height"] == 150
        assert action["opacity"] == 0.7
        assert action["position"] == "top-right"

    def test_map_tool_to_action_watermark_pdf_defaults(self):
        """Test mapping watermark-pdf tool with minimal options."""
        self.builder.add_step("watermark-pdf", options={"text": "TEST"})
        action = self.builder._actions[0]
        assert action["type"] == "watermark"
        assert action["text"] == "TEST"
        assert action["width"] == 200  # Default
        assert action["height"] == 100  # Default

    def test_map_tool_to_action_apply_redactions(self):
        """Test mapping apply-redactions tool."""
        self.builder.add_step("apply-redactions")
        action = self.builder._actions[0]
        assert action["type"] == "applyRedactions"


class TestBuilderFileHandling:
    """Test suite for BuildAPIWrapper file handling."""

    def test_builder_stores_file_for_upload(self):
        """Test that builder stores files for later upload."""
        builder = BuildAPIWrapper(None, "test.pdf")

        # The file is stored for later preparation during execute
        assert "file" in builder._files
        assert builder._files["file"] == "test.pdf"

    def test_builder_handles_bytes_input(self):
        """Test that builder handles bytes input."""
        content = b"PDF content bytes"
        builder = BuildAPIWrapper(None, content)

        assert "file" in builder._files
        assert builder._files["file"] == content


class TestBuilderExecute:
    """Test suite for BuildAPIWrapper execute method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client._http_client = Mock()
        self.builder = BuildAPIWrapper(self.mock_client, "test.pdf")

    @patch("nutrient_dws.builder.prepare_file_for_upload")
    @patch("nutrient_dws.builder.save_file_output")
    def test_execute_without_output_path(self, mock_save, mock_prepare):
        """Test execute without output path returns bytes."""
        mock_prepare.return_value = ("file", ("test.pdf", b"content", "application/pdf"))
        self.mock_client._http_client.post.return_value = b"processed content"

        result = self.builder.execute()

        assert result == b"processed content"
        mock_save.assert_not_called()
        self.mock_client._http_client.post.assert_called_once()

    @patch("nutrient_dws.builder.prepare_file_for_upload")
    @patch("nutrient_dws.builder.save_file_output")
    def test_execute_with_output_path(self, mock_save, mock_prepare):
        """Test execute with output path saves file."""
        mock_prepare.return_value = ("file", ("test.pdf", b"content", "application/pdf"))
        self.mock_client._http_client.post.return_value = b"processed content"

        result = self.builder.execute("output.pdf")

        assert result is None
        mock_save.assert_called_once_with(b"processed content", "output.pdf")
        self.mock_client._http_client.post.assert_called_once()

    @patch("nutrient_dws.builder.prepare_file_for_upload")
    def test_execute_builds_correct_instructions(self, mock_prepare):
        """Test that execute builds correct instructions."""
        mock_prepare.return_value = ("file", ("test.pdf", b"content", "application/pdf"))
        self.mock_client._http_client.post.return_value = b"result"

        self.builder.add_step("convert-to-pdf")
        self.builder.add_step("watermark-pdf", options={"text": "TEST"})
        self.builder.set_output_options(optimize=True)

        self.builder.execute()

        # Verify the client.post was called with correct parameters
        call_args = self.mock_client._http_client.post.call_args
        assert call_args[0][0] == "/build"  # endpoint
        assert "files" in call_args[1]
        assert "json_data" in call_args[1]

        # Check the instruction structure
        instructions = call_args[1]["json_data"]
        assert "parts" in instructions
        assert "actions" in instructions
        assert "output" in instructions  # Should include output options
        assert len(instructions["actions"]) == 2
        assert instructions["actions"][0]["type"] == "convert-to-pdf"
        assert instructions["actions"][1]["type"] == "watermark"

    @patch("nutrient_dws.builder.prepare_file_for_upload")
    def test_execute_with_no_client_raises_error(self, mock_prepare):
        """Test that execute without client raises appropriate error."""
        mock_prepare.return_value = ("file", ("test.pdf", b"content", "application/pdf"))
        builder = BuildAPIWrapper(None, "test.pdf")

        with pytest.raises(AttributeError):
            builder.execute()

    @patch("nutrient_dws.builder.prepare_file_for_upload")
    def test_execute_propagates_client_errors(self, mock_prepare):
        """Test that execute propagates errors from HTTP client."""
        from nutrient_dws.exceptions import APIError

        mock_prepare.return_value = ("file", ("test.pdf", b"content", "application/pdf"))
        self.mock_client._http_client.post.side_effect = APIError("API error", 400, "Bad request")

        with pytest.raises(APIError):
            self.builder.execute()


class TestBuilderEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("nutrient_dws.builder.prepare_file_for_upload")
    def test_builder_with_empty_actions(self, mock_prepare):
        """Test builder with no actions added."""
        mock_prepare.return_value = ("file", ("test.pdf", b"content", "application/pdf"))
        mock_client = Mock()
        mock_client._http_client = Mock()
        mock_client._http_client.post.return_value = b"empty workflow result"

        builder = BuildAPIWrapper(mock_client, "test.pdf")
        result = builder.execute()

        assert result == b"empty workflow result"

        # Verify instructions have empty actions
        call_args = mock_client._http_client.post.call_args
        instructions = call_args[1]["json_data"]
        assert instructions["actions"] == []

    @patch("nutrient_dws.builder.prepare_file_for_upload")
    def test_builder_action_order_preservation(self, mock_prepare):
        """Test that actions are executed in the correct order."""
        mock_prepare.return_value = ("file", ("test.pdf", b"content", "application/pdf"))
        mock_client = Mock()
        mock_client._http_client = Mock()
        mock_client._http_client.post.return_value = b"ordered result"

        builder = BuildAPIWrapper(mock_client, "test.pdf")
        builder.add_step("convert-to-pdf")
        builder.add_step("ocr-pdf", options={"language": "english"})
        builder.add_step("rotate-pages", options={"degrees": 90})
        builder.add_step("watermark-pdf", options={"text": "FINAL"})

        builder.execute()

        # Verify action order
        call_args = mock_client._http_client.post.call_args
        instructions = call_args[1]["json_data"]
        actions = instructions["actions"]

        assert len(actions) == 4
        assert actions[0]["type"] == "convert-to-pdf"
        assert actions[1]["type"] == "ocr"
        assert actions[2]["type"] == "rotate"
        assert actions[3]["type"] == "watermark"

    def test_builder_with_large_file_input(self):
        """Test builder with large file input."""
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB

        builder = BuildAPIWrapper(None, large_content)
        assert builder._input_file == large_content

    def test_builder_set_page_labels(self):
        """Test setting page labels."""
        builder = BuildAPIWrapper(None, "test.pdf")

        labels = [
            {"pages": {"start": 0, "end": 3}, "label": "Introduction"},
            {"pages": {"start": 3, "end": 10}, "label": "Chapter 1"},
            {"pages": {"start": 10}, "label": "Appendix"},
        ]

        result = builder.set_page_labels(labels)

        assert result is builder  # Should return self for chaining
        assert builder._output_options["labels"] == labels

    def test_builder_set_page_labels_chaining(self):
        """Test page labels can be chained with other operations."""
        builder = BuildAPIWrapper(None, "test.pdf")

        labels = [{"pages": {"start": 0, "end": 1}, "label": "Cover"}]

        result = (
            builder.add_step("rotate-pages", options={"degrees": 90})
            .set_page_labels(labels)
            .set_output_options(metadata={"title": "Test"})
        )

        assert result is builder
        assert len(builder._actions) == 1
        assert builder._output_options["labels"] == labels
        assert builder._output_options["metadata"]["title"] == "Test"

    def test_builder_options_none_handling(self):
        """Test builder handles None options gracefully."""
        builder = BuildAPIWrapper(None, "test.pdf")
        result = builder.add_step("convert-to-pdf", options=None)

        assert result is builder
        assert len(builder._actions) == 1
        assert builder._actions[0]["type"] == "convert-to-pdf"

    def test_builder_empty_output_options(self):
        """Test builder with empty output options."""
        builder = BuildAPIWrapper(None, "test.pdf")
        result = builder.set_output_options()

        assert result is builder
        # Should still create empty output options dict
        assert isinstance(builder._output_options, dict)
