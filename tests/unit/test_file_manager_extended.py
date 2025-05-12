"""
Unit tests for the extended functionality of the FileManager class.

This module contains tests for the additional methods added to the FileManager class:
- ensure_directory_exists()
- safe_process_file()
"""

import pytest
import os
import tempfile
import uuid
from unittest.mock import patch, MagicMock

# Import the actual implementation
from meet2obsidian.utils.file_manager import FileManager


class TestExtendedFunctionality:
    """Tests for the extended FileManager functionality."""
    
    def test_ensure_directory_exists(self):
        """Test ensuring a directory exists."""
        manager = FileManager()
        
        # Test with a new directory path
        test_dir = os.path.join(tempfile.gettempdir(), f"test_dir_{os.urandom(4).hex()}")
        
        try:
            # Directory should not exist initially
            assert not os.path.exists(test_dir)
            
            # Create the directory
            success, error = manager.ensure_directory_exists(test_dir)
            
            assert success is True
            assert error is None
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
            
            # Test with an existing directory (should succeed)
            success, error = manager.ensure_directory_exists(test_dir)
            
            assert success is True
            assert error is None
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)
    
    def test_ensure_directory_exists_conflict(self):
        """Test ensuring a directory exists when there's a file with the same name."""
        manager = FileManager()
        
        # Create a file
        fd, file_path = tempfile.mkstemp()
        os.close(fd)
        
        try:
            # Try to create a directory with the same path as the file
            success, error = manager.ensure_directory_exists(file_path)
            
            assert success is False
            assert error is not None
            assert "not a directory" in error.lower()
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_safe_process_file(self):
        """Test safely processing a file."""
        manager = FileManager()
        
        # Create a source file with test content
        fd, source_path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as f:
            f.write(b'test content')
        
        # Define target path
        target_path = os.path.join(tempfile.gettempdir(), f"processed_{os.urandom(4).hex()}.txt")
        
        try:
            # Define a simple transformation function (convert to uppercase)
            def to_uppercase(data):
                return data.upper()
            
            # Process the file
            success, error, output_path = manager.safe_process_file(
                source_path, 
                target_path,
                processing_function=to_uppercase
            )
            
            assert success is True
            assert error is None
            assert output_path == target_path
            
            # Check that source file is deleted
            assert not os.path.exists(source_path)
            
            # Check that target file exists with transformed content
            assert os.path.exists(target_path)
            with open(target_path, 'rb') as f:
                content = f.read()
            assert content == b'TEST CONTENT'
        finally:
            # Clean up
            if os.path.exists(source_path):
                os.unlink(source_path)
            if os.path.exists(target_path):
                os.unlink(target_path)
    
    def test_safe_process_file_with_identity(self):
        """Test safely processing a file with the identity function."""
        manager = FileManager()
        
        # Create a source file with test content
        fd, source_path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as f:
            f.write(b'test content')
        
        # Define target path
        target_path = os.path.join(tempfile.gettempdir(), f"processed_{os.urandom(4).hex()}.txt")
        
        try:
            # Process the file with identity function (no transformation)
            success, error, output_path = manager.safe_process_file(
                source_path, 
                target_path,
                processing_function=FileManager.identity_function,
                secure_delete=True  # Use secure deletion
            )
            
            assert success is True
            assert error is None
            assert output_path == target_path
            
            # Check that source file is deleted
            assert not os.path.exists(source_path)
            
            # Check that target file exists with same content
            assert os.path.exists(target_path)
            with open(target_path, 'rb') as f:
                content = f.read()
            assert content == b'test content'
        finally:
            # Clean up
            if os.path.exists(source_path):
                os.unlink(source_path)
            if os.path.exists(target_path):
                os.unlink(target_path)
                
    def test_safe_process_file_error_handling(self):
        """Test error handling in safe_process_file."""
        manager = FileManager()
        
        # Create a source file with test content
        fd, source_path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as f:
            f.write(b'test content')
        
        # Define target path 
        target_path = os.path.join(tempfile.gettempdir(), f"processed_{os.urandom(4).hex()}.txt")
        
        try:
            # Define a function that raises an exception
            def raises_exception(data):
                raise ValueError("Test exception")
            
            # Process the file with failing function
            success, error, output_path = manager.safe_process_file(
                source_path, 
                target_path,
                processing_function=raises_exception
            )
            
            assert success is False
            assert error is not None
            assert "test exception" in error.lower()
            assert output_path is None
            
            # The source file should still exist (no deletion on error)
            assert os.path.exists(source_path)
            
            # The target file should not exist
            assert not os.path.exists(target_path)
        finally:
            # Clean up
            if os.path.exists(source_path):
                os.unlink(source_path)
            if os.path.exists(target_path):
                os.unlink(target_path)