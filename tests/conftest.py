"""
Конфигурационный файл для pytest.
Добавляет родительскую директорию в путь Python для правильного импорта модулей.
"""

import os
import sys

# Добавляем директорию проекта в путь Python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)