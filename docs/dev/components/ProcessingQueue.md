# Компонент: Система обработки очереди файлов

## Обзор

Система обработки очереди файлов (Processing Queue System) — это компонент, отвечающий за управление файлами, ожидающими обработки, их приоритизацию, отслеживание состояния обработки и обеспечение надежного восстановления после сбоев или перезапуска приложения.

## Ключевые компоненты

### 1. ProcessingStatus (Enum)

Перечисление, определяющее возможные состояния файла в процессе обработки:

```python
class ProcessingStatus(Enum):
    """Enum representing the status of a file in the processing queue."""
    PENDING = 0      # File is waiting to be processed
    PROCESSING = 1   # File is currently being processed
    COMPLETED = 2    # File has been successfully processed
    ERROR = 3        # Error occurred during processing, may be retried
    FAILED = 4       # Processing failed permanently (max retries exceeded)
```

### 2. ProcessingState

Класс, представляющий состояние отдельного файла в очереди обработки:

```python
class ProcessingState:
    """
    Represents the state of a file in the processing queue.
    
    Attributes:
        file_path (str): Path to the file
        status (ProcessingStatus): Current status of the file
        priority (int): Processing priority (higher numbers = higher priority)
        metadata (Dict[str, Any]): Additional metadata about the file
        created_at (datetime): When the file was added to the queue
        updated_at (datetime): When the state was last updated
        started_at (datetime): When processing started (optional)
        completed_at (datetime): When processing completed (optional)
        error_count (int): Number of processing errors
        max_retries (int): Maximum number of retry attempts
        error_message (str): Last error message (optional)
    """
```

### 3. FileProcessor

Класс, отвечающий за обработку файлов:

```python
class FileProcessor:
    """
    Handles file processing operations.
    
    Attributes:
        process_func (Callable): Function that processes a file
        logger (logging.Logger): Logger instance
        max_workers (int): Maximum number of concurrent worker threads
    """
```

### 4. ProcessingQueue

Класс, управляющий очередью файлов:

```python
class ProcessingQueue:
    """
    Manages a queue of files for processing.
    
    Attributes:
        processor (FileProcessor): Processor for handling files
        persistence_file (str): Path to file for saving/loading queue state
        logger (logging.Logger): Logger instance
    """
```

## Архитектура

Система использует многослойную архитектуру:

1. **Уровень состояния** (`ProcessingState`) — отслеживает состояние отдельных файлов
2. **Уровень обработки** (`FileProcessor`) — обрабатывает файлы с поддержкой потоков
3. **Уровень очереди** (`ProcessingQueue`) — управляет очередью файлов с поддержкой приоритетов

## Последовательность обработки файла

1. Файл добавляется в очередь через `ProcessingQueue.add_file()`
2. Файл получает начальный статус `PENDING`
3. Файл выбирается для обработки на основе приоритета через `ProcessingQueue.process_next()`
4. Статус файла меняется на `PROCESSING`
5. `FileProcessor` обрабатывает файл с помощью переданной функции обработки
6. По завершении статус меняется на:
   - `COMPLETED` при успешной обработке
   - `ERROR` при ошибке (возможны повторные попытки)
   - `FAILED` если исчерпано максимальное количество попыток

## Ключевые функции и методы

### ProcessingState

```python
def mark_as_processing(self) -> None:
    """Mark the file as currently being processed."""
    
def mark_as_completed(self) -> None:
    """Mark the file as successfully completed."""
    
def mark_as_error(self, error_message: str) -> None:
    """Mark the file as having an error."""
    
def mark_as_failed(self) -> None:
    """Mark the file as permanently failed (max retries exceeded)."""
    
def can_retry(self) -> bool:
    """Check if file can be retried based on error count."""
    
def to_dict(self) -> Dict[str, Any]:
    """Convert state to dictionary for serialization."""
    
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingState':
    """Create state from dictionary after deserialization."""
```

### FileProcessor

```python
def process_file(self, file_path: str, metadata: Dict[str, Any]) -> concurrent.futures.Future:
    """Process a file asynchronously using the thread pool."""
    
def process_file_sync(self, file_path: str, metadata: Dict[str, Any]) -> bool:
    """Process a file synchronously (blocking)."""
    
def register_callback(self, callback: Callable[[str, ProcessingStatus, Dict[str, Any]], None]) -> None:
    """Register a callback function to be called when file status changes."""
    
def shutdown(self, wait: bool = True) -> None:
    """Shutdown the processor, optionally waiting for pending tasks."""
```

### ProcessingQueue

```python
def add_file(self, file_path: str, priority: int = 0, metadata: Optional[Dict[str, Any]] = None,
             max_retries: int = 3) -> bool:
    """Add a file to the processing queue."""
    
def process_next(self) -> bool:
    """Process the next file in the queue based on priority."""
    
def process_all(self, max_files: Optional[int] = None) -> int:
    """Process all pending files in the queue."""
    
def get_status(self, file_path: str) -> Optional[ProcessingStatus]:
    """Get the current status of a file in the queue."""
    
def get_all_files(self) -> Dict[str, ProcessingState]:
    """Get all files in the queue with their states."""
    
def save_state(self, file_path: Optional[str] = None) -> bool:
    """Save the current state to a file."""
    
def load_state(self, file_path: Optional[str] = None) -> bool:
    """Load the state from a file."""
    
def register_callback(self, callback: Callable[[str, ProcessingStatus, Dict[str, Any]], None]) -> None:
    """Register a callback function to be notified of file status changes."""
    
def remove_file(self, file_path: str) -> bool:
    """Remove a file from the queue."""
    
def stop(self, wait: bool = True) -> None:
    """Stop the processing queue."""
```

## Система обратных вызовов (Callbacks)

Система поддерживает механизм обратных вызовов, который позволяет внешним компонентам подписываться на изменения состояния файлов:

```python
def register_callback(callback: Callable[[str, ProcessingStatus, Dict[str, Any]], None]) -> None
```

Функция обратного вызова получает:
- Путь к файлу
- Новый статус файла
- Метаданные файла (включая информацию об ошибках)

## Взаимодействие с другими компонентами

### Взаимодействие с FileMonitor

`FileMonitor` использует `ProcessingQueue` для добавления обнаруженных файлов в очередь обработки:

```python
class FileMonitor:
    # ...
    def __init__(self, directory: str, file_patterns: List[str], processing_queue: ProcessingQueue, ...):
        self.processing_queue = processing_queue
        # ...
        
    def _handle_file_event(self, file_path: str):
        # Добавление файла в очередь при обнаружении
        self.processing_queue.add_file(file_path)
```

### Взаимодействие с ApplicationManager

`ApplicationManager` управляет `ProcessingQueue` и отслеживает статус обработки:

```python
class ApplicationManager:
    # ...
    def initialize_components(self) -> bool:
        # ...
        # Создание и настройка ProcessingQueue
        self.processing_queue = ProcessingQueue(
            processor=FileProcessor(self._process_file),
            persistence_file=os.path.join(app_support_dir, "processing_queue.json"),
            logger=self.logger
        )
        
        # Регистрация обратного вызова для отслеживания статуса
        self.processing_queue.register_callback(self._handle_file_status_change)
        # ...
```

## Персистентность и восстановление

Система поддерживает сохранение и загрузку состояния очереди в/из JSON-файла:

```python
# Сохранение состояния
processing_queue.save_state("/path/to/state.json")

# Загрузка состояния
processing_queue.load_state("/path/to/state.json")
```

Формат JSON-файла:

```json
{
  "/path/to/file1.mp4": {
    "file_path": "/path/to/file1.mp4",
    "status": "COMPLETED",
    "priority": 0,
    "metadata": {"type": "meeting", "duration": 3600},
    "created_at": "2025-05-14T10:00:00.123456",
    "updated_at": "2025-05-14T10:15:30.654321",
    "started_at": "2025-05-14T10:01:00.123456",
    "completed_at": "2025-05-14T10:15:30.654321",
    "error_count": 0,
    "max_retries": 3,
    "error_message": null
  },
  "/path/to/file2.mp4": {
    "file_path": "/path/to/file2.mp4",
    "status": "ERROR",
    "priority": 1,
    "metadata": {"type": "lecture"},
    "created_at": "2025-05-14T11:00:00.123456",
    "updated_at": "2025-05-14T11:05:30.654321",
    "started_at": "2025-05-14T11:01:00.123456",
    "completed_at": null,
    "error_count": 1,
    "max_retries": 3,
    "error_message": "Failed to extract audio: invalid file format"
  }
}
```

## Параметры конфигурации

Система поддерживает следующие параметры конфигурации:

```python
# В config.py или аналогичном
config = {
    "processing": {
        "max_concurrent_files": 2,      # Максимальное количество одновременно обрабатываемых файлов
        "max_retries": 3,               # Максимальное количество попыток обработки файла
        "default_priority": 0,          # Приоритет по умолчанию для новых файлов
        "persistence_file": "...",      # Путь к файлу сохранения состояния очереди
        "auto_process": True            # Автоматическая обработка файлов при добавлении
    }
}
```

## Примеры использования

### Базовое использование

```python
from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.processing.queue import ProcessingQueue

# Функция обработки файла
def process_file(file_path, metadata):
    # Реальная обработка файла...
    print(f"Processing {file_path} with metadata: {metadata}")
    return True  # True = успех, False = ошибка

# Создание обработчика
processor = FileProcessor(process_file)

# Создание очереди
queue = ProcessingQueue(processor, persistence_file="queue_state.json")

# Добавление файлов
queue.add_file("/path/to/file1.mp4", priority=1)
queue.add_file("/path/to/file2.mp4", priority=2)  # Будет обработан первым (более высокий приоритет)

# Обработка всех файлов
queue.process_all()

# Сохранение состояния
queue.save_state()
```

### Использование обратных вызовов

```python
# Функция обратного вызова
def status_callback(file_path, status, metadata):
    print(f"File {file_path} status changed to {status.name}")
    if status == ProcessingStatus.COMPLETED:
        print(f"File processed successfully: {file_path}")
    elif status == ProcessingStatus.ERROR:
        print(f"Error processing file: {file_path}, message: {metadata.get('error')}")

# Регистрация обратного вызова
queue.register_callback(status_callback)
```

### Восстановление после перезапуска

```python
# Создание очереди при запуске приложения
queue = ProcessingQueue(processor, persistence_file="queue_state.json")

# Загрузка сохраненного состояния
if queue.load_state():
    print("Queue state loaded successfully")
    
    # Показать состояние очереди
    all_files = queue.get_all_files()
    print(f"Loaded {len(all_files)} files:")
    for file_path, state in all_files.items():
        print(f"- {file_path}: {state.status.name}")
    
    # Продолжить обработку прерванных файлов
    queue.process_all()
```

## Тестирование

### Модульные тесты

Для компонента реализованы следующие модульные тесты:

1. `test_processing_state.py` — тесты для класса ProcessingState
2. `test_processing_queue_add.py` — тесты для добавления файлов в очередь
3. `test_processing_queue_process.py` — тесты для обработки файлов
4. `test_processing_queue_recovery.py` — тесты для сохранения/загрузки состояния
5. `test_processing_queue_priority.py` — тесты для приоритетной обработки

### Интеграционные тесты

Для интеграции с другими компонентами реализованы:

1. `test_processing_queue.py` — интеграционные тесты для всей системы
2. `test_processing_queue_simplified.py` — упрощенные тесты для основной функциональности
3. `test_persistence.py` — тесты для механизма сохранения/загрузки состояния

### Запуск тестов

Для запуска всех тестов, связанных с системой обработки очереди:

```bash
python -m tests.run_processing_queue_tests
```

## Рекомендации по использованию

1. **Настройка функции обработки**:
   ```python
   def process_file(file_path, metadata):
       # Включите обработку исключений
       try:
           # Реальная обработка файла...
           return True
       except Exception as e:
           logger.error(f"Error processing {file_path}: {str(e)}")
           return False
   ```

2. **Приоритизация файлов**:
   ```python
   # Высокоприоритетные файлы (обрабатываются первыми)
   queue.add_file("/path/to/important.mp4", priority=10)
   
   # Обычные файлы
   queue.add_file("/path/to/normal.mp4", priority=0)
   
   # Низкоприоритетные файлы (обрабатываются последними)
   queue.add_file("/path/to/background.mp4", priority=-10)
   ```

3. **Использование метаданных**:
   ```python
   queue.add_file(
       "/path/to/file.mp4",
       metadata={
           "type": "meeting",
           "duration": 3600,
           "participants": ["Alice", "Bob"],
           "tags": ["important", "quarterly"]
       }
   )
   ```

4. **Регулярное сохранение состояния**:
   ```python
   # В основном цикле приложения
   def run_application():
       # ...
       try:
           while True:
               queue.process_all()
               queue.save_state()  # Регулярное сохранение
               time.sleep(60)  # Периодическая проверка
       except Exception as e:
           logger.error(f"Error in main loop: {str(e)}")
           queue.save_state()  # Сохранение при ошибке
   ```

## Дальнейшие улучшения

1. **Поддержка пауз и возобновления** — возможность приостановить и возобновить обработку очереди.

2. **Интеграция с API состояния** — предоставление API для проверки состояния очереди через CLI или веб-интерфейс.

3. **Приоритетные правила** — определение правил для автоматического назначения приоритетов на основе метаданных файлов.

4. **Лимиты очереди** — ограничение размера очереди и политики вытеснения для предотвращения перегрузки.

5. **Расширенная визуализация** — инструменты для визуализации состояния очереди и процесса обработки.