"""
Module for safe file management operations.

This module provides a FileManager class for handling file operations with proper
error handling, permission checking, and recovery mechanisms.
"""

import os
import shutil
import stat
import time
import logging
import errno
import tempfile
import uuid
import functools
from typing import Tuple, Optional, Any, Dict, Callable, TypeVar, cast

# Type variables for better type annotations
T = TypeVar('T')
R = TypeVar('R')


def handle_file_errors(operation_name: str = None):
    """
    Decorator to handle file operation errors consistently.
    
    Args:
        operation_name: Name of the operation being performed (optional)
        
    Returns:
        Decorated function with standardized error handling
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get operation name for error messages
            op_name = operation_name or func.__name__.replace('_', ' ')
            
            try:
                return func(self, *args, **kwargs)
            except OSError as e:
                self.last_error = e
                self.last_error_code = getattr(e, 'errno', None)
                error_message = f"Error during {op_name}: {str(e)}"
                self.logger.error(error_message)
                
                # Determine appropriate return value based on function's return type annotation
                return_type = func.__annotations__.get('return')
                if return_type and hasattr(return_type, '__origin__') and return_type.__origin__ is tuple:
                    # For tuple returns with 3 items (success, error_msg, extra_data)
                    if len(return_type.__args__) == 3:
                        return False, error_message, None
                    # For tuple returns with 2 items (success, error_msg)
                    else:
                        return False, error_message
                # Default return for unspecified return types
                return False, error_message
            except Exception as e:
                self.last_error = e
                self.last_error_code = None
                error_message = f"Unexpected error during {op_name}: {str(e)}"
                self.logger.error(error_message)
                
                # Determine appropriate return value
                return_type = func.__annotations__.get('return')
                if return_type and hasattr(return_type, '__origin__') and return_type.__origin__ is tuple:
                    # For tuple returns with 3 items
                    if len(return_type.__args__) == 3:
                        return False, error_message, None
                    # For tuple returns with 2 items
                    else:
                        return False, error_message
                # Default return
                return False, error_message
        return wrapper
    return decorator


class FileManager:
    """Class for safe file management operations."""
    
    # Constants for error handling
    RETRY_ERROR_CODES = (errno.EINTR, errno.EAGAIN, errno.EBUSY)
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0
    
    def __init__(self, logger=None):
        """
        Initialize the file manager.
        
        Args:
            logger: Logger for recording operations (optional)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.last_error = None
        self.last_error_code = None
    
    def _check_path_exists(self, path: str, error_prefix: str = "") -> Tuple[bool, Optional[str]]:
        """
        Check if a path exists.
        
        Args:
            path: Path to check
            error_prefix: Prefix for error message
            
        Returns:
            Tuple[bool, Optional[str]]: (exists, error message if not)
        """
        if not os.path.exists(path):
            self.last_error = FileNotFoundError(f"{error_prefix} does not exist: {path}")
            self.last_error_code = errno.ENOENT
            self.logger.error(f"Attempted to access nonexistent path: {path}")
            return False, str(self.last_error)
        return True, None
    
    def _check_is_directory(self, path: str, error_prefix: str = "") -> Tuple[bool, Optional[str]]:
        """
        Check if a path is a directory.
        
        Args:
            path: Path to check
            error_prefix: Prefix for error message
            
        Returns:
            Tuple[bool, Optional[str]]: (is directory, error message if not)
        """
        exists, error = self._check_path_exists(path, error_prefix)
        if not exists:
            return False, error
            
        if not os.path.isdir(path):
            self.last_error = NotADirectoryError(f"{error_prefix} is not a directory: {path}")
            self.last_error_code = errno.ENOTDIR
            self.logger.error(f"Attempted to use non-directory path: {path}")
            return False, str(self.last_error)
        return True, None
    
    def _check_target_path(self, target_path: str, overwrite: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Check if a target path can be written to.
        
        Args:
            target_path: Target path to check
            overwrite: Whether to allow overwriting existing files
            
        Returns:
            Tuple[bool, Optional[str]]: (can write, error message if not)
        """
        if os.path.exists(target_path) and not overwrite:
            self.last_error = FileExistsError(f"Target already exists: {target_path}")
            self.last_error_code = errno.EEXIST
            self.logger.error(f"Target exists and overwrite=False: {target_path}")
            return False, str(self.last_error)
        return True, None
    
    def _create_parent_directory(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Create parent directory for a path if it doesn't exist.
        
        Args:
            path: Path whose parent directory should be created
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            return self.ensure_directory_exists(parent_dir)
        return True, None

    @handle_file_errors("file deletion")
    def delete_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file at the specified path.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        exists, error = self._check_path_exists(file_path, "File")
        if not exists:
            return False, error
        
        os.unlink(file_path)
        self.logger.info(f"File deleted: {file_path}")
        return True, None
    
    @handle_file_errors("secure file deletion")
    def secure_delete_file(self, file_path: str, passes: int = 3) -> Tuple[bool, Optional[str]]:
        """
        Securely delete a file by overwriting its content multiple times.
        
        Args:
            file_path: Path to the file to delete
            passes: Number of overwrite passes (default: 3)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        exists, error = self._check_path_exists(file_path, "File")
        if not exists:
            return False, error
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Perform multiple overwrite passes
        for pass_num in range(passes):
            # Determine pattern for this pass
            if pass_num == 0:
                pattern = b'\x00'  # Zeros
            elif pass_num == 1:
                pattern = b'\xFF'  # Ones
            else:
                # Pseudo-random data (different for each pass)
                import random
                pattern = bytes([random.randint(0, 255) for _ in range(min(1024, file_size or 1024))])
            
            # Overwrite the file with the pattern
            with open(file_path, 'wb') as f:
                # For larger files, write in chunks
                if len(pattern) < file_size:
                    for chunk in range(0, file_size, len(pattern)):
                        remaining = min(len(pattern), file_size - chunk)
                        f.write(pattern[:remaining])
                else:
                    f.write(pattern[:file_size] if file_size > 0 else pattern)
                
                # Ensure data is written to disk
                f.flush()
                os.fsync(f.fileno())
        
        # Delete the file
        os.unlink(file_path)
        self.logger.info(f"File securely deleted: {file_path} ({passes} passes)")
        return True, None
    
    @handle_file_errors("directory deletion")
    def delete_directory(self, dir_path: str, recursive: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Delete a directory.
        
        Args:
            dir_path: Path to the directory to delete
            recursive: Delete recursively with contents (default: False)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        is_dir, error = self._check_is_directory(dir_path, "Directory")
        if not is_dir:
            return False, error
        
        if recursive:
            shutil.rmtree(dir_path)
            self.logger.info(f"Directory recursively deleted: {dir_path}")
        else:
            try:
                os.rmdir(dir_path)
                self.logger.info(f"Empty directory deleted: {dir_path}")
            except OSError as e:
                if e.errno == errno.ENOTEMPTY:
                    error_message = f"Directory not empty (use recursive=True): {dir_path}"
                    self.logger.error(error_message)
                    return False, error_message
                raise
        
        return True, None
    
    def _retry_operation(self, operation: Callable[[], T], 
                        error_msg: str,
                        max_retries: int = DEFAULT_MAX_RETRIES, 
                        retry_delay: float = DEFAULT_RETRY_DELAY,
                        timeout: Optional[float] = None) -> Tuple[bool, Optional[str], Optional[T]]:
        """
        Retry an operation with proper error handling and timeout.
        
        Args:
            operation: Callable operation to retry
            error_msg: Error message for logging
            max_retries: Maximum retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
            timeout: Operation timeout in seconds (default: None)
            
        Returns:
            Tuple[bool, Optional[str], Optional[T]]: (success, error message, result)
        """
        # Set start time for timeout tracking
        start_time = time.time() if timeout else None
        
        # Attempt the operation with retries
        attempts = 0
        last_exception = None
        
        while attempts < max_retries:
            try:
                # Check timeout if specified
                if timeout and start_time and time.time() - start_time > timeout:
                    self.last_error = TimeoutError(f"Operation timed out after {timeout} seconds")
                    error_message = str(self.last_error)
                    self.logger.error(error_message)
                    return False, error_message, None
                
                # Execute operation
                result = operation()
                return True, None, result
                
            except OSError as e:
                # Handle specific error conditions
                if e.errno in self.RETRY_ERROR_CODES:
                    attempts += 1
                    last_exception = e
                    
                    if attempts < max_retries:
                        self.logger.warning(f"Temporary error (attempt {attempts}/{max_retries}): {str(e)}")
                        time.sleep(retry_delay)
                        continue
                
                # Other errors are raised immediately
                self.last_error = e
                self.last_error_code = e.errno
                self.logger.error(f"{error_msg}: {str(e)}")
                return False, str(e), None
        
        # All retries exhausted
        self.last_error = last_exception
        self.last_error_code = getattr(last_exception, 'errno', None) if last_exception else None
        error_message = f"Failed after {max_retries} attempts: {str(last_exception)}"
        self.logger.error(error_message)
        return False, error_message, None
    
    @handle_file_errors("file move")
    def move_file(self, source_path: str, target_path: str, 
                 overwrite: bool = False, create_dirs: bool = False,
                 max_retries: int = DEFAULT_MAX_RETRIES, 
                 retry_delay: float = DEFAULT_RETRY_DELAY,
                 timeout: float = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Move a file to a new location.
        
        Args:
            source_path: Path to the source file
            target_path: Target path
            overwrite: Overwrite existing file (default: False)
            create_dirs: Create intermediate directories (default: False)
            max_retries: Maximum retry attempts for temporary errors (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
            timeout: Operation timeout in seconds (default: None)
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, error message, new path)
        """
        # Check source existence
        exists, error = self._check_path_exists(source_path, "Source file")
        if not exists:
            return False, error, None
        
        # Check if target can be written
        can_write, error = self._check_target_path(target_path, overwrite)
        if not can_write:
            return False, error, None
        
        # Create target directories if needed
        if create_dirs:
            target_dir = os.path.dirname(target_path)
            if target_dir:
                success, error = self.ensure_directory_exists(target_dir)
                if not success:
                    return False, error, None
        
        # Define retry operation for file move
        def do_move():
            try:
                # Try OS rename operation first (fastest)
                os.rename(source_path, target_path)
                self.logger.info(f"File moved: {source_path} -> {target_path}")
                return target_path
            except OSError as e:
                # Handle cross-device link error
                if e.errno == errno.EXDEV:
                    shutil.copy2(source_path, target_path)
                    os.unlink(source_path)
                    self.logger.info(f"File moved (copy+delete): {source_path} -> {target_path}")
                    return target_path
                raise
        
        # Execute with retry logic
        success, error, result = self._retry_operation(
            operation=do_move,
            error_msg=f"Error moving file {source_path} -> {target_path}",
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout
        )
        
        return success, error, result
    
    @handle_file_errors("directory move")
    def move_directory(self, source_dir: str, target_dir: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Move a directory to a new location.
        
        Args:
            source_dir: Path to the source directory
            target_dir: Target directory path
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, error message, new path)
        """
        # Check source directory
        is_dir, error = self._check_is_directory(source_dir, "Source directory")
        if not is_dir:
            return False, error, None
        
        # Create parent directory if needed
        parent_dir = os.path.dirname(target_dir)
        if parent_dir and not os.path.exists(parent_dir):
            success, error = self.ensure_directory_exists(parent_dir)
            if not success:
                return False, error, None
        
        try:
            # Try shutil.move first (handles most cases)
            shutil.move(source_dir, target_dir)
            self.logger.info(f"Directory moved: {source_dir} -> {target_dir}")
            return True, None, target_dir
        except OSError as e:
            # Handle cross-device move (EXDEV) by copying and deleting
            if e.errno == errno.EXDEV:
                shutil.copytree(source_dir, target_dir)
                shutil.rmtree(source_dir)
                self.logger.info(f"Directory moved (copy+delete): {source_dir} -> {target_dir}")
                return True, None, target_dir
            raise
    
    @handle_file_errors("file copy")
    def copy_file(self, source_path: str, target_path: str, 
                 overwrite: bool = False, create_dirs: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Copy a file to a new location.
        
        Args:
            source_path: Path to the source file
            target_path: Target path
            overwrite: Overwrite existing file (default: False)
            create_dirs: Create intermediate directories (default: False)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        # Check source existence
        exists, error = self._check_path_exists(source_path, "Source file")
        if not exists:
            return False, error
        
        # Check if target can be written
        can_write, error = self._check_target_path(target_path, overwrite)
        if not can_write:
            return False, error
        
        # Create target directories if needed
        if create_dirs:
            success, error = self._create_parent_directory(target_path)
            if not success:
                return False, error
        
        # Copy the file with metadata
        shutil.copy2(source_path, target_path)
        self.logger.info(f"File copied: {source_path} -> {target_path}")
        return True, None
    
    @handle_file_errors("permission check")
    def check_permission(self, path: str, permission_type: str) -> bool:
        """
        Check if a path has the specified permission.
        
        Args:
            path: Path to check
            permission_type: Type of permission ('read', 'write', 'execute')
            
        Returns:
            bool: True if path has the permission, False otherwise
        """
        if not os.path.exists(path):
            self.logger.debug(f"Path does not exist for permission check: {path}")
            return False
        
        if permission_type == 'read':
            result = os.access(path, os.R_OK)
            self.logger.debug(f"Read permission check for {path}: {result}")
            return result
        elif permission_type == 'write':
            result = os.access(path, os.W_OK)
            self.logger.debug(f"Write permission check for {path}: {result}")
            return result
        elif permission_type == 'execute':
            result = os.access(path, os.X_OK)
            self.logger.debug(f"Execute permission check for {path}: {result}")
            return result
        else:
            self.logger.warning(f"Unknown permission type: {permission_type}")
            return False
    
    @handle_file_errors("permission setting")
    def set_permissions(self, path: str, read: bool = True, write: bool = True, 
                      execute: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Set permissions on a file or directory.
        
        Args:
            path: Path to set permissions on
            read: Allow reading (default: True)
            write: Allow writing (default: True)
            execute: Allow execution (default: False)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        exists, error = self._check_path_exists(path)
        if not exists:
            return False, error
        
        # Build permission mode
        mode = 0
        if read:
            mode |= stat.S_IRUSR
        if write:
            mode |= stat.S_IWUSR
        if execute:
            mode |= stat.S_IXUSR
        
        # Set permissions
        os.chmod(path, mode)
        self.logger.info(f"Set permissions on {path}: read={read}, write={write}, execute={execute}")
        return True, None
    
    @handle_file_errors("path accessibility check")
    def check_path_accessible(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a path is accessible (all parent directories are accessible).
        
        Args:
            path: Path to check
            
        Returns:
            Tuple[bool, Optional[str]]: (is accessible, error message)
        """
        # Check the file or final directory
        if os.path.exists(path):
            if not os.access(path, os.R_OK):
                error_message = f"No read permission for path: {path}"
                self.logger.error(error_message)
                return False, error_message
            
            self.logger.debug(f"Path is accessible: {path}")
            return True, None
        
        # Check parent directories
        parent_dir = os.path.dirname(path)
        if not parent_dir:
            error_message = f"Invalid path: {path}"
            self.logger.error(error_message)
            return False, error_message
        
        if not os.path.exists(parent_dir):
            error_message = f"Parent directory does not exist: {parent_dir}"
            self.logger.error(error_message)
            return False, error_message
        
        if not os.access(parent_dir, os.R_OK | os.W_OK | os.X_OK):
            error_message = f"Insufficient permissions for parent directory: {parent_dir}"
            self.logger.error(error_message)
            return False, error_message
        
        self.logger.debug(f"Path has accessible parent directory: {path}")
        return True, None
    
    def get_last_error(self) -> Optional[Exception]:
        """
        Get the last error encountered.
        
        Returns:
            Exception or None: Last error object
        """
        return self.last_error
    
    def get_last_error_code(self) -> Optional[int]:
        """
        Get the error code from the last error.
        
        Returns:
            int or None: Last error code
        """
        return self.last_error_code
    
    @handle_file_errors("directory creation")
    def ensure_directory_exists(self, directory_path: str) -> Tuple[bool, Optional[str]]:
        """
        Ensure that a directory exists, creating it and any parent directories if necessary.
        
        Args:
            directory_path: Path to the directory to create
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        if os.path.exists(directory_path):
            if not os.path.isdir(directory_path):
                self.last_error = NotADirectoryError(f"Path exists but is not a directory: {directory_path}")
                self.last_error_code = errno.ENOTDIR
                error_message = str(self.last_error)
                self.logger.error(error_message)
                return False, error_message
            return True, None
        
        # Create directory with parents
        os.makedirs(directory_path, exist_ok=True)
        self.logger.info(f"Created directory: {directory_path}")
        return True, None
    
    @handle_file_errors("file processing")
    def safe_process_file(self, source_path: str, target_path: str, 
                         processing_function: Callable[[bytes], bytes], 
                         buffer_size: int = 8192,
                         secure_delete: bool = False,
                         create_dirs: bool = True,
                         overwrite: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Safely process a file by reading from source, applying a function, and writing to target.
        
        This method handles common file operations safely with proper error handling.
        
        Args:
            source_path: Path to the source file
            target_path: Path to write the processed file
            processing_function: Function to apply to the source data (bytes -> bytes)
            buffer_size: Buffer size for reading file in chunks
            secure_delete: Whether to securely delete the source file 
            create_dirs: Create target directories if they don't exist
            overwrite: Overwrite existing target file
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, error message, output path)
        """
        temp_file = None
        
        try:
            # Check source existence
            exists, error = self._check_path_exists(source_path, "Source file")
            if not exists:
                return False, error, None
            
            # Check if target can be written
            can_write, error = self._check_target_path(target_path, overwrite)
            if not can_write:
                return False, error, None
            
            # Create target directory if needed
            if create_dirs:
                target_dir = os.path.dirname(target_path)
                if target_dir:
                    success, error = self.ensure_directory_exists(target_dir)
                    if not success:
                        return False, f"Failed to create target directory: {error}", None
            
            # Create temporary file for processing
            success, error, temp_file = self.create_temp_file(
                prefix="safe_process_", 
                suffix=".tmp",
                dir=os.path.dirname(target_path) if os.path.dirname(target_path) else None
            )
            
            if not success:
                return False, f"Failed to create temporary file: {error}", None
            
            # Process the file
            with open(source_path, 'rb') as src_file, open(temp_file, 'wb') as tmp_file:
                while True:
                    chunk = src_file.read(buffer_size)
                    if not chunk:
                        break
                    
                    # Apply the processing function
                    processed_chunk = processing_function(chunk)
                    tmp_file.write(processed_chunk)
                    
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            
            # Move the temporary file to the target path
            if os.path.exists(target_path) and overwrite:
                os.unlink(target_path)
            
            success, error, _ = self.move_file(temp_file, target_path, overwrite=True)
            
            if not success:
                return False, f"Failed to move processed file to target: {error}", None
            
            # Delete source file if requested
            if secure_delete:
                success, error = self.secure_delete_file(source_path)
            else:
                success, error = self.delete_file(source_path)
            
            if not success:
                self.logger.warning(f"Failed to delete source file: {error}")
                # Continue anyway since the processing was successful
            
            self.logger.info(f"Successfully processed file: {source_path} -> {target_path}")
            return True, None, target_path
            
        except Exception as e:
            self.last_error = e
            error_message = f"Error processing file {source_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message, None
        
        finally:
            # Clean up temporary file if it exists and wasn't moved
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    self.logger.warning(f"Failed to delete temporary file: {temp_file}")
    
    @staticmethod
    def identity_function(data: bytes) -> bytes:
        """Identity function that returns input unchanged, for use with safe_process_file."""
        return data
    
    @handle_file_errors("temporary file creation")
    def create_temp_file(self, prefix: str = "meet2obs_", suffix: str = "",
                       content: Optional[bytes] = None, mode: str = "w+b",
                       dir: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a temporary file with optional content.
        
        Args:
            prefix: Prefix for the temporary filename (default: "meet2obs_")
            suffix: Suffix for the temporary filename (default: "")
            content: Optional content to write to the file
            mode: File mode for opening (default: "w+b")
            dir: Directory where the file should be created (default: system temp dir)
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, error message, file path)
        """
        # Generate unique identifier
        unique_id = str(uuid.uuid4())[:8]
        
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=f"{prefix}{unique_id}_", dir=dir)
        
        try:
            # Write content if provided
            if content is not None:
                with os.fdopen(fd, "wb") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
            else:
                # Close the file descriptor if we're not writing content
                os.close(fd)
            
            self.logger.info(f"Created temporary file: {temp_path}")
            return True, None, temp_path
        
        except Exception as e:
            # Clean up on error
            try:
                os.close(fd)
            except:
                pass
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            raise
    
    @handle_file_errors("disk space check")
    def get_disk_space(self, path: str) -> Tuple[bool, Optional[str], Optional[Dict[str, int]]]:
        """
        Get disk space information for the filesystem containing the specified path.
        
        Args:
            path: Path to check
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, int]]]: (success, error message, space info)
            
            Where space info is a dictionary with keys:
            - 'total': Total space in bytes
            - 'used': Used space in bytes
            - 'free': Free space in bytes
            - 'available': Available space in bytes (may differ from free due to quotas)
        """
        exists, error = self._check_path_exists(path)
        if not exists:
            return False, error, None
        
        # Get disk usage statistics
        st = os.statvfs(path)
        
        # Calculate space values
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        available = st.f_bavail * st.f_frsize
        used = total - free
        
        # Create result dictionary
        space_info = {
            'total': total,
            'used': used,
            'free': free,
            'available': available
        }
        
        self.logger.debug(f"Disk space info for {path}: {space_info}")
        return True, None, space_info
    
    @handle_file_errors("space availability check")
    def has_sufficient_space(self, path: str, required_bytes: int) -> Tuple[bool, Optional[str], bool]:
        """
        Check if there is sufficient disk space available for an operation.
        
        Args:
            path: Path where the operation will be performed
            required_bytes: Required space in bytes
            
        Returns:
            Tuple[bool, Optional[str], bool]: (success, error message, has sufficient space)
        """
        # Get disk space info
        success, error, space_info = self.get_disk_space(path)
        
        if not success:
            return False, f"Error checking disk space: {error}", False
        
        # Check if we have enough available space
        has_space = space_info['available'] >= required_bytes
        
        if has_space:
            self.logger.debug(f"Sufficient space available at {path} "
                           f"({space_info['available']} bytes available, {required_bytes} bytes required)")
        else:
            self.logger.warning(f"Insufficient space at {path} "
                             f"({space_info['available']} bytes available, {required_bytes} bytes required)")
        
        return True, None, has_space