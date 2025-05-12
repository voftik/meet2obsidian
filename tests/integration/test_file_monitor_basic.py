"""
Simplified integration tests for FileMonitor functionality.

These tests focus on the most basic and reliable functionality without
being sensitive to timing issues that can cause failures in CI environments.
"""

import os
import time
import tempfile
import pytest
from unittest.mock import MagicMock

from meet2obsidian.monitor import FileMonitor

# Mark as integration test
pytestmark = [
    pytest.mark.integration
]

# Constants for tests
MIN_FILE_AGE_SECONDS = 5  # Minimum age for file stability


class TestFileMonitorBasicIntegration:
    """Basic integration tests for FileMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor_dir = os.path.join(self.temp_dir.name, "monitor")
        os.makedirs(self.monitor_dir, exist_ok=True)
        
        # Create a logger mock
        self.logger = MagicMock()
        
        # Create FileMonitor with test directory and short poll interval
        self.file_monitor = FileMonitor(
            directory=self.monitor_dir,
            file_patterns=["*.mp4", "*.txt"],  # Include txt for easier testing
            poll_interval=1,  # Very short polling interval for tests
            logger=self.logger
        )
        
        # Mock callback
        self.mock_callback = MagicMock()
        self.file_monitor.register_file_callback(self.mock_callback)
    
    def teardown_method(self):
        """Clean up test environment."""
        # Ensure the file monitor is stopped
        if hasattr(self, 'file_monitor') and self.file_monitor.is_monitoring:
            self.file_monitor.stop()
        
        # Clean up the temporary directory
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
    
    def test_start_stop(self):
        """Test starting and stopping the file monitor."""
        # Start the monitor
        result = self.file_monitor.start()
        assert result is True
        assert self.file_monitor.is_monitoring is True
        
        # Stop the monitor
        result = self.file_monitor.stop()
        assert result is True
        assert self.file_monitor.is_monitoring is False
    
    def test_direct_scanning(self):
        """Test direct call to scan_directory method."""
        # Create a test file
        test_file = os.path.join(self.monitor_dir, "test.mp4")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Wait for file to be stable
        time.sleep(MIN_FILE_AGE_SECONDS + 1)
        
        # Scan for files directly (no thread involved)
        new_files = self.file_monitor._scan_directory()
        
        # Verify file was found
        assert test_file in new_files
        assert test_file in self.file_monitor.observed_files
    
    def test_file_pattern_filtering_direct(self):
        """Test that only files matching patterns are detected."""
        # Create files with different extensions
        mp4_file = os.path.join(self.monitor_dir, "video.mp4")
        txt_file = os.path.join(self.monitor_dir, "document.txt")
        pdf_file = os.path.join(self.monitor_dir, "document.pdf")  # Should be ignored
        
        # Write content to all files
        for file_path in [mp4_file, txt_file, pdf_file]:
            with open(file_path, 'w') as f:
                f.write("Test content")
        
        # Wait for files to be stable
        time.sleep(MIN_FILE_AGE_SECONDS + 1)
        
        # Scan directly
        new_files = self.file_monitor._scan_directory()
        
        # Verify only mp4 and txt files are detected
        assert mp4_file in new_files
        assert txt_file in new_files
        assert pdf_file not in new_files
    
    def test_empty_file_skipping_direct(self):
        """Test that empty files are skipped."""
        # Create a normal and an empty file
        normal_file = os.path.join(self.monitor_dir, "normal.mp4")
        empty_file = os.path.join(self.monitor_dir, "empty.mp4")
        
        # Write content to normal file, leave empty file empty
        with open(normal_file, 'w') as f:
            f.write("Test content")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        # Wait for files to be stable
        time.sleep(MIN_FILE_AGE_SECONDS + 1)
        
        # Scan directly
        new_files = self.file_monitor._scan_directory()
        
        # Verify only non-empty file is detected
        assert normal_file in new_files
        assert empty_file not in new_files
        
        # But both files are in observed_files
        assert normal_file in self.file_monitor.observed_files
        assert empty_file in self.file_monitor.observed_files
    
    def test_too_recent_files_direct(self):
        """Test that too recent files are not yet considered stable."""
        test_file = os.path.join(self.monitor_dir, "recent.mp4")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Don't wait - file should be too fresh
        
        # Scan directly
        new_files = self.file_monitor._scan_directory()
        
        # File should be in observed_files but not in returned new files
        assert test_file in self.file_monitor.observed_files
        assert test_file not in new_files