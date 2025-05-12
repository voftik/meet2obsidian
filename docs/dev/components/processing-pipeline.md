# Processing Pipeline Component

## Overview

The ProcessingPipeline component implements EPIC 27: Integration of File Processing Components. It acts as the central coordination system that connects the FileWatcher, ProcessingQueue, AudioExtractor, and CacheManager components into a cohesive system.

## Import Definitions

```python
from meet2obsidian.utils.logging import get_logger, setup_component_logging
from meet2obsidian.monitor import FileMonitor
from meet2obsidian.processing.queue import ProcessingQueue
from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.audio.extractor import AudioExtractor
from meet2obsidian.cache import CacheManager
```

## Component Dependencies

The ProcessingPipeline integrates several existing components:

1. **FileMonitor** (from `meet2obsidian.monitor`):
   - Responsible for monitoring directories for new files
   - Provides file validation and stabilization detection
   - Triggers callbacks when new files are detected

2. **ProcessingQueue** (from `meet2obsidian.processing.queue`):
   - Manages the queue of files to be processed
   - Handles file status tracking (pending, processing, completed, error, failed)
   - Provides thread-safe operations for concurrent processing

3. **FileProcessor** (from `meet2obsidian.processing.processor`):
   - Processes files in a thread-safe manner
   - Executes processing logic provided by the pipeline
   - Manages processing state and error handling

4. **AudioExtractor** (from `meet2obsidian.audio.extractor`):
   - Extracts audio from video files
   - Supports various formats and quality profiles
   - Provides validation and error handling

5. **CacheManager** (from `meet2obsidian.cache`):
   - Caches processing results to avoid redundant processing
   - Provides thread-safe cache operations
   - Supports cache invalidation and expiration

## Key Classes and Functions

### ProcessingPipeline Class

```python
class ProcessingPipeline:
    """
    Connects file monitoring, processing queue, and audio extraction components.
    
    This class integrates the various components of the meet2obsidian system:
    - FileMonitor: Detects new video files in a directory
    - ProcessingQueue: Manages the queue of files to be processed
    - AudioExtractor: Extracts audio from video files
    - CacheManager: Handles caching of results
    """
```

#### Constructor Parameters

- `watch_directory`: Directory to monitor for new video files
- `output_directory`: Directory to store processed output files
- `cache_directory`: Directory for caching results (optional)
- `audio_format`: Format for extracted audio files
- `audio_quality`: Quality profile for audio extraction
- `file_patterns`: Patterns of video files to monitor
- `max_concurrent`: Maximum number of concurrent processing tasks
- `min_file_age_seconds`: Minimum age of file before processing
- `log_dir`: Directory to store log files
- `log_level`: Logging level
- `logger`: Optional logger instance

#### Key Methods

- `start()`: Start the processing pipeline
- `stop()`: Stop the processing pipeline
- `get_status()`: Get status information about the processing pipeline
- `retry_errors()`: Retry files that encountered errors
- `clear_completed()`: Clear completed files from the queue

## Configuration

The ProcessingPipeline can be configured through the YAML configuration file:

```yaml
paths:
  video_directory: "/path/to/videos"
  audio_directory: "/path/to/audio"
  cache_directory: "/path/to/cache"
  log_directory: "/path/to/logs"

processing:
  file_patterns: ["*.mp4", "*.mov", "*.webm", "*.mkv"]
  min_file_age_seconds: 5
  max_concurrent_files: 3

audio:
  format: "m4a"
  quality: "medium"

system:
  loglevel: "info"
  logging:
    console: true
    file: true
```

## Integration with ApplicationManager

The ProcessingPipeline is integrated with the ApplicationManager class. The ApplicationManager:

1. Creates the ProcessingPipeline during component initialization
2. Starts and stops the pipeline as part of application lifecycle management
3. Includes pipeline status in application status reports
4. Forwards configuration to the pipeline

## Usage Example

```python
# Create and configure the pipeline
pipeline = ProcessingPipeline(
    watch_directory="/path/to/videos",
    output_directory="/path/to/audio",
    cache_directory="/path/to/cache",
    audio_format="m4a",
    audio_quality="medium",
    file_patterns=["*.mp4", "*.mov"],
    max_concurrent=3,
    min_file_age_seconds=5,
    log_dir="/path/to/logs",
    log_level="info"
)

# Start the pipeline
pipeline.start()

# Get status information
status = pipeline.get_status()

# Process a specific file (useful for testing)
test_file = "/path/to/videos/test.mp4"
metadata = {
    "source_path": test_file,
    "output_format": "m4a",
    "quality": "medium",
    "output_directory": "/path/to/audio"
}
pipeline._on_new_file(test_file)

# Retry any files that encountered errors
retry_count = pipeline.retry_errors()

# Stop the pipeline
pipeline.stop()
```

## Threading and Concurrency

The ProcessingPipeline uses multiple threads for concurrent operations:

1. FileMonitor runs in its own thread for watching files
2. ProcessingQueue runs its own worker threads for processing files
3. The number of concurrent processing threads is controlled by `max_concurrent`

All components implement thread-safe operations with appropriate locking.