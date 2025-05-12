# Application Manager

## Overview

The Application Manager is a central component in meet2obsidian responsible for controlling the application's lifecycle, including starting and stopping services, monitoring application status, handling signals, and managing integration between various components.

## Key Features

- Application lifecycle management (start/stop/restart)
- Signal handling for graceful termination
- Component initialization and shutdown
- Status tracking and reporting
- Process monitoring
- Integration with LaunchAgents for autostart functionality
- File processing job management
- Comprehensive error handling

## Components

### `ApplicationManager` Class

Located in `meet2obsidian/core.py`, this class is the main controller for the application:

```python
class ApplicationManager:
    """
    Management of the meet2obsidian application state.
    
    This class is responsible for starting and stopping the main application processes,
    as well as tracking its state and managing autostart features.
    """
```

#### Key Methods

- **`start()`**: Starts the application and its components
- **`stop(force=False)`**: Stops the application and its components
- **`restart(force=False)`**: Restarts the application
- **`get_status()`**: Gets comprehensive status information
- **`is_running()`**: Checks if the application is currently running
- **`register_signal_handlers()`**: Sets up signal handlers for graceful termination
- **`initialize_components()`**: Initializes all application components
- **`shutdown_components()`**: Gracefully shuts down all components
- **`setup_autostart(enable=True, keep_alive=True, run_at_load=True)`**: Configures application autostart
- **`check_autostart_status()`**: Checks the current autostart configuration
- **`add_job(job_id, job_info)`**: Adds a new processing job
- **`complete_job(job_id, success=True, error=None)`**: Marks a job as completed

## Usage in CLI Commands

The ApplicationManager is used extensively in the CLI commands:

```python
# Example from service_command.py
@service.command()
@click.pass_context
def start(ctx, autostart):
    """Start the meet2obsidian service."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Start the application
    with console.status("[bold cyan]Starting service...[/bold cyan]", spinner="dots") as status:
        success = app_manager.start()
        # ...
```

## Process Management

### PID File

The ApplicationManager uses a PID file to track the running instance:

- Default location: `~/Library/Application Support/meet2obsidian/meet2obsidian.pid`
- Contains the process ID of the running application
- Used to check if the application is already running
- Automatically created on start and removed on stop
- Prevents multiple instances from running simultaneously

### Signal Handling

The ApplicationManager sets up signal handlers for graceful termination:

```python
def register_signal_handlers(self) -> bool:
    """Register signal handlers for graceful termination."""
    try:
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        self.logger.debug("Signal handlers registered successfully")
        return True
    except Exception as e:
        self.logger.error(f"Error registering signal handlers: {str(e)}")
        return False
```

When a termination signal is received, the application shuts down gracefully.

## Component Management

The ApplicationManager initializes and shuts down all other components:

- Configuration Manager
- File Monitor
- (Future components like Audio Processor, Transcription Service, etc.)

```python
def initialize_components(self) -> bool:
    """Initialize application components."""
    try:
        # Load configuration
        from meet2obsidian.config import ConfigManager
        self.config_manager = ConfigManager()
        
        # Initialize File Monitor if directory is configured
        video_dir = self.config_manager.get_value("paths.video_directory", default="")
        if video_dir:
            from meet2obsidian.monitor import FileMonitor
            self.file_monitor = FileMonitor(...)
            # ...
        
        # Initialize other components...
        
        return True
    except Exception as e:
        self.logger.error(f"Error initializing components: {str(e)}")
        return False
```

## LaunchAgent Integration

The ApplicationManager integrates with LaunchAgents for macOS autostart functionality:

```python
def setup_autostart(self, enable=True, keep_alive=True, run_at_load=True) -> bool:
    """Configure autostart via LaunchAgent."""
    # Platform-specific check
    if sys.platform != 'darwin':
        return self.setup_autostart_non_macos(enable)
        
    # LaunchAgent configuration
    try:
        from meet2obsidian.launchagent import LaunchAgentManager
        manager = LaunchAgentManager(...)
        
        if enable:
            # Install LaunchAgent
            # ...
        else:
            # Uninstall LaunchAgent
            # ...
    except Exception as e:
        self.logger.warning(f"Using legacy autostart setup: {str(e)}")
        return self._setup_autostart_legacy(enable)
```

## Job Management

The ApplicationManager maintains a list of active jobs and their status:

```python
def add_job(self, job_id: str, job_info: Dict[str, Any]) -> None:
    """Add a new job to the active jobs list."""
    job_entry = {"id": job_id, "info": job_info, "start_time": datetime.datetime.now().isoformat()}
    self._active_jobs.append(job_entry)
    self._pending_files += 1
    self.logger.debug(f"Added job: {job_id}")

def complete_job(self, job_id: str, success: bool = True, error: str = None) -> None:
    """Mark a job as completed."""
    # Remove job from active jobs
    for i, job in enumerate(self._active_jobs):
        if job["id"] == job_id:
            self._active_jobs.pop(i)
            break
    
    # Update job status
    # ...
```

## Testing

The ApplicationManager is thoroughly tested:

- Unit tests for basic functionality (`tests/unit/test_application_manager.py`)
- Specific tests for LaunchAgent integration (`tests/unit/test_application_manager_launchagent.py`)
- Mocked unit tests to verify component interactions (`tests/unit/test_application_manager_mock.py`)
- Integration tests for system interactions (`tests/integration/test_application_manager_integration.py`)

## Future Enhancements

Potential future enhancements for the ApplicationManager include:

- Support for more sophisticated component dependency management
- Enhanced job scheduling and prioritization
- Resource usage monitoring and throttling
- Improved error recovery mechanisms
- Support for clustered operation in multi-machine environments