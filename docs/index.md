# Meet2Obsidian

## Что такое Meet2Obsidian?

Meet2Obsidian - это инструмент, который автоматически преобразует записи встреч (аудио/видео) в структурированные заметки в [Obsidian](https://obsidian.md/). Он использует AI для транскрибации и анализа записей и создания полезных заметок с учётом контекста.

## Возможности

- **Автоматическая транскрибация** записей встреч с помощью API Rev.ai
- **AI-анализ** транскрипций с использованием Claude API
- **Генерация структурированных заметок** с выделением ключевых моментов, задач и решений
- **Интеграция с Obsidian** для хранения и связывания заметок
- **Мониторинг директорий** для автоматической обработки новых записей
- **Гибкая настройка** через конфигурационные файлы
- **Структурированное логирование** для отслеживания работы и диагностики проблем
- **Безопасное хранение API-ключей** в системном хранилище ключей с удобным CLI-интерфейсом управления

## Приступая к работе

Чтобы начать использовать Meet2Obsidian:

1. [Установите](user/getting-started/installation.md) приложение
2. Настройте API ключи для Rev.ai и Claude
3. Настройте директории для мониторинга и выходных заметок
4. Запустите приложение или настройте автозапуск

Для получения подробных инструкций, обратитесь к [руководству по началу работы](user/getting-started/installation.md).

## Документация

### Пользовательская документация

- [Руководство по установке](user/getting-started/installation.md)
- [Использование](usage.md)
- [Управление API-ключами](user/usage/api-keys-management.md)
- [Логирование](user/usage/logging.md)
- [Устранение неполадок](user/troubleshooting/README.md)

### Документация для разработчиков

- [Руководство по разработке](development.md)
- [Компоненты](dev/components/)
- [API](api/)

## Лицензия

Meet2Obsidian распространяется под лицензией MIT. Подробную информацию смотрите в файле [LICENSE](../LICENSE).