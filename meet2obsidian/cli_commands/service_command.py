# meet2obsidian/cli_commands/service_command.py

import click
import time
import subprocess
from pathlib import Path
from rich.console import Console
from rich.spinner import Spinner
from meet2obsidian.utils.logging import get_logger
from meet2obsidian.core import ApplicationManager

@click.group(name="service")
@click.pass_context
def service(ctx):
    """Управление сервисом meet2obsidian."""
    pass

@service.command()
@click.option('--autostart/--no-autostart', default=None, help='Настроить автозапуск при входе в систему.')
@click.pass_context
def start(ctx, autostart):
    """Запустить сервис meet2obsidian."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Создаем менеджер приложения
    app_manager = ApplicationManager()
    
    # Проверяем, запущен ли уже сервис
    if app_manager.is_running():
        console.print("[warning]Сервис уже запущен[/warning]")
        return
    
    # Анимация запуска
    with console.status("[bold cyan]Запуск сервиса...[/bold cyan]", spinner="dots") as status:
        success = app_manager.start()
        # Даем время на запуск
        time.sleep(1.5)
    
    if success:
        console.print("[success]✓ Сервис успешно запущен[/success]")
        logger.info("Сервис успешно запущен")
    else:
        console.print("[error]✗ Ошибка при запуске сервиса[/error]")
        logger.error("Ошибка при запуске сервиса")
        return
    
    # Настраиваем автозапуск, если указана опция
    if autostart is not None:
        with console.status("[bold cyan]Настройка автозапуска...[/bold cyan]", spinner="dots"):
            autostart_success = app_manager.setup_autostart(autostart)
        
        if autostart_success:
            action = "настроен" if autostart else "отключен"
            console.print(f"[success]✓ Автозапуск {action}[/success]")
            logger.info(f"Автозапуск {action}")
        else:
            console.print("[error]✗ Ошибка при настройке автозапуска[/error]")
            logger.error("Ошибка при настройке автозапуска")

@service.command()
@click.option('--force', is_flag=True, help='Принудительная остановка сервиса.')
@click.pass_context
def stop(ctx, force):
    """Остановить сервис meet2obsidian."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Создаем менеджер приложения
    app_manager = ApplicationManager()
    
    # Проверяем, запущен ли сервис
    if not app_manager.is_running():
        console.print("[warning]Сервис не запущен[/warning]")
        return
    
    # Анимация остановки
    with console.status("[bold cyan]Остановка сервиса...[/bold cyan]", spinner="dots") as status:
        success = app_manager.stop(force=force)
        # Даем время на остановку
        time.sleep(1.5)
    
    if success:
        console.print("[success]✓ Сервис успешно остановлен[/success]")
        logger.info("Сервис успешно остановлен")
    else:
        console.print("[error]✗ Ошибка при остановке сервиса[/error]")
        logger.error("Ошибка при остановке сервиса")

def register_commands(cli):
    """Регистрация команд сервиса в CLI."""
    cli.add_command(service)