# meet2obsidian/cli_commands/config_command.py

import click
import json
import os
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from meet2obsidian.utils.logging import get_logger
from meet2obsidian.config import ConfigManager

@click.group(name="config")
@click.option('--config-path', help='Путь к файлу конфигурации.')
@click.pass_context
def config(ctx, config_path):
    """Управление конфигурацией meet2obsidian."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.config"))
    
    # Создаем экземпляр ConfigManager
    config_manager = ConfigManager(config_path=config_path)
    
    # Сохраняем экземпляр в контексте
    ctx.obj['config_manager'] = config_manager

@config.command()
@click.option('--format', '-f', 'format_type', type=click.Choice(['text', 'json', 'yaml']), 
             default='yaml', help='Формат вывода конфигурации.')
@click.pass_context
def show(ctx, format_type):
    """Показать текущую конфигурацию."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.config"))
    config_manager = ctx.obj.get('config_manager')
    
    # Получаем текущую конфигурацию
    current_config = config_manager.get_config()
    
    if format_type == 'json':
        # Форматируем как JSON
        config_str = json.dumps(current_config, indent=2)
        syntax = Syntax(config_str, "json", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Текущая конфигурация (JSON)", border_style="cyan"))
    elif format_type == 'yaml':
        # Для YAML нужно импортировать
        try:
            import yaml
            config_str = yaml.dump(current_config, default_flow_style=False, sort_keys=False)
            syntax = Syntax(config_str, "yaml", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Текущая конфигурация (YAML)", border_style="cyan"))
        except ImportError:
            # Если PyYAML не установлен, используем JSON
            console.print("[warning]PyYAML не установлен, используем JSON[/warning]")
            config_str = json.dumps(current_config, indent=2)
            syntax = Syntax(config_str, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Текущая конфигурация (JSON)", border_style="cyan"))
    else:  # text
        # Вывод в виде таблицы
        _print_config_as_table(console, current_config)
    
    logger.info("Просмотр текущей конфигурации")

@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """Установить значение параметра конфигурации."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.config"))
    config_manager = ctx.obj.get('config_manager')
    
    # Пытаемся преобразовать значение в соответствующий тип
    try:
        # Пробуем сначала как число
        try:
            value_converted = json.loads(value.lower())
        except ValueError:
            # Если не удалось, оставляем как строку
            value_converted = value
        
        # Устанавливаем значение
        success = config_manager.set_value(key, value_converted)
        
        if success:
            # Сохраняем изменения
            config_manager.save_config()
            console.print(f"[success]✓ Параметр [bold]{key}[/bold] успешно изменен на [bold]{value}[/bold][/success]")
            logger.info(f"Параметр {key} успешно изменен на {value}")
        else:
            console.print(f"[error]✗ Ошибка при установке параметра [bold]{key}[/bold][/error]")
            logger.error(f"Ошибка при установке параметра {key}")
            return 1
    except Exception as e:
        console.print(f"[error]✗ Ошибка при установке параметра: {str(e)}[/error]")
        logger.error(f"Ошибка при установке параметра {key}: {str(e)}")
        return 1

@config.command()
@click.option('--confirm', is_flag=True, help='Подтвердить сброс конфигурации без запроса.')
@click.pass_context
def reset(ctx, confirm):
    """Сбросить конфигурацию к значениям по умолчанию."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.config"))
    config_manager = ctx.obj.get('config_manager')
    
    if not confirm:
        # Запрашиваем подтверждение
        if not click.confirm("Вы уверены, что хотите сбросить конфигурацию к значениям по умолчанию?"):
            console.print("[warning]Сброс конфигурации отменен[/warning]")
            return
    
    # Создаем конфигурацию по умолчанию
    default_config = config_manager.create_default_config()
    
    # Сохраняем конфигурацию
    success = config_manager.save_config(config=default_config)
    
    if success:
        console.print("[success]✓ Конфигурация успешно сброшена к значениям по умолчанию[/success]")
        logger.info("Конфигурация успешно сброшена к значениям по умолчанию")
    else:
        console.print("[error]✗ Ошибка при сбросе конфигурации[/error]")
        logger.error("Ошибка при сбросе конфигурации")
        return 1

@config.command()
@click.argument('path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.pass_context
def import_config(ctx, path):
    """Импортировать конфигурацию из файла."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.config"))
    config_manager = ctx.obj.get('config_manager')
    
    try:
        # Пытаемся загрузить конфигурацию из указанного файла
        with open(path, 'r') as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                try:
                    import yaml
                    imported_config = yaml.safe_load(f)
                except ImportError:
                    console.print("[error]✗ PyYAML не установлен, не удается импортировать YAML[/error]")
                    return 1
            else:
                imported_config = json.load(f)
        
        # Проверяем конфигурацию
        errors = config_manager.validate_config(imported_config)
        
        if errors:
            console.print("[error]✗ Импортируемая конфигурация содержит ошибки:[/error]")
            for error in errors:
                console.print(f"  - {error}")
            return 1
        
        # Сохраняем импортированную конфигурацию
        success = config_manager.save_config(config=imported_config)
        
        if success:
            console.print(f"[success]✓ Конфигурация успешно импортирована из [bold]{path}[/bold][/success]")
            logger.info(f"Конфигурация успешно импортирована из {path}")
        else:
            console.print("[error]✗ Ошибка при сохранении импортированной конфигурации[/error]")
            logger.error("Ошибка при сохранении импортированной конфигурации")
            return 1
            
    except Exception as e:
        console.print(f"[error]✗ Ошибка при импорте конфигурации: {str(e)}[/error]")
        logger.error(f"Ошибка при импорте конфигурации: {str(e)}")
        return 1

@config.command()
@click.argument('path', type=click.Path(file_okay=True, dir_okay=False, writable=True))
@click.option('--format', '-f', 'format_type', type=click.Choice(['json', 'yaml']), 
             default='json', help='Формат экспорта конфигурации.')
@click.pass_context
def export(ctx, path, format_type):
    """Экспортировать конфигурацию в файл."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.config"))
    config_manager = ctx.obj.get('config_manager')
    
    # Получаем текущую конфигурацию
    current_config = config_manager.get_config()
    
    try:
        # Создаем директории, если их нет
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        # Экспортируем конфигурацию в указанном формате
        with open(path, 'w') as f:
            if format_type == 'yaml':
                try:
                    import yaml
                    yaml.dump(current_config, f, default_flow_style=False, sort_keys=False)
                except ImportError:
                    console.print("[error]✗ PyYAML не установлен, не удается экспортировать в YAML[/error]")
                    return 1
            else:  # json
                json.dump(current_config, f, indent=2)
        
        console.print(f"[success]✓ Конфигурация успешно экспортирована в [bold]{path}[/bold][/success]")
        logger.info(f"Конфигурация успешно экспортирована в {path}")
    except Exception as e:
        console.print(f"[error]✗ Ошибка при экспорте конфигурации: {str(e)}[/error]")
        logger.error(f"Ошибка при экспорте конфигурации: {str(e)}")
        return 1

def _print_config_as_table(console, config, prefix=''):
    """Вывод конфигурации в виде древовидной таблицы."""
    table = Table(title="Конфигурация meet2obsidian", show_header=True, header_style="bold cyan")
    table.add_column("Параметр", style="dim")
    table.add_column("Значение")
    
    def _add_config_to_table(config, prefix=''):
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Для вложенных словарей выводим заголовок секции
                table.add_row(f"[bold]{full_key}[/bold]", "")
                # И рекурсивно обрабатываем содержимое
                _add_config_to_table(value, full_key)
            else:
                # Для обычных значений просто выводим строку
                table.add_row(full_key, str(value))
    
    _add_config_to_table(config)
    console.print(table)

def register_commands(cli):
    """Регистрация команд конфигурации в CLI."""
    cli.add_command(config)