"""
Security utilities for meet2obsidian.

This module provides functions and classes for security-related operations,
such as securely storing and retrieving API keys using the system keychain.
"""

import logging
import keyring
from typing import Optional, Dict, Any, List


class KeychainManager:
    """
    Manage API keys through macOS Keychain.

    This class provides methods for securely storing, retrieving, and managing
    API keys using macOS Keychain through the keyring library. It handles
    common operations such as saving, retrieving, and deleting API keys with
    proper error handling and logging.

    Attributes:
        SERVICE_NAME: Service name used for all keychain entries.

    Example:
        >>> from meet2obsidian.utils.logging import setup_logging, get_logger
        >>> from meet2obsidian.utils.security import KeychainManager
        >>>
        >>> # Set up logging and create a keychain manager
        >>> setup_logging(level="info")
        >>> logger = get_logger("my_component")
        >>> keychain = KeychainManager(logger=logger)
        >>>
        >>> # Store an API key
        >>> keychain.store_api_key("rev_ai", "my_api_key_value")
        >>>
        >>> # Retrieve an API key
        >>> api_key = keychain.get_api_key("rev_ai")
        >>> if api_key:
        >>>     # Use the API key
        >>>     print(f"API key found: {api_key[:4]}***")
        >>>
        >>> # Check if a key exists
        >>> if keychain.key_exists("claude"):
        >>>     print("Claude API key exists")
        >>>
        >>> # Delete an API key
        >>> keychain.delete_api_key("test_key")
    """

    SERVICE_NAME = "meet2obsidian"

    def __init__(self, logger=None):
        """
        Initialize the key manager.

        Args:
            logger: Logger object (optional). If not provided, a new logger is created.
        """
        self.logger = logger or logging.getLogger(__name__)

    def store_api_key(self, key_name: str, api_key: str) -> bool:
        """
        Store an API key in the keychain.

        Args:
            key_name: Key name (e.g., 'rev_ai', 'claude')
            api_key: API key value

        Returns:
            bool: True on success, False on error
        """
        if not key_name:
            self.logger.error("Cannot store API key: key name cannot be empty")
            return False

        if not api_key:
            self.logger.warning(f"Storing empty API key for {key_name}")

        # Check if the key already exists (for logging purposes)
        key_exists = self.key_exists(key_name)

        try:
            keyring.set_password(self.SERVICE_NAME, key_name, api_key)

            if key_exists:
                self.logger.info(f"API key {key_name} successfully updated in the keychain")
            else:
                self.logger.info(f"API key {key_name} successfully stored in the keychain")

            return True
        except Exception as e:
            self.logger.error(f"Error storing API key {key_name}: {str(e)}")
            return False

    def get_api_key(self, key_name: str) -> Optional[str]:
        """
        Retrieve an API key from the keychain.

        Args:
            key_name: Key name

        Returns:
            str or None: API key value if found, otherwise None
        """
        if not key_name:
            self.logger.error("Cannot retrieve API key: key name cannot be empty")
            return None

        try:
            api_key = keyring.get_password(self.SERVICE_NAME, key_name)
            if api_key:
                self.logger.debug(f"API key {key_name} successfully retrieved from the keychain")
                return api_key
            else:
                self.logger.warning(f"API key {key_name} not found in the keychain")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving API key {key_name}: {str(e)}")
            return None

    def delete_api_key(self, key_name: str) -> bool:
        """
        Delete an API key from the keychain.

        Args:
            key_name: Key name

        Returns:
            bool: True on success, False on error
        """
        if not key_name:
            self.logger.error("Cannot delete API key: key name cannot be empty")
            return False

        # Check key existence before deletion
        if not self.key_exists(key_name):
            self.logger.warning(f"Cannot delete API key {key_name}: key not found")
            return False

        try:
            keyring.delete_password(self.SERVICE_NAME, key_name)
            self.logger.info(f"API key {key_name} successfully deleted from the keychain")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting API key {key_name}: {str(e)}")
            return False

    def key_exists(self, key_name: str) -> bool:
        """
        Check if an API key exists in the keychain.

        Args:
            key_name: Key name to check

        Returns:
            bool: True if the key exists, False otherwise
        """
        if not key_name:
            self.logger.error("Cannot check API key: key name cannot be empty")
            return False

        try:
            api_key = keyring.get_password(self.SERVICE_NAME, key_name)
            return api_key is not None
        except Exception as e:
            self.logger.error(f"Error checking API key {key_name}: {str(e)}")
            return False

    def get_api_keys_status(self) -> Dict[str, bool]:
        """
        Get the status of required API keys.

        Returns a dictionary with the status of each required API key.

        Returns:
            Dict[str, bool]: Dictionary where keys are API key names and values are existence status
        """
        required_keys = ["rev_ai", "claude"]
        return {key: self.key_exists(key) for key in required_keys}

    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key for secure display.

        Args:
            api_key: API key to mask
            visible_chars: Number of characters to keep visible at the beginning

        Returns:
            str: Masked API key string
        """
        if not api_key:
            return ""

        if len(api_key) <= visible_chars:
            return api_key

        return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)