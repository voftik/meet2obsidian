"""
Интерфейс командной строки для просмотра и управления логами.

Этот модуль предоставляет CLI команды для просмотра и управления логами в meet2obsidian.
"""

import os
import click
import json
from typing import List, Dict, Any, Optional

from meet2obsidian.utils.logging import get_last_logs


def format_log_entry(log_entry: Dict[str, Any], format_type: str = "plain") -> str:
    """
    Форматирует запись лога для отображения.
    
    Args:
        log_entry: Запись лога в виде словаря
        format_type: Тип форматирования (plain, json, color)
        
    Returns:
        str: Отформатированная запись лога
    """
    if format_type == "json":
        return json.dumps(log_entry, indent=2, ensure_ascii=False)
    
    # Извлекаем общие поля
    timestamp = log_entry.get("timestamp", "")
    level = log_entry.get("level", "").upper()
    logger_name = log_entry.get("logger", "")
    message = log_entry.get("message", "")
    
    # Форматирование для обычного текста или цветного вывода
    if format_type == "color":
        # Определение цветов для разных уровней логирования
        colors = {
            "DEBUG": click.style("DEBUG", fg="cyan"),
            "INFO": click.style("INFO", fg="green"),
            "WARNING": click.style("WARNING", fg="yellow"),
            "ERROR": click.style("ERROR", fg="red"),
            "CRITICAL": click.style("CRITICAL", fg="red", bold=True)
        }
        level_str = colors.get(level, level)
    else:
        level_str = level
    
    # Создание базовой отформатированной строки
    formatted = f"{timestamp} [{level_str}] {logger_name}: {message}"
    
    # Добавление любых дополнительных полей
    additional = {k: v for k, v in log_entry.items() 
                 if k not in ["timestamp", "level", "logger", "message"]}
    
    if additional:
        if format_type == "color":
            additional_str = click.style(str(additional), fg="blue")
        else:
            additional_str = str(additional)
        formatted += f" {additional_str}"
    
    return formatted


@click.group()
def logs():
    """Управление и просмотр логов приложения."""
    pass


@logs.command()
@click.option("--count", "-n", default=20, help="Количество записей лога для показа.")
@click.option("--level", "-l", default="info", 
              type=click.Choice(["debug", "info", "warning", "error", "critical"], 
                              case_sensitive=False),
              help="Минимальный уровень логирования для показа.")
@click.option("--format", "-f", "format_type", default="color",
              type=click.Choice(["plain", "json", "color"], case_sensitive=False),
              help="Формат вывода для записей лога.")
@click.option("--log-file", "-o", help="Пользовательский путь к файлу лога.")
def show(count: int, level: str, format_type: str, log_file: Optional[str]):
    """
    Показать последние записи лога.
    
    Примеры:
        meet2obsidian logs show
        meet2obsidian logs show --count 50 --level error
        meet2obsidian logs show --format json
    """
    # Определение пути к файлу лога
    if not log_file:
        log_file = os.path.expanduser("~/Library/Logs/meet2obsidian/meet2obsidian.log")
    
    if not os.path.exists(log_file):
        click.echo(f"Файл лога не найден: {log_file}")
        return
    
    # Получение логов
    logs = get_last_logs(log_file, count, level)
    
    if not logs:
        click.echo("Не найдено подходящих записей лога.")
        return
    
    # Форматирование и отображение логов
    click.echo(f"Показано последних {len(logs)} записей лога (Уровень: {level.upper()} и выше):")
    
    for log_entry in logs:
        click.echo(format_log_entry(log_entry, format_type))


@logs.command()
@click.option("--log-file", "-o", help="Пользовательский путь к файлу лога.")
@click.confirmation_option(prompt="Вы уверены, что хотите очистить файл лога?")
def clear(log_file: Optional[str]):
    """
    Очистить файл лога.
    
    Примеры:
        meet2obsidian logs clear
    """
    # Определение пути к файлу лога
    if not log_file:
        log_file = os.path.expanduser("~/Library/Logs/meet2obsidian/meet2obsidian.log")
    
    if not os.path.exists(log_file):
        click.echo(f"Файл лога не найден: {log_file}")
        return
    
    # Очистка файла лога
    try:
        open(log_file, 'w').close()
        click.echo(f"Файл лога очищен: {log_file}")
    except Exception as e:
        click.echo(f"Ошибка при очистке файла лога: {str(e)}")


def register_commands(cli):
    """Регистрация команд логирования в CLI."""
    cli.add_command(logs)