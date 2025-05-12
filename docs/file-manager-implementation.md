# File Manager Implementation

This document outlines the implementation of the FileManager class, which provides robust file operations with comprehensive error handling.

## Overview

The `FileManager` class provides a safe and reliable way to perform common file operations:

- File deletion (standard and secure)
- Directory operations (creation, deletion)
- File moving and copying
- Permission management
- Path accessibility verification
- Error handling and recovery

The implementation follows a defensive programming approach with extensive error handling, logging, and recovery mechanisms to ensure reliability in various scenarios.

## Core Features

### Safe File Operations

- **Error Handling**: All operations return success/error status with detailed error messages
- **Logging**: Comprehensive logging of all operations for troubleshooting
- **Recovery**: Automatic recovery from temporary errors
- **Cross-Device Operations**: Handles file operations across different devices/filesystems

### Security Features

- **Secure Deletion**: Multi-pass overwriting of files before deletion
- **Permission Management**: Fine-grained control of file permissions
- **Access Verification**: Path accessibility checking before operations

## API Reference

### Main Methods

```python
# File Operations
delete_file(file_path) -> (success, error)
secure_delete_file(file_path, passes=3) -> (success, error)
delete_directory(dir_path, recursive=False) -> (success, error)
move_file(source_path, target_path, overwrite=False, create_dirs=False, 
          max_retries=3, retry_delay=1.0, timeout=None) -> (success, error, new_path)
move_directory(source_dir, target_dir) -> (success, error, new_path)
copy_file(source_path, target_path, overwrite=False, create_dirs=False) -> (success, error)

# Permission Operations
check_permission(path, permission_type) -> bool
set_permissions(path, read=True, write=True, execute=False) -> (success, error)
check_path_accessible(path) -> (is_accessible, error)

# Error Handling
get_last_error() -> Exception
get_last_error_code() -> int
```

## Error Handling

The FileManager implements comprehensive error handling for various error scenarios:

| Error Type | Handling Strategy | Return Value |
|------------|-------------------|--------------|
| File not found | Report detailed error | (False, error_message) |
| Permission denied | Report error with permission details | (False, error_message) |
| Disk space issues | Report insufficient space error | (False, error_message) |
| File in use | Report file locked error | (False, error_message) |
| Cross-device move | Fall back to copy+delete | (True, None, new_path) |
| Temporary errors | Auto-retry with configurable attempts | (True/False, error_message) |
| Timeouts | Cancel operation after timeout | (False, timeout_message) |

## Usage Examples

### Basic File Operations

```python
# Initialize FileManager with logger
from meet2obsidian.utils.file_manager import FileManager
manager = FileManager(logger=logger)

# Delete a file
success, error = manager.delete_file('/path/to/file.txt')
if not success:
    logger.error(f"Failed to delete file: {error}")

# Copy a file
success, error = manager.copy_file('/path/to/source.txt', '/path/to/destination.txt')
if success:
    logger.info("File copied successfully")
```

### Advanced Operations

```python
# Securely delete a file with 7 passes
success, error = manager.secure_delete_file('/path/to/sensitive.txt', passes=7)

# Move a file with automatic directory creation
success, error, new_path = manager.move_file(
    '/path/to/source.txt', 
    '/path/to/nonexistent/dir/file.txt', 
    create_dirs=True
)

# Set read-only permissions
success, error = manager.set_permissions('/path/to/file.txt', read=True, write=False, execute=False)
```

## Platform Compatibility

The FileManager is designed to work across different platforms with special handling for platform-specific issues:

- **Windows**: Handles file locking issues and permission differences
- **macOS**: Proper handling of resource forks and extended attributes
- **Linux**: Full support for POSIX permissions

## Test Coverage

The FileManager implementation is backed by comprehensive test coverage:

- **Unit Tests**: Tests for individual operations and error scenarios
- **Integration Tests**: Tests for complex workflows and system integration
- **Error Simulation**: Tests for various error conditions and recovery
- **Permission Tests**: Tests for permission operations on different file types

## Implementation Notes

1. All error messages are standardized and include detailed information
2. Operations are designed to be atomic where possible
3. Recovery mechanisms are implemented for common transient errors
4. Timeout handling prevents operations from hanging indefinitely
5. Logging provides detailed information for troubleshooting

## Future Enhancements

- File ownership manipulation
- Extended attribute management
- Checksumming and verification
- File locking mechanisms
- Asynchronous operations