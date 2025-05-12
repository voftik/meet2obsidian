#!/usr/bin/env python3
"""
Простой пример использования модуля логирования meet2obsidian.

Этот скрипт демонстрирует основные возможности модуля логирования,
включая настройку, получение логгеров, логирование с разными уровнями,
и использование контекстных данных.
"""

import os
import sys
import time

# Добавляем родительскую директорию в путь импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем модуль логирования
from meet2obsidian.utils.logging import setup_logging, get_logger, create_diagnostic_log_entry

def main():
    print("Демонстрация модуля логирования meet2obsidian\n")
    
    # Создаем директорию для логов в текущей директории
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "test.log")
    
    print(f"Настройка логирования с файлом: {log_file}")
    
    # Настраиваем логирование с выводом в файл и консоль
    setup_logging(
        log_level="debug",
        log_file=log_file,
        max_bytes=5 * 1024 * 1024,  # 5 MB
        backup_count=3,
        add_console_handler=True
    )
    
    # Получаем основной логгер
    logger = get_logger("test_main", component="main")
    
    # Создаем диагностическую запись
    print("Создание диагностической записи...")
    create_diagnostic_log_entry(logger, {"app_version": "0.1.0"})
    
    # Логирование с разными уровнями
    print("Логирование с разными уровнями...")
    logger.debug("Это отладочное сообщение", detail="extra debug info")
    logger.info("Это информационное сообщение", status="running")
    logger.warning("Это предупреждение", warning_code=101)
    logger.error("Это сообщение об ошибке", error_code=404)
    
    # Демонстрация контекстного логирования
    print("Демонстрация контекстного логирования...")
    # Создаем логгер с контекстом пользователя
    user_logger = logger.bind(user_id="user123")
    user_logger.info("Действие пользователя", action="login")
    
    # Добавляем еще один уровень контекста
    session_logger = user_logger.bind(session_id="sess456")
    session_logger.info("Действие в сессии", action="view_profile")
    
    # Логирование исключения
    print("Демонстрация логирования исключения...")
    try:
        # Вызываем исключение для примера
        result = 1 / 0
    except Exception as e:
        logger.exception("Произошло исключение", operation="division")
    
    # Проверка вращения файлов логов
    print("Генерация логов для проверки ротации (может занять некоторое время)...")
    for i in range(1000):
        logger.info(f"Тестовое сообщение {i}", data="x" * 100)
    
    print("\nПроверка работы модуля логирования завершена!")
    print(f"Файл лога создан в: {log_file}")
    print("Содержимое файла лога (последние 5 строк):")
    
    # Показываем последние 5 строк файла лога
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(line.strip())
    except Exception as e:
        print(f"Ошибка при чтении файла лога: {e}")
    
    # Проверка ротированных файлов
    rotated_files = [f for f in os.listdir(log_dir) if f.startswith("test.log.")]
    if rotated_files:
        print(f"\nСозданы ротированные файлы: {', '.join(rotated_files)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())