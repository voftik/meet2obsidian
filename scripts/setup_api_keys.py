#!/usr/bin/env python3

import argparse
import logging
import sys
import requests
import anthropic
import os
import sys

# Добавляем родительскую директорию в путь, чтобы импортировать модули проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from meet2obsidian.utils.security import KeychainManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("api_key_setup")

def test_rev_ai_key(api_key):
    """Проверка валидности ключа Rev.ai API"""
    url = "https://api.rev.ai/speechtotext/v1/account"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            account_info = response.json()
            logger.info(f"Rev.ai API key is valid. Account: {account_info.get('email')}")
            return True
        else:
            logger.error(f"Rev.ai API key validation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking Rev.ai API key: {str(e)}")
        return False

def test_claude_key(api_key):
    """Проверка валидности ключа Claude API"""
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
            logger.info("Claude API key is valid.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking Claude API key: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Setup API keys for meet2obsidian")
    parser.add_argument('--revai', help='Rev.ai API key')
    parser.add_argument('--claude', help='Claude API key')
    parser.add_argument('--test', action='store_true', help='Only test existing keys')
    
    args = parser.parse_args()
    
    keychain = KeychainManager(logger)
    
    # Проверка ключей Rev.ai
    if args.test or not args.revai:
        existing_key = keychain.get_api_key("rev_ai")
        if existing_key:
            logger.info("Testing existing Rev.ai API key...")
            test_rev_ai_key(existing_key)
        else:
            logger.warning("No Rev.ai API key found in Keychain.")
    
    if args.revai:
        logger.info("Testing provided Rev.ai API key...")
        if test_rev_ai_key(args.revai):
            keychain.store_api_key("rev_ai", args.revai)
    
    # Проверка ключей Claude
    if args.test or not args.claude:
        existing_key = keychain.get_api_key("claude")
        if existing_key:
            logger.info("Testing existing Claude API key...")
            test_claude_key(existing_key)
        else:
            logger.warning("No Claude API key found in Keychain.")
    
    if args.claude:
        logger.info("Testing provided Claude API key...")
        if test_claude_key(args.claude):
            keychain.store_api_key("claude", args.claude)
    
    # Если не указаны аргументы, выводим справку
    if not (args.revai or args.claude or args.test):
        parser.print_help()

if __name__ == "__main__":
    main()
    #!/usr/bin/env python3

import argparse
import logging
import sys
import requests
import anthropic
import os
import sys

# Добавляем родительскую директорию в путь, чтобы импортировать модули проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from meet2obsidian.utils.security import KeychainManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("api_key_setup")

def test_rev_ai_key(api_key):
    """Проверка валидности ключа Rev.ai API"""
    url = "https://api.rev.ai/speechtotext/v1/account"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            account_info = response.json()
            logger.info(f"Rev.ai API key is valid. Account: {account_info.get('email')}")
            return True
        else:
            logger.error(f"Rev.ai API key validation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking Rev.ai API key: {str(e)}")
        return False

def test_claude_key(api_key):
    """Проверка валидности ключа Claude API"""
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
            logger.info("Claude API key is valid.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking Claude API key: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Setup API keys for meet2obsidian")
    parser.add_argument('--revai', help='Rev.ai API key')
    parser.add_argument('--claude', help='Claude API key')
    parser.add_argument('--test', action='store_true', help='Only test existing keys')
    
    args = parser.parse_args()
    
    keychain = KeychainManager(logger)
    
    # Проверка ключей Rev.ai
    if args.test or not args.revai:
        existing_key = keychain.get_api_key("rev_ai")
        if existing_key:
            logger.info("Testing existing Rev.ai API key...")
            test_rev_ai_key(existing_key)
        else:
            logger.warning("No Rev.ai API key found in Keychain.")
    
    if args.revai:
        logger.info("Testing provided Rev.ai API key...")
        if test_rev_ai_key(args.revai):
            keychain.store_api_key("rev_ai", args.revai)
    
    # Проверка ключей Claude
    if args.test or not args.claude:
        existing_key = keychain.get_api_key("claude")
        if existing_key:
            logger.info("Testing existing Claude API key...")
            test_claude_key(existing_key)
        else:
            logger.warning("No Claude API key found in Keychain.")
    
    if args.claude:
        logger.info("Testing provided Claude API key...")
        if test_claude_key(args.claude):
            keychain.store_api_key("claude", args.claude)
    
    # Если не указаны аргументы, выводим справку
    if not (args.revai or args.claude or args.test):
        parser.print_help()

if __name__ == "__main__":
    main()