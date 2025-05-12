"""
Configuration file for pytest.
Adds the parent directory to the Python path for correct module imports.
Registers pytest markers for different types of tests.
Defines helper functions and fixtures for testing.
"""

import os
import sys
import re
import pytest

# Добавляем директорию проекта в путь Python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def pytest_configure(config):
    """
    Register custom pytest markers.
    """
    config.addinivalue_line("markers", "integration: marker for integration tests")
    config.addinivalue_line("markers", "unit: marker for unit tests")
    config.addinivalue_line("markers", "slow: marker for slow tests")
    config.addinivalue_line("markers", "launchagent: marker for LaunchAgent tests")


# Helper classes and functions for tests

class AnyStringContaining:
    """
    Helper class to check if a string contains a specified substring.

    Usage examples:
        assert log_message == AnyStringContaining("error")
        mock_logger.error.assert_called_with(AnyStringContaining("failed to start"))
    """

    def __init__(self, substring):
        self.substring = substring

    def __eq__(self, other):
        if not isinstance(other, str):
            return False
        return self.substring in other

    def __repr__(self):
        return f"AnyStringContaining({self.substring!r})"


class AnyStringMatching:
    """
    Helper class to check if a string matches a specified regular expression.

    Usage examples:
        assert log_message == AnyStringMatching(r"Error \\d+")
        mock_logger.error.assert_called_with(AnyStringMatching(r"^Failed to.*$"))
    """

    def __init__(self, pattern):
        self.pattern = pattern
        self.regex = re.compile(pattern)

    def __eq__(self, other):
        if not isinstance(other, str):
            return False
        return bool(self.regex.search(other))

    def __repr__(self):
        return f"AnyStringMatching({self.pattern!r})"


# Подключаем вспомогательные классы к pytest через fixture
@pytest.fixture(autouse=True)
def add_helpers(monkeypatch):
    """
    Adds helper functions and classes to pytest.
    This allows using them in tests without needing to import them.
    """
    # Create helpers namespace and add helper functions
    pytest.helpers = type('helpers', (), {})
    pytest.helpers.ANY_STRING_CONTAINING = AnyStringContaining
    pytest.helpers.ANY_STRING_MATCHING = AnyStringMatching


# LaunchAgent testing fixtures
@pytest.fixture
def temp_plist_path(tmp_path):
    """
    Fixture that provides a temporary path for a LaunchAgent plist file.
    """
    plist_path = tmp_path / "com.test.meet2obsidian.plist"
    return str(plist_path)


@pytest.fixture
def mock_launchctl():
    """
    Fixture that mocks the launchctl command.
    """
    with patch('subprocess.run') as mock_run:
        # Mock successful operation
        mock_run.return_value = type('MockCompletedProcess', (), {
            'returncode': 0,
            'stdout': '',
            'stderr': ''
        })
        yield mock_run