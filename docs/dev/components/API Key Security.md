# Безопасное хранение API-ключей

## Обзор

Компонент безопасного хранения API-ключей отвечает за надежное хранение и получение чувствительных данных, таких как API-ключи сторонних сервисов (Rev.ai, Claude и т.д.). Компонент использует системное хранилище ключей (macOS Keychain), чтобы обеспечить безопасность данных.

## Архитектура

Основной класс компонента - `KeychainManager`, который находится в модуле `meet2obsidian.utils.security`. Класс предоставляет интерфейс для работы с системным хранилищем ключей через библиотеку `keyring`.

### Диаграмма компонентов

```
                 +----------------+
                 | KeychainManager|
                 +----------------+
                 | - SERVICE_NAME |
                 +----------------+
                 | + store_api_key|
                 | + get_api_key  |
                 | + delete_api_key|
                 +----------------+
                          |
                          | Использует
                          v
                 +----------------+
                 |     keyring    |
                 +----------------+
                 | Библиотека для |
                 | работы с        |
                 | хранилищем      |
                 | ключей          |
                 +----------------+
                          |
                          | Взаимодействует с
                          v
                 +----------------+
                 |  OS Keychain   |
                 |  (macOS)       |
                 +----------------+
```

## API

### KeychainManager

```python
class KeychainManager:
    def __init__(self, logger=None):
        """
        Инициализация менеджера ключей.
        
        Args:
            logger: Объект логгера (опционально). Если не указан, создается новый логгер.
        """
        
    def store_api_key(self, key_name: str, api_key: str) -> bool:
        """
        Сохранение API-ключа в хранилище.
        
        Args:
            key_name: Название ключа (например, 'rev_ai', 'claude')
            api_key: Значение API-ключа
            
        Returns:
            bool: True в случае успеха, False при ошибке
        """
        
    def get_api_key(self, key_name: str) -> Optional[str]:
        """
        Получение API-ключа из хранилища.
        
        Args:
            key_name: Название ключа
            
        Returns:
            str или None: Значение API-ключа, если найден, иначе None
        """
        
    def delete_api_key(self, key_name: str) -> bool:
        """
        Удаление API-ключа из хранилища.
        
        Args:
            key_name: Название ключа
            
        Returns:
            bool: True в случае успеха, False при ошибке
        """
```

## Использование

### Пример использования

```python
from meet2obsidian.utils.security import KeychainManager
from meet2obsidian.utils.logging import get_logger

# Создаем логгер
logger = get_logger("security_example")

# Создаем экземпляр KeychainManager
keychain_manager = KeychainManager(logger=logger)

# Сохранение API-ключа
api_key = "your_api_key_here"
success = keychain_manager.store_api_key("rev_ai", api_key)

if success:
    logger.info("API-ключ успешно сохранен")

# Получение API-ключа
saved_key = keychain_manager.get_api_key("rev_ai")

if saved_key:
    logger.info("API-ключ успешно получен")
    
# Удаление API-ключа
if keychain_manager.delete_api_key("rev_ai"):
    logger.info("API-ключ успешно удален")
```

### Интеграция в CLI

```python
import click
from meet2obsidian.utils.security import KeychainManager

@click.command()
@click.option("--key", prompt="Название API-ключа", help="Название ключа (например, rev_ai)")
@click.option("--value", prompt="Значение API-ключа", help="Значение API-ключа")
def set_api_key(key, value):
    """Сохранение API-ключа в системное хранилище."""
    keychain_manager = KeychainManager()
    if keychain_manager.store_api_key(key, value):
        click.echo(f"API-ключ {key} успешно сохранен")
    else:
        click.echo(f"Ошибка при сохранении API-ключа {key}")
```

## Безопасность

- API-ключи хранятся в системном хранилище ключей (macOS Keychain)
- Ключи не сохраняются в файлах конфигурации или коде
- Доступ к ключам контролируется системой безопасности операционной системы
- Логирование чувствительной информации ограничено (не записываются значения ключей)

## Тестирование

Компонент имеет два типа тестов:

1. **Модульные тесты**: проверяют функциональность с использованием моков для имитации взаимодействия с системным хранилищем ключей
   - `tests/unit/test_security.py`

2. **Интеграционные тесты**: проверяют взаимодействие с реальным системным хранилищем ключей
   - `tests/integration/test_security_integration.py`

### Запуск тестов

```bash
# Запуск только модульных тестов (по умолчанию)
./tests/run_tests.py

# Запуск всех тестов, включая интеграционные
./tests/run_tests.py --integration

# Запуск только тестов безопасности
./tests/run_tests.py tests/unit/test_security.py
```

## Ограничения и известные проблемы

- Компонент в основном ориентирован на работу с macOS Keychain
- На других операционных системах используются соответствующие хранилища ключей через библиотеку `keyring`
- В средах без графического интерфейса может потребоваться дополнительная настройка `keyring`

## Будущие улучшения

- Поддержка шифрования ключей с использованием пользовательского пароля
- Реализация проверки авторизации для доступа к ключам
- Добавление возможности временного хранения ключей в памяти для повышения производительности