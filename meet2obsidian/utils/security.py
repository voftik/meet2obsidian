"""
Утилиты безопасности для meet2obsidian.

Этот модуль предоставляет функции и классы для операций, связанных с безопасностью,
таких как безопасное хранение и получение API-ключей с использованием системного хранилища ключей.
"""

import logging
import keyring
from typing import Optional, Dict, Any, List


class KeychainManager:
    """
    Управление API-ключами через macOS Keychain.

    Этот класс предоставляет методы для безопасного хранения, извлечения и управления
    API-ключами с использованием macOS Keychain через библиотеку keyring. Он обрабатывает
    общие операции, такие как сохранение, получение и удаление API-ключей с
    корректной обработкой ошибок и логированием.

    Attributes:
        SERVICE_NAME: Имя сервиса, используемое для всех записей в keychain.

    Example:
        >>> from meet2obsidian.utils.logging import setup_logging, get_logger
        >>> from meet2obsidian.utils.security import KeychainManager
        >>>
        >>> # Настройка логирования и создание менеджера keychain
        >>> setup_logging(level="info")
        >>> logger = get_logger("my_component")
        >>> keychain = KeychainManager(logger=logger)
        >>>
        >>> # Сохранение API-ключа
        >>> keychain.store_api_key("rev_ai", "my_api_key_value")
        >>>
        >>> # Получение API-ключа
        >>> api_key = keychain.get_api_key("rev_ai")
        >>> if api_key:
        >>>     # Использование API-ключа
        >>>     print(f"API-ключ найден: {api_key[:4]}***")
        >>>
        >>> # Проверка существования ключа
        >>> if keychain.key_exists("claude"):
        >>>     print("API-ключ Claude существует")
        >>>
        >>> # Удаление API-ключа
        >>> keychain.delete_api_key("test_key")
    """

    SERVICE_NAME = "meet2obsidian"

    def __init__(self, logger=None):
        """
        Инициализация менеджера ключей.

        Args:
            logger: Объект логгера (опционально). Если не указан, создается новый логгер.
        """
        self.logger = logger or logging.getLogger(__name__)

    def store_api_key(self, key_name: str, api_key: str) -> bool:
        """
        Сохранение API-ключа в хранилище.

        Args:
            key_name: Название ключа (например, 'rev_ai', 'claude')
            api_key: Значение API-ключа

        Returns:
            bool: True в случае успеха, False при ошибке
        """
        if not key_name:
            self.logger.error("Невозможно сохранить API-ключ: имя ключа не может быть пустым")
            return False

        if not api_key:
            self.logger.warning(f"Сохранение пустого API-ключа для {key_name}")

        # Проверка, существует ли ключ (для целей логирования)
        key_exists = self.key_exists(key_name)

        try:
            keyring.set_password(self.SERVICE_NAME, key_name, api_key)

            if key_exists:
                self.logger.info(f"API-ключ {key_name} успешно обновлен в хранилище")
            else:
                self.logger.info(f"API-ключ {key_name} успешно сохранен в хранилище")

            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении API-ключа {key_name}: {str(e)}")
            return False

    def get_api_key(self, key_name: str) -> Optional[str]:
        """
        Получение API-ключа из хранилища.

        Args:
            key_name: Название ключа

        Returns:
            str или None: Значение API-ключа, если найден, иначе None
        """
        if not key_name:
            self.logger.error("Невозможно получить API-ключ: имя ключа не может быть пустым")
            return None

        try:
            api_key = keyring.get_password(self.SERVICE_NAME, key_name)
            if api_key:
                self.logger.debug(f"API-ключ {key_name} успешно получен из хранилища")
                return api_key
            else:
                self.logger.warning(f"API-ключ {key_name} не найден в хранилище")
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении API-ключа {key_name}: {str(e)}")
            return None

    def delete_api_key(self, key_name: str) -> bool:
        """
        Удаление API-ключа из хранилища.

        Args:
            key_name: Название ключа

        Returns:
            bool: True в случае успеха, False при ошибке
        """
        if not key_name:
            self.logger.error("Невозможно удалить API-ключ: имя ключа не может быть пустым")
            return False

        # Проверка существования ключа перед удалением
        if not self.key_exists(key_name):
            self.logger.warning(f"Невозможно удалить API-ключ {key_name}: ключ не найден")
            return False

        try:
            keyring.delete_password(self.SERVICE_NAME, key_name)
            self.logger.info(f"API-ключ {key_name} успешно удален из хранилища")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при удалении API-ключа {key_name}: {str(e)}")
            return False

    def key_exists(self, key_name: str) -> bool:
        """
        Проверка существования API-ключа в хранилище.

        Args:
            key_name: Название ключа для проверки

        Returns:
            bool: True если ключ существует, False в противном случае
        """
        if not key_name:
            self.logger.error("Невозможно проверить API-ключ: имя ключа не может быть пустым")
            return False

        try:
            api_key = keyring.get_password(self.SERVICE_NAME, key_name)
            return api_key is not None
        except Exception as e:
            self.logger.error(f"Ошибка при проверке API-ключа {key_name}: {str(e)}")
            return False

    def get_api_keys_status(self) -> Dict[str, bool]:
        """
        Получение статуса необходимых API-ключей.

        Возвращает словарь со статусом каждого необходимого API-ключа.

        Returns:
            Dict[str, bool]: Словарь, где ключи - имена API-ключей, значения - статус существования
        """
        required_keys = ["rev_ai", "claude"]
        return {key: self.key_exists(key) for key in required_keys}

    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Маскирование API-ключа для безопасного отображения.

        Args:
            api_key: API-ключ для маскирования
            visible_chars: Количество символов, которые останутся видимыми в начале

        Returns:
            str: Маскированная строка API-ключа
        """
        if not api_key:
            return ""

        if len(api_key) <= visible_chars:
            return api_key

        return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)