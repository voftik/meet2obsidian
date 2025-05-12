# FileManager Component

The FileManager component provides a comprehensive solution for safe and reliable file operations in the Meet2Obsidian project. It includes functionality for secure file deletion, file movement, permission handling, and error recovery.

## Overview

The `FileManager` class is designed to handle all file operations in the application with a focus on safety, security, and detailed error reporting. It follows defensive programming principles to ensure that file operations are performed correctly and handles various error scenarios gracefully.

Key features:
- Safe file deletion with proper error handling
- Secure deletion with multi-pass overwriting for sensitive data
- Directory operations with recursive capabilities
- File and directory movement with cross-device support
- File permission checking and modification
- Path accessibility verification
- Comprehensive error handling with detailed reporting
- Disk space management
- Temporary file creation and handling
- Integration with other components through the `safe_process_file` method

## Implementation Details

The FileManager is implemented in the `meet2obsidian/utils/file_manager.py` file. All methods follow a consistent pattern:
- Return values are tuples containing success status, error messages, and additional data
- Every operation has proper error handling with detailed error messages
- Operations that could fail due to transient errors include retry mechanisms
- All file operations are logged with appropriate log levels

### Core Methods

The following core methods are available:

#### File Deletion

```python
def delete_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
    """Delete a file at the specified path."""
    
def secure_delete_file(self, file_path: str, passes: int = 3) -> Tuple[bool, Optional[str]]:
    """Securely delete a file by overwriting its content multiple times."""
    
def delete_directory(self, dir_path: str, recursive: bool = False) -> Tuple[bool, Optional[str]]:
    """Delete a directory, optionally with all its contents."""
```

#### File Movement

```python
def move_file(self, source_path: str, target_path: str, 
             overwrite: bool = False, create_dirs: bool = False,
             max_retries: int = 3, retry_delay: float = 1.0,
             timeout: float = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """Move a file to a new location."""
    
def move_directory(self, source_dir: str, target_dir: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Move a directory to a new location."""
    
def copy_file(self, source_path: str, target_path: str, 
             overwrite: bool = False, create_dirs: bool = False) -> Tuple[bool, Optional[str]]:
    """Copy a file to a new location."""
```

#### Permission Management

```python
def check_permission(self, path: str, permission_type: str) -> bool:
    """Check if a path has the specified permission (read, write, execute)."""
    
def set_permissions(self, path: str, read: bool = True, write: bool = True, 
                  execute: bool = False) -> Tuple[bool, Optional[str]]:
    """Set permissions on a file or directory."""
    
def check_path_accessible(self, path: str) -> Tuple[bool, Optional[str]]:
    """Check if a path is accessible (all parent directories are accessible)."""
```

#### Error Handling

```python
def get_last_error(self) -> Optional[Exception]:
    """Get the last error encountered."""
    
def get_last_error_code(self) -> Optional[int]:
    """Get the error code from the last error."""
```

### Extended Functionality

The FileManager includes extended functionality for disk space management, temporary file handling, and integration with other components:

#### Disk Space Management

```python
def get_disk_space(self, path: str) -> Tuple[bool, Optional[str], Optional[Dict[str, int]]]:
    """Get disk space information for the filesystem containing the specified path."""
    
def has_sufficient_space(self, path: str, required_bytes: int) -> Tuple[bool, Optional[str], bool]:
    """Check if there is sufficient disk space available for an operation."""
```

#### Directory and Temporary File Management

```python
def ensure_directory_exists(self, directory_path: str) -> Tuple[bool, Optional[str]]:
    """Ensure that a directory exists, creating it and any parent directories if necessary."""
    
def create_temp_file(self, prefix: str = "meet2obs_", suffix: str = "", 
                    content: Optional[bytes] = None, mode: str = "w+b",
                    dir: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """Create a temporary file with optional content."""
```

#### Component Integration

```python
def safe_process_file(self, source_path: str, target_path: str, 
                     processing_function: callable, 
                     buffer_size: int = 8192,
                     secure_delete: bool = False,
                     create_dirs: bool = True,
                     overwrite: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
    """Safely process a file by reading from source, applying a function, and writing to target."""
    
@staticmethod
def identity_function(data: bytes) -> bytes:
    """Identity function that returns input unchanged, for use with safe_process_file."""
```

## Error Handling

All methods in the FileManager include proper error handling for various scenarios:

- File not found errors
- Permission denied errors
- Directory not empty errors
- Cross-device link errors (when moving between filesystems)
- Insufficient disk space errors
- Timeout errors
- Transient errors with automatic retries

When an error occurs, the method returns a tuple with:
- `False` to indicate failure
- A detailed error message
- Additional data as needed (e.g., the output file path)

The FileManager also maintains internal state to track the last error and error code, which can be retrieved using `get_last_error()` and `get_last_error_code()`.

## Integration with Other Components

The FileManager is designed to integrate with other components like AudioExtractor, ProcessingQueue, and more. The `safe_process_file` method provides a simple interface for components to process files safely with proper error handling and resource cleanup.

Here's an example of how to use the FileManager with the AudioExtractor:

```python
def process_audio_file(audio_path, output_path):
    file_manager = FileManager()
    
    # Check disk space
    success, error, has_space = file_manager.has_sufficient_space(
        os.path.dirname(output_path), 
        os.path.getsize(audio_path) * 2  # Estimate needed space
    )
    
    if not success or not has_space:
        return False, f"Insufficient disk space: {error}"
    
    # Define processing function
    def extract_audio(data):
        # Audio extraction logic here
        return processed_data
    
    # Process the file
    return file_manager.safe_process_file(
        audio_path, 
        output_path,
        processing_function=extract_audio,
        secure_delete=False,  # Keep the original file
        create_dirs=True,     # Create output directories if needed
        overwrite=True        # Overwrite existing output file
    )
```

## Testing

The FileManager component is thoroughly tested with both unit and extended functionality tests:

- Tests for file deletion and secure deletion
- Tests for file and directory movement
- Tests for permission checking and modification
- Tests for error handling and recovery
- Tests for disk space management
- Tests for temporary file creation and handling
- Tests for safe file processing

## Example

An example application demonstrating FileManager usage is available in `/examples/file_manager_example.py`. This example shows how to:

1. Initialize the FileManager
2. Process audio files safely
3. Handle errors properly
4. Clean up resources

## Conclusion

The FileManager component provides a comprehensive and robust solution for file operations in the Meet2Obsidian project. Its defensive programming approach, thorough error handling, and integration capabilities make it a reliable foundation for all file-related operations in the application.