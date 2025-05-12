# FileMonitor Component

The FileMonitor component is responsible for detecting new video files in a specified directory and triggering their processing. It's a crucial part of the automated workflow in meet2obsidian.

## Overview

FileMonitor uses a thread-based approach to scan directories for new files matching specific patterns. It ensures that files are only processed when they have finished being copied and are stable. This is particularly important for video files, which may be large and take time to copy.

## Key Features

- Monitors directories for new files matching specified patterns
- Detects when files have completed copying using a stability period
- Filters files based on extension patterns
- Provides callbacks when new files are detected
- Offers safe thread management (start/stop/status)
- Maintains queues for file processing

## Class Structure

```python
class FileMonitor:
    """
    Monitors a directory for new files and starts processing when they appear.
    Uses a separate thread to watch for file changes.
    """

    def __init__(self, directory: str, file_patterns: Optional[List[str]] = None,
                 poll_interval: int = 60, logger=None):
        """Initialize a file monitor."""
        # ...

    def start(self) -> bool:
        """Start the file monitoring thread."""
        # ...

    def stop(self) -> bool:
        """Stop the file monitoring thread."""
        # ...
    
    def register_file_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback function to be called when a new file is found."""
        # ...
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the file monitor."""
        # ...
    
    def _scan_directory(self) -> List[str]:
        """
        Scan the directory for files matching patterns.
        
        Files are only considered for processing if they meet the following criteria:
        1. They match one of the file patterns
        2. They have not been observed before
        3. They have not been modified for a certain period (to avoid processing files still being written)
        """
        # ...

    def _monitor_loop(self) -> None:
        """Main loop for monitoring directory for new files."""
        # ...
```

## Usage Examples

### Basic Usage

```python
from meet2obsidian.monitor import FileMonitor
from meet2obsidian.utils.logging import get_logger

# Create a logger
logger = get_logger("example")

# Create a file monitor
monitor = FileMonitor(
    directory="/path/to/videos",
    file_patterns=["*.mp4", "*.mov"],
    poll_interval=30,  # Check every 30 seconds
    logger=logger
)

# Define a callback function
def process_file(file_path: str) -> None:
    logger.info(f"Processing file: {file_path}")
    # ... process the file ...

# Register the callback
monitor.register_file_callback(process_file)

# Start monitoring
monitor.start()

# ... application continues ...

# When done, stop monitoring
monitor.stop()
```

### Integration with ApplicationManager

```python
class VideoProcessor:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.file_monitor = None
        
    def initialize(self):
        # Create and configure the file monitor
        watch_dir = self.config.get("watch_directory", "~/Videos")
        self.file_monitor = FileMonitor(
            directory=watch_dir,
            file_patterns=["*.mp4", "*.mov", "*.webm"],
            poll_interval=self.config.get("poll_interval", 60),
            logger=self.logger
        )
        
        # Register callback
        self.file_monitor.register_file_callback(self.process_video)
        
        # Start monitoring
        return self.file_monitor.start()
        
    def shutdown(self):
        # Stop monitoring when application shuts down
        if self.file_monitor:
            return self.file_monitor.stop()
        return True
        
    def process_video(self, file_path):
        self.logger.info(f"New video detected: {file_path}")
        # ... process the video ...
```

## File Stability Detection

A key feature of FileMonitor is its ability to detect when a file has finished being copied and is stable enough for processing. This is done by:

1. Checking file modification time (must be older than a minimum age)
2. Ensuring the file size is non-zero
3. Tracking observed files across scans

```python
# Set minimum age for a file to be considered stable (seconds)
min_file_age_seconds = 5  # Default to 5 seconds

# Get current time for age calculations
current_time = time.time()

# Make sure the file is stable (hasn't been modified recently)
if file_age >= min_file_age_seconds:
    # Get file size
    file_size = os.path.getsize(file_path)

    # Skip empty files
    if file_size == 0:
        self.logger.warning(f"Skipping empty file: {os.path.basename(file_path)}")
        continue

    # Add to the list of files ready for processing
    new_files.append(file_path)
```

## Thread Management

FileMonitor uses a dedicated thread for monitoring. The thread management follows best practices:

1. Uses daemon threads for automatic cleanup if the main thread exits
2. Uses thread events for signaling thread termination
3. Includes timeout when joining threads to prevent hangs
4. Gracefully handles start/stop errors

```python
# Start monitoring thread
self._stop_event.clear()
self._monitor_thread = threading.Thread(
    target=self._monitor_loop,
    name="FileMonitorThread",
    daemon=True
)
self._monitor_thread.start()

# When stopping:
# Signal thread to stop
self._stop_event.set()

# Wait for thread to finish (with timeout)
if self._monitor_thread and self._monitor_thread.is_alive():
    self._monitor_thread.join(timeout=5)
    if self._monitor_thread.is_alive():
        self.logger.warning("File monitor thread did not stop gracefully")
```

## Error Handling

FileMonitor implements robust error handling:

1. Catches and logs exceptions during scanning
2. Handles file-level errors without failing the entire scan
3. Implements a throttled retry mechanism for monitoring loop errors
4. Safely handles callback exceptions

```python
# In the monitoring loop:
try:
    # Scan for new files
    new_files = self._scan_directory()
    
    # Process new files...
except Exception as e:
    self.logger.error(f"Error in monitoring loop: {str(e)}")
    # Sleep a bit before retrying to avoid tight loops in case of repeated errors
    time.sleep(5)

# For callbacks:
if self._file_callback:
    try:
        self._file_callback(file_path)
    except Exception as e:
        self.logger.error(f"Error in file callback: {str(e)}")
```

## Testing

FileMonitor has comprehensive unit and integration tests:

- `tests/unit/test_file_monitor.py`: Unit tests using mocks
- `tests/integration/test_file_monitor_integration.py`: Full integration tests
- `tests/integration/test_file_monitor_basic.py`: Simplified integration tests

See [FileMonitor Tests](../../tmp/epic17_file_monitor_tests_report.md) for more information on testing approaches.

## Performance Considerations

- File scanning uses `glob` which is efficient for directory traversal
- A polling approach is used (rather than event-based monitoring) for cross-platform compatibility
- The polling interval is configurable (minimum 5 seconds)
- Detected files are tracked in sets for efficient membership testing
- Files are cached in `observed_files` to prevent reprocessing

## Integration Points

- **ApplicationManager**: FileMonitor can be initialized and managed by the ApplicationManager
- **Callbacks**: FileMonitor calls registered callbacks when new files are detected
- **CLICommands**: FileMonitor can be controlled through CLI commands

## Future Enhancements

Potential future enhancements to consider:

1. Event-based file monitoring on platforms that support it
2. Extended pattern matching (regex, include/exclude patterns)
3. Enhanced file stability detection (content hash checks)
4. Recursive directory monitoring
5. Automatic retry for failed file processing