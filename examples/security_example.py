#!/usr/bin/env python3
"""
Пример использования модуля безопасного хранения API-ключей meet2obsidian.

Этот скрипт демонстрирует основные возможности модуля безопасности,
включая сохранение, получение и удаление API-ключей.
"""

import os
import sys

# Добавляем родительскую директорию в путь импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем модули
from meet2obsidian.utils.security import KeychainManager
try:
    from meet2obsidian.utils.logging import setup_logging, get_logger
    has_logging = True
except ImportError:
    has_logging = False
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger("security_example")

def main():
    """Демонстрация работы с API-ключами."""
    print("Демонстрация модуля безопасного хранения API-ключей meet2obsidian\n")
    
    # Настройка логирования
    if has_logging:
        setup_logging(log_level="INFO")
        logger = get_logger("security_example")
    else:
        logger = logging.getLogger("security_example")
    
    # Создаем экземпляр KeychainManager
    keychain_manager = KeychainManager(logger=logger)
    
    # Примеры ключей для демонстрации
    test_key_name = "test_demo_key"
    test_key_value = "this_is_a_test_api_key_value_123456"
    
    print(f"1. Сохранение API-ключа '{test_key_name}'")
    result = keychain_manager.store_api_key(test_key_name, test_key_value)
    if result:
        print("✓ API-ключ успешно сохранен")
    else:
        print("✗ Ошибка при сохранении API-ключа")
    
    print(f"\n2. Получение API-ключа '{test_key_name}'")
    retrieved_key = keychain_manager.get_api_key(test_key_name)
    if retrieved_key:
        print(f"✓ API-ключ успешно получен: {retrieved_key[:5]}{'*' * (len(retrieved_key) - 5)}")
        print(f"  Соответствие оригиналу: {'Да' if retrieved_key == test_key_value else 'Нет'}")
    else:
        print("✗ API-ключ не найден")
    
    print(f"\n3. Удаление API-ключа '{test_key_name}'")
    result = keychain_manager.delete_api_key(test_key_name)
    if result:
        print("✓ API-ключ успешно удален")
    else:
        print("✗ Ошибка при удалении API-ключа")
    
    # Проверка удаления
    print(f"\n4. Проверка удаления API-ключа '{test_key_name}'")
    retrieved_key = keychain_manager.get_api_key(test_key_name)
    if retrieved_key is None:
        print("✓ API-ключ успешно удален (не найден при запросе)")
    else:
        print("✗ API-ключ все еще существует")
    
    # Обработка ошибок
    print("\n5. Обработка ошибок")
    
    print("  5.1. Пустое имя ключа")
    result = keychain_manager.store_api_key("", "some_value")
    if not result:
        print("  ✓ Пустое имя ключа корректно обработано")
    
    print("  5.2. Пустое значение ключа")
    result = keychain_manager.store_api_key("empty_value_key", "")
    if result:
        print("  ✓ Пустое значение ключа корректно сохранено (с предупреждением)")
        # Очистка после теста
        keychain_manager.delete_api_key("empty_value_key")
    
    print("\nПроверка модуля безопасного хранения API-ключей завершена!")
    return 0

if __name__ == "__main__":
    sys.exit(main())