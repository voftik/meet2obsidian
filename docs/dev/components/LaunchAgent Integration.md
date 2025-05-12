# LaunchAgent Integration

## Overview

The LaunchAgent Integration is a key component in meet2obsidian that enables macOS users to configure the application to automatically start when the user logs in. It leverages macOS's native LaunchAgent system to ensure the application can run as a background service with proper startup and shutdown handling.

## Key Features

- Generation of LaunchAgent plist files with customizable options
- Installation and uninstallation of LaunchAgents
- Comprehensive status checking and reporting
- Integration with ApplicationManager for unified service management
- Enhanced CLI commands for autostart configuration

## Components

### `LaunchAgentManager` Class

Located in `meet2obsidian/launchagent.py`, this class is responsible for all LaunchAgent-related operations.

```python
class LaunchAgentManager:
    """
    Manages LaunchAgent creation, installation, and status for meet2obsidian.
    
    This class provides methods to:
    - Generate plist files for LaunchAgents
    - Install (load) LaunchAgents
    - Uninstall (unload) LaunchAgents
    - Check LaunchAgent status
    """
```

#### Key Methods

- **`generate_plist_file(working_directory=None, env_vars=None)`**: Creates a properly formatted plist file with customizable parameters
- **`install()`**: Installs (loads) the LaunchAgent into the system
- **`uninstall()`**: Uninstalls (unloads) the LaunchAgent from the system
- **`get_status()`**: Checks if the LaunchAgent is currently active
- **`get_full_status()`**: Gets comprehensive information about the LaunchAgent
- **`plist_exists()`**: Checks if the plist file exists

### CLI Integration

The LaunchAgent functionality is exposed through the CLI via the `autostart` command in `cli_commands/service_command.py`:

```
meet2obsidian service autostart --enable       # Enable autostart
meet2obsidian service autostart --disable      # Disable autostart
meet2obsidian service autostart --status       # Show autostart status
```

Additional options:
- `--keep-alive/--no-keep-alive`: Control whether the service restarts if it crashes
- `--run-at-load/--no-run-at-load`: Control whether the service starts when the LaunchAgent is loaded

## Default Configuration

By default, the LaunchAgent is configured with the following settings:

- **Label**: `com.user.meet2obsidian`
- **Program**: Path to the user's Python executable
- **Arguments**: `["-m", "meet2obsidian", "service", "start"]`
- **Run at Load**: `true`
- **Keep Alive**: `true`
- **Standard Output Path**: `~/Library/Logs/meet2obsidian/stdout.log`
- **Standard Error Path**: `~/Library/Logs/meet2obsidian/stderr.log`

## Usage in ApplicationManager

The `ApplicationManager` class in `core.py` integrates with the LaunchAgent functionality:

```python
def setup_autostart(self, enable=True, keep_alive=True, run_at_load=True) -> bool:
    """
    Configure autostart via LaunchAgent.
    
    Args:
        enable: True to enable autostart, False to disable
        keep_alive: Whether the process should be kept alive if it exits
        run_at_load: Whether the process should run when the agent is loaded
        
    Returns:
        bool: True if setup completed successfully, False otherwise
    """
    # Implementation details...
```

This provides a high-level interface for other components to manage autostart functionality without needing to directly interact with the LaunchAgent system.

## Cross-Platform Considerations

While LaunchAgents are specific to macOS, the design includes fallbacks for other platforms:

- The code checks `sys.platform` to determine the operating system
- On non-macOS platforms, an appropriate warning is logged
- The `setup_autostart_non_macos()` method provides a hook for future platform-specific implementations

## Configuration Integration

The LaunchAgent settings can be customized through the application's configuration system:

```python
"system": {
    "autostart": {
        "enabled": True,
        "keep_alive": True,
        "run_at_load": True,
        "environment_variables": {}  # Custom environment variables
    },
    # Other system settings...
}
```

## Testing

Comprehensive tests for the LaunchAgent functionality include:

- Unit tests for plist generation (`tests/unit/test_launchagent.py`)
- Unit tests for installation/uninstallation
- Unit tests for status checking
- Integration tests with the ApplicationManager (`tests/unit/test_application_manager_launchagent.py`)
- System integration tests (`tests/integration/test_launchagent_integration.py`)

## Implementation Notes

- The LaunchAgent implementation follows macOS best practices for service management
- The plist file generation uses correct XML formatting with proper escaping
- Error handling is thorough with descriptive error messages
- Status checking handles different macOS versions (newer versions return JSON, older versions return plain text)