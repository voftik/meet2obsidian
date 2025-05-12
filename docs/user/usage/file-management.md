# File Management in Meet2Obsidian

Meet2Obsidian includes robust file management capabilities designed to safely handle source files, processed files, and temporary data. This guide explains how Meet2Obsidian manages files throughout the processing pipeline.

## Overview

The file management system in Meet2Obsidian is designed to:

- Safely handle source files (videos, audio)
- Securely delete sensitive data when appropriate
- Reliably move files between directories
- Handle errors gracefully
- Ensure sufficient disk space is available
- Create and manage temporary files

## Source File Handling

When Meet2Obsidian processes a source file (like a video recording), it follows these steps:

1. **File Detection**: The system detects the file in the monitored directory
2. **File Stability Checking**: The system waits until the file is fully copied and stable
3. **Processing Queue**: The file is added to the processing queue
4. **Processing**: When the file is processed, it's read safely in chunks
5. **Output Creation**: The processed output (audio file, transcript, notes) is created
6. **Source File Handling**: Depending on your configuration, the source file is:
   - Left in place
   - Moved to an archive directory
   - Deleted securely
   - Deleted normally

## Configuration

You can configure how Meet2Obsidian handles files by editing your configuration file:

```yaml
file_handling:
  # What to do with source files after processing
  # Options: keep, move, delete, secure_delete
  source_file_action: move
  
  # Where to move source files if source_file_action is "move"
  archive_directory: ~/Documents/MeetArchive
  
  # Number of passes for secure deletion
  secure_delete_passes: 3
  
  # Create backup copies of output files
  create_backups: true
  
  # Directory for temporary files
  temp_directory: ~/.meet2obsidian/temp
```

You can edit this configuration using the CLI:

```bash
# Set the source file action
meet2obsidian config set file_handling.source_file_action move

# Set the archive directory
meet2obsidian config set file_handling.archive_directory ~/Documents/MeetArchive
```

## Secure Deletion

If you choose the `secure_delete` option for source files, Meet2Obsidian will overwrite the file content multiple times before deleting it. This makes it much harder to recover the data using file recovery tools.

The secure deletion process:
1. Overwrites the file with all zeros
2. Overwrites the file with all ones
3. Overwrites the file with random data
4. Finally deletes the file

The number of passes can be configured with the `secure_delete_passes` option.

> **Note**: While secure deletion makes recovery difficult, it's not a guarantee, especially on SSD drives with wear leveling. For truly sensitive data, consider using full-disk encryption.

## Disk Space Management

Meet2Obsidian automatically checks for available disk space before processing files. If there isn't enough space, the operation will be paused, and a warning will be logged.

The system estimates the required space based on:
- The size of the source file
- The type of processing being performed
- Historical data from similar operations

## Temporary Files

During processing, Meet2Obsidian may create temporary files for intermediate results. These files are:
- Created in the configured temporary directory
- Given unique names to avoid conflicts
- Automatically cleaned up after processing completes or fails

You generally don't need to manage temporary files manually, but you can configure the location using the `temp_directory` setting.

## Error Handling

If an error occurs during file operations, Meet2Obsidian will:
1. Log detailed error information
2. Retry transient errors automatically (up to 3 times by default)
3. Keep source files intact if processing fails
4. Clean up any partial output or temporary files

Errors are reported in the application logs, which you can view with:

```bash
meet2obsidian logs show
```

## Cross-Device Operations

Meet2Obsidian handles moving files between different filesystems (like from an external drive to your main drive) automatically. When a cross-device move is detected, the system:
1. Copies the file to the destination
2. Verifies the copy was successful
3. Deletes the original file

This process is transparent to you and ensures files are handled correctly regardless of where they're stored.

## Best Practices

For best results with file management in Meet2Obsidian:

1. **Set up adequate space** for your archive directory
2. **Regularly check** the application logs for any file-related warnings
3. **Use the backup feature** for important files
4. **Consider your privacy needs** when choosing between regular and secure deletion
5. **Organize your directories** to keep source files separate from output files

## Related CLI Commands

The following CLI commands relate to file management:

```bash
# Process a specific file immediately
meet2obsidian process file /path/to/file.mp4

# Check the status of the processing queue
meet2obsidian process status

# View file-related errors
meet2obsidian logs show --level error --module file_manager
```

## Troubleshooting

If you encounter issues with file management:

1. **Check the logs** for detailed error messages
2. **Ensure you have write permissions** for all relevant directories
3. **Verify disk space** is sufficient
4. **Check file usage** to ensure files aren't locked by another application
5. **Reset the processing queue** if it gets stuck: `meet2obsidian process reset`

For persistent issues, please refer to the troubleshooting guide or contact support.