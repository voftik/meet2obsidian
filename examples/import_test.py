#!/usr/bin/env python3
"""
Простой тест для проверки импорта из модуля meet2obsidian.
"""

import os
import sys

# Добавляем родительскую директорию в путь импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Проверяем, что мы можем импортировать файлы из проекта
print("Пути импорта Python:", sys.path)
print("\nПроверка доступа к файлам проекта:")
print(f"Родительская директория: {os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}")

try:
    # Импортируем какой-нибудь модуль из проекта
    from meet2obsidian import __init__
    print("✓ Успешно импортирован модуль meet2obsidian")
except ImportError as e:
    print(f"✗ Ошибка импорта: {e}")

# Проверяем доступ к модулю логирования
try:
    import meet2obsidian.utils.logging
    print("✓ Успешно импортирован модуль logging")
except ImportError as e:
    print(f"✗ Ошибка импорта модуля logging: {e}")

# Проверяем наличие файла с модулем логирования
logging_path = os.path.join(os.path.dirname(__file__), '..', 'meet2obsidian', 'utils', 'logging.py')
print(f"\nПроверка файла logging.py: {os.path.exists(logging_path)}")

if __name__ == "__main__":
    pass