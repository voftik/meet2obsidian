#!/usr/bin/env python3
"""
Скрипт для запуска тестов.
Добавляет родительскую директорию в путь Python для правильного импорта модулей.

Использование:
    ./run_tests.py                    # Запустить все модульные тесты
    ./run_tests.py --integration      # Запустить модульные и интеграционные тесты
    ./run_tests.py path/to/test.py    # Запустить конкретный тест
"""

import os
import sys
import argparse
import pytest

# Добавляем директорию проекта в путь Python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def parse_args():
    """
    Парсинг аргументов командной строки.
    """
    parser = argparse.ArgumentParser(description='Запуск тестов meet2obsidian')
    parser.add_argument('--integration', action='store_true', help='Запустить интеграционные тесты')
    parser.add_argument('test_paths', nargs='*', help='Пути к файлам тестов для запуска')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Настройка аргументов pytest
    pytest_args = ["-v"]

    # Исключаем интеграционные тесты по умолчанию
    if not args.integration:
        pytest_args.append("-m")
        pytest_args.append("not integration")

    # Если указаны пути к тестам, используем их
    if args.test_paths:
        pytest_args.extend(args.test_paths)
    else:
        # По умолчанию запускаем все тесты в директории tests/
        pytest_args.append(os.path.dirname(__file__))

    # Запускаем pytest
    print(f"Запуск тестов с аргументами: {' '.join(pytest_args)}")
    sys.exit(pytest.main(pytest_args))