# Архитектура CLI Meet2Obsidian

## Обзор

Этот документ описывает модульную архитектуру интерфейса командной строки (CLI) в meet2obsidian. CLI реализован с использованием библиотеки Click и построен на основе принципов модульного дизайна для обеспечения масштабируемости и удобства сопровождения.

## Структура CLI-интерфейса

CLI meet2obsidian имеет модульную структуру, где каждая группа команд реализована в отдельном модуле:

```
meet2obsidian/cli_commands/
├── __init__.py
├── apikeys_command.py
├── completion.py
├── config_command.py
├── logs_command.py
├── service_command.py
└── status_command.py
```

Главный входной файл CLI:
```
meet2obsidian/cli.py
```

## Ключевые компоненты

### Главный вход CLI (cli.py)

Главный файл CLI создает основной объект командной строки и регистрирует все группы команд:

```python
@click.group()
@click.version_option("0.1.0")
@click.option('--verbose', is_flag=True, help='Включить подробный вывод.')
@click.option('--log-file', help='Путь к файлу лога. По умолчанию: ~/Library/Logs/meet2obsidian/meet2obsidian.log')
@click.pass_context
def cli(ctx, verbose, log_file):
    """Meet2Obsidian — утилита для превращения Google Meet видео в заметки Obsidian."""
    # Инициализация контекста и общего состояния
    ctx.ensure_object(dict)
    
    # Настройка логирования и консоли
    console = Console()
    ctx.obj['console'] = console
    ctx.obj['verbose'] = verbose
    
    # Настройка логирования
    ...
```

### Модули команд

Каждый модуль команд определяет группу команд, связанных с конкретной функциональностью:

#### Команды управления сервисом (service_command.py)

```python
@click.group()
def service():
    """Управление сервисом Meet2Obsidian."""
    pass

@service.command()
@click.option('--autostart/--no-autostart', default=None, help='Настроить автозапуск при входе в систему.')
@click.pass_context
def start(ctx, autostart):
    """Запустить сервис meet2obsidian."""
    ...

@service.command()
@click.option('--force', is_flag=True, help='Принудительное завершение процесса.')
@click.pass_context
def stop(ctx, force):
    """Остановить сервис meet2obsidian."""
    ...
```

#### Команды управления конфигурацией (config_command.py)

```python
@click.group()
@click.pass_context
def config(ctx):
    """Управление конфигурацией Meet2Obsidian."""
    # Инициализация менеджера конфигурации
    ...

@config.command()
@click.option('--format', '-f', 'format_type', type=click.Choice(['text', 'json', 'yaml']), 
             default='yaml', help='Формат вывода конфигурации.')
@click.pass_context
def show(ctx, format_type):
    """Показать текущую конфигурацию."""
    ...
```

#### Команды управления API-ключами (apikeys_command.py)

```python
@click.group()
def apikeys():
    """Управление API-ключами для внешних сервисов."""
    pass

@apikeys.command()
@click.argument('key_name')
@click.option('--value', prompt=True, hide_input=True,
              help='Значение API-ключа. Если не указано, будет запрошено.')
def set(key_name, value):
    """
    Установить API-ключ в защищенное хранилище.
    """
    ...
```

#### Команды для просмотра и управления логами (logs_command.py)

```python
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
def show(count, level, format_type, log_file):
    """
    Показать последние записи лога.
    """
    ...
```

#### Команды получения статуса (status_command.py)

```python
@click.command()
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'table']), 
             default='table', help='Формат вывода.')
@click.option('--detailed/--no-detailed', '-d/', default=False, 
              help='Показать подробную информацию о состоянии системы.')
@click.pass_context
def status(ctx, format, detailed):
    """Показать статус Meet2Obsidian."""
    ...
```

#### Команды автодополнения оболочки (completion.py)

```python
@click.command()
@click.option('--shell', '-s', type=click.Choice(['bash', 'zsh', 'fish', 'powershell']), 
             help='Тип оболочки, для которой генерировать скрипт автодополнения.')
@click.option('--install', is_flag=True, help='Установить автодополнение в профиль оболочки.')
@click.pass_context
def completion(ctx, shell, install):
    """Управление автодополнением команд в оболочке."""
    ...
```

### ApplicationManager (core.py)

Класс ApplicationManager предоставляет интерфейс для управления процессом meet2obsidian. Он используется командами CLI для операций запуска, остановки и проверки статуса:

```python
class ApplicationManager:
    """Класс для управления приложением meet2obsidian."""
    
    def __init__(self, logger=None):
        """Инициализация менеджера приложения."""
        self.logger = logger or get_logger("core.app_manager")
        self.config_manager = ConfigManager()
        
    def start(self) -> bool:
        """Запуск процесса meet2obsidian."""
        ...
        
    def stop(self, force=False) -> bool:
        """Остановка процесса meet2obsidian."""
        ...
        
    def is_running(self) -> bool:
        """Проверка, запущен ли процесс meet2obsidian."""
        ...
        
    def get_status(self) -> dict:
        """Получение информации о статусе приложения."""
        ...
        
    def setup_autostart(self, enable=True) -> bool:
        """Настройка автозапуска через LaunchAgent."""
        ...
```

## Обработка ошибок

Реализован механизм централизованной обработки ошибок через декоратор:

```python
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
            
            # Логируем подробную информацию
            logger.error(f"Ошибка в команде {ctx.command.name}: {str(e)}")
            
            if ctx.obj.get('verbose', False):
                console.print(f"[error]✗ Ошибка: {str(e)}[/error]")
                console.print(f"Трассировка:\n{trace}")
            else:
                console.print(f"[error]✗ Ошибка: {str(e)}[/error]")
                
            return 1
    return wrapper
```

## Форматирование вывода

Для форматирования вывода используется библиотека Rich, что позволяет создавать более наглядные и удобные для восприятия сообщения:

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

# Создание таблицы с данными
table = Table(title="Статус Meet2Obsidian", show_header=True, header_style="bold cyan")
table.add_column("Параметр", style="dim")
table.add_column("Значение")

# Базовая информация
status_text = "[bold green]Запущен[/bold green]" if status_data["running"] else "[bold red]Остановлен[/bold red]"
table.add_row("Статус", status_text)

# Вывод в консоль
console.print(table)
```

## Интеграция моделей в CLI

CLI тесно интегрирован с другими моделями системы:

1. **ConfigManager**: для работы с конфигурацией
2. **KeychainManager**: для управления API-ключами
3. **ApplicationManager**: для управления процессами приложения
4. **Logger**: для структурированного логирования

## Регистрация команд

Команды регистрируются в главном CLI через модуль `__init__.py` в каталоге `cli_commands`:

```python
def register_all_commands(cli):
    """Регистрация всех команд CLI."""
    from .service_command import register_commands as register_service_commands
    from .status_command import register_commands as register_status_commands
    from .config_command import register_commands as register_config_commands
    from .logs_command import register_commands as register_logs_commands
    from .apikeys_command import register_commands as register_apikeys_commands
    from .completion import register_commands as register_completion_commands

    register_service_commands(cli)
    register_status_commands(cli)
    register_config_commands(cli)
    register_logs_commands(cli)
    register_apikeys_commands(cli)
    register_completion_commands(cli)
```

## Передача контекста

Click позволяет передавать контекст между командами, что используется для распространения общих объектов, таких как консоль, логгер и менеджеры:

```python
@click.pass_context
def start(ctx, autostart):
    """Запустить сервис meet2obsidian."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Создаем менеджер приложения
    app_manager = ApplicationManager()
```

## Заключение

Архитектура CLI meet2obsidian реализует модульный подход к организации команд интерфейса. Это позволяет легко добавлять новые команды, изменять существующие и поддерживать код в читаемом состоянии. Модульность обеспечивает хорошую тестируемость и упрощает сопровождение кода.