# LaunchAgent Component

The LaunchAgent component enables meet2obsidian to start automatically when a user logs in on macOS systems. It provides a high-level interface for creating, installing, and managing LaunchAgents through the macOS launchd service management system.

## Overview

LaunchAgents are a macOS-specific feature that allows applications to be started automatically at login. The LaunchAgent component in meet2obsidian handles the creation and management of LaunchAgent configuration files (plist files) and interacts with the launchd system to control their behavior.

## Key Features

- Generates LaunchAgent plist files with customizable options
- Installs and uninstalls LaunchAgents
- Checks LaunchAgent status (installed, enabled, running)
- Retrieves detailed LaunchAgent information
- Provides a high-level API for autostart management

## Class Structure

```python
class LaunchAgentManager:
    """
    Manages LaunchAgent configuration for automatic startup on macOS.
    
    This class handles the creation, installation, and management of LaunchAgents
    through the macOS launchd service management system.
    """
    
    def __init__(self, label: str, executable: str, arguments: Optional[List[str]] = None, 
                logger=None):
        """Initialize a LaunchAgent manager."""
        # ...
        
    def install(self, keep_alive=True, run_at_load=True, working_directory=None,
               environment_vars=None) -> bool:
        """Install the LaunchAgent."""
        # ...
        
    def uninstall(self) -> bool:
        """Uninstall the LaunchAgent."""
        # ...
        
    def get_status(self) -> Dict[str, bool]:
        """
        Get basic status information about the LaunchAgent.
        
        Returns:
            dict: Dictionary with installed, enabled, and running status
        """
        # ...
        
    def get_full_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status information about the LaunchAgent.
        
        Returns:
            dict: Dictionary with basic status, detailed status, and plist content
        """
        # ...
        
    def _generate_plist_content(self, keep_alive=True, run_at_load=True, 
                               working_directory=None, environment_vars=None) -> str:
        """Generate the XML content for the LaunchAgent plist file."""
        # ...
        
    def _load_launchagent(self) -> bool:
        """Load the LaunchAgent using launchctl."""
        # ...
        
    def _unload_launchagent(self) -> bool:
        """Unload the LaunchAgent using launchctl."""
        # ...
        
    def _get_launchctl_status(self) -> Optional[Dict[str, str]]:
        """Get detailed status information from launchctl."""
        # ...
```

## Usage Examples

### Basic Usage

```python
from meet2obsidian.launchagent import LaunchAgentManager
from meet2obsidian.utils.logging import get_logger

# Create a logger
logger = get_logger("launchagent_example")

# Create a LaunchAgent manager
manager = LaunchAgentManager(
    label="com.user.meet2obsidian",
    executable="/usr/bin/python3",
    arguments=["-m", "meet2obsidian", "service", "start"],
    logger=logger
)

# Install the LaunchAgent
result = manager.install(
    keep_alive=True,
    run_at_load=True,
    working_directory="/Users/username/Documents/meet2obsidian"
)

if result:
    print("LaunchAgent installed successfully")
else:
    print("Failed to install LaunchAgent")

# Check status
status = manager.get_status()
print(f"LaunchAgent status: {status}")

# Get detailed status
full_status = manager.get_full_status()
print(f"LaunchAgent detailed status: {full_status}")

# Uninstall when no longer needed
manager.uninstall()
```

### Integration with ApplicationManager

```python
def enable_autostart(self, working_directory=None):
    """
    Enable automatic startup of the application.
    
    Args:
        working_directory (str): Optional working directory for the process
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current executable path
        executable = sys.executable
        
        # Create LaunchAgent manager
        manager = LaunchAgentManager(
            label=self.config.get('autostart.label', 'com.user.meet2obsidian'),
            executable=executable,
            arguments=['--color=always', '-m', 'meet2obsidian', 'service', 'start'],
            logger=self.logger
        )
        
        # Install LaunchAgent
        result = manager.install(
            keep_alive=True,
            run_at_load=True,
            working_directory=working_directory or os.getcwd()
        )
        
        if result:
            self.logger.info("Autostart enabled successfully")
            return True
        else:
            self.logger.error("Failed to enable autostart")
            return False
    
    except Exception as e:
        self.logger.error(f"Error enabling autostart: {str(e)}")
        return False
```

## LaunchAgent Plist Generation

LaunchAgents are configured through plist (property list) files. The `_generate_plist_content` method creates these files with configurable options:

```python
def _generate_plist_content(self, keep_alive=True, run_at_load=True, working_directory=None,
                           environment_vars=None):
    """
    Generate the XML content for the LaunchAgent plist file.
    
    Args:
        keep_alive (bool): Whether to restart the process if it exits
        run_at_load (bool): Whether to start the process when LaunchAgent is loaded
        working_directory (str): Optional working directory for the process
        environment_vars (dict): Optional environment variables
        
    Returns:
        str: XML content for the plist file
    """
    # Create basic plist structure
    plist_dict = {
        'Label': self.label,
        'ProgramArguments': self.program_arguments,
        'KeepAlive': keep_alive,
        'RunAtLoad': run_at_load
    }
    
    # Add optional parameters if provided
    if working_directory:
        plist_dict['WorkingDirectory'] = working_directory
    
    if environment_vars:
        plist_dict['EnvironmentVariables'] = environment_vars
    
    # Convert to XML
    return plistlib.dumps(plist_dict).decode('utf-8')
```

## Status Checking

The LaunchAgent component provides detailed status information:

```python
def get_full_status(self):
    """
    Get comprehensive status information about the LaunchAgent.
    
    Returns:
        dict: Dictionary with basic status, detailed status, and plist content
    """
    result = {
        'basic': self.get_status(),
        'details': {},
        'plist': {},
        'file_path': self.plist_path
    }
    
    # If installed, get detailed status and plist content
    if result['basic']['installed']:
        # Get detailed status from launchctl
        launchctl_status = self._get_launchctl_status()
        if launchctl_status:
            result['details'] = launchctl_status
        
        # Get plist content
        try:
            with open(self.plist_path, 'r') as f:
                plist_content = f.read()
                plist_dict = plistlib.loads(plist_content.encode('utf-8'))
                result['plist'] = plist_dict
        except Exception as e:
            self.logger.warning(f"Error reading plist file: {str(e)}")
    
    return result
```

## macOS Version Compatibility

The component handles differences in launchctl output format across macOS versions:

```python
def _parse_launchctl_list_output(self, output):
    """
    Parse the output of launchctl list command.
    
    Args:
        output (str): Output from launchctl list command
        
    Returns:
        dict: Dictionary with parsed information or None if not found
    """
    # Different output formats for different macOS versions
    
    # Format 1: PID Status Label (older macOS)
    # Example: "12345 0 com.example.service"
    pid_status_pattern = r'^\s*(\d+|-)\s+(\d+|-)\s+(.*)$'
    
    # Format 2: JSON-style output (newer macOS)
    # Example: "{" label = com.example.service; pid = 12345; status = 0; }"
    json_style_pattern = r'{\s*"?label"?\s*=\s*([^;]+);\s*"?pid"?\s*=\s*([^;]+);\s*"?status"?\s*=\s*([^;]+);'
    
    # Try to match against different formats
    for line in output.splitlines():
        # Check if this line contains our label
        if self.label in line:
            # Try Format 1
            match = re.match(pid_status_pattern, line.strip())
            if match:
                pid, status, label = match.groups()
                if label.strip() == self.label:
                    return {
                        'pid': pid,
                        'status': status,
                        'label': label.strip()
                    }
            
            # Try Format 2
            match = re.search(json_style_pattern, line)
            if match:
                label, pid, status = match.groups()
                if label.strip().strip('"') == self.label:
                    return {
                        'pid': pid.strip(),
                        'status': status.strip(),
                        'label': label.strip().strip('"')
                    }
    
    return None
```

## Command-line Script

In addition to the Python API, the component includes a shell script for manual installation:

```bash
#!/bin/bash
# Script for setting up meet2obsidian autostart through LaunchAgent on macOS
# This script provides a manual alternative to using the CLI command:
# meet2obsidian service autostart --enable

# Default configuration
LABEL="com.user.meet2obsidian"
WORKING_DIRECTORY=""
KEEP_ALIVE=true
RUN_AT_LOAD=true

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-keep-alive)
            KEEP_ALIVE=false
            shift
            ;;
        --no-run-at-load)
            RUN_AT_LOAD=false
            shift
            ;;
        --label)
            LABEL="$2"
            shift
            shift
            ;;
        --working-dir)
            WORKING_DIRECTORY="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-keep-alive] [--no-run-at-load] [--label LABEL] [--working-dir DIRECTORY]"
            exit 1
            ;;
    esac
done

# ... rest of script ...
```

## Testing

LaunchAgent functionality has comprehensive unit and integration tests:

- `tests/unit/test_launchagent.py`: Unit tests using mocks
- `tests/integration/test_launchagent_integration.py`: Integration tests with the actual system

See [LaunchAgent Tests](../../tmp/epic15_launchagent_tests_report.md) for more information on testing approaches.

## Error Handling

LaunchAgent includes robust error handling:

1. Catches and logs exceptions during installation/uninstallation
2. Handles subprocess errors when interacting with launchctl
3. Gracefully handles missing or malformed plist files
4. Provides clear error messages for troubleshooting

```python
try:
    # Try to unload first (in case it's already loaded)
    if os.path.exists(self.plist_path):
        self._unload_launchagent()
        
    # Remove the plist file
    if os.path.exists(self.plist_path):
        os.remove(self.plist_path)
        self.logger.info(f"Removed LaunchAgent plist: {self.plist_path}")
    
    return True

except Exception as e:
    self.logger.error(f"Error uninstalling LaunchAgent: {str(e)}")
    return False
```

## Integration Points

- **ApplicationManager**: LaunchAgent can be managed through the ApplicationManager
- **CLI Commands**: LaunchAgent can be controlled through CLI commands
- **System Services**: LaunchAgent interacts with the launchd system service

## Platform Considerations

The LaunchAgent component is specifically designed for macOS systems. For cross-platform autostart functionality, additional implementations would be needed:

- Windows: Registry entries or Scheduled Tasks
- Linux: systemd user services, desktop entries, or init scripts

## Future Enhancements

Potential future enhancements to consider:

1. Support for additional LaunchAgent options (StartInterval, WatchPaths, etc.)
2. Migration to launchctl 2.0 interface for newer macOS versions
3. Extended error information for troubleshooting
4. Support for system-wide LaunchDaemons (requires admin privileges)
5. Cross-platform autostart implementations