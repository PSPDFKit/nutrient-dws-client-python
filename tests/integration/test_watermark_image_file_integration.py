"""Integration tests for image file watermark functionality."""

import os
from pathlib import Path
from typing import Optional, Union

import pytest

from nutrient_dws import NutrientClient

try:
    from . import integration_config  # type: ignore[attr-defined]

    API_KEY: Optional[str] = integration_config.API_KEY
    BASE_URL: Optional[str] = getattr(integration_config, "BASE_URL", None)
    TIMEOUT: int = getattr(integration_config, "TIMEOUT", 60)
except ImportError:
    API_KEY = None
    BASE_URL = None
    TIMEOUT = 60


def assert_is_pdf(file_path_or_bytes: Union[str, bytes]) -> None:
    """Assert that a file or bytes is a valid PDF."""
    if isinstance(file_path_or_bytes, str):
        with open(file_path_or_bytes, "rb") as f:
            content = f.read(8)
    else:
        content = file_path_or_bytes[:8]

    assert content.startswith(b"%PDF-"), (
        f"File does not start with PDF magic number, got: {content!r}"
    )


def create_test_image(tmp_path: Path, filename: str = "watermark.png") -> str:
    """Create a simple test PNG image."""
    try:
        # Try to use PIL to create a proper image
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="red")
        image_path = tmp_path / filename
        img.save(str(image_path))
        return str(image_path)
    except ImportError:
        # Fallback to a simple but valid PNG if PIL is not available
        # This is a 50x50 red PNG image
        png_data = (
            b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52"
            b"\x00\x00\x00\x32\x00\x00\x00\x32\x08\x02\x00\x00\x00\x91\x5d\x1f"
            b"\xe6\x00\x00\x00\x4b\x49\x44\x41\x54\x78\x9c\xed\xce\xb1\x01\x00"
            b"\x10\x00\xc0\x30\xfc\xff\x33\x0f\x58\x32\x31\x34\x17\x64\xee\xf1"
            b"\xa3\xf5\x3a\x70\x57\x4b\xd4\x12\xb5\x44\x2d\x51\x4b\xd4\x12\xb5"
            b"\x44\x2d\x51\x4b\xd4\x12\xb5\x44\x2d\x51\x4b\xd4\x12\xb5\x44\x2d"
            b"\x51\x4b\xd4\x12\xb5\x44\x2d\x51\x4b\xd4\x12\xb5\x44\x2d\x71\x00"
            b"\x41\xaa\x01\x63\x85\xb8\x32\xab\x00\x00\x00\x00\x49\x45\x4e\x44"
            b"\xae\x42\x60\x82"
        )
        image_path = tmp_path / filename
        image_path.write_bytes(png_data)
        return str(image_path)


@pytest.mark.skipif(not API_KEY, reason="No API key configured in integration_config.py")
class TestWatermarkImageFileIntegration:
    """Integration tests for image file watermark functionality."""

    @pytest.fixture
    def client(self):
        """Create a client with the configured API key."""
        client = NutrientClient(api_key=API_KEY, timeout=TIMEOUT)
        yield client
        client.close()

    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF file for testing."""
        return os.path.join(os.path.dirname(__file__), "..", "data", "sample.pdf")

    def test_watermark_pdf_with_image_file_path(self, client, sample_pdf_path, tmp_path):
        """Test watermark_pdf with local image file path."""
        # Create a test image
        image_path = create_test_image(tmp_path)

        result = client.watermark_pdf(
            sample_pdf_path,
            image_file=image_path,
            width=100,
            height=50,
            opacity=0.5,
            position="bottom-right",
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_watermark_pdf_with_image_bytes(self, client, sample_pdf_path):
        """Test watermark_pdf with image as bytes."""
        # Create a proper PNG image as bytes
        try:
            import io

            from PIL import Image

            img = Image.new("RGB", (100, 100), color="blue")
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            png_bytes = img_buffer.getvalue()
        except ImportError:
            # Fallback to a 50x50 red PNG if PIL is not available
            png_bytes = (
                b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52"
                b"\x00\x00\x00\x32\x00\x00\x00\x32\x08\x02\x00\x00\x00\x91\x5d\x1f"
                b"\xe6\x00\x00\x00\x4b\x49\x44\x41\x54\x78\x9c\xed\xce\xb1\x01\x00"
                b"\x10\x00\xc0\x30\xfc\xff\x33\x0f\x58\x32\x31\x34\x17\x64\xee\xf1"
                b"\xa3\xf5\x3a\x70\x57\x4b\xd4\x12\xb5\x44\x2d\x51\x4b\xd4\x12\xb5"
                b"\x44\x2d\x51\x4b\xd4\x12\xb5\x44\x2d\x51\x4b\xd4\x12\xb5\x44\x2d"
                b"\x51\x4b\xd4\x12\xb5\x44\x2d\x51\x4b\xd4\x12\xb5\x44\x2d\x71\x00"
                b"\x41\xaa\x01\x63\x85\xb8\x32\xab\x00\x00\x00\x00\x49\x45\x4e\x44"
                b"\xae\x42\x60\x82"
            )

        result = client.watermark_pdf(
            sample_pdf_path,
            image_file=png_bytes,
            width=150,
            height=75,
            opacity=0.8,
            position="top-left",
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_watermark_pdf_with_image_file_output_path(self, client, sample_pdf_path, tmp_path):
        """Test watermark_pdf with image file saving to output path."""
        # Create a test image
        image_path = create_test_image(tmp_path)
        output_path = str(tmp_path / "watermarked_with_image.pdf")

        result = client.watermark_pdf(
            sample_pdf_path,
            image_file=image_path,
            width=200,
            height=100,
            opacity=0.7,
            position="center",
            output_path=output_path,
        )

        assert result is None
        assert (tmp_path / "watermarked_with_image.pdf").exists()
        assert (tmp_path / "watermarked_with_image.pdf").stat().st_size > 0
        assert_is_pdf(output_path)

    def test_watermark_pdf_with_file_like_object(self, client, sample_pdf_path, tmp_path):
        """Test watermark_pdf with image as file-like object."""
        # Create a test image
        image_path = create_test_image(tmp_path)

        # Read as file-like object
        with open(image_path, "rb") as image_file:
            result = client.watermark_pdf(
                sample_pdf_path,
                image_file=image_file,
                width=120,
                height=60,
                opacity=0.6,
                position="top-center",
            )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_builder_api_with_image_file_watermark(self, client, sample_pdf_path, tmp_path):
        """Test Builder API with image file watermark."""
        # Create a test image
        image_path = create_test_image(tmp_path)

        # Use builder API
        result = (
            client.build(sample_pdf_path)
            .add_step(
                "watermark-pdf",
                options={
                    "image_file": image_path,
                    "width": 180,
                    "height": 90,
                    "opacity": 0.4,
                    "position": "bottom-left",
                },
            )
            .execute()
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)

    def test_multiple_watermarks_with_image_files(self, client, sample_pdf_path, tmp_path):
        """Test applying multiple watermarks including image files."""
        # Create test images
        image1_path = create_test_image(tmp_path, "watermark1.png")

        # Chain multiple watermark operations
        result = (
            client.build(sample_pdf_path)
            .add_step(
                "watermark-pdf",
                options={
                    "text": "DRAFT",
                    "width": 200,
                    "height": 100,
                    "opacity": 0.3,
                    "position": "center",
                },
            )
            .add_step(
                "watermark-pdf",
                options={
                    "image_file": image1_path,
                    "width": 100,
                    "height": 50,
                    "opacity": 0.5,
                    "position": "top-right",
                },
            )
            .execute()
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert_is_pdf(result)
