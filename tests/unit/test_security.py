"""
Тесты для модуля безопасного хранения API-ключей.

Модульные тесты для класса KeychainManager в meet2obsidian.utils.security,
который отвечает за безопасное хранение и получение API-ключей
из системного хранилища ключей.
"""

import unittest
from unittest.mock import patch, MagicMock
import logging
import keyring
import sys

# Импортируем тестируемый класс
from meet2obsidian.utils.security import KeychainManager


class TestKeychainManager(unittest.TestCase):
    """Тесты для класса KeychainManager."""

    def setUp(self):
        """Настройка тестовых объектов."""
        # Создаем мок логгера для тестирования
        self.mock_logger = MagicMock(spec=logging.Logger)
        
        # Тестовые данные
        self.service_name = "meet2obsidian"
        self.key_name = "test_api"
        self.api_key = "test_api_key_value"
        
        # Создаем экземпляр с мок-логгером
        self.keychain_manager = KeychainManager(logger=self.mock_logger)

    def tearDown(self):
        """Очистка после тестов."""
        pass

    @patch('keyring.set_password')
    def test_store_api_key_success(self, mock_set_password):
        """Тест успешного сохранения API-ключа."""
        # Настраиваем мок для успешного выполнения
        mock_set_password.return_value = None
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.store_api_key(self.key_name, self.api_key)
        
        # Проверяем результат
        self.assertTrue(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_set_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            self.key_name, 
            self.api_key
        )
        
        # Проверяем логирование
        self.mock_logger.info.assert_called_once()

    @patch('keyring.set_password')
    def test_store_api_key_error(self, mock_set_password):
        """Тест обработки ошибок при сохранении API-ключа."""
        # Настраиваем мок для генерации исключения
        mock_set_password.side_effect = Exception("Test error")
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.store_api_key(self.key_name, self.api_key)
        
        # Проверяем результат
        self.assertFalse(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_set_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            self.key_name, 
            self.api_key
        )
        
        # Проверяем логирование ошибки
        self.mock_logger.error.assert_called_once()

    @patch('keyring.get_password')
    def test_get_api_key_success(self, mock_get_password):
        """Тест успешного получения API-ключа."""
        # Настраиваем мок для возврата значения
        mock_get_password.return_value = self.api_key
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.get_api_key(self.key_name)
        
        # Проверяем результат
        self.assertEqual(result, self.api_key)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_get_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            self.key_name
        )
        
        # Проверяем логирование
        self.mock_logger.debug.assert_called_once()

    @patch('keyring.get_password')
    def test_get_api_key_not_found(self, mock_get_password):
        """Тест получения несуществующего API-ключа."""
        # Настраиваем мок для возврата None (ключ не найден)
        mock_get_password.return_value = None
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.get_api_key(self.key_name)
        
        # Проверяем результат
        self.assertIsNone(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_get_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            self.key_name
        )
        
        # Проверяем предупреждение в логе
        self.mock_logger.warning.assert_called_once()

    @patch('keyring.get_password')
    def test_get_api_key_error(self, mock_get_password):
        """Тест обработки ошибок при получении API-ключа."""
        # Настраиваем мок для генерации исключения
        mock_get_password.side_effect = Exception("Test error")
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.get_api_key(self.key_name)
        
        # Проверяем результат
        self.assertIsNone(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_get_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            self.key_name
        )
        
        # Проверяем логирование ошибки
        self.mock_logger.error.assert_called_once()

    @patch('keyring.delete_password')
    def test_delete_api_key_success(self, mock_delete_password):
        """Тест успешного удаления API-ключа."""
        # Настраиваем мок для успешного выполнения
        mock_delete_password.return_value = None
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.delete_api_key(self.key_name)
        
        # Проверяем результат
        self.assertTrue(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_delete_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            self.key_name
        )
        
        # Проверяем логирование
        self.mock_logger.info.assert_called_once()

    @patch('keyring.delete_password')
    def test_delete_api_key_error(self, mock_delete_password):
        """Тест обработки ошибок при удалении API-ключа."""
        # Настраиваем мок для генерации исключения
        mock_delete_password.side_effect = Exception("Test error")
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.delete_api_key(self.key_name)
        
        # Проверяем результат
        self.assertFalse(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_delete_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            self.key_name
        )
        
        # Проверяем логирование ошибки
        self.mock_logger.error.assert_called_once()

    def test_store_api_key_empty_key(self):
        """Тест сохранения API-ключа с пустым именем."""
        # Вызываем тестируемый метод с пустым именем ключа
        result = self.keychain_manager.store_api_key("", self.api_key)
        
        # Проверяем результат - должен быть False, т.к. пустые имена ключей должны отклоняться
        self.assertFalse(result)
        
        # Проверяем логирование ошибки
        self.mock_logger.error.assert_called_once()

    def test_store_api_key_empty_value(self):
        """Тест сохранения пустого значения API-ключа."""
        # Вызываем тестируемый метод с пустым значением ключа
        result = self.keychain_manager.store_api_key(self.key_name, "")
        
        # Предполагаем, что пустые значения разрешены, но вызывают предупреждение
        self.assertTrue(result)
        
        # Проверяем логирование предупреждения
        self.mock_logger.warning.assert_called_once()

    def test_get_api_key_empty_key(self):
        """Тест получения API-ключа с пустым именем."""
        # Вызываем тестируемый метод с пустым именем ключа
        result = self.keychain_manager.get_api_key("")
        
        # Проверяем результат - должен быть None, т.к. пустые имена ключей должны отклоняться
        self.assertIsNone(result)
        
        # Проверяем логирование ошибки
        self.mock_logger.error.assert_called_once()

    def test_delete_api_key_empty_key(self):
        """Тест удаления API-ключа с пустым именем."""
        # Вызываем тестируемый метод с пустым именем ключа
        result = self.keychain_manager.delete_api_key("")
        
        # Проверяем результат - должен быть False, т.к. пустые имена ключей должны отклоняться
        self.assertFalse(result)
        
        # Проверяем логирование ошибки
        self.mock_logger.error.assert_called_once()


class TestKeychainManagerEdgeCases(unittest.TestCase):
    """Тесты для граничных случаев и специальных сценариев."""

    def setUp(self):
        """Настройка тестовых объектов."""
        # Создаем мок логгера для тестирования
        self.mock_logger = MagicMock(spec=logging.Logger)
        
        # Создаем экземпляр с мок-логгером
        self.keychain_manager = KeychainManager(logger=self.mock_logger)

    @patch('keyring.set_password')
    def test_store_special_characters(self, mock_set_password):
        """Тест сохранения ключа со специальными символами."""
        # Специальные символы в имени и значении ключа
        key_name = "test!@#$%^&*()"
        api_key = "value!@#$%^&*()"
        
        # Настраиваем мок для успешного выполнения
        mock_set_password.return_value = None
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.store_api_key(key_name, api_key)
        
        # Проверяем результат
        self.assertTrue(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_set_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            key_name, 
            api_key
        )

    @patch('keyring.set_password')
    def test_store_very_long_key(self, mock_set_password):
        """Тест сохранения очень длинного имени и значения ключа."""
        # Очень длинное имя и значение ключа
        key_name = "x" * 1000
        api_key = "y" * 5000
        
        # Настраиваем мок для успешного выполнения
        mock_set_password.return_value = None
        
        # Вызываем тестируемый метод
        result = self.keychain_manager.store_api_key(key_name, api_key)
        
        # Проверяем результат
        self.assertTrue(result)
        
        # Проверяем, что мок был вызван с правильными аргументами
        mock_set_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            key_name, 
            api_key
        )

    @patch('keyring.get_password')
    @patch('keyring.set_password')
    def test_update_existing_key(self, mock_set_password, mock_get_password):
        """Тест обновления существующего API-ключа."""
        # Начальное значение ключа
        key_name = "test_key"
        initial_value = "initial_value"
        updated_value = "updated_value"
        
        # Настраиваем моки
        mock_get_password.return_value = initial_value
        mock_set_password.return_value = None
        
        # Сначала получаем существующий ключ
        existing_value = self.keychain_manager.get_api_key(key_name)
        self.assertEqual(existing_value, initial_value)
        
        # Теперь обновляем ключ
        result = self.keychain_manager.store_api_key(key_name, updated_value)
        self.assertTrue(result)
        
        # Проверяем, что set_password был вызван с обновленным значением
        mock_set_password.assert_called_once_with(
            self.keychain_manager.SERVICE_NAME, 
            key_name, 
            updated_value
        )

    @unittest.skipIf(sys.platform != 'darwin', "Пропускаем тест, специфичный для macOS")
    def test_service_name_constant(self):
        """Тест правильной установки константы SERVICE_NAME."""
        # Проверяем константу имени сервиса
        self.assertEqual(self.keychain_manager.SERVICE_NAME, "meet2obsidian")


if __name__ == '__main__':
    unittest.main()