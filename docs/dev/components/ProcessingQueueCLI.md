# Processing Queue CLI Interface

This document describes the CLI interface for managing the processing queue in meet2obsidian.

## Overview

The Processing Queue CLI interface provides commands for viewing queue status, adding files to the queue, retrying failed files, and clearing completed files. It is implemented in the `process_command.py` module.

## Command Structure

```
meet2obsidian process [COMMAND] [OPTIONS]
```

Available commands:
- `status`: Show status of the processing queue
- `add`: Add a file to the processing queue
- `retry`: Retry failed files in the processing queue
- `clear`: Clear completed files from the processing queue

## Command Details

### Status Command

The `status` command displays the current status of the processing queue.

```
meet2obsidian process status [OPTIONS]
```

Options:
- `--detailed`, `-d`: Show detailed information about files in queue
- `--format`, `-f`: Output format (`table`, `text`, or `json`), default: `table`

Example output (table format):
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃     Processing Queue Status      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Status        │ Count │ Percentage │
├───────────────┼───────┼────────────┤
│ Pending       │ 3     │ 30.0%      │
│ Processing    │ 2     │ 20.0%      │
│ Completed     │ 4     │ 40.0%      │
│ Error         │ 1     │ 10.0%      │
│ Failed        │ 0     │ 0.0%       │
│ Total         │ 10    │ 100.0%     │
└───────────────┴───────┴────────────┘
```

With `--detailed` option, additional tables are displayed showing the specific files in each state.

### Add Command

The `add` command adds a file to the processing queue.

```
meet2obsidian process add FILE_PATH [OPTIONS]
```

Arguments:
- `FILE_PATH`: Path to the file to add to the queue (must exist)

Options:
- `--priority`, `-p`: Processing priority (higher number = higher priority), default: 0

Example:
```
meet2obsidian process add /path/to/video.mp4 --priority 5
```

### Retry Command

The `retry` command resets all files with errors for reprocessing.

```
meet2obsidian process retry
```

Example output:
```
✓ Reset 3 files for retry.
```

### Clear Command

The `clear` command removes all completed files from the queue.

```
meet2obsidian process clear
```

Example output:
```
✓ Cleared 4 completed files from the queue.
```

## Implementation Details

### Command Group Definition

The command group is defined in `process_command.py`:

```python
@click.group(name="process")
def process():
    """Manage the processing queue."""
    pass
```

### ApplicationManager Integration

The CLI commands interact with the ApplicationManager to perform queue management operations:

1. **Status Command**: Calls `app_manager.get_processing_queue_status()` to retrieve queue status
2. **Add Command**: Calls `app_manager._handle_new_file()` to add a file to the queue
3. **Retry Command**: Calls `app_manager.retry_failed_files()` to retry failed files
4. **Clear Command**: Calls `app_manager.clear_completed_files()` to clear completed files

### Output Formatting

The module includes helper functions for formatting output in different formats:

- `_print_queue_status_table()`: Formats queue status as a table using rich.table
- `_print_queue_status_text()`: Formats queue status as plain text
- `_print_detailed_file_tables()`: Displays tables of files in different states

### Error Handling

All commands include proper error handling:

- Check if the application is running before performing operations
- Handle errors from the ApplicationManager gracefully
- Provide meaningful error messages to the user

## Testing

The CLI commands are tested in `tests/unit/test_process_command.py` using the click.testing.CliRunner and unittest.mock.

Tests include:
- Testing command existence and registration
- Testing behavior when the application is not running
- Testing the status command with different formats
- Testing retry and clear commands with different scenarios

## Usage Examples

### Basic Workflow

```bash
# Start the service
meet2obsidian service start

# Check queue status
meet2obsidian process status

# Add a file to the queue
meet2obsidian process add /path/to/video.mp4

# Check status with details
meet2obsidian process status --detailed

# If there are files with errors, retry them
meet2obsidian process retry

# Once files are processed, clean up the queue
meet2obsidian process clear
```

### Troubleshooting

```bash
# Check if the service is running
meet2obsidian status

# Check queue status in JSON format for detailed analysis
meet2obsidian process status --format json

# Check logs for errors
meet2obsidian logs show --level error

# Retry failed files
meet2obsidian process retry
```

## Future Enhancements

Potential future enhancements for the processing queue CLI:

1. Add command to pause/resume processing
2. Add command to remove specific files from the queue
3. Add support for batch operations (multiple files at once)
4. Add interactive mode for queue management
5. Add support for showing processing progress in real-time