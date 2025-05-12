"""
Integration tests for the FileManager class.

These tests verify the FileManager's interaction with the actual file system
and test complete workflows involving multiple operations.
"""

import pytest
import os
import tempfile
import time
import subprocess
import signal
import sys
import stat
import shutil
from pathlib import Path

# Import the actual implementation
from meet2obsidian.utils.file_manager import FileManager

# Simple logger setup for tests
def setup_logger(name):
    """Configure a logger for testing."""
    import logging
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Add a console handler if not already set up
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class TestFileManagerIntegration:
    """Integration tests for the FileManager class."""
    
    @pytest.fixture
    def logger(self):
        """Creates a logger for tests."""
        return setup_logger("test_file_manager")
    
    @pytest.fixture
    def manager(self, logger):
        """Creates a FileManager instance with configured logger."""
        return FileManager(logger=logger)
    
    def test_complete_file_workflow(self, manager):
        """Test a complete workflow of file operations."""
        # Create temporary directories
        source_dir = tempfile.mkdtemp()
        target_dir = tempfile.mkdtemp()
        
        try:
            # 1. Create a test file
            test_file_path = os.path.join(source_dir, "test_file.txt")
            with open(test_file_path, 'w') as f:
                f.write("Test content for file operations")
            
            # 2. Check file existence and permissions
            assert os.path.exists(test_file_path)
            assert manager.check_permission(test_file_path, 'read') is True
            assert manager.check_permission(test_file_path, 'write') is True
            
            # 3. Move file to target directory
            target_path = os.path.join(target_dir, "moved_file.txt")
            success, error, new_path = manager.move_file(test_file_path, target_path)
            
            assert success is True
            assert error is None
            assert new_path == target_path
            assert not os.path.exists(test_file_path)
            assert os.path.exists(target_path)
            
            # 4. Copy file back to source directory
            copy_path = os.path.join(source_dir, "copied_file.txt")
            success, error = manager.copy_file(target_path, copy_path)
            
            assert success is True
            assert error is None
            assert os.path.exists(target_path)  # Original remains
            assert os.path.exists(copy_path)    # Copy created
            
            # 5. Check content of copied file
            with open(copy_path, 'r') as f:
                content = f.read()
            assert content == "Test content for file operations"
            
            # 6. Change permissions (if on POSIX system)
            if os.name == 'posix':
                success, error = manager.set_permissions(copy_path, read=True, write=False, execute=False)
                assert success is True
                assert manager.check_permission(copy_path, 'read') is True
                assert manager.check_permission(copy_path, 'write') is False
                
                # Restore permissions for further operations
                os.chmod(copy_path, 0o644)
            
            # 7. Securely delete files
            success, error = manager.secure_delete_file(target_path)
            assert success is True
            assert not os.path.exists(target_path)
            
            success, error = manager.delete_file(copy_path)
            assert success is True
            assert not os.path.exists(copy_path)
            
        finally:
            # Cleanup
            for dir_path in [source_dir, target_dir]:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)
    
    def test_directory_operations(self, manager):
        """Test complete workflow for directory operations."""
        # Create base temporary directory
        base_dir = tempfile.mkdtemp()
        try:
            # 1. Create source directory with files
            source_dir = os.path.join(base_dir, "source_dir")
            os.makedirs(source_dir)
            
            # Create some files in the source directory
            for i in range(3):
                file_path = os.path.join(source_dir, f"file{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"Content for file {i}")
            
            # Create a subdirectory with a file
            subdir = os.path.join(source_dir, "subdir")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "subfile.txt"), 'w') as f:
                f.write("Content in subdirectory")
            
            # 2. Move directory to new location
            target_dir = os.path.join(base_dir, "target_dir")
            success, error, new_path = manager.move_directory(source_dir, target_dir)
            
            assert success is True
            assert error is None
            assert new_path == target_dir
            assert not os.path.exists(source_dir)
            assert os.path.exists(target_dir)
            assert os.path.exists(os.path.join(target_dir, "file0.txt"))
            assert os.path.exists(os.path.join(target_dir, "subdir", "subfile.txt"))
            
            # 3. Create a new directory to test deletion
            delete_dir = os.path.join(base_dir, "delete_dir")
            os.makedirs(delete_dir)
            with open(os.path.join(delete_dir, "testfile.txt"), 'w') as f:
                f.write("File to be deleted")
            
            # 4. Test recursive directory deletion
            success, error = manager.delete_directory(delete_dir, recursive=True)
            assert success is True
            assert error is None
            assert not os.path.exists(delete_dir)
            
            # 5. Test path accessibility
            is_accessible, error = manager.check_path_accessible(target_dir)
            assert is_accessible is True
            assert error is None
            
            is_accessible, error = manager.check_path_accessible(os.path.join(target_dir, "nonexistent.txt"))
            assert is_accessible is True  # Parent directory is accessible
            assert error is None
            
        finally:
            # Cleanup
            if os.path.exists(base_dir):
                shutil.rmtree(base_dir, ignore_errors=True)
    
    def test_file_locking_scenario(self, manager):
        """Test scenario with a file being locked by another process."""
        # Skip on non-POSIX systems
        if not sys.platform.startswith('linux') and not sys.platform.startswith('darwin'):
            pytest.skip("Test requires POSIX-compatible platform")
        
        # Create temporary file
        fd, file_path = tempfile.mkstemp()
        os.close(fd)
        
        process = None
        try:
            # Write content to file
            with open(file_path, 'w') as f:
                f.write("File that will be locked")
            
            # Start a separate process that keeps the file open
            process = subprocess.Popen(['tail', '-f', file_path], stdout=subprocess.PIPE)
            
            # Give the process time to start
            time.sleep(1)
            
            # Try to move the file - this may fail on some systems due to file being in use
            target_path = file_path + ".moved"
            success, error, _ = manager.move_file(file_path, target_path)
            
            # Some systems might allow moving an open file, so we don't assert on success
            if not success:
                assert error is not None
                assert os.path.exists(file_path)  # Original file should still exist
            
            # Terminate the process
            process.terminate()
            process.wait(timeout=2)
            process = None
            
            # Now moving the file should work
            if os.path.exists(file_path) and not os.path.exists(target_path):
                success, error, _ = manager.move_file(file_path, target_path)
                assert success is True
                assert error is None
                assert os.path.exists(target_path)
            
            # Clean up the moved file if it exists
            if os.path.exists(target_path):
                success, error = manager.delete_file(target_path)
                assert success is True
                assert not os.path.exists(target_path)
            
        finally:
            # Terminate process if still running
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except:
                    process.kill()
            
            # Cleanup files
            for path in [file_path, file_path + ".moved"]:
                if os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass
    
    def test_error_handling_with_recovery(self, manager):
        """Test error handling with recovery for file operations."""
        # Create temporary directories and files
        source_dir = tempfile.mkdtemp()
        target_dir = tempfile.mkdtemp()
        
        try:
            # 1. Test handling nonexistent file
            nonexistent_path = os.path.join(source_dir, "nonexistent.txt")
            success, error = manager.delete_file(nonexistent_path)
            assert success is False
            assert "not exist" in error.lower() or "no such file" in error.lower()
            
            # 2. Test handling file without permissions
            if os.name == 'posix':
                # Create a file with restricted permissions
                restricted_path = os.path.join(source_dir, "restricted.txt")
                with open(restricted_path, 'w') as f:
                    f.write("Restricted file content")
                
                # Make file read-only
                os.chmod(restricted_path, stat.S_IREAD)
                
                # Try to delete the file
                success, error = manager.delete_file(restricted_path)

                # The operation might succeed or fail depending on the system
                # On macOS, read-only files can often still be deleted by the owner

                if not success:
                    # If it failed, we need to recover by changing permissions
                    assert "permission denied" in error.lower()

                    # Recovery: change permissions and try again
                    os.chmod(restricted_path, stat.S_IREAD | stat.S_IWRITE)
                    success, error = manager.delete_file(restricted_path)
                    assert success is True

                # At this point the file should be gone
                assert not os.path.exists(restricted_path)
            
            # 3. Test handling target directory not existing
            source_path = os.path.join(source_dir, "source_file.txt")
            with open(source_path, 'w') as f:
                f.write("Source file to be moved")
            
            nonexistent_dir = os.path.join(target_dir, "nonexistent_dir")
            target_path = os.path.join(nonexistent_dir, "moved_file.txt")
            
            # First attempt without create_dirs should fail
            success, error, _ = manager.move_file(source_path, target_path, create_dirs=False)
            assert success is False
            assert not os.path.exists(target_path)
            
            # Recovery: try again with create_dirs=True
            success, error, _ = manager.move_file(source_path, target_path, create_dirs=True)
            assert success is True
            assert error is None
            assert os.path.exists(target_path)
            assert not os.path.exists(source_path)
            
        finally:
            # Cleanup
            for dir_path in [source_dir, target_dir]:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)