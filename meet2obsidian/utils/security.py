import keyring
import logging

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
            logger: Объект логгера (опционально)
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def store_api_key(self, key_name, api_key):
        """
        Сохранение API-ключа в Keychain.
        
        Args:
            key_name (str): Название ключа (например, 'rev_ai', 'claude')
            api_key (str): Значение API-ключа
            
        Returns:
            bool: True в случае успеха, False при ошибке
        """
        try:
            keyring.set_password(self.SERVICE_NAME, key_name, api_key)
            self.logger.info(f"API-ключ {key_name} успешно сохранен в Keychain")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении API-ключа {key_name}: {str(e)}")
            return False
    
    def get_api_key(self, key_name):
        """
        Получение API-ключа из Keychain.
        
        Args:
            key_name (str): Название ключа (например, 'rev_ai', 'claude')
            
        Returns:
            str or None: Значение API-ключа или None при ошибке
        """
        try:
            api_key = keyring.get_password(self.SERVICE_NAME, key_name)
            if api_key:
                self.logger.debug(f"API-ключ {key_name} успешно получен из Keychain")
                return api_key
            else:
                self.logger.warning(f"API-ключ {key_name} не найден в Keychain")
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении API-ключа {key_name}: {str(e)}")
            return None
    
    def delete_api_key(self, key_name):
        """
        Удаление API-ключа из Keychain.
        
        Args:
            key_name (str): Название ключа (например, 'rev_ai', 'claude')
            
        Returns:
            bool: True в случае успеха, False при ошибке
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, key_name)
            self.logger.info(f"API-ключ {key_name} успешно удален из Keychain")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при удалении API-ключа {key_name}: {str(e)}")
            return False
        
        