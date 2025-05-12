#!/usr/bin/env python3
"""
Пример использования модуля безопасности для управления API-ключами.

Этот скрипт демонстрирует, как использовать класс KeychainManager
для хранения, получения и управления API-ключами для meet2obsidian.
"""

import os
import sys
import time
from typing import Optional

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Импортируем необходимые модули
try:
    from meet2obsidian.utils.logging import setup_logging, get_logger
    from meet2obsidian.utils.security import KeychainManager
    has_logging = True
except ImportError:
    import logging
    has_logging = False
    logging.basicConfig(level=logging.INFO)


def print_step(step_number: int, description: str):
    """Печать форматированного заголовка шага."""
    print(f"\n{step_number}. {description}")


def print_result(success: bool, message: str):
    """Печать форматированного сообщения о результате."""
    marker = "✓" if success else "✗"
    print(f"  {marker} {message}")


def main():
    """Запуск примера модуля безопасности."""
    print("Демонстрация системы управления API-ключами meet2obsidian\n")
    
    # Настройка логирования
    if has_logging:
        setup_logging(log_level="INFO", add_console_handler=True)
        logger = get_logger("security_example")
    else:
        logger = logging.getLogger("security_example")
    
    # Создание экземпляра KeychainManager
    keychain = KeychainManager(logger=logger)
    
    # Определение тестовой информации о ключе
    test_key_name = "test_demo_key"
    test_key_value = "this_is_a_test_api_key_for_demonstration"
    
    # Шаг 1: Сохранение API-ключа
    print_step(1, f"Сохранение API-ключа '{test_key_name}'")
    store_result = keychain.store_api_key(test_key_name, test_key_value)
    print_result(store_result, "API-ключ успешно сохранен" if store_result else "Не удалось сохранить API-ключ")
    
    # Шаг 2: Проверка существования ключа
    print_step(2, f"Проверка существования API-ключа '{test_key_name}'")
    key_exists = keychain.key_exists(test_key_name)
    print_result(key_exists, f"API-ключ '{test_key_name}' существует в хранилище")
    
    # Шаг 3: Получение API-ключа
    print_step(3, f"Получение API-ключа '{test_key_name}'")
    retrieved_key = keychain.get_api_key(test_key_name)
    retrieval_success = retrieved_key is not None
    
    # Маскирование ключа перед отображением
    masked_key = keychain.mask_api_key(retrieved_key, visible_chars=6)
    print_result(retrieval_success, f"API-ключ успешно получен: {masked_key}")
    
    # Проверка, что полученный ключ соответствует оригиналу
    if retrieval_success:
        matches = retrieved_key == test_key_value
        print_result(matches, "Полученный ключ соответствует оригинальному ключу")
    
    # Шаг 4: Обновление API-ключа
    print_step(4, f"Обновление API-ключа '{test_key_name}'")
    updated_value = f"{test_key_value}_updated"
    update_result = keychain.store_api_key(test_key_name, updated_value)
    print_result(update_result, "API-ключ успешно обновлен")
    
    # Проверка обновления
    updated_key = keychain.get_api_key(test_key_name)
    update_verified = updated_key == updated_value
    print_result(update_verified, "Обновление API-ключа подтверждено")
    
    # Шаг 5: Удаление API-ключа
    print_step(5, f"Удаление API-ключа '{test_key_name}'")
    delete_result = keychain.delete_api_key(test_key_name)
    print_result(delete_result, "API-ключ успешно удален" if delete_result else "Не удалось удалить API-ключ")
    
    # Шаг 6: Проверка удаления путем проверки существования ключа
    print_step(6, f"Проверка, что API-ключ '{test_key_name}' был удален")
    key_still_exists = keychain.key_exists(test_key_name)
    print_result(not key_still_exists, f"API-ключ '{test_key_name}' больше не существует в хранилище")
    
    # Шаг 7: Демонстрация обработки ошибок для пустых ключей
    print_step(7, "Демонстрация обработки ошибок")
    
    print("  7.1. Пустое имя ключа")
    empty_key_result = keychain.store_api_key("", "some_value")
    print_result(not empty_key_result, "Пустое имя ключа корректно отклонено")
    
    print("  7.2. Пустое значение ключа")
    empty_value_result = keychain.store_api_key("empty_value_test", "")
    print_result(empty_value_result, "Пустое значение ключа обработано корректно (с предупреждением)")
    
    # Очистка тестовых ключей
    keychain.delete_api_key("empty_value_test")
    
    # Шаг 8: Проверка статуса API-ключей
    print_step(8, "Проверка статуса необходимых API-ключей")
    status = keychain.get_api_keys_status()
    
    for key_name, exists in status.items():
        print_result(True, f"API-ключ '{key_name}': {'Настроен' if exists else 'Не настроен'}")
    
    # Шаг 9: Попытка удаления несуществующего ключа
    print_step(9, "Попытка удаления несуществующего ключа")
    non_existent_result = keychain.delete_api_key("non_existent_key")
    print_result(not non_existent_result, "Удаление несуществующего ключа корректно обработано")
    
    print("\nДемонстрация управления API-ключами завершена!")


if __name__ == "__main__":
    main()