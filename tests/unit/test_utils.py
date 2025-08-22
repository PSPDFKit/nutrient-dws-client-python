import os
from unittest import mock

import pytest
import re
from nutrient_dws.utils import (
    get_user_agent,
    get_library_version,
)


class TestUtilityFunctions:
    """Unit tests for utility functions"""

    def test_get_library_version_returns_valid_semver(self):
        """Should return a valid semver version string"""
        version = get_library_version()

        assert version is not None
        assert isinstance(version, str)
        assert len(version) > 0

        # Check if it matches semver pattern (major.minor.patch)
        semver_pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$'
        assert re.match(semver_pattern, version)

    def test_get_library_version_consistency(self):
        """Should return the version consistently"""
        version = get_library_version()

        # The version should match whatever is in the package metadata
        # We don't hardcode the expected version to avoid breaking on version updates
        assert re.match(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$', version)
        assert len(version) > 0

    def test_get_user_agent_returns_formatted_string(self):
        """Should return a properly formatted User-Agent string"""
        user_agent = get_user_agent()

        assert user_agent is not None
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0

    def test_get_user_agent_follows_expected_format(self):
        """Should follow the expected User-Agent format"""
        user_agent = get_user_agent()

        # Should match: nutrient-dws/VERSION
        expected_pattern = r'^nutrient-dws/\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$'
        assert re.match(expected_pattern, user_agent)

    @mock.patch.dict(
        os.environ,
        {
            "PYTHON_ENV": "development",
        },
        clear=True,
    )
    def test_get_user_agent_follows_expected_format_development(self):
        """Should follow the expected User-Agent format in development"""
        user_agent = get_user_agent()

        # Should match: nutrient-dws/VERSION
        assert user_agent == "nutrient-dws/0.0.0-dev"


    def test_get_user_agent_includes_correct_library_name(self):
        """Should include the correct library name"""
        user_agent = get_user_agent()

        assert 'nutrient-dws' in user_agent

    def test_get_user_agent_includes_current_library_version(self):
        """Should include the current library version"""
        user_agent = get_user_agent()
        version = get_library_version()

        assert version in user_agent

    def test_get_user_agent_consistency(self):
        """Should have consistent format across multiple calls"""
        user_agent1 = get_user_agent()
        user_agent2 = get_user_agent()

        assert user_agent1 == user_agent2

    def test_get_user_agent_expected_format_with_current_version(self):
        """Should return the expected User-Agent format with current version"""
        user_agent = get_user_agent()
        version = get_library_version()

        assert user_agent == f"nutrient-dws/{version}"
