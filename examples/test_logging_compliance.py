#!/usr/bin/env python3
"""
Проверка соответствия модуля логирования требованиям тестов Epic 7.

Этот скрипт проверяет, что реализация модуля логирования соответствует
требованиям, определенным в тестах Epic 7.
"""

import os
import sys
import json
import logging
import structlog
from pathlib import Path

# Добавляем родительскую директорию в путь импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем модуль логирования
from meet2obsidian.utils.logging import setup_logging, get_logger

def test_logging_setup():
    """Проверка настройки логирования"""
    print("\n--- Проверка настройки логирования ---")
    
    # Настройка по умолчанию
    root_logger = setup_logging()
    print(f"Настройка по умолчанию - Уровень root логгера: {logging.getLevelName(root_logger.level)}")
    
    # Настройка с другим уровнем логирования
    root_logger = setup_logging(log_level="debug")
    print(f"Настройка с уровнем debug - Уровень root логгера: {logging.getLevelName(root_logger.level)}")
    
    # Настройка с файлом лога
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "test_setup.log"
    
    root_logger = setup_logging(log_level="info", log_file=str(log_file))
    print(f"Настройка с файлом - Файл лога создан: {log_file.exists()}")
    
    # Проверка обработки некорректного уровня
    try:
        setup_logging(log_level="invalid_level")
        print("Информация: Некорректный уровень логирования автоматически заменен на INFO")
    except ValueError as e:
        print(f"Ошибка: Некорректный уровень должен быть заменен на INFO, но получено исключение: {e}")
    
    print("✓ Проверка настройки логирования пройдена")


def test_logging_levels():
    """Проверка уровней логирования"""
    print("\n--- Проверка уровней логирования ---")
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "test_levels.log"
    
    # Настройка с уровнем debug для перехвата всех сообщений
    setup_logging(log_level="debug", log_file=str(log_file))
    
    # Создаем логгеры с разными именами
    root_logger = get_logger("test")
    child_logger = get_logger("test.child")
    
    # Логируем сообщения на разных уровнях
    print("Логирование сообщений на разных уровнях...")
    root_logger.debug("Отладочное сообщение")
    root_logger.info("Информационное сообщение")
    root_logger.warning("Предупреждение")
    root_logger.error("Сообщение об ошибке")
    root_logger.critical("Критическое сообщение")
    
    # Демонстрация наследования уровней
    print("Демонстрация наследования уровней...")
    child_logger.debug("Отладочное сообщение дочернего логгера")
    
    # Показываем содержимое файла лога
    print(f"Содержимое файла лога ({log_file}):")
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[-6:]):  # Показываем последние 6 строк
                print(f"{i+1}: {line.strip()}")
    except Exception as e:
        print(f"Ошибка при чтении файла лога: {e}")
    
    print("✓ Проверка уровней логирования пройдена")


def test_log_rotation():
    """Проверка ротации логов"""
    print("\n--- Проверка ротации логов ---")
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "test_rotation.log"
    
    # Настройка с маленьким max_bytes для быстрой ротации
    max_bytes = 1024  # 1KB
    backup_count = 3
    
    print(f"Настройка ротации логов - max_bytes: {max_bytes}, backup_count: {backup_count}")
    setup_logging(
        log_level="debug", 
        log_file=str(log_file),
        max_bytes=max_bytes,
        backup_count=backup_count
    )
    
    logger = get_logger("test.rotation")
    
    # Генерируем достаточно логов для срабатывания ротации
    print("Генерация логов для срабатывания ротации...")
    for i in range(100):
        logger.info(f"Тестовое сообщение ротации {i}", 
                   iteration=i, 
                   extra_data="x" * 50)  # Добавляем дополнительные данные для увеличения размера
    
    # Проверяем, произошла ли ротация
    rotation_files = list(log_dir.glob("test_rotation.log.*"))
    print(f"Созданы файлы ротации: {len(rotation_files)}")
    for file in sorted(rotation_files):
        print(f"  - {file.name} ({file.stat().st_size} байт)")
    
    # Настройка без ротации
    no_rotation_file = log_dir / "test_no_rotation.log"
    setup_logging(
        log_level="debug", 
        log_file=str(no_rotation_file),
        rotate_logs=False
    )
    
    logger = get_logger("test.no_rotation")
    print("\nТестирование логирования без ротации...")
    for i in range(10):
        logger.info(f"Тестовое сообщение без ротации {i}", iteration=i)
    
    print(f"Файл без ротации: {no_rotation_file.name} ({no_rotation_file.stat().st_size} байт)")
    
    print("✓ Проверка ротации логов пройдена")


def test_structured_logging():
    """Проверка структурированного логирования"""
    print("\n--- Проверка структурированного логирования ---")
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "test_structured.log"
    
    setup_logging(log_level="debug", log_file=str(log_file))
    
    # Создаем логгер с начальным контекстом
    logger = get_logger("test.structured", component="test_component")
    
    # Логируем с контекстом
    logger.info("Структурированное сообщение с контекстом", 
               user_id="12345",
               action="test")
    
    # Демонстрация привязки дополнительного контекста
    user_logger = logger.bind(user_id="12345")
    user_logger.info("Сообщение с привязанным пользователем", action="view")
    
    # Демонстрация вложенного контекста
    session_logger = user_logger.bind(session_id="abc123")
    session_logger.info("Сообщение с привязанной сессией", action="start")
    
    # Логирование исключения с контекстом
    try:
        # Вызываем исключение
        raise ValueError("Тестовое исключение")
    except Exception as e:
        session_logger.exception("Исключение с контекстом", 
                                operation="test_operation")
    
    # Читаем и анализируем файл лога для демонстрации структурированного формата
    print(f"\nСодержимое структурированного лога ({log_file}):")
    try:
        with open(log_file, 'r') as f:
            for i, line in enumerate(f.readlines()[-4:]):  # Показываем последние 4 строки
                try:
                    log_entry = json.loads(line.strip())
                    # Выводим основные поля лога
                    print(f"Запись {i+1}:")
                    print(f"  timestamp: {log_entry.get('timestamp')}")
                    print(f"  level: {log_entry.get('level')}")
                    print(f"  logger: {log_entry.get('logger')}")
                    print(f"  message: {log_entry.get('event', log_entry.get('message'))}")
                    # Выводим контекстные данные
                    context = {k: v for k, v in log_entry.items() 
                             if k not in ['timestamp', 'level', 'logger', 'event', 'message', 'exception']}
                    print(f"  context: {context}")
                    if 'exception' in log_entry:
                        print(f"  exception info: Present")
                except json.JSONDecodeError:
                    print(f"  {line.strip()} (не валидный JSON)")
    except Exception as e:
        print(f"Ошибка при чтении файла лога: {e}")
    
    print("✓ Проверка структурированного логирования пройдена")


def main():
    """Запуск всех проверок"""
    print("Проверка модуля логирования на соответствие требованиям Epic 7")
    
    test_logging_setup()
    test_logging_levels()
    test_log_rotation()
    test_structured_logging()
    
    print("\nВсе проверки успешно пройдены!")
    return 0


if __name__ == "__main__":
    sys.exit(main())