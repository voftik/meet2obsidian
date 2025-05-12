#!/usr/bin/env python3
"""
Скрипт для запуска тестов.
Добавляет родительскую директорию в путь Python для правильного импорта модулей.
"""

import os
import sys
import pytest

# Добавляем директорию проекта в путь Python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    # Запускаем pytest с аргументами командной строки
    args = ["-v"]
    
    # Добавляем остальные аргументы командной строки
    args.extend(sys.argv[1:])
    
    # Запускаем pytest
    sys.exit(pytest.main(args))