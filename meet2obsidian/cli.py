"""
Интерфейс командной строки для meet2obsidian.

Этот модуль определяет основной интерфейс командной строки для приложения
meet2obsidian и регистрирует все доступные команды.
"""

import os
import sys
import functools
import click
from rich.console import Console
from rich.theme import Theme

from meet2obsidian.utils.logging import setup_logging, get_logger
from meet2obsidian.cli_commands import (
    logs_command,
    apikeys_command,
    service_command,
    status_command,
    config_command,
    process_command,
    cache_command,
    completion
)

# Создаем консоль с цветовой темой
console = Console(theme=Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
}))

def cli_error_handler(func):
    """Декоратор для обработки ошибок в CLI-командах."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ctx = click.get_current_context()
            console = ctx.obj.get('console', Console())
            logger = ctx.obj.get('logger', get_logger("cli.error"))
            
            # Получаем трассировку
            import traceback
            trace = traceback.format_exc()
            
            # Логируем подробную информацию
            logger.error(f"Ошибка в команде {ctx.command.name}: {str(e)}\n{trace}")
            
            # Выводим сообщение пользователю
            if ctx.obj.get('verbose', False):
                console.print(f"[error]✗ Ошибка: {str(e)}[/error]")
                console.print(f"Трассировка:\n{trace}")
            else:
                console.print(f"[error]✗ Ошибка: {str(e)}[/error]")
                console.print("[info]Для получения подробной информации запустите команду с опцией --verbose[/info]")
            
            return 1
    return wrapper

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Показать версию и выйти.')
@click.option('-v', '--verbose', is_flag=True, help='Включить подробный вывод.')
@click.option('--log-file', help='Путь к файлу лога.')
@click.pass_context
def cli(ctx, version, verbose, log_file):
    """Meet2Obsidian - автоматическая обработка записей встреч и создание заметок в Obsidian."""
    # Настройка глобального контекста
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['console'] = console
    
    # Если запрошена версия, показываем ее и выходим
    if version:
        # TODO: Импортировать версию из модуля
        console.print(f"[bold]meet2obsidian[/bold], версия [cyan]0.1.0[/cyan]")
        return
    
    # Настройка логирования
    log_level = "debug" if verbose else "info"
    
    if not log_file:
        # Определение пути к логу по умолчанию
        log_dir = os.path.expanduser("~/Library/Logs/meet2obsidian")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "meet2obsidian.log")
    
    # Настройка логирования
    setup_logging(log_level=log_level, log_file=log_file)
    ctx.obj['logger'] = get_logger("cli")
    
    if verbose:
        console.print(f"[info]Подробный режим включен. Логи записываются в: {log_file}[/info]")
    
    # Если команда не указана, показываем справку
    if ctx.invoked_subcommand is None and not version:
        console.print(ctx.get_help())

@cli.command()
@click.option("--api", type=click.Choice(["rev_ai", "claude"]), help="Проверить только указанный API.")
@click.pass_context
@cli_error_handler
def test(ctx, api):
    """Проверить настройки и соединения с API."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.test"))
    
    logger.info("Команда test выполнена", api=api)
    
    if api:
        console.print(f"Проверка соединения с {api}...")
    else:
        console.print("Проверка всех настроек и соединений...")

# Регистрация команд из других модулей
logs_command.register_commands(cli)
apikeys_command.register_commands(cli)
service_command.register_commands(cli)
status_command.register_commands(cli)
config_command.register_commands(cli)
process_command.register_commands(cli)
cache_command.register_commands(cli)
completion.register_commands(cli)

def main():
    """Точка входа для CLI."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[error]Ошибка: {str(e)}[/error]", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()