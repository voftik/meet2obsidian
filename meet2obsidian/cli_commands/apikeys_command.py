"""
Интерфейс командной строки для управления API-ключами.

Этот модуль предоставляет CLI-команды для установки, получения, вывода списка и удаления
API-ключей, хранящихся в системном хранилище ключей.
"""

import os
import click
import json
from typing import Dict, Optional, Any

from meet2obsidian.utils.logging import get_logger
from meet2obsidian.utils.security import KeychainManager


@click.group()
def apikeys():
    """Управление API-ключами для внешних сервисов."""
    pass


@apikeys.command()
@click.argument('key_name')
@click.option('--value', prompt=True, hide_input=True,
              help='Значение API-ключа. Если не указано, будет запрошено.')
def set(key_name: str, value: str):
    """
    Установить API-ключ в защищенное хранилище.
    
    Примеры:
        meet2obsidian apikeys set rev_ai
        meet2obsidian apikeys set claude --value sk-ant-apiXXXXXX
    """
    logger = get_logger("cli.apikeys")
    keychain = KeychainManager(logger=logger)
    
    # Проверка имени ключа
    if not key_name:
        click.echo("Error: Key name cannot be empty.")
        return
    
    # Сохранение ключа
    result = keychain.store_api_key(key_name, value)
    
    if result:
        click.echo(f"API key '{key_name}' successfully saved to storage.")
    else:
        click.echo(f"Error: Failed to save API key '{key_name}'.")


@apikeys.command()
@click.argument('key_name')
@click.option('--show/--no-show', default=False, 
              help='Показать фактическое значение API-ключа. По умолчанию маскируется.')
def get(key_name: str, show: bool):
    """
    Получить API-ключ из защищенного хранилища.
    
    Примеры:
        meet2obsidian apikeys get rev_ai
        meet2obsidian apikeys get claude --show
    """
    logger = get_logger("cli.apikeys")
    keychain = KeychainManager(logger=logger)
    
    # Проверка существования ключа
    if not keychain.key_exists(key_name):
        click.echo(f"Error: API key '{key_name}' not found.")
        return
    
    # Получение ключа
    api_key = keychain.get_api_key(key_name)
    
    if api_key:
        if show:
            click.echo(f"API-ключ '{key_name}': {api_key}")
        else:
            masked_key = keychain.mask_api_key(api_key, visible_chars=4)
            click.echo(f"API-ключ '{key_name}': {masked_key}")
    else:
        click.echo(f"Error: Failed to get API key '{key_name}'.")


@apikeys.command()
@click.option('--format', '-f', 'format_type', default="table",
              type=click.Choice(['table', 'json'], case_sensitive=False),
              help='Формат вывода для статуса ключей.')
def list(format_type: str):
    """
    Вывести список всех необходимых API-ключей и их статус.
    
    Примеры:
        meet2obsidian apikeys list
        meet2obsidian apikeys list --format json
    """
    logger = get_logger("cli.apikeys")
    keychain = KeychainManager(logger=logger)
    
    # Получение статуса всех необходимых ключей
    status = keychain.get_api_keys_status()
    
    if format_type.lower() == "json":
        # Вывод в формате JSON
        click.echo(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        # Вывод в виде таблицы
        click.echo("API Keys Status:")
        click.echo("------------------------")
        for key_name, exists in status.items():
            status_str = click.style("Configured", fg="green") if exists else click.style("Not configured", fg="red")
            click.echo(f"{key_name.ljust(12)}: {status_str}")


@apikeys.command()
@click.argument('key_name')
@click.confirmation_option(prompt="Are you sure you want to delete this API key?")
def delete(key_name: str):
    """
    Удалить API-ключ из защищенного хранилища.
    
    Примеры:
        meet2obsidian apikeys delete test_key
    """
    logger = get_logger("cli.apikeys")
    keychain = KeychainManager(logger=logger)
    
    # Проверка существования ключа
    if not keychain.key_exists(key_name):
        click.echo(f"Error: API key '{key_name}' not found.")
        return
    
    # Удаление ключа
    result = keychain.delete_api_key(key_name)
    
    if result:
        click.echo(f"API key '{key_name}' successfully deleted.")
    else:
        click.echo(f"Error: Failed to delete API key '{key_name}'.")


@apikeys.command()
@click.option('--rev-ai', prompt=True, hide_input=True, 
              help='API-ключ Rev.ai. Если не указан, будет запрошен.')
@click.option('--claude', prompt=True, hide_input=True, 
              help='API-ключ Claude. Если не указан, будет запрошен.')
def setup(rev_ai: str, claude: str):
    """
    Настроить все необходимые API-ключи одной командой.
    
    Эта команда настроит одновременно API-ключи Rev.ai и Claude.
    
    Примеры:
        meet2obsidian apikeys setup
        meet2obsidian apikeys setup --rev-ai YOUR_REV_AI_KEY --claude YOUR_CLAUDE_KEY
    """
    logger = get_logger("cli.apikeys")
    keychain = KeychainManager(logger=logger)
    
    # Сохранение API-ключа Rev.ai
    result_rev = keychain.store_api_key("rev_ai", rev_ai)
    if result_rev:
        click.echo("Rev.ai API key successfully saved to storage.")
    else:
        click.echo("Error: Failed to save Rev.ai API key.")
    
    # Сохранение API-ключа Claude
    result_claude = keychain.store_api_key("claude", claude)
    if result_claude:
        click.echo("Claude API key successfully saved to storage.")
    else:
        click.echo("Error: Failed to save Claude API key.")
    
    # Итог
    if result_rev and result_claude:
        click.echo("\nAll API keys successfully configured.")
    elif result_rev or result_claude:
        click.echo("\nSome API keys were configured, but others failed. Check logs for details.")
    else:
        click.echo("\nFailed to configure API keys. Check logs for details.")


def register_commands(cli):
    """Регистрация команд apikeys в CLI."""
    cli.add_command(apikeys)