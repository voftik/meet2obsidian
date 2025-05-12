# File Monitor

## Overview

The File Monitor is a core component of meet2obsidian responsible for detecting new video files in a configured directory. It enables automated processing by monitoring specified directories for matching file patterns and triggering callbacks when new files are found.

## Key Features

- Directory monitoring with customizable file patterns
- Configurable polling interval for resource efficiency
- Multi-threaded implementation for responsive monitoring
- Robust error handling and recovery
- File detection callbacks for pipeline integration
- Graceful start/stop functionality
- Detailed status reporting

## Components

### `FileMonitor` Class

Located in `meet2obsidian/monitor.py`, this class is responsible for monitoring directories for new files:

```python
class FileMonitor:
    """
    Monitors a directory for new files and starts processing when they appear.
    Uses a separate thread to watch for file changes.
    """
```

#### Key Methods

- **`start()`**: Starts the file monitoring thread
- **`stop()`**: Stops the file monitoring thread
- **`register_file_callback(callback)`**: Registers a callback function to be called when a new file is found
- **`get_status()`**: Gets status information about the file monitor
- **`_scan_directory()`**: Internal method that performs the actual directory scanning
- **`_monitor_loop()`**: Internal method that runs the monitoring loop in a separate thread

### Integration with ApplicationManager

The `ApplicationManager` class in `core.py` initializes and manages the FileMonitor:

```python
def initialize_components(self) -> bool:
    """Initialize application components."""
    try:
        # Configuration setup...
        
        # Initialize FileMonitor if video directory is configured
        video_dir = self.config_manager.get_value("paths.video_directory", default="")
        if video_dir:
            self.logger.info(f"Video directory monitoring configured: {video_dir}")
            
            # Create and configure FileMonitor
            self.file_monitor = FileMonitor(
                directory=os.path.expanduser(video_dir),
                file_patterns=patterns,
                poll_interval=poll_interval,
                logger=self.logger
            )
            
            # Register callback function
            self.file_monitor.register_file_callback(self._handle_new_file)
            
            # Start monitoring
            if not self.file_monitor.start():
                self.logger.error("Error starting file monitoring")
                return False
                
            self.logger.info(f"File monitoring started for {video_dir}")
            
        # ...
    except Exception as e:
        self.logger.error(f"Error initializing components: {str(e)}")
        return False
```

## Configuration

The FileMonitor can be configured through the application's configuration system:

```python
"processing": {
    "poll_interval": 60,  # Directory polling interval in seconds
    "file_patterns": ["*.mp4", "*.mov", "*.webm", "*.mkv"]  # File patterns to monitor
}
```

## File Processing Pipeline

When a new file is detected, the FileMonitor triggers a callback that initiates the processing pipeline:

1. The `_handle_new_file()` method in ApplicationManager is called with the file path
2. A job is created for the file and added to the active jobs list
3. The file is processed according to the application's pipeline (in future implementations)

```python
def _handle_new_file(self, file_path: str) -> None:
    """Handle detection of a new file by the file monitor."""
    try:
        self.logger.info(f"Processing new file: {os.path.basename(file_path)}")
        
        # Create a job ID based on file name and timestamp
        job_id = f"job_{os.path.basename(file_path)}_{int(time.time())}"
        
        # Add job to active jobs
        job_info = {
            "file": file_path,
            "stage": "detected",
            "progress": "0%"
        }
        self.add_job(job_id, job_info)
        
        # In future implementations, this will trigger the full processing pipeline
        self.logger.info(f"Created job {job_id} for file: {file_path}")
        
    except Exception as e:
        self.logger.error(f"Error handling new file {file_path}: {str(e)}")
```

## Implementation Details

### Threading Model

The FileMonitor uses a dedicated background thread for monitoring:

- The thread is created as a daemon thread, so it doesn't prevent application exit
- The thread continuously polls the directory at the configured interval
- A threading.Event object is used to signal the thread to stop
- The thread gracefully exits when stop() is called

### File Detection Algorithm

The file detection algorithm works as follows:

1. Scan the directory for all files matching the specified patterns
2. Compare the found files with the previously observed files
3. Identify new files (those not in the observed files set)
4. Update the observed files set to include all current files
5. Process each new file by:
   - Adding it to the processing queue
   - Logging its discovery
   - Calling the registered callback function

### Error Handling

The FileMonitor includes robust error handling:

- Errors during directory scanning are logged but don't crash the monitoring thread
- Errors in the callback function are caught and logged without disrupting monitoring
- If repeated errors occur, a small delay is introduced to prevent tight error loops
- The monitoring thread can recover from transient errors

## Future Enhancements

Potential future enhancements for the FileMonitor include:

- Using filesystem event notifications (watchdog) instead of polling for improved efficiency
- Supporting multiple directories with different file patterns
- Adding file exclusion patterns
- Implementing file modification detection (not just new files)
- Adding file metadata analysis before processing