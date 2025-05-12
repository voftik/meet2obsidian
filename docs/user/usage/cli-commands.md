# Команды CLI

Meet2Obsidian предоставляет интерфейс командной строки (CLI) для удобного использования различных функций программы.

## Основные команды

### Запуск приложения

```bash
# Запуск с настройками по умолчанию
meet2obsidian run

# Запуск с указанием конфигурационного файла
meet2obsidian run --config /path/to/config.yaml
```

### Обработка файла

```bash
# Обработка одного файла
meet2obsidian process /path/to/meeting.mp4

# Обработка файла с указанием выходной директории
meet2obsidian process /path/to/meeting.mp4 --output /path/to/notes
```

### Настройка

```bash
# Инициализация конфигурационного файла
meet2obsidian config init

# Настройка API ключей
meet2obsidian config set-api-keys
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
```

### Очистка логов

```bash
# Очистить основной файл логов
meet2obsidian logs clear

# Очистить все ротированные файлы логов
meet2obsidian logs clear --all
```

### Создание диагностической информации

```bash
# Создать диагностическую запись в логах
meet2obsidian logs diagnostic

# Создать полный отчет о системе
meet2obsidian logs diagnostic --full
```

## Мониторинг

```bash
# Запустить мониторинг директорий
meet2obsidian monitor start

# Остановить мониторинг
meet2obsidian monitor stop

# Показать статус мониторинга
meet2obsidian monitor status
```

## Опции логирования

Все команды поддерживают следующие опции логирования:

```bash
# Изменить уровень логирования
meet2obsidian --log-level debug run

# Указать файл для логов
meet2obsidian --log-file /path/to/custom.log run
```

## Справка

Для получения справки по любой команде:

```bash
# Общая справка
meet2obsidian --help

# Справка по определенной команде
meet2obsidian logs --help
meet2obsidian logs show --help
```