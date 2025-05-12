# Команды CLI

Meet2Obsidian предоставляет интуитивный интерфейс командной строки (CLI) для удобного управления всеми функциями программы.

## Основные команды

### Команды управления сервисом

Управление основными функциями Meet2Obsidian осуществляется через группу команд `service`:

```bash
# Запуск сервиса Meet2Obsidian
meet2obsidian service start

# Запуск с настройкой автозапуска
meet2obsidian service start --autostart

# Остановка сервиса
meet2obsidian service stop

# Принудительная остановка сервиса
meet2obsidian service stop --force
```

### Проверка статуса

```bash
# Базовая проверка статуса
meet2obsidian status

# Подробный статус
meet2obsidian status --detailed

# Вывод в формате JSON
meet2obsidian status --format json

# Вывод в текстовом формате
meet2obsidian status --format text
```

## Команды управления конфигурацией

Meet2Obsidian предоставляет гибкие возможности для управления конфигурацией.

### Просмотр и изменение конфигурации

```bash
# Показать текущую конфигурацию
meet2obsidian config show

# Показать конфигурацию в формате JSON
meet2obsidian config show --format json

# Установить значение параметра конфигурации
meet2obsidian config set paths.video_directory /path/to/videos

# Сбросить конфигурацию к значениям по умолчанию
meet2obsidian config reset
```

### Импорт и экспорт конфигурации

```bash
# Экспортировать конфигурацию в файл
meet2obsidian config export /path/to/config.yaml

# Экспортировать в формате JSON
meet2obsidian config export /path/to/config.json --format json

# Импортировать конфигурацию из файла
meet2obsidian config import /path/to/config.yaml
```

## Команды для работы с логами

Meet2Obsidian предоставляет команды для управления и просмотра логов.

### Показать логи

```bash
# Показать последние 20 записей логов
meet2obsidian logs show

# Показать определенное количество записей
meet2obsidian logs show --count 50

# Показать логи определенного уровня
meet2obsidian logs show --level error

# Показать логи в формате JSON
meet2obsidian logs show --format json

# Показать логи из нестандартного файла
meet2obsidian logs show --log-file /path/to/custom.log
```

### Очистка логов

```bash
# Очистить файл логов
meet2obsidian logs clear
```

## Команды управления очередью обработки

Meet2Obsidian предоставляет команды для управления очередью обработки файлов.

### Просмотр статуса очереди

```bash
# Показать статус очереди обработки
meet2obsidian process status

# Показать подробную информацию о файлах в очереди
meet2obsidian process status --detailed

# Вывод статуса в формате JSON
meet2obsidian process status --format json

# Вывод статуса в текстовом формате
meet2obsidian process status --format text
```

### Добавление файлов в очередь

```bash
# Добавить файл в очередь обработки
meet2obsidian process add /path/to/video.mp4

# Добавить файл с высоким приоритетом
meet2obsidian process add /path/to/important_video.mp4 --priority 10
```

### Управление обработкой файлов

```bash
# Повторная обработка файлов с ошибками
meet2obsidian process retry

# Очистка завершенных файлов из очереди
meet2obsidian process clear
```

## Команды управления API-ключами

Meet2Obsidian предоставляет команды для управления API-ключами, используемыми для доступа к внешним сервисам.

### Настройка API-ключей

```bash
# Настройка всех API-ключей одной командой (с интерактивным вводом)
meet2obsidian apikeys setup

# Настройка всех API-ключей с передачей значений через опции
meet2obsidian apikeys setup --rev-ai YOUR_REV_AI_KEY --claude YOUR_CLAUDE_KEY

# Установка отдельного API-ключа (с интерактивным вводом)
meet2obsidian apikeys set rev_ai

# Установка отдельного API-ключа (с указанием значения)
meet2obsidian apikeys set rev_ai --value YOUR_REV_AI_KEY
```

### Просмотр информации об API-ключах

```bash
# Просмотр списка всех API-ключей
meet2obsidian apikeys list

# Просмотр списка в формате JSON
meet2obsidian apikeys list --format json

# Получение API-ключа (маскированное значение)
meet2obsidian apikeys get rev_ai

# Получение полного значения API-ключа
meet2obsidian apikeys get rev_ai --show
```

### Удаление API-ключей

```bash
# Удаление API-ключа (с запросом подтверждения)
meet2obsidian apikeys delete test_key

# Удаление API-ключа без запроса подтверждения
meet2obsidian apikeys delete test_key --yes
```

## Автодополнение команд

Meet2Obsidian поддерживает автодополнение команд для различных оболочек.

```bash
# Вывод скрипта автодополнения для текущей оболочки
meet2obsidian completion

# Вывод скрипта автодополнения для конкретной оболочки
meet2obsidian completion --shell bash
meet2obsidian completion --shell zsh
meet2obsidian completion --shell fish

# Установка автодополнения в профиль оболочки
meet2obsidian completion --install
```

## Глобальные опции

Все команды поддерживают следующие глобальные опции:

```bash
# Получение справки по любой команде
meet2obsidian --help
meet2obsidian service --help
meet2obsidian service start --help

# Вывод версии программы
meet2obsidian --version

# Включение подробного режима вывода
meet2obsidian --verbose status

# Указание пользовательского файла для логов
meet2obsidian --log-file /path/to/custom.log status
```

## Форматирование вывода

Meet2Obsidian использует цветное форматирование для улучшения восприятия вывода команд:

- Зеленым цветом выделяются успешные операции ✅
- Красным цветом выделяются ошибки и предупреждения ❌
- Голубым цветом выделяются заголовки таблиц и важная информация ℹ️
- Затененным текстом выделяются метки и менее важная информация

## Примеры использования

### Полный цикл запуска и проверки

```bash
# Установка API-ключей
meet2obsidian apikeys setup

# Настройка путей к файлам
meet2obsidian config set paths.video_directory ~/Videos/GoogleMeet
meet2obsidian config set paths.obsidian_vault ~/Documents/Obsidian/MainVault

# Запуск сервиса с автозапуском
meet2obsidian service start --autostart

# Проверка статуса
meet2obsidian status --detailed

# Проверка очереди обработки
meet2obsidian process status --detailed
```

### Диагностика проблем

```bash
# Проверка статуса API-ключей
meet2obsidian apikeys list

# Просмотр логов ошибок
meet2obsidian logs show --level error --count 50

# Проверка файлов с ошибками обработки
meet2obsidian process status --detailed

# Повторная обработка файлов с ошибками
meet2obsidian process retry

# Проверка конфигурации
meet2obsidian config show
```

### Создание резервной копии настроек

```bash
# Экспорт конфигурации
meet2obsidian config export ~/backup/meet2obsidian-config.yaml

# Экспорт API-ключей (не рекомендуется для обеспечения безопасности)
# Вместо этого используйте настройку ключей при необходимости
meet2obsidian apikeys list --format json > ~/backup/api-keys-status.json
```