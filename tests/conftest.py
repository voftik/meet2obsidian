"""
Конфигурационный файл для pytest.
Добавляет родительскую директорию в путь Python для правильного импорта модулей.
Регистрирует маркеры pytest для разных типов тестов.
"""

import os
import sys
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