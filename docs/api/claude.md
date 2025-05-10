# Claude API Спецификация для meet2obsidian

## Обзор

Claude API предоставляет доступ к языковым моделям Anthropic для анализа текста и генерации контента. В контексте проекта meet2obsidian, Claude API используется для анализа транскрибированного текста встреч с целью извлечения структурированной информации, такой как:

- Основная информация о встрече
- Краткое содержание
- Выявленные договорённости
- Задачи и последующие действия

## Аутентификация

Все запросы к API Claude требуют аутентификации с использованием API-ключа.

- **Заголовок**: `x-api-key`
- **Значение**: Ваш API-ключ Anthropic
- **Хранение**: В проекте meet2obsidian API-ключи должны храниться в macOS Keychain через модуль `KeychainManager`

```python
# Пример получения ключа из Keychain
api_key = keychain_manager.get_api_key("claude")

# Пример инициализации клиента
client = anthropic.Anthropic(api_key=api_key)
```

## Основные ресурсы API

### Модели

Claude API предоставляет доступ к различным моделям. В meet2obsidian предпочтительно использовать:

| Модель | Описание | Токены контекста | Use-case |
|--------|----------|-------------------|----------|
| claude-3-opus-20240229 | Высокая точность | 200K | Детальный анализ транскрипций |
| claude-3-sonnet-20240229 | Баланс скорость/точность | 200K | Стандартный анализ |
| claude-3-haiku-20240307 | Наименьшая задержка | 200K | Быстрая обработка коротких транскрипций |
| claude-3-7-sonnet-20250219 | Новейшая версия | 200K | Улучшенная точность |

### Сообщения API

Основной эндпоинт API для взаимодействия с Claude:

- **Эндпоинт**: `/v1/messages`
- **Метод**: POST
- **Тип содержимого**: `application/json`

## Структура запроса

```json
{
  "model": "claude-3-opus-20240229",
  "max_tokens": 1000,
  "temperature": 0.1,
  "messages": [
    {
      "role": "user",
      "content": "Текст транскрипции и инструкции для анализа"
    }
  ],
  "system": "Системная инструкция для установки контекста"
}
```

### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| model | string | Да | Идентификатор модели Claude для использования |
| max_tokens | integer | Да | Максимальное количество токенов для генерации |
| temperature | number | Нет | Уровень "креативности" (0.0-1.0), рекомендуется 0.1 для аналитических задач |
| messages | array | Да | Массив сообщений, определяющий контекст запроса |
| system | string | Нет | Системная инструкция для установки общего контекста обработки |

## Структура ответа

```json
{
  "id": "msg_0123456789abcdef",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Структурированный анализ встречи..."
    }
  ],
  "model": "claude-3-opus-20240229",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 1024,
    "output_tokens": 756
  }
}
```

### Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| id | string | Уникальный идентификатор сообщения |
| type | string | Тип объекта (всегда "message") |
| role | string | Роль сообщения (всегда "assistant") |
| content | array | Массив блоков контента в ответе |
| model | string | Модель, использованная для генерации ответа |
| stop_reason | string | Причина остановки генерации |
| usage | object | Информация об использованных токенах |

## Шаблоны промптов для meet2obsidian

В контексте meet2obsidian, для каждого типа анализа используются специализированные промпты:

### 1. Извлечение информации о встрече

```python
MEETING_INFO_PROMPT = """
Ты анализируешь транскрипцию встречи. Извлеки ключевую информацию о встрече, включая:
1. Очевидную цель/тип встречи
2. Основных участников (если упоминаются имена)
3. Дату и время (если упоминаются)
4. Основные обсуждаемые темы

Форматируй ответ в виде аккуратного markdown без дополнительных комментариев. Просто предоставь извлеченную информацию.

ТРАНСКРИПЦИЯ:
{transcript}
"""
```

### 2. Создание краткого содержания

```python
SUMMARY_PROMPT = """
Создай лаконичное резюме следующей транскрипции встречи. Сосредоточься на самых важных моментах, решениях и выводах. Ограничь резюме примерно 200-300 словами, отформатировав его в виде абзацев markdown без заголовков.

ТРАНСКРИПЦИЯ:
{transcript}
"""
```

### 3. Извлечение договоренностей и решений

```python
AGREEMENTS_PROMPT = """
Извлеки все соглашения и решения, принятые во время этой встречи. Включи:
1. Четкие решения, которые были приняты
2. Обязательства, с которыми согласились участники
3. Точки согласия, достигнутые в ходе обсуждения

Форматируй в виде маркированного списка markdown, каждое соглашение отдельным пунктом. Если четких соглашений не было, укажи это.

ТРАНСКРИПЦИЯ:
{transcript}
"""
```

### 4. Извлечение задач

```python
TASKS_PROMPT = """
Извлеки все пункты действий, задачи и последующие шаги, упомянутые на этой встрече. Для каждого пункта укажи:
1. Конкретную задачу
2. Кто ответственен (если указано)
3. Сроки выполнения (если указаны)

Форматируй в виде чек-листа markdown, используя формат:
- [ ] Описание задачи (Ответственный, Срок)

Если ответственный или срок не указаны, опусти эту часть. Если задачи не были назначены, укажи это.

ТРАНСКРИПЦИЯ:
{transcript}
"""
```

## Обработка длинных транскрипций

Claude API имеет ограничения на количество токенов входного контекста. Для обработки длинных транскрипций рекомендуется:

1. Разделять транскрипцию на части, не превышающие лимит токенов модели
2. Обрабатывать каждую часть отдельно
3. Объединять результаты для создания итогового вывода

```python
def process_long_transcript(transcript, prompt_template, max_chunk_tokens=100000):
    # Разбиение транскрипции на части
    chunks = split_transcript_into_chunks(transcript, max_chunk_tokens)
    results = []
    
    # Обработка каждой части
    for chunk in chunks:
        chunk_prompt = prompt_template.format(transcript=chunk)
        chunk_result = call_claude_api(chunk_prompt)
        results.append(chunk_result)
    
    # Объединение результатов
    return combine_results(results)
```

## Обработка ошибок и повторные попытки

При работе с внешними API рекомендуется реализовать механизм повторных попыток с экспоненциальной задержкой:

```python
def call_with_retry(func, *args, max_retries=3, **kwargs):
    """Выполнение функции с повторными попытками при сбоях"""
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            return func(*args, **kwargs)
        except (anthropic.APIError, anthropic.APIConnectionError, anthropic.RateLimitError) as e:
            attempt += 1
            last_error = e
            if attempt < max_retries:
                sleep_time = 2 ** attempt  # Экспоненциальная задержка
                time.sleep(sleep_time)
    
    # Исчерпаны все попытки
    raise last_error
```

## Пример интеграции с Python SDK

```python
import anthropic
import time

class ClaudeAPIClient:
    def __init__(self, api_key, model="claude-3-opus-20240229", cache_manager=None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.cache_manager = cache_manager
    
    def analyze_transcript(self, transcript, prompt_template, **params):
        """Анализ транскрипции с использованием указанного шаблона промпта"""
        # Формирование кэш-ключа
        if self.cache_manager:
            cache_key = f"{hash(transcript)[:20]}_{hash(prompt_template)[:20]}"
            cached_result = self.cache_manager.get('claude_analysis', cache_key)
            if cached_result:
                return cached_result
        
        # Формирование промпта
        full_prompt = prompt_template.format(transcript=transcript, **params)
        
        # Вызов API с повторными попытками
        response = self._call_api_with_retry(
            full_prompt,
            max_tokens=params.get('max_tokens', 1000),
            temperature=params.get('temperature', 0.1)
        )
        
        result = response.content[0].text
        
        # Сохранение в кэш
        if self.cache_manager:
            self.cache_manager.store('claude_analysis', cache_key, result)
        
        return result
    
    def _call_api_with_retry(self, prompt, max_retries=3, **params):
        """Вызов API с механизмом повторных попыток"""
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            try:
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=params.get('max_tokens', 1000),
                    temperature=params.get('temperature', 0.1),
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
            except (anthropic.APIError, anthropic.APIConnectionError, anthropic.RateLimitError) as e:
                attempt += 1
                last_error = e
                if attempt < max_retries:
                    sleep_time = 2 ** attempt  # Экспоненциальная задержка
                    time.sleep(sleep_time)
        
        # Исчерпаны все попытки
        raise last_error
```

## Отслеживание использования токенов

Ответы API Claude включают информацию об использовании токенов, которую следует отслеживать для контроля расходов:

```python
def track_token_usage(response, logger):
    """Отслеживание использования токенов"""
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    total_tokens = input_tokens + output_tokens
    
    logger.info(
        "API usage",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens
    )
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens
    }
```

## Интеграция с системой кэширования meet2obsidian

Для оптимизации использования API рекомендуется интегрироваться с системой кэширования:

```python
def analyze_with_cache(transcript, prompt_template, cache_manager, **params):
    """Анализ транскрипции с использованием кэша"""
    # Создание уникального ключа кэша
    cache_key = f"{hashlib.md5(transcript.encode()).hexdigest()}_{hashlib.md5(prompt_template.encode()).hexdigest()}"
    
    # Проверка наличия результата в кэше
    cached_result = cache_manager.get('claude_analysis', cache_key)
    if cached_result:
        return cached_result
    
    # Выполнение анализа при отсутствии в кэше
    result = call_claude_api(transcript, prompt_template, **params)
    
    # Сохранение результата в кэш
    cache_manager.store('claude_analysis', cache_key, result)
    
    return result
```

## Рекомендации по использованию API в meet2obsidian

1. **Температура**: Используйте низкое значение (0.1-0.2) для аналитических задач
2. **Системный промпт**: Установите системный промпт для определения роли и контекста
3. **Токенизация**: Учитывайте, что разные типы контента используют разное количество токенов
4. **Кэширование**: Всегда кэшируйте результаты для экономии затрат и улучшения отзывчивости
5. **Обработка ошибок**: Реализуйте надежную обработку ошибок и механизм повторных попыток
6. **Разделение контента**: Разработайте стратегию разделения длинных транскрипций

## Лимиты и ограничения

1. **Длина контекста**: Ограничение на максимальную длину входного контекста (обычно 100K-200K токенов)
2. **Квоты API**: Учитывайте лимиты запросов в своем плане API
3. **Стоимость**: Отслеживайте использование токенов для контроля затрат
4. **Задержка**: API имеет переменную задержку в зависимости от размера входного/выходного контекста

## Приложение: Коды ошибок API и их обработка

| Код ошибки | Описание | Рекомендуемая обработка |
|------------|----------|-------------------------|
| 400 | Неверный запрос | Проверить и исправить параметры запроса |
| 401 | Ошибка аутентификации | Проверить API-ключ |
| 403 | Запрещено | Проверить права доступа и квоты |
| 404 | Не найдено | Проверить эндпоинт и доступность ресурса |
| 429 | Превышение лимита запросов | Реализовать задержку и повторные попытки |
| 500 | Внутренняя ошибка сервера | Повторить запрос позже |

## Полезные ресурсы

1. [Официальная документация Claude API](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
2. [Python SDK для Claude API](https://github.com/anthropics/anthropic-sdk-python)
3. [Руководство по промптингу Claude](https://docs.anthropic.com/claude/docs/introduction-to-prompt-design)
4. [Рекомендации по работе с длинными документами](https://docs.anthropic.com/claude/docs/long-document-chunking-strategies)