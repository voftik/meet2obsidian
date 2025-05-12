# meet2obsidian/cli_commands/status_command.py

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from meet2obsidian.utils.logging import get_logger
from meet2obsidian.core import ApplicationManager
from meet2obsidian.utils.security import KeychainManager

@click.command()
@click.option('--detailed', '-d', is_flag=True, help='Показать подробную информацию о статусе.')
@click.option('--format', '-f', 'format_type', type=click.Choice(['text', 'json', 'table']), 
             default='table', help='Формат вывода.')
@click.pass_context
def status(ctx, detailed, format_type):
    """Показать текущий статус сервиса meet2obsidian."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.status"))
    
    # Создаем менеджер приложения
    app_manager = ApplicationManager()
    keychain_manager = KeychainManager()
    
    # Проверяем, запущен ли сервис
    is_running = app_manager.is_running()
    
    # Базовая информация о статусе
    status_data = {
        "running": is_running,
        "api_keys": keychain_manager.get_api_keys_status()
    }
    
    # Если сервис запущен, получаем дополнительную информацию
    if is_running:
        status_data.update(app_manager.get_status())
    
    # Выводим информацию в соответствии с запрошенным форматом
    if format_type == 'json':
        console.print(json.dumps(status_data, indent=2))
        return
    
    if format_type == 'text':
        _print_status_text(console, status_data, detailed)
    else:  # table
        _print_status_table(console, status_data, detailed)
    
    logger.info("Запрошена информация о статусе")

def _print_status_table(console, status_data, detailed):
    """Форматирование статуса в виде таблицы."""
    # Основная таблица статуса
    main_table = Table(title="Статус Meet2Obsidian", show_header=True, header_style="bold cyan")
    main_table.add_column("Параметр", style="dim")
    main_table.add_column("Значение")
    
    # Базовая информация
    status_text = "[bold green]Запущен[/bold green]" if status_data["running"] else "[bold red]Остановлен[/bold red]"
    main_table.add_row("Статус", status_text)
    
    if status_data["running"]:
        main_table.add_row("Время работы", status_data.get("uptime", "Неизвестно"))
        main_table.add_row("Обработано файлов", str(status_data.get("processed_files", 0)))
        main_table.add_row("В очереди", str(status_data.get("pending_files", 0)))
    
    # API ключи
    api_keys = status_data.get("api_keys", {})
    for key, exists in api_keys.items():
        key_status = "[green]✓[/green]" if exists else "[red]✗[/red]"
        main_table.add_row(f"API ключ {key}", key_status)
    
    console.print(main_table)
    
    # Если запрошена подробная информация и сервис запущен
    if detailed and status_data["running"]:
        _print_detailed_tables(console, status_data)

def _print_detailed_tables(console, status_data):
    """Вывод подробных таблиц со статусом."""
    # Активные задачи
    if "active_jobs" in status_data and status_data["active_jobs"]:
        jobs_table = Table(title="Активные задачи", show_header=True, header_style="bold cyan")
        jobs_table.add_column("Файл", style="dim")
        jobs_table.add_column("Этап")
        jobs_table.add_column("Прогресс")
        
        for job in status_data["active_jobs"]:
            jobs_table.add_row(
                job.get("file", "Неизвестно"),
                job.get("stage", "Неизвестно"),
                job.get("progress", "0%")
            )
        
        console.print(jobs_table)
    
    # Последние ошибки
    if "last_errors" in status_data and status_data["last_errors"]:
        errors_table = Table(title="Последние ошибки", show_header=True, header_style="bold red")
        errors_table.add_column("Время", style="dim")
        errors_table.add_column("Компонент")
        errors_table.add_column("Сообщение")
        
        for error in status_data["last_errors"]:
            errors_table.add_row(
                error.get("time", "Неизвестно"),
                error.get("component", "Неизвестно"),
                error.get("message", "Неизвестно")
            )
        
        console.print(errors_table)

def _print_status_text(console, status_data, detailed):
    """Форматирование статуса в виде текста."""
    status_text = "Запущен" if status_data["running"] else "Остановлен"
    console.print(f"Статус: [bold]{'[green]' if status_data['running'] else '[red]'}{status_text}[/]")
    
    if status_data["running"]:
        console.print(f"Время работы: {status_data.get('uptime', 'Неизвестно')}")
        console.print(f"Обработано файлов: {status_data.get('processed_files', 0)}")
        console.print(f"В очереди: {status_data.get('pending_files', 0)}")
    
    # API ключи
    console.print("\nAPI ключи:")
    api_keys = status_data.get("api_keys", {})
    for key, exists in api_keys.items():
        status_mark = "[green]✓[/green]" if exists else "[red]✗[/red]"
        console.print(f"  {key}: {status_mark}")
    
    # Подробная информация при необходимости
    if detailed and status_data["running"]:
        # Активные задачи
        if "active_jobs" in status_data and status_data["active_jobs"]:
            console.print("\n[bold]Активные задачи:[/bold]")
            for job in status_data["active_jobs"]:
                console.print(f"  Файл: {job.get('file', 'Неизвестно')}")
                console.print(f"    Этап: {job.get('stage', 'Неизвестно')}")
                console.print(f"    Прогресс: {job.get('progress', '0%')}")
        
        # Последние ошибки
        if "last_errors" in status_data and status_data["last_errors"]:
            console.print("\n[bold red]Последние ошибки:[/bold red]")
            for error in status_data["last_errors"]:
                console.print(f"  [{error.get('time', 'Неизвестно')}] {error.get('component', 'Неизвестно')}: {error.get('message', 'Неизвестно')}")

def register_commands(cli):
    """Регистрация команды статуса в CLI."""
    cli.add_command(status)