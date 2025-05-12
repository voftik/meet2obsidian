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
from typing import Tuple, Optional, Any


class FileManager:
    """Class for safe file management operations."""
    
    def __init__(self, logger=None):
        """
        Initialize the file manager.
        
        Args:
            logger: Logger for recording operations (optional)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.last_error = None
        self.last_error_code = None
    
    def delete_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file at the specified path.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        try:
            if not os.path.exists(file_path):
                self.last_error = FileNotFoundError(f"File does not exist: {file_path}")
                self.last_error_code = errno.ENOENT
                self.logger.error(f"Attempted to delete nonexistent file: {file_path}")
                return False, str(self.last_error)
            
            os.unlink(file_path)
            self.logger.info(f"File deleted: {file_path}")
            return True, None
        except OSError as e:
            self.last_error = e
            self.last_error_code = e.errno
            error_message = f"Error deleting file {file_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
        except Exception as e:
            self.last_error = e
            error_message = f"Unexpected error deleting file {file_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def secure_delete_file(self, file_path: str, passes: int = 3) -> Tuple[bool, Optional[str]]:
        """
        Securely delete a file by overwriting its content multiple times.
        
        Args:
            file_path: Path to the file to delete
            passes: Number of overwrite passes (default: 3)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        try:
            if not os.path.exists(file_path):
                self.last_error = FileNotFoundError(f"File does not exist: {file_path}")
                self.last_error_code = errno.ENOENT
                self.logger.error(f"Attempted to securely delete nonexistent file: {file_path}")
                return False, str(self.last_error)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Perform multiple overwrite passes
            for pass_num in range(passes):
                pattern = None
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
            
        except OSError as e:
            self.last_error = e
            self.last_error_code = e.errno
            error_message = f"Error securely deleting file {file_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
        except Exception as e:
            self.last_error = e
            error_message = f"Unexpected error securely deleting file {file_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def delete_directory(self, dir_path: str, recursive: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Delete a directory.
        
        Args:
            dir_path: Path to the directory to delete
            recursive: Delete recursively with contents (default: False)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        try:
            if not os.path.exists(dir_path):
                self.last_error = FileNotFoundError(f"Directory does not exist: {dir_path}")
                self.last_error_code = errno.ENOENT
                self.logger.error(f"Attempted to delete nonexistent directory: {dir_path}")
                return False, str(self.last_error)
            
            if not os.path.isdir(dir_path):
                self.last_error = NotADirectoryError(f"Path is not a directory: {dir_path}")
                self.last_error_code = errno.ENOTDIR
                self.logger.error(f"Attempted to delete non-directory path: {dir_path}")
                return False, str(self.last_error)
            
            if recursive:
                shutil.rmtree(dir_path)
                self.logger.info(f"Directory recursively deleted: {dir_path}")
            else:
                try:
                    os.rmdir(dir_path)
                    self.logger.info(f"Empty directory deleted: {dir_path}")
                except OSError as e:
                    if e.errno == errno.ENOTEMPTY:
                        self.last_error = e
                        self.last_error_code = e.errno
                        error_message = f"Directory not empty (use recursive=True): {dir_path}"
                        self.logger.error(error_message)
                        return False, error_message
                    raise
            
            return True, None
            
        except OSError as e:
            self.last_error = e
            self.last_error_code = e.errno
            error_message = f"Error deleting directory {dir_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
        except Exception as e:
            self.last_error = e
            error_message = f"Unexpected error deleting directory {dir_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def move_file(self, source_path: str, target_path: str, 
                 overwrite: bool = False, create_dirs: bool = False,
                 max_retries: int = 3, retry_delay: float = 1.0,
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
        try:
            if not os.path.exists(source_path):
                self.last_error = FileNotFoundError(f"Source file does not exist: {source_path}")
                self.last_error_code = errno.ENOENT
                self.logger.error(f"Attempted to move nonexistent file: {source_path}")
                return False, str(self.last_error), None
            
            # Create target directories if requested
            if create_dirs:
                target_dir = os.path.dirname(target_path)
                if target_dir and not os.path.exists(target_dir):
                    try:
                        os.makedirs(target_dir)
                        self.logger.info(f"Created target directory: {target_dir}")
                    except OSError as e:
                        self.last_error = e
                        self.last_error_code = e.errno
                        error_message = f"Failed to create target directory {target_dir}: {str(e)}"
                        self.logger.error(error_message)
                        return False, error_message, None
            
            # Check if target file exists
            if os.path.exists(target_path) and not overwrite:
                self.last_error = FileExistsError(f"Target file already exists: {target_path}")
                self.last_error_code = errno.EEXIST
                self.logger.error(f"Target file exists and overwrite=False: {target_path}")
                return False, str(self.last_error), None
            
            # Set timeout if specified
            if timeout:
                start_time = time.time()
            
            # Attempt to move the file with retries
            attempts = 0
            last_exception = None
            
            while attempts < max_retries:
                try:
                    # Check timeout
                    if timeout and time.time() - start_time > timeout:
                        self.last_error = TimeoutError(f"Operation timed out after {timeout} seconds")
                        error_message = str(self.last_error)
                        self.logger.error(error_message)
                        return False, error_message, None
                    
                    # Try OS rename operation first
                    os.rename(source_path, target_path)
                    self.logger.info(f"File moved: {source_path} -> {target_path}")
                    return True, None, target_path
                    
                except OSError as e:
                    # Handle specific error conditions
                    if e.errno == errno.EXDEV:
                        # Cross-device link error - fall back to copy + delete
                        try:
                            shutil.copy2(source_path, target_path)
                            os.unlink(source_path)
                            self.logger.info(f"File moved (copy+delete): {source_path} -> {target_path}")
                            return True, None, target_path
                        except OSError as copy_error:
                            self.last_error = copy_error
                            self.last_error_code = copy_error.errno
                            error_message = f"Error moving file between devices {source_path} -> {target_path}: {str(copy_error)}"
                            self.logger.error(error_message)
                            return False, error_message, None
                    
                    # Handle temporary errors with retry
                    elif e.errno in (errno.EINTR, errno.EAGAIN, errno.EBUSY):
                        attempts += 1
                        last_exception = e
                        
                        if attempts < max_retries:
                            self.logger.warning(f"Temporary error moving file (attempt {attempts}/{max_retries}): {str(e)}")
                            time.sleep(retry_delay)
                            continue
                    
                    # Other errors
                    self.last_error = e
                    self.last_error_code = e.errno
                    error_message = f"Error moving file {source_path} -> {target_path}: {str(e)}"
                    self.logger.error(error_message)
                    return False, error_message, None
            
            # All retries exhausted
            self.last_error = last_exception
            self.last_error_code = last_exception.errno if last_exception else None
            error_message = f"Failed to move file after {max_retries} attempts: {str(last_exception)}"
            self.logger.error(error_message)
            return False, error_message, None
            
        except Exception as e:
            self.last_error = e
            error_message = f"Unexpected error moving file {source_path} -> {target_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message, None
    
    def move_directory(self, source_dir: str, target_dir: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Move a directory to a new location.
        
        Args:
            source_dir: Path to the source directory
            target_dir: Target directory path
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, error message, new path)
        """
        try:
            if not os.path.exists(source_dir):
                self.last_error = FileNotFoundError(f"Source directory does not exist: {source_dir}")
                self.last_error_code = errno.ENOENT
                self.logger.error(f"Attempted to move nonexistent directory: {source_dir}")
                return False, str(self.last_error), None
            
            if not os.path.isdir(source_dir):
                self.last_error = NotADirectoryError(f"Source path is not a directory: {source_dir}")
                self.last_error_code = errno.ENOTDIR
                self.logger.error(f"Attempted to move non-directory path: {source_dir}")
                return False, str(self.last_error), None
            
            # Create parent directory if it doesn't exist
            parent_dir = os.path.dirname(target_dir)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir)
                    self.logger.info(f"Created parent directory: {parent_dir}")
                except OSError as e:
                    self.last_error = e
                    self.last_error_code = e.errno
                    error_message = f"Failed to create parent directory {parent_dir}: {str(e)}"
                    self.logger.error(error_message)
                    return False, error_message, None
            
            try:
                # Try using shutil.move first
                shutil.move(source_dir, target_dir)
                self.logger.info(f"Directory moved: {source_dir} -> {target_dir}")
                return True, None, target_dir
                
            except OSError as e:
                # Handle cross-device move
                if e.errno == errno.EXDEV:
                    try:
                        # Copy directory tree then remove source
                        shutil.copytree(source_dir, target_dir)
                        shutil.rmtree(source_dir)
                        self.logger.info(f"Directory moved (copy+delete): {source_dir} -> {target_dir}")
                        return True, None, target_dir
                    except OSError as copy_error:
                        self.last_error = copy_error
                        self.last_error_code = copy_error.errno
                        error_message = f"Error moving directory between devices {source_dir} -> {target_dir}: {str(copy_error)}"
                        self.logger.error(error_message)
                        return False, error_message, None
                    
                # Re-raise other errors
                raise
                
        except OSError as e:
            self.last_error = e
            self.last_error_code = e.errno
            error_message = f"Error moving directory {source_dir} -> {target_dir}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message, None
        except Exception as e:
            self.last_error = e
            error_message = f"Unexpected error moving directory {source_dir} -> {target_dir}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message, None
    
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
        try:
            if not os.path.exists(source_path):
                self.last_error = FileNotFoundError(f"Source file does not exist: {source_path}")
                self.last_error_code = errno.ENOENT
                self.logger.error(f"Attempted to copy nonexistent file: {source_path}")
                return False, str(self.last_error)
            
            # Create target directories if requested
            if create_dirs:
                target_dir = os.path.dirname(target_path)
                if target_dir and not os.path.exists(target_dir):
                    try:
                        os.makedirs(target_dir)
                        self.logger.info(f"Created target directory: {target_dir}")
                    except OSError as e:
                        self.last_error = e
                        self.last_error_code = e.errno
                        error_message = f"Failed to create target directory {target_dir}: {str(e)}"
                        self.logger.error(error_message)
                        return False, error_message
            
            # Check if target file exists
            if os.path.exists(target_path) and not overwrite:
                self.last_error = FileExistsError(f"Target file already exists: {target_path}")
                self.last_error_code = errno.EEXIST
                self.logger.error(f"Target file exists and overwrite=False: {target_path}")
                return False, str(self.last_error)
            
            # Copy the file with metadata
            shutil.copy2(source_path, target_path)
            self.logger.info(f"File copied: {source_path} -> {target_path}")
            return True, None
            
        except OSError as e:
            self.last_error = e
            self.last_error_code = e.errno
            error_message = f"Error copying file {source_path} -> {target_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
        except Exception as e:
            self.last_error = e
            error_message = f"Unexpected error copying file {source_path} -> {target_path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def check_permission(self, path: str, permission_type: str) -> bool:
        """
        Check if a path has the specified permission.
        
        Args:
            path: Path to check
            permission_type: Type of permission ('read', 'write', 'execute')
            
        Returns:
            bool: True if path has the permission, False otherwise
        """
        try:
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
                
        except Exception as e:
            self.last_error = e
            self.logger.error(f"Error checking permission {permission_type} for {path}: {str(e)}")
            return False
    
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
        try:
            if not os.path.exists(path):
                self.last_error = FileNotFoundError(f"Path does not exist: {path}")
                self.last_error_code = errno.ENOENT
                self.logger.error(f"Attempted to set permissions on nonexistent path: {path}")
                return False, str(self.last_error)
            
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
            
        except OSError as e:
            self.last_error = e
            self.last_error_code = e.errno
            error_message = f"Error setting permissions on {path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
        except Exception as e:
            self.last_error = e
            error_message = f"Unexpected error setting permissions on {path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def check_path_accessible(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a path is accessible (all parent directories are accessible).
        
        Args:
            path: Path to check
            
        Returns:
            Tuple[bool, Optional[str]]: (is accessible, error message)
        """
        try:
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
            
        except Exception as e:
            self.last_error = e
            error_message = f"Error checking path accessibility for {path}: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
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