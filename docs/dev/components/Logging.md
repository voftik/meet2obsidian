# Модуль логирования

## Обзор

Модуль логирования предоставляет единый интерфейс для структурированного логирования во всех компонентах приложения. Он обеспечивает интеграцию между стандартной библиотекой Python `logging` и библиотекой `structlog` для создания структурированных логов в формате JSON.

Модуль реализует следующие возможности:
- Структурированное логирование с контекстными данными
- Вывод логов в файл и консоль
- Ротация файлов логов
- Настраиваемые уровни логирования
- Логирование исключений с трассировкой стека
- Диагностическое логирование системной информации

## Архитектура

Модуль логирования находится в `meet2obsidian.utils.logging` и включает следующие основные функции:

- `setup_logging()` - настраивает систему логирования
- `get_logger()` - получает структурированный логгер
- `get_last_logs()` - получает последние записи из файла логов
- `create_diagnostic_log_entry()` - создает диагностическую запись

## Примеры использования

### Базовое использование

```python
from meet2obsidian.utils.logging import setup_logging, get_logger

# Настройка логирования
setup_logging(log_level="info", log_file="/path/to/logs/app.log")

# Получение логгера для модуля
logger = get_logger("my_module")

# Логирование сообщений
logger.info("Приложение запущено")
logger.error("Операция не удалась", error_code=500, retry=True)
```

### Логирование с контекстом

```python
# Получение логгера с начальным контекстом
logger = get_logger("auth_module", user_id="12345")

# Логирование с дополнительным контекстом
logger.info("Действие пользователя", action="login", status="success")

# Создание логгера с дополнительным контекстом
session_logger = logger.bind(session_id="abc123")
session_logger.warning("Необычная активность", location="Новое местоположение")
```

### Логирование исключений

```python
try:
    # Код, который может вызвать исключение
    result = 1 / 0
except Exception as e:
    logger.exception("Произошло исключение", operation="деление")
```

### Получение последних логов

```python
from meet2obsidian.utils.logging import get_last_logs

# Получение последних 10 ошибок
error_logs = get_last_logs("/path/to/logs/app.log", count=10, level="error")
for log in error_logs:
    print(f"{log['timestamp']} - {log['event']}")
```

### Диагностическое логирование

```python
from meet2obsidian.utils.logging import create_diagnostic_log_entry, get_logger

logger = get_logger("diagnostics")
create_diagnostic_log_entry(logger, {"app_version": "1.0.0"})
```

## API

### setup_logging()

```python
def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    rotate_logs: bool = True,
    add_console_handler: bool = True,
    additional_processors: Optional[List] = None
) -> logging.Logger
```

Настраивает систему логирования с использованием structlog и стандартного logging.

**Параметры:**
- `log_level` - Уровень логирования (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`). По умолчанию `"INFO"`.
- `log_file` - Путь к файлу логов. Если `None`, логи выводятся только в консоль.
- `max_bytes` - Максимальный размер файла логов перед ротацией (в байтах).
- `backup_count` - Количество файлов истории для хранения.
- `rotate_logs` - Использовать ли `RotatingFileHandler` (`True`) или обычный `FileHandler` (`False`).
- `add_console_handler` - Если `True`, добавляет консольный обработчик к корневому логгеру.
- `additional_processors` - Дополнительные процессоры structlog для добавления.

**Возвращает:**
- `logging.Logger` - Настроенный корневой логгер.

### get_logger()

```python
def get_logger(name: str, **initial_values) -> structlog.stdlib.BoundLogger
```

Возвращает структурированный логгер с указанным именем и начальными значениями контекста.

**Параметры:**
- `name` - Имя логгера, обычно имя модуля.
- `**initial_values` - Начальные значения контекста для привязки к логгеру.

**Возвращает:**
- `structlog.stdlib.BoundLogger` - Настроенный структурированный логгер.

### get_last_logs()

```python
def get_last_logs(log_file: str, count: int = 50, level: str = "info") -> List[Dict[str, Any]]
```

Получает последние N записей логов из файла лога.

**Параметры:**
- `log_file` - Путь к файлу лога.
- `count` - Количество записей логов для получения.
- `level` - Минимальный уровень лога для получения (`"debug"`, `"info"`, `"warning"`, `"error"`, `"critical"`).

**Возвращает:**
- `List[Dict[str, Any]]` - Последние записи логов в виде разобранных JSON объектов.

### create_diagnostic_log_entry()

```python
def create_diagnostic_log_entry(logger: structlog.stdlib.BoundLogger, environment: Dict[str, Any] = None) -> None
```

Создает диагностическую запись в логе с информацией о системе.

**Параметры:**
- `logger` - Структурированный логгер для использования.
- `environment` - Дополнительная информация о среде для включения.

## Формат логов

Логи создаются в формате JSON со следующими стандартными полями:

- `timestamp` - ISO-форматированная временная метка
- `level` - Уровень логирования (debug, info, warning, error, critical)
- `logger` - Имя логгера
- `event` - Сообщение лога
- Контекстные данные - Любые дополнительные поля, переданные при логировании

Пример записи лога:
```json
{
  "timestamp": "2023-05-12T10:15:30.123456Z",
  "level": "info",
  "logger": "auth_module",
  "event": "Действие пользователя",
  "user_id": "12345",
  "action": "login",
  "status": "success"
}
```

## Тестирование

Модуль логирования имеет обширный набор unit-тестов в `tests/unit/test_logging.py`, который проверяет:

- Настройку логирования с различными параметрами
- Работу функций создания и использования логгеров
- Поддержку различных уровней логирования
- Настройку и работу ротации логов
- Функциональность структурированного логирования с контекстом

## Примеры

В директории `examples/` есть примеры использования модуля логирования:

- `logging_example.py` - демонстрирует основные возможности модуля
- `test_logging_compliance.py` - проверяет соответствие модуля требованиям