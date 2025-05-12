#!/usr/bin/env python3
"""
Настройка и проверка API-ключей для meet2obsidian.

Этот скрипт помогает настроить и проверить API-ключи для Rev.ai и Claude,
сохраняя их безопасно в системном хранилище ключей.

Использование:
    python setup_api_keys.py --revai <КЛЮЧ> --claude <КЛЮЧ>  # Настройка API-ключей
    python setup_api_keys.py --test                          # Проверка существующих API-ключей
    python setup_api_keys.py --status                        # Проверка наличия API-ключей
    python setup_api_keys.py --list                          # Вывод всех API-ключей
    python setup_api_keys.py --delete rev_ai                 # Удаление API-ключа
"""

import argparse
import sys
import os
import requests
import anthropic
import time
import getpass
from typing import Dict, List, Optional, Any, Union

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from meet2obsidian.utils.logging import setup_logging, get_logger
    from meet2obsidian.utils.security import KeychainManager
    has_logging = True
except ImportError:
    import logging
    has_logging = False
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger("setup_api_keys")

def test_rev_ai_key(api_key):
    """Проверяет, является ли ключ Rev.ai API действительным, выполняя тестовый запрос."""
    url = "https://api.rev.ai/speechtotext/v1/account"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    logger = get_logger("setup_api_keys") if has_logging else logging.getLogger("setup_api_keys")
    logger.info("Проверка API-ключа Rev.ai...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            account_info = response.json()
            logger.info(f"API-ключ Rev.ai действителен. Аккаунт: {account_info.get('email')}")
            return True
        else:
            logger.error(f"Проверка API-ключа Rev.ai не удалась: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке API-ключа Rev.ai: {str(e)}")
        return False

def test_claude_key(api_key):
    """Проверяет, является ли ключ Claude API действительным, выполняя тестовый запрос."""
    logger = get_logger("setup_api_keys") if has_logging else logging.getLogger("setup_api_keys")
    logger.info("Проверка API-ключа Claude...")
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Say hello"}
            ]
        )
        if response:
            logger.info("API-ключ Claude действителен.")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке API-ключа Claude: {str(e)}")
        return False

def setup_api_keys(args):
    """Настраивает API-ключи на основе аргументов командной строки."""
    logger = get_logger("setup_api_keys") if has_logging else logging.getLogger("setup_api_keys")
    keychain = KeychainManager(logger)
    
    # Отслеживаем общий успех
    all_successful = True
    
    # Обработка ключа Rev.ai API
    if args.revai:
        logger.info("Настройка API-ключа Rev.ai...")
        
        # Сначала проверяем ключ
        if test_rev_ai_key(args.revai):
            # Сохраняем ключ в хранилище
            if keychain.store_api_key("rev_ai", args.revai):
                logger.info("API-ключ Rev.ai успешно сохранен.")
                print("API-ключ Rev.ai: Настроен ✓")
            else:
                logger.error("Не удалось сохранить API-ключ Rev.ai.")
                print("API-ключ Rev.ai: Не удалось сохранить ✗")
                all_successful = False
        else:
            logger.error("Проверка API-ключа Rev.ai не удалась. Ключ не сохранен.")
            print("API-ключ Rev.ai: Недействителен ✗")
            all_successful = False
    elif args.test or args.status:
        # Просто проверяем, существует ли ключ и является ли он действительным
        api_key = keychain.get_api_key("rev_ai")
        if api_key:
            if args.test:
                valid = test_rev_ai_key(api_key)
                status = "Действителен ✓" if valid else "Недействителен ✗"
            else:
                status = "Настроен"
            print(f"API-ключ Rev.ai: {status}")
        else:
            print("API-ключ Rev.ai: Не настроен ✗")
            all_successful = False
    
    # Обработка ключа Claude API
    if args.claude:
        logger.info("Настройка API-ключа Claude...")
        
        # Сначала проверяем ключ
        if test_claude_key(args.claude):
            # Сохраняем ключ в хранилище
            if keychain.store_api_key("claude", args.claude):
                logger.info("API-ключ Claude успешно сохранен.")
                print("API-ключ Claude: Настроен ✓")
            else:
                logger.error("Не удалось сохранить API-ключ Claude.")
                print("API-ключ Claude: Не удалось сохранить ✗")
                all_successful = False
        else:
            logger.error("Проверка API-ключа Claude не удалась. Ключ не сохранен.")
            print("API-ключ Claude: Недействителен ✗")
            all_successful = False
    elif args.test or args.status:
        # Просто проверяем, существует ли ключ и является ли он действительным
        api_key = keychain.get_api_key("claude")
        if api_key:
            if args.test:
                valid = test_claude_key(api_key)
                status = "Действителен ✓" if valid else "Недействителен ✗"
            else:
                status = "Настроен"
            print(f"API-ключ Claude: {status}")
        else:
            print("API-ключ Claude: Не настроен ✗")
            all_successful = False
    
    # Если запрошен просмотр всех ключей
    if args.list:
        print("\nСтатус всех API-ключей:")
        print("------------------------")
        statuses = keychain.get_api_keys_status()
        for key_name, exists in statuses.items():
            status = "Настроен" if exists else "Не настроен"
            print(f"{key_name.ljust(10)}: {status}")
    
    return all_successful

def prompt_api_key(key_name: str, allow_empty: bool = False) -> Optional[str]:
    """
    Запрашивает у пользователя API-ключ с маскированным вводом.

    Args:
        key_name: Название ключа для запроса
        allow_empty: Разрешить пустое значение

    Returns:
        str или None: Введенное значение или None, если ввод пустой и allow_empty=False
    """
    logger = get_logger("setup_api_keys") if has_logging else logging.getLogger("setup_api_keys")

    prompt_text = f"Введите API-ключ для {key_name}: "
    api_key = getpass.getpass(prompt_text)

    if not api_key and not allow_empty:
        logger.warning(f"API-ключ для {key_name} не был введен.")
        return None

    return api_key

def delete_api_key(key_name: str) -> bool:
    """
    Удаляет API-ключ из хранилища.

    Args:
        key_name: Название ключа для удаления

    Returns:
        bool: True в случае успеха, False при ошибке
    """
    logger = get_logger("setup_api_keys") if has_logging else logging.getLogger("setup_api_keys")
    keychain = KeychainManager(logger)

    logger.info(f"Удаление API-ключа {key_name}...")

    # Проверка существования ключа
    if not keychain.key_exists(key_name):
        logger.warning(f"API-ключ {key_name} не найден в хранилище.")
        print(f"API-ключ {key_name}: Не найден ✗")
        return False

    # Запрос подтверждения
    confirm = input(f"Вы уверены, что хотите удалить API-ключ {key_name}? (y/N): ")
    if confirm.lower() not in ["y", "yes"]:
        logger.info("Удаление отменено пользователем.")
        print("Удаление отменено.")
        return False

    # Удаление ключа
    result = keychain.delete_api_key(key_name)
    if result:
        logger.info(f"API-ключ {key_name} успешно удален.")
        print(f"API-ключ {key_name}: Удален ✓")
        return True
    else:
        logger.error(f"Не удалось удалить API-ключ {key_name}.")
        print(f"API-ключ {key_name}: Не удалось удалить ✗")
        return False

def main():
    """Разбор аргументов и запуск скрипта."""
    parser = argparse.ArgumentParser(description="Настройка API-ключей для meet2obsidian")

    # Аргументы для API-ключей
    parser.add_argument('--revai', help='API-ключ Rev.ai')
    parser.add_argument('--claude', help='API-ключ Claude')

    # Аргументы для действий
    parser.add_argument('--test', action='store_true', help='Проверить существующие ключи')
    parser.add_argument('--status', action='store_true', help='Показать статус API-ключей')
    parser.add_argument('--list', action='store_true', help='Показать список всех API-ключей')
    parser.add_argument('--delete', metavar='KEY_NAME', help='Удалить указанный API-ключ')
    parser.add_argument('--interactive', '-i', action='store_true', help='Запустить в интерактивном режиме')
    parser.add_argument('--verbose', '-v', action='store_true', help='Включить подробное логирование')

    args = parser.parse_args()

    # Настройка логирования
    if has_logging:
        log_level = "DEBUG" if args.verbose else "INFO"
        setup_logging(log_level=log_level, add_console_handler=True)
    else:
        logging_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(level=logging_level)

    logger = get_logger("setup_api_keys") if has_logging else logging.getLogger("setup_api_keys")

    # Интерактивный режим
    if args.interactive:
        logger.info("Запуск в интерактивном режиме...")
        print("=== Интерактивная настройка API-ключей ===")

        # Запрос ключей у пользователя
        revai_key = prompt_api_key("Rev.ai", allow_empty=True)
        claude_key = prompt_api_key("Claude", allow_empty=True)

        # Обновление аргументов
        if revai_key:
            args.revai = revai_key
        if claude_key:
            args.claude = claude_key

    # Удаление ключа
    if args.delete:
        return 0 if delete_api_key(args.delete) else 1

    # Если не указаны аргументы, показываем справку
    if not any([args.revai, args.claude, args.test, args.status, args.list, args.interactive]):
        parser.print_help()
        return 1

    # Запускаем настройку
    success = setup_api_keys(args)

    # Возвращаем соответствующий код выхода
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())