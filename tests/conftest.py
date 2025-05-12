"""
Конфигурационный файл для pytest.
Добавляет родительскую директорию в путь Python для правильного импорта модулей.
Регистрирует маркеры pytest для разных типов тестов.
Определяет вспомогательные функции для тестирования.
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
    Регистрация пользовательских маркеров pytest.
    """
    config.addinivalue_line("markers", "integration: маркер для интеграционных тестов")
    config.addinivalue_line("markers", "unit: маркер для модульных тестов")
    config.addinivalue_line("markers", "slow: маркер для медленных тестов")


# Вспомогательные классы и функции для тестов

class AnyStringContaining:
    """
    Вспомогательный класс для проверки, содержит ли строка указанную подстроку.

    Примеры использования:
        assert log_message == AnyStringContaining("ошибка")
        mock_logger.error.assert_called_with(AnyStringContaining("не удалось запустить"))
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
    Вспомогательный класс для проверки, соответствует ли строка указанному регулярному выражению.

    Примеры использования:
        assert log_message == AnyStringMatching(r"Error \d+")
        mock_logger.error.assert_called_with(AnyStringMatching(r"^Не удалось.*$"))
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
    Добавляет вспомогательные функции и классы к pytest.
    Это позволяет использовать их в тестах без необходимости импорта.
    """
    # Создаем пространство имен helpers и добавляем туда вспомогательные функции
    pytest.helpers = type('helpers', (), {})
    pytest.helpers.ANY_STRING_CONTAINING = AnyStringContaining
    pytest.helpers.ANY_STRING_MATCHING = AnyStringMatching