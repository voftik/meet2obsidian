"""
Интеграционные тесты для класса KeychainManager.

Эти тесты взаимодействуют с реальным системным хранилищем ключей.
Они помечены как 'integration' и должны пропускаться в средах CI/CD
или при запуске модульных тестов.

ВНИМАНИЕ: Эти тесты будут создавать и удалять реальные записи в вашем системном хранилище,
но будут использовать специальные тестовые ключи, которые не должны конфликтовать с реальными приложениями.
"""

import unittest
import os
import sys
import pytest
import uuid

from meet2obsidian.utils.security import KeychainManager


@pytest.mark.integration
@pytest.mark.skipif(sys.platform != 'darwin', reason="Тесты для macOS Keychain запускаются только на Darwin")
class TestKeychainManagerIntegration(unittest.TestCase):
    """
    Интеграционные тесты для класса KeychainManager.
    
    Эти тесты взаимодействуют с реальной системой хранения ключей.
    Они должны запускаться только на машинах разработчиков с соответствующими разрешениями.
    """

    def setUp(self):
        """Настройка тестовых объектов."""
        # Генерируем уникальный префикс для тестов, чтобы избежать конфликтов
        self.test_prefix = f"test_keychain_{uuid.uuid4().hex[:8]}"
        
        # Создаем тестовые имена ключей
        self.test_key_name = f"{self.test_prefix}_key"
        self.test_key_value = f"value_{uuid.uuid4().hex}"
        
        # Создаем экземпляр KeychainManager
        self.keychain_manager = KeychainManager()

    def tearDown(self):
        """
        Очистка после тестов.
        
        Этот метод гарантирует, что в хранилище не останутся тестовые ключи.
        """
        # Удаляем все тестовые ключи, созданные во время тестирования
        try:
            self.keychain_manager.delete_api_key(self.test_key_name)
        except:
            pass  # Игнорируем ошибки при очистке

    def test_store_and_retrieve_key(self):
        """Тест сохранения и получения ключа из реального хранилища."""
        # Сохраняем тестовый ключ
        result = self.keychain_manager.store_api_key(self.test_key_name, self.test_key_value)
        self.assertTrue(result, "Не удалось сохранить тестовый ключ в хранилище")
        
        # Получаем тестовый ключ
        retrieved_value = self.keychain_manager.get_api_key(self.test_key_name)
        self.assertEqual(retrieved_value, self.test_key_value,
                         "Полученное значение не соответствует сохраненному")

    def test_delete_key(self):
        """Тест удаления ключа из реального хранилища."""
        # Сначала сохраняем тестовый ключ
        self.keychain_manager.store_api_key(self.test_key_name, self.test_key_value)
        
        # Проверяем, что он сохранен
        self.assertIsNotNone(self.keychain_manager.get_api_key(self.test_key_name),
                            "Тестовый ключ не был сохранен правильно")
        
        # Удаляем тестовый ключ
        result = self.keychain_manager.delete_api_key(self.test_key_name)
        self.assertTrue(result, "Не удалось удалить тестовый ключ из хранилища")
        
        # Проверяем, что он удален
        self.assertIsNone(self.keychain_manager.get_api_key(self.test_key_name),
                         "Тестовый ключ не был удален правильно")

    def test_get_nonexistent_key(self):
        """Тест получения несуществующего ключа."""
        # Пытаемся получить ключ, который не должен существовать
        nonexistent_key = f"{self.test_prefix}_nonexistent_{uuid.uuid4().hex}"
        retrieved_value = self.keychain_manager.get_api_key(nonexistent_key)
        
        # Проверяем, что результат None
        self.assertIsNone(retrieved_value, 
                         "Получение несуществующего ключа должно возвращать None")

    def test_update_existing_key(self):
        """Тест обновления существующего ключа в хранилище."""
        # Сначала сохраняем тестовый ключ
        self.keychain_manager.store_api_key(self.test_key_name, self.test_key_value)
        
        # Проверяем, что он сохранен
        self.assertEqual(self.keychain_manager.get_api_key(self.test_key_name), 
                        self.test_key_value,
                        "Начальное значение ключа не было сохранено правильно")
        
        # Обновляем ключ новым значением
        new_value = f"updated_{uuid.uuid4().hex}"
        result = self.keychain_manager.store_api_key(self.test_key_name, new_value)
        self.assertTrue(result, "Не удалось обновить тестовый ключ в хранилище")
        
        # Проверяем, что ключ был обновлен
        retrieved_value = self.keychain_manager.get_api_key(self.test_key_name)
        self.assertEqual(retrieved_value, new_value,
                        "Обновленное значение ключа не было сохранено правильно")


if __name__ == '__main__':
    unittest.main()