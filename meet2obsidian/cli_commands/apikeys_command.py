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
        click.echo("Ошибка: Имя ключа не может быть пустым.")
        return
    
    # Сохранение ключа
    result = keychain.store_api_key(key_name, value)
    
    if result:
        click.echo(f"API-ключ '{key_name}' успешно сохранен в хранилище.")
    else:
        click.echo(f"Ошибка: Не удалось сохранить API-ключ '{key_name}'.")


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
        click.echo(f"Ошибка: API-ключ '{key_name}' не найден.")
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
        click.echo(f"Ошибка: Не удалось получить API-ключ '{key_name}'.")


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
        click.echo("Статус API-ключей:")
        click.echo("------------------------")
        for key_name, exists in status.items():
            status_str = click.style("Настроен", fg="green") if exists else click.style("Не настроен", fg="red")
            click.echo(f"{key_name.ljust(12)}: {status_str}")


@apikeys.command()
@click.argument('key_name')
@click.confirmation_option(prompt="Вы уверены, что хотите удалить этот API-ключ?")
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
        click.echo(f"Ошибка: API-ключ '{key_name}' не найден.")
        return
    
    # Удаление ключа
    result = keychain.delete_api_key(key_name)
    
    if result:
        click.echo(f"API-ключ '{key_name}' успешно удален.")
    else:
        click.echo(f"Ошибка: Не удалось удалить API-ключ '{key_name}'.")


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
        click.echo("API-ключ Rev.ai успешно сохранен в хранилище.")
    else:
        click.echo("Ошибка: Не удалось сохранить API-ключ Rev.ai.")
    
    # Сохранение API-ключа Claude
    result_claude = keychain.store_api_key("claude", claude)
    if result_claude:
        click.echo("API-ключ Claude успешно сохранен в хранилище.")
    else:
        click.echo("Ошибка: Не удалось сохранить API-ключ Claude.")
    
    # Итог
    if result_rev and result_claude:
        click.echo("\nВсе API-ключи успешно настроены.")
    elif result_rev or result_claude:
        click.echo("\nНекоторые API-ключи были настроены, но другие не удалось. Проверьте логи для получения подробностей.")
    else:
        click.echo("\nНе удалось настроить API-ключи. Проверьте логи для получения подробностей.")


def register_commands(cli):
    """Регистрация команд apikeys в CLI."""
    cli.add_command(apikeys)