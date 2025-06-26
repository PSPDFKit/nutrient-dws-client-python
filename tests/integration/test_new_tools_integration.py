"""Integration tests for newly added Direct API methods.

These tests require a valid API key configured in integration_config.py and
test the new Direct API methods against the live Nutrient DWS API.
"""

from pathlib import Path

import pytest

from nutrient_dws import NutrientClient

try:
    from . import integration_config  # type: ignore[attr-defined]

    API_KEY: str | None = integration_config.API_KEY
    BASE_URL: str | None = getattr(integration_config, "BASE_URL", None)
    TIMEOUT: int = getattr(integration_config, "TIMEOUT", 60)
except ImportError:
    API_KEY = None
    BASE_URL = None
    TIMEOUT = 60


def assert_is_pdf(file_path_or_bytes: str | bytes) -> None:
    """Assert that a file or bytes is a valid PDF.

    Args:
        file_path_or_bytes: Path to file or bytes content to check.
    """
    if isinstance(file_path_or_bytes, (str, bytes)):
        if isinstance(file_path_or_bytes, str):
            with open(file_path_or_bytes, "rb") as f:
                content = f.read(8)
        else:
            content = file_path_or_bytes[:8]

        # Check PDF magic number
        assert content.startswith(b"%PDF-"), (
            f"File does not start with PDF magic number, got: {content!r}"
        )
    else:
        raise ValueError("Input must be file path string or bytes")


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestCreateRedactionsIntegration:
    """Integration tests for create_redactions methods."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        return NutrientClient(api_key=API_KEY, timeout=TIMEOUT)

    @pytest.fixture
    def sample_pdf_with_sensitive_data(self, tmp_path):
        """Create a PDF with sensitive data for testing redactions."""
        # For now, we'll use a sample PDF. In a real scenario, we'd create one with sensitive data
        sample_path = Path(__file__).parent.parent / "data" / "sample.pdf"
        if not sample_path.exists():
            pytest.skip(f"Sample PDF not found at {sample_path}")
        return str(sample_path)

    def test_create_redactions_preset_ssn(self, client, sample_pdf_with_sensitive_data):
        """Test creating redactions with SSN preset."""
        result = client.create_redactions_preset(
            sample_pdf_with_sensitive_data, preset="social-security-number"
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_create_redactions_preset_with_output_file(
        self, client, sample_pdf_with_sensitive_data, tmp_path
    ):
        """Test creating redactions with preset and saving to file."""
        output_path = tmp_path / "redacted_preset.pdf"
        result = client.create_redactions_preset(
            sample_pdf_with_sensitive_data, preset="email", output_path=str(output_path)
        )
        assert result is None
        assert output_path.exists()
        assert_is_pdf(str(output_path))

    def test_create_redactions_regex(self, client, sample_pdf_with_sensitive_data):
        """Test creating redactions with regex pattern."""
        # Pattern for simple numbers (which should exist in any PDF)
        result = client.create_redactions_regex(
            sample_pdf_with_sensitive_data, pattern=r"\d+", case_sensitive=False
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_create_redactions_text(self, client, sample_pdf_with_sensitive_data):
        """Test creating redactions for exact text matches."""
        # Use a very common letter that should exist
        result = client.create_redactions_text(
            sample_pdf_with_sensitive_data, text="a", case_sensitive=False, whole_words_only=False
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_create_redactions_with_appearance(self, client, sample_pdf_with_sensitive_data):
        """Test creating redactions with custom appearance."""
        result = client.create_redactions_text(
            sample_pdf_with_sensitive_data,
            text="e",  # Very common letter
            case_sensitive=False,
            appearance_fill_color="#FF0000",
            appearance_stroke_color="#000000",
        )
        assert_is_pdf(result)
        assert len(result) > 0


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestOptimizePDFIntegration:
    """Integration tests for optimize_pdf method."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        return NutrientClient(api_key=API_KEY, timeout=TIMEOUT)

    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF file."""
        sample_path = Path(__file__).parent.parent / "data" / "sample.pdf"
        if not sample_path.exists():
            pytest.skip(f"Sample PDF not found at {sample_path}")
        return str(sample_path)

    def test_optimize_pdf_basic(self, client, sample_pdf_path):
        """Test basic PDF optimization."""
        result = client.optimize_pdf(sample_pdf_path)
        assert_is_pdf(result)
        assert len(result) > 0

    def test_optimize_pdf_grayscale(self, client, sample_pdf_path):
        """Test PDF optimization with grayscale options."""
        result = client.optimize_pdf(
            sample_pdf_path, grayscale_text=True, grayscale_graphics=True, grayscale_images=True
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_optimize_pdf_reduce_quality(self, client, sample_pdf_path):
        """Test PDF optimization with reduced image quality."""
        result = client.optimize_pdf(sample_pdf_path, reduce_image_quality=50)
        assert_is_pdf(result)
        assert len(result) > 0

    def test_optimize_pdf_linearize(self, client, sample_pdf_path):
        """Test PDF optimization with linearization."""
        result = client.optimize_pdf(sample_pdf_path, linearize=True)
        assert_is_pdf(result)
        assert len(result) > 0

    def test_optimize_pdf_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test PDF optimization with output file."""
        output_path = tmp_path / "optimized.pdf"
        result = client.optimize_pdf(
            sample_pdf_path,
            grayscale_images=True,
            reduce_image_quality=70,
            output_path=str(output_path),
        )
        assert result is None
        assert output_path.exists()
        assert_is_pdf(str(output_path))

    def test_optimize_pdf_invalid_quality_raises_error(self, client, sample_pdf_path):
        """Test that invalid image quality raises ValueError."""
        with pytest.raises(ValueError, match="reduce_image_quality must be between 1 and 100"):
            client.optimize_pdf(sample_pdf_path, reduce_image_quality=0)

        with pytest.raises(ValueError, match="reduce_image_quality must be between 1 and 100"):
            client.optimize_pdf(sample_pdf_path, reduce_image_quality=101)


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestPasswordProtectPDFIntegration:
    """Integration tests for password_protect_pdf method."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        return NutrientClient(api_key=API_KEY, timeout=TIMEOUT)

    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF file."""
        sample_path = Path(__file__).parent.parent / "data" / "sample.pdf"
        if not sample_path.exists():
            pytest.skip(f"Sample PDF not found at {sample_path}")
        return str(sample_path)

    def test_password_protect_user_password(self, client, sample_pdf_path):
        """Test password protection with user password only."""
        result = client.password_protect_pdf(sample_pdf_path, user_password="test123")
        assert_is_pdf(result)
        assert len(result) > 0

    def test_password_protect_both_passwords(self, client, sample_pdf_path):
        """Test password protection with both user and owner passwords."""
        result = client.password_protect_pdf(
            sample_pdf_path, user_password="user123", owner_password="owner456"
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_password_protect_with_permissions(self, client, sample_pdf_path):
        """Test password protection with custom permissions."""
        result = client.password_protect_pdf(
            sample_pdf_path,
            user_password="test123",
            permissions={
                "print": False,
                "modification": False,
                "extract": True,
                "annotations": True,
            },
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_password_protect_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test password protection with output file."""
        output_path = tmp_path / "protected.pdf"
        result = client.password_protect_pdf(
            sample_pdf_path,
            user_password="secret",
            owner_password="admin",
            permissions={"print": True, "modification": False},
            output_path=str(output_path),
        )
        assert result is None
        assert output_path.exists()
        assert_is_pdf(str(output_path))

    def test_password_protect_no_password_raises_error(self, client, sample_pdf_path):
        """Test that no password raises ValueError."""
        with pytest.raises(
            ValueError, match="At least one of user_password or owner_password must be provided"
        ):
            client.password_protect_pdf(sample_pdf_path)


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestSetPDFMetadataIntegration:
    """Integration tests for set_pdf_metadata method."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        return NutrientClient(api_key=API_KEY, timeout=TIMEOUT)

    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF file."""
        sample_path = Path(__file__).parent.parent / "data" / "sample.pdf"
        if not sample_path.exists():
            pytest.skip(f"Sample PDF not found at {sample_path}")
        return str(sample_path)

    def test_set_pdf_metadata_title_author(self, client, sample_pdf_path):
        """Test setting PDF title and author."""
        result = client.set_pdf_metadata(
            sample_pdf_path, title="Test Document", author="Test Author"
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_set_pdf_metadata_all_fields(self, client, sample_pdf_path):
        """Test setting all PDF metadata fields."""
        result = client.set_pdf_metadata(
            sample_pdf_path,
            title="Complete Test Document",
            author="John Doe",
            subject="Testing PDF Metadata",
            keywords="test, pdf, metadata, nutrient",
            creator="Nutrient DWS Python Client",
            producer="Test Suite",
        )
        assert_is_pdf(result)
        assert len(result) > 0

    def test_set_pdf_metadata_with_output_file(self, client, sample_pdf_path, tmp_path):
        """Test setting PDF metadata with output file."""
        output_path = tmp_path / "metadata.pdf"
        result = client.set_pdf_metadata(
            sample_pdf_path,
            title="Output Test",
            keywords="output, test",
            output_path=str(output_path),
        )
        assert result is None
        assert output_path.exists()
        assert_is_pdf(str(output_path))

    def test_set_pdf_metadata_no_fields_raises_error(self, client, sample_pdf_path):
        """Test that no metadata fields raises ValueError."""
        with pytest.raises(ValueError, match="At least one metadata field must be provided"):
            client.set_pdf_metadata(sample_pdf_path)


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestApplyInstantJSONIntegration:
    """Integration tests for apply_instant_json method."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        return NutrientClient(api_key=API_KEY, timeout=TIMEOUT)

    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF file."""
        sample_path = Path(__file__).parent.parent / "data" / "sample.pdf"
        if not sample_path.exists():
            pytest.skip(f"Sample PDF not found at {sample_path}")
        return str(sample_path)

    @pytest.fixture
    def sample_instant_json(self, tmp_path):
        """Create a sample Instant JSON file."""
        json_content = """{
            "annotations": [
                {
                    "type": "text",
                    "pageIndex": 0,
                    "bbox": [100, 100, 200, 150],
                    "content": "Test annotation"
                }
            ]
        }"""
        json_path = tmp_path / "annotations.json"
        json_path.write_text(json_content)
        return str(json_path)

    def test_apply_instant_json_from_file(self, client, sample_pdf_path, sample_instant_json):
        """Test applying Instant JSON from file."""
        result = client.apply_instant_json(sample_pdf_path, sample_instant_json)
        assert_is_pdf(result)
        assert len(result) > 0

    def test_apply_instant_json_from_bytes(self, client, sample_pdf_path):
        """Test applying Instant JSON from bytes."""
        json_bytes = b"""{
            "annotations": [
                {
                    "type": "highlight",
                    "pageIndex": 0,
                    "rects": [[50, 50, 150, 70]]
                }
            ]
        }"""
        result = client.apply_instant_json(sample_pdf_path, json_bytes)
        assert_is_pdf(result)
        assert len(result) > 0

    def test_apply_instant_json_with_output_file(
        self, client, sample_pdf_path, sample_instant_json, tmp_path
    ):
        """Test applying Instant JSON with output file."""
        output_path = tmp_path / "annotated.pdf"
        result = client.apply_instant_json(
            sample_pdf_path, sample_instant_json, output_path=str(output_path)
        )
        assert result is None
        assert output_path.exists()
        assert_is_pdf(str(output_path))

    @pytest.mark.skip(reason="Requires valid Instant JSON URL")
    def test_apply_instant_json_from_url(self, client, sample_pdf_path):
        """Test applying Instant JSON from URL."""
        # This test would require a valid URL with Instant JSON content
        pass


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestApplyXFDFIntegration:
    """Integration tests for apply_xfdf method."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        return NutrientClient(api_key=API_KEY, timeout=TIMEOUT)

    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF file."""
        sample_path = Path(__file__).parent.parent / "data" / "sample.pdf"
        if not sample_path.exists():
            pytest.skip(f"Sample PDF not found at {sample_path}")
        return str(sample_path)

    @pytest.fixture
    def sample_xfdf(self, tmp_path):
        """Create a sample XFDF file."""
        xfdf_content = """<?xml version="1.0" encoding="UTF-8"?>
<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
    <annots>
        <text page="0" rect="100,100,200,150" title="Test">
            <contents>Test XFDF annotation</contents>
        </text>
    </annots>
</xfdf>"""
        xfdf_path = tmp_path / "annotations.xfdf"
        xfdf_path.write_text(xfdf_content)
        return str(xfdf_path)

    def test_apply_xfdf_from_file(self, client, sample_pdf_path, sample_xfdf):
        """Test applying XFDF from file."""
        result = client.apply_xfdf(sample_pdf_path, sample_xfdf)
        assert_is_pdf(result)
        assert len(result) > 0

    def test_apply_xfdf_from_bytes(self, client, sample_pdf_path):
        """Test applying XFDF from bytes."""
        xfdf_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
    <annots>
        <highlight page="0" rect="50,50,150,70"/>
    </annots>
</xfdf>"""
        result = client.apply_xfdf(sample_pdf_path, xfdf_bytes)
        assert_is_pdf(result)
        assert len(result) > 0

    def test_apply_xfdf_with_output_file(self, client, sample_pdf_path, sample_xfdf, tmp_path):
        """Test applying XFDF with output file."""
        output_path = tmp_path / "xfdf_annotated.pdf"
        result = client.apply_xfdf(sample_pdf_path, sample_xfdf, output_path=str(output_path))
        assert result is None
        assert output_path.exists()
        assert_is_pdf(str(output_path))

    @pytest.mark.skip(reason="Requires valid XFDF URL")
    def test_apply_xfdf_from_url(self, client, sample_pdf_path):
        """Test applying XFDF from URL."""
        # This test would require a valid URL with XFDF content
        pass
