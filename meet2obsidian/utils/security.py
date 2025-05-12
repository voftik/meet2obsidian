"""
Утилиты безопасности для meet2obsidian.

Этот модуль предоставляет функции и классы для операций, связанных с безопасностью,
таких как безопасное хранение и получение API-ключей с использованием системного хранилища ключей.
"""

import logging
import keyring
from typing import Optional


class KeychainManager:
    """
    Управление API-ключами через macOS Keychain.
    Обеспечивает безопасное хранение и извлечение ключей API.
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

        try:
            keyring.set_password(self.SERVICE_NAME, key_name, api_key)
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

        try:
            keyring.delete_password(self.SERVICE_NAME, key_name)
            self.logger.info(f"API-ключ {key_name} успешно удален из хранилища")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при удалении API-ключа {key_name}: {str(e)}")
            return False