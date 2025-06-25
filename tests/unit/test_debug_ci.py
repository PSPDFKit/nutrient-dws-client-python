"""Debug test to understand CI failures."""

import sys
import platform


def test_python_version():
    """Print Python version info."""
    print(f"\nPython version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    assert True


def test_import_watermark():
    """Test importing the watermark functionality."""
    try:
        from nutrient_dws.api.direct import DirectAPIMixin
        print("\nDirectAPIMixin imported successfully")
        
        # Check if watermark_pdf has image_file parameter
        import inspect
        sig = inspect.signature(DirectAPIMixin.watermark_pdf)
        params = list(sig.parameters.keys())
        print(f"watermark_pdf parameters: {params}")
        assert "image_file" in params
        
    except Exception as e:
        print(f"\nImport failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_basic_watermark_import():
    """Test basic imports work."""
    try:
        from nutrient_dws import NutrientClient
        print("\nNutrientClient imported successfully")
        assert True
    except Exception as e:
        print(f"\nBasic import failed: {e}")
        raise