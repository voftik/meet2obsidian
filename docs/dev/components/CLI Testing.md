# Тестирование CLI Meet2Obsidian

## Обзор

Этот документ описывает подход к тестированию интерфейса командной строки (CLI) в meet2obsidian. Система тестирования CLI обеспечивает всестороннюю проверку взаимодействия пользователя с приложением через командную строку, включая обработку команд, аргументов и опций.

## Структура тестов

Тесты CLI разделены на две категории:

1. **Модульные тесты** (`tests/unit/test_cli.py`) - проверяют функциональность отдельных команд и аргументов с использованием мокирования для изоляции от внешних зависимостей.

2. **Интеграционные тесты** (`tests/integration/test_cli_integration.py`) - проверяют взаимодействие CLI с реальными компонентами системы, такими как хранилище API-ключей.

## Организация тестов по командам

Тесты CLI организованы по командным группам, каждая из которых тестируется в отдельном тестовом классе:

```python
class TestServiceCommand:
    """Tests for the service command group."""
    # Тесты для команд service

class TestStatusCommand:
    """Tests for the status command."""
    # Тесты для команды status

class TestConfigCommand:
    """Tests for the config command."""
    # Тесты для команды config

class TestLogsCommand:
    """Tests for the logs command group."""
    # Тесты для команд logs

class TestApiKeysCommand:
    """Tests for the apikeys command group."""
    # Тесты для команд apikeys

class TestCompletionCommand:
    """Tests for the completion command."""
    # Тесты для команды completion

class TestArgumentProcessing:
    """Tests for command-line argument processing."""
    # Тесты для обработки аргументов
```

## Инструменты и подходы

### Click Testing

Для тестирования CLI, написанного с использованием библиотеки Click, применяется класс `CliRunner`, который предоставляет метод `invoke` для эмуляции запуска команд:

```python
from click.testing import CliRunner

def test_help_option():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert "Usage:" in result.output
```

### Мокирование зависимостей

Модульные тесты используют библиотеку `unittest.mock` для изоляции тестируемого кода от его зависимостей:

```python
def test_service_start_basic(self):
    """Test basic invocation of the service start command."""
    runner = CliRunner()

    with patch('meet2obsidian.cli_commands.service_command.ApplicationManager') as mock_app_manager:
        mock_instance = mock_app_manager.return_value
        mock_instance.is_running.return_value = False
        mock_instance.start.return_value = True

        result = runner.invoke(cli, ['service', 'start'])

        assert result.exit_code == 0
        mock_instance.start.assert_called_once()
```

### Проверка поведения при ошибках

Тесты также проверяют корректное поведение CLI при различных ошибках:

```python
def test_service_stop_not_running(self):
    """Test service stop command when service is not running."""
    runner = CliRunner()

    with patch('meet2obsidian.cli_commands.service_command.ApplicationManager') as mock_app_manager:
        mock_instance = mock_app_manager.return_value
        mock_instance.is_running.return_value = False

        result = runner.invoke(cli, ['service', 'stop'])

        assert result.exit_code == 0
        assert "не запущен" in result.output
        mock_instance.stop.assert_not_called()
```

## Примеры тестов по группам команд

### Тесты команд управления сервисом (service)

```python
class TestServiceCommand:
    """Tests for the service command group."""

    def test_service_command_exists(self):
        """Test that service command group exists."""
        runner = CliRunner()
        result = runner.invoke(cli, ['service', '--help'])

        assert result.exit_code == 0
        assert "service" in result.output
        assert "start" in result.output
        assert "stop" in result.output

    def test_service_start_basic(self):
        """Test basic invocation of the service start command."""
        # ...

    def test_service_start_already_running(self):
        """Test service start command when service is already running."""
        # ...

    def test_service_start_with_autostart(self):
        """Test service start command with autostart option."""
        # ...

    def test_service_stop_basic(self):
        """Test basic invocation of the service stop command."""
        # ...

    def test_service_stop_with_force(self):
        """Test service stop command with force option."""
        # ...
```

### Тесты команд управления конфигурацией (config)

```python
class TestConfigCommand:
    """Tests for the config command."""

    def test_config_command_exists(self):
        """Test that config command group exists."""
        # ...

    def test_config_show_command(self):
        """Test config show command."""
        # ...

    def test_config_show_with_json_format(self):
        """Test config show command with json format."""
        # ...

    def test_config_set_valid_key(self):
        """Test config set command with valid key."""
        # ...

    def test_config_set_invalid_key(self):
        """Test config set command with invalid key."""
        # ...

    def test_config_reset_with_confirmation(self):
        """Test config reset command with confirmation."""
        # ...

    def test_config_export_command(self):
        """Test config export command."""
        # ...
```

### Тесты команд управления API-ключами (apikeys)

```python
class TestApiKeysCommand:
    """Tests for the apikeys command group."""

    def test_apikeys_command_exists(self):
        """Test that apikeys command group exists."""
        # ...

    def test_apikeys_set_command(self):
        """Test apikeys set command."""
        # ...

    def test_apikeys_get_command_with_masked_output(self):
        """Test apikeys get command with masked output."""
        # ...

    def test_apikeys_get_command_with_show_option(self):
        """Test apikeys get command with show option."""
        # ...

    def test_apikeys_list_command_table_format(self):
        """Test apikeys list command with table format."""
        # ...

    def test_apikeys_list_command_json_format(self):
        """Test apikeys list command with json format."""
        # ...

    def test_apikeys_delete_command_with_confirmation(self):
        """Test apikeys delete command with confirmation."""
        # ...

    def test_apikeys_setup_command(self):
        """Test apikeys setup command."""
        # ...
```

## Тестирование обработки аргументов

```python
class TestArgumentProcessing:
    """Tests for command-line argument processing."""

    def test_help_option(self):
        """Test --help option."""
        # ...

    def test_version_option(self):
        """Test --version option."""
        # ...

    def test_invalid_command(self):
        """Test handling of nonexistent command."""
        # ...

    def test_verbose_option(self):
        """Test --verbose option."""
        # ...
```

## Особенности тестирования

### Тестирование цветного вывода

CLI использует библиотеку Rich для форматирования вывода. При тестировании проверяется наличие определенных строк в выводе, игнорируя управляющие последовательности цветов:

```python
def test_status_basic(self):
    """Test basic invocation of the status command."""
    # ...
    
    result = runner.invoke(cli, ['status'])
    
    assert result.exit_code == 0
    assert "Статус" in result.output
    assert "Запущен" in result.output or "Остановлен" in result.output
```

### Тестирование интерактивного ввода

Для команд, требующих интерактивного ввода, используется параметр `input`:

```python
def test_apikeys_set_with_input(self):
    """Test apikeys set command with interactive input."""
    runner = CliRunner()
    
    with patch('meet2obsidian.cli_commands.apikeys_command.KeychainManager') as mock_keychain_manager:
        mock_instance = mock_keychain_manager.return_value
        mock_instance.store_api_key.return_value = True
        
        result = runner.invoke(cli, ['apikeys', 'set', 'test_key'], input='test_value\n')
        
        assert result.exit_code == 0
        mock_instance.store_api_key.assert_called_once_with('test_key', 'test_value')
```

### Тестирование подтверждений

Для команд с подтверждением используется такой же подход:

```python
def test_config_reset_with_confirmation(self):
    """Test config reset command with confirmation."""
    runner = CliRunner()
    
    with patch(...):
        # ...
        result = runner.invoke(cli, ['config', 'reset'], input='y\n')
        # ...
```

## Покрытие тестами

Тесты CLI обеспечивают около 71% покрытия кода команд CLI. Покрытие отдельных модулей:

- `service_command.py`: 88%
- `apikeys_command.py`: 84%
- `logs_command.py`: 82%
- `status_command.py`: 66%
- `config_command.py`: 58%
- `completion.py`: 61%

## Запуск тестов CLI

### Запуск всех тестов CLI

```bash
python -m pytest tests/unit/test_cli.py -v
```

### Запуск тестов для конкретной группы команд

```bash
python -m pytest tests/unit/test_cli.py::TestServiceCommand -v
python -m pytest tests/unit/test_cli.py::TestConfigCommand -v
python -m pytest tests/unit/test_cli.py::TestApiKeysCommand -v
```

### Запуск конкретного теста

```bash
python -m pytest tests/unit/test_cli.py::TestServiceCommand::test_service_start_basic -v
```

### Запуск тестов с отчетом о покрытии

```bash
python -m pytest tests/unit/test_cli.py --cov=meet2obsidian.cli_commands
```

## Дальнейшее развитие тестирования CLI

1. Увеличение покрытия кода для модулей `config_command.py` и `completion.py`
2. Добавление интеграционных тестов для проверки взаимодействия с реальной файловой системой
3. Создание тестов для проверки корректности конфигурационных файлов, создаваемых CLI
4. Улучшение тестирования обработки ошибок и исключительных ситуаций
5. Реализация тестов для проверки взаимодействия с менеджером процессов (ApplicationManager)

## Заключение

Система тестирования CLI meet2obsidian обеспечивает всестороннюю проверку интерфейса командной строки приложения. Модульные тесты проверяют правильность работы отдельных команд, опций и обработки ошибок. Все модули CLI имеют тестовое покрытие, что позволяет поддерживать высокое качество кода и обеспечивать корректную работу CLI даже при внесении изменений в базовую функциональность.