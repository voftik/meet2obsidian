"""
Unit tests for FileMonitor implementation.

These tests focus on unit testing the FileMonitor class functionality
without requiring actual file system operations.
"""

import os
import time
import pytest
import threading
import queue
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from meet2obsidian.monitor import FileMonitor


class TestFileMonitorInit:
    """Tests for FileMonitor initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        logger_mock = MagicMock()
        monitor = FileMonitor(directory="/test/dir", logger=logger_mock)

        assert monitor.directory == "/test/dir"
        assert monitor.file_patterns == ["*.mp4", "*.mov", "*.webm", "*.mkv"]
        assert monitor.poll_interval == 60
        assert monitor.logger == logger_mock
        assert not monitor.is_monitoring
        assert isinstance(monitor._stop_event, threading.Event)
        assert monitor._monitor_thread is None
        assert isinstance(monitor._file_queue, queue.Queue)
        assert isinstance(monitor._processed_files, set)
        assert isinstance(monitor.observed_files, set)
        assert monitor.last_scan_time is None
        assert monitor._file_callback is None

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        logger_mock = MagicMock()
        monitor = FileMonitor(
            directory="/test/custom/dir",
            file_patterns=["*.avi", "*.mkv"],
            poll_interval=30,
            logger=logger_mock
        )

        assert monitor.directory == "/test/custom/dir"
        assert monitor.file_patterns == ["*.avi", "*.mkv"]
        assert monitor.poll_interval == 30
        assert monitor.logger == logger_mock

    def test_init_with_short_poll_interval(self):
        """Test that poll_interval is at least 5 seconds."""
        logger_mock = MagicMock()
        monitor = FileMonitor(
            directory="/test/dir",
            poll_interval=2,  # Too short, should be set to 5
            logger=logger_mock
        )

        assert monitor.poll_interval == 5

    def test_init_expands_home_directory(self):
        """Test that home directory is expanded."""
        logger_mock = MagicMock()
        
        with patch('os.path.abspath') as mock_abspath, \
             patch('os.path.expanduser') as mock_expanduser:
            
            mock_expanduser.return_value = "/Users/test/expanded/dir"
            mock_abspath.return_value = "/absolute/path/to/expanded/dir"
            
            monitor = FileMonitor(directory="~/test/dir", logger=logger_mock)
            
            mock_expanduser.assert_called_once_with("~/test/dir")
            mock_abspath.assert_called_once_with("/Users/test/expanded/dir")
            assert monitor.directory == "/absolute/path/to/expanded/dir"


class TestFileMonitorStartStop:
    """Tests for starting and stopping the FileMonitor."""

    def setup_method(self):
        """Set up test environment."""
        self.logger_mock = MagicMock()
        self.monitor = FileMonitor(directory="/test/dir", logger=self.logger_mock)

    @patch('os.path.exists')
    @patch('threading.Thread')
    def test_start_success(self, mock_thread, mock_exists):
        """Test successful start of the monitor."""
        mock_exists.return_value = True
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Mock _scan_directory to avoid actual filesystem operations
        self.monitor._scan_directory = MagicMock(return_value=[])
        
        result = self.monitor.start()
        
        assert result is True
        assert self.monitor.is_monitoring is True
        mock_exists.assert_called_once_with("/test/dir")
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        self.monitor._scan_directory.assert_called_once()

    @patch('os.path.exists')
    def test_start_directory_not_exists(self, mock_exists):
        """Test start when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = self.monitor.start()
        
        assert result is False
        assert self.monitor.is_monitoring is False
        mock_exists.assert_called_once_with("/test/dir")
        self.logger_mock.error.assert_called_once()

    @patch('os.path.exists')
    def test_start_already_running(self, mock_exists):
        """Test start when monitor is already running."""
        mock_exists.return_value = True
        self.monitor.is_monitoring = True
        self.monitor._scan_directory = MagicMock(return_value=[])

        result = self.monitor.start()

        assert result is True
        self.logger_mock.info.assert_called_with("File monitor is already running")

    @patch('threading.Thread')
    def test_start_exception(self, mock_thread):
        """Test start with exception."""
        mock_thread.side_effect = Exception("Test error")
        
        # Mock exists to return True
        with patch('os.path.exists', return_value=True):
            # Mock _scan_directory to avoid actual filesystem operations
            self.monitor._scan_directory = MagicMock(return_value=[])
            
            result = self.monitor.start()
            
            assert result is False
            assert self.monitor.is_monitoring is False
            self.logger_mock.error.assert_called_once()

    def test_stop_success(self):
        """Test successful stop of the monitor."""
        # Set up running monitor
        self.monitor.is_monitoring = True
        self.monitor._stop_event = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True  # Thread is alive
        self.monitor._monitor_thread = mock_thread

        result = self.monitor.stop()

        assert result is True
        assert self.monitor.is_monitoring is False
        self.monitor._stop_event.set.assert_called_once()
        mock_thread.join.assert_called_once_with(timeout=5)

    def test_stop_not_running(self):
        """Test stop when monitor is not running."""
        self.monitor.is_monitoring = False
        
        result = self.monitor.stop()
        
        assert result is True
        self.logger_mock.info.assert_called_with("File monitor is not running")

    def test_stop_thread_not_stopping(self):
        """Test stop when thread doesn't stop on time."""
        # Set up running monitor
        self.monitor.is_monitoring = True
        self.monitor._stop_event = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True  # Thread still alive after join
        self.monitor._monitor_thread = mock_thread
        
        result = self.monitor.stop()
        
        assert result is True  # Still returns True
        assert self.monitor.is_monitoring is False
        self.logger_mock.warning.assert_called_once_with("File monitor thread did not stop gracefully")

    def test_stop_exception(self):
        """Test stop with exception."""
        # Set up running monitor
        self.monitor.is_monitoring = True
        self.monitor._stop_event = MagicMock()
        self.monitor._stop_event.set.side_effect = Exception("Test error")
        
        result = self.monitor.stop()
        
        assert result is False
        self.logger_mock.error.assert_called_once()


class TestFileMonitorRegistration:
    """Tests for callback registration."""

    def setup_method(self):
        """Set up test environment."""
        self.logger_mock = MagicMock()
        self.monitor = FileMonitor(directory="/test/dir", logger=self.logger_mock)

    def test_register_file_callback(self):
        """Test registering a callback function."""
        callback_mock = MagicMock()
        
        self.monitor.register_file_callback(callback_mock)
        
        assert self.monitor._file_callback == callback_mock

    def test_register_multiple_callbacks(self):
        """Test registering multiple callbacks (last one wins)."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        self.monitor.register_file_callback(callback1)
        self.monitor.register_file_callback(callback2)
        
        assert self.monitor._file_callback == callback2
        assert self.monitor._file_callback != callback1


class TestFileMonitorStatus:
    """Tests for status reporting."""

    def setup_method(self):
        """Set up test environment."""
        self.logger_mock = MagicMock()
        self.monitor = FileMonitor(
            directory="/test/status/dir",
            file_patterns=["*.mp4", "*.avi"],
            logger=self.logger_mock
        )

    def test_get_status_not_running(self):
        """Test getting status when not running."""
        self.monitor._monitor_thread = None
        self.monitor._processed_files = set(["file1.mp4", "file2.mp4"])
        self.monitor._file_queue = queue.Queue()
        
        status = self.monitor.get_status()
        
        assert status["directory"] == "/test/status/dir"
        assert status["patterns"] == ["*.mp4", "*.avi"]
        assert status["running"] is False
        assert status["files_processed"] == 2
        assert status["pending_files"] == 0

    def test_get_status_running(self):
        """Test getting status when running."""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        self.monitor._monitor_thread = mock_thread
        self.monitor._processed_files = set(["file1.mp4", "file2.mp4", "file3.mp4"])
        
        # Add some files to the queue
        self.monitor._file_queue = queue.Queue()
        self.monitor._file_queue.put("file4.mp4")
        self.monitor._file_queue.put("file5.mp4")
        
        status = self.monitor.get_status()
        
        assert status["directory"] == "/test/status/dir"
        assert status["patterns"] == ["*.mp4", "*.avi"]
        assert status["running"] is True
        assert status["files_processed"] == 3
        assert status["pending_files"] == 2


class TestFileMonitorScanDirectory:
    """Tests for the directory scanning functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.logger_mock = MagicMock()
        self.monitor = FileMonitor(
            directory="/test/scan/dir",
            file_patterns=["*.mp4", "*.mov"],
            logger=self.logger_mock
        )

    @patch('glob.glob')
    @patch('os.path.getmtime')
    @patch('os.path.getsize')
    @patch('time.time')
    def test_scan_directory_new_files(self, mock_time, mock_getsize, mock_getmtime, mock_glob):
        """Test scanning directory for new files."""
        # Setup mocks
        mock_time.return_value = 1000.0  # Current time
        mock_glob.side_effect = [
            ["/test/scan/dir/file1.mp4", "/test/scan/dir/file2.mp4"],  # *.mp4 pattern
            ["/test/scan/dir/file3.mov"]  # *.mov pattern
        ]
        # All files are old enough (10 seconds old)
        mock_getmtime.return_value = 990.0
        # All files have content
        mock_getsize.return_value = 1024
        
        # Monitor has no observed files yet
        self.monitor.observed_files = set()
        
        # Run test
        result = self.monitor._scan_directory()
        
        # Verify
        assert len(result) == 3
        assert "/test/scan/dir/file1.mp4" in result
        assert "/test/scan/dir/file2.mp4" in result
        assert "/test/scan/dir/file3.mov" in result
        
        # Verify observed_files is updated
        assert len(self.monitor.observed_files) == 3
        assert "/test/scan/dir/file1.mp4" in self.monitor.observed_files
        assert "/test/scan/dir/file2.mp4" in self.monitor.observed_files
        assert "/test/scan/dir/file3.mov" in self.monitor.observed_files
        
        # Verify mock calls
        mock_glob.assert_any_call("/test/scan/dir/*.mp4")
        mock_glob.assert_any_call("/test/scan/dir/*.mov")

    @patch('glob.glob')
    @patch('os.path.getmtime')
    @patch('os.path.getsize')
    @patch('time.time')
    def test_scan_directory_no_new_files(self, mock_time, mock_getsize, mock_getmtime, mock_glob):
        """Test scanning directory with no new files."""
        # Setup mocks
        mock_time.return_value = 1000.0
        mock_glob.side_effect = [
            ["/test/scan/dir/file1.mp4", "/test/scan/dir/file2.mp4"],
            ["/test/scan/dir/file3.mov"]
        ]
        
        # All files are already observed
        self.monitor.observed_files = {
            "/test/scan/dir/file1.mp4", 
            "/test/scan/dir/file2.mp4", 
            "/test/scan/dir/file3.mov"
        }
        
        # Run test
        result = self.monitor._scan_directory()
        
        # Verify no new files found
        assert len(result) == 0
        
        # Observed files remain the same
        assert len(self.monitor.observed_files) == 3

    @patch('glob.glob')
    @patch('os.path.getmtime')
    @patch('os.path.getsize')
    @patch('time.time')
    def test_scan_directory_too_recent_files(self, mock_time, mock_getsize, mock_getmtime, mock_glob):
        """Test scanning directory with files that are too recent to process."""
        # This test verifies that files modified too recently are not returned as stable

        # Setup mocks
        mock_time.return_value = 1000.0
        # The order here doesn't matter - we'll control stability with getmtime
        mock_glob.side_effect = [
            ["/test/scan/dir/file1.mp4", "/test/scan/dir/file2.mp4"],
            []
        ]

        # Create a mapping to ensure consistent mtimes regardless of call order
        file_mtimes = {
            "/test/scan/dir/file1.mp4": 995.0,  # 5s old (min age is 5s) - stable
            "/test/scan/dir/file2.mp4": 998.0   # 2s old - too recent
        }

        # Use a custom side effect that returns mtime based on path
        def getmtime_side_effect(path):
            return file_mtimes.get(path, 990.0)

        mock_getmtime.side_effect = getmtime_side_effect
        mock_getsize.return_value = 1024

        # No observed files yet
        self.monitor.observed_files = set()

        # Run test
        result = self.monitor._scan_directory()

        # Verify only the stable file is returned
        assert len(result) == 1
        assert "/test/scan/dir/file1.mp4" in result
        assert "/test/scan/dir/file2.mp4" not in result

        # But both files are in observed_files
        assert len(self.monitor.observed_files) == 2
        assert "/test/scan/dir/file1.mp4" in self.monitor.observed_files
        assert "/test/scan/dir/file2.mp4" in self.monitor.observed_files

        # Debug log for too recent file
        self.logger_mock.debug.assert_called_once()

    @patch('glob.glob')
    @patch('os.path.getmtime')
    @patch('os.path.getsize')
    @patch('time.time')
    def test_scan_directory_empty_files(self, mock_time, mock_getsize, mock_getmtime, mock_glob):
        """Test scanning directory with empty files."""
        # Setup mocks
        mock_time.return_value = 1000.0
        mock_glob.side_effect = [
            ["/test/scan/dir/file1.mp4", "/test/scan/dir/empty.mp4"],
            []
        ]
        # Both files are old enough
        mock_getmtime.return_value = 990.0

        # Setup mock to return size properly - the order is important for FileMonitor
        # In the _scan_directory method, it processes files in the order they're returned from glob,
        # so we need to make sure the mock's behavior matches our test expectations.
        file_sizes = {
            "/test/scan/dir/file1.mp4": 1024,
            "/test/scan/dir/empty.mp4": 0
        }
        mock_getsize.side_effect = lambda path: file_sizes.get(path, 0)

        # No observed files yet
        self.monitor.observed_files = set()

        # Run test
        result = self.monitor._scan_directory()

        # Verify only the non-empty file is returned
        assert len(result) == 1
        assert "/test/scan/dir/file1.mp4" in result
        assert "/test/scan/dir/empty.mp4" not in result

        # But both files are in observed_files
        assert len(self.monitor.observed_files) == 2

        # Warning log for empty file
        self.logger_mock.warning.assert_called_once()

    @patch('glob.glob')
    @patch('os.path.getmtime')
    @patch('os.path.getsize')
    @patch('time.time')
    def test_scan_directory_file_error(self, mock_time, mock_getsize, mock_getmtime, mock_glob):
        """Test scanning directory with file that raises an error."""
        # Setup mocks
        mock_time.return_value = 1000.0
        mock_glob.side_effect = [
            ["/test/scan/dir/file1.mp4", "/test/scan/dir/error.mp4"],
            []
        ]

        # When FileMonitor._scan_directory processes files, it iterates through them.
        # We need to ensure the error happens for the second file, not the first.
        # Setup getmtime to succeed for first file and fail for second
        def getmtime_side_effect(path):
            if path == "/test/scan/dir/error.mp4":
                raise OSError("Test file error")
            return 990.0
        mock_getmtime.side_effect = getmtime_side_effect

        # Setup getsize to return valid size (only for the first file,
        # as the second will error before getsize is called)
        mock_getsize.return_value = 1024

        # No observed files yet
        self.monitor.observed_files = set()

        # Run test
        result = self.monitor._scan_directory()

        # Only the valid file should be returned
        assert len(result) == 1
        assert "/test/scan/dir/file1.mp4" in result

        # Both files are in observed_files (observed_files is updated with all files from glob)
        assert len(self.monitor.observed_files) == 2
        assert "/test/scan/dir/file1.mp4" in self.monitor.observed_files
        assert "/test/scan/dir/error.mp4" in self.monitor.observed_files

        # Warning log for the file with error
        self.logger_mock.warning.assert_called_once()

    @patch('glob.glob')
    def test_scan_directory_exception(self, mock_glob):
        """Test scanning directory with an exception."""
        # Setup mocks to raise an exception
        mock_glob.side_effect = Exception("Test scan exception")
        
        # Run test
        result = self.monitor._scan_directory()
        
        # Verify empty result due to exception
        assert len(result) == 0
        
        # Error log for the exception
        self.logger_mock.error.assert_called_once()


class TestFileMonitorLoop:
    """Tests for the monitoring loop."""

    def setup_method(self):
        """Set up test environment."""
        self.logger_mock = MagicMock()
        self.monitor = FileMonitor(
            directory="/test/loop/dir",
            poll_interval=5,
            logger=self.logger_mock
        )
        self.mock_callback = MagicMock()
        self.monitor.register_file_callback(self.mock_callback)
        
        # Mock _scan_directory to avoid actual filesystem operations
        self.monitor._scan_directory = MagicMock()
        
        # Setup stop event for controlled testing
        self.monitor._stop_event = MagicMock()
        # By default, set() returns False the first time, then True
        self.monitor._stop_event.is_set.side_effect = [False, True]

    def test_monitor_loop_processes_files(self):
        """Test that the monitor loop processes files properly."""
        # Return a list of files from scan
        self.monitor._scan_directory.return_value = [
            "/test/loop/dir/file1.mp4",
            "/test/loop/dir/file2.mp4"
        ]
        
        # Run the monitor loop
        self.monitor._monitor_loop()
        
        # Verify scan was called
        self.monitor._scan_directory.assert_called_once()
        
        # Verify both files were queued
        assert self.monitor._file_queue.qsize() == 2
        
        # Verify both files triggered callbacks
        assert self.mock_callback.call_count == 2
        self.mock_callback.assert_any_call("/test/loop/dir/file1.mp4")
        self.mock_callback.assert_any_call("/test/loop/dir/file2.mp4")
        
        # Verify loop waited for poll interval
        self.monitor._stop_event.wait.assert_called_once_with(5)

    def test_monitor_loop_no_files(self):
        """Test monitor loop with no files found."""
        # Return no files from scan
        self.monitor._scan_directory.return_value = []
        
        # Run the monitor loop
        self.monitor._monitor_loop()
        
        # Verify scan was called
        self.monitor._scan_directory.assert_called_once()
        
        # Verify no files were queued or processed
        assert self.monitor._file_queue.qsize() == 0
        self.mock_callback.assert_not_called()
        
        # Verify loop waited for poll interval
        self.monitor._stop_event.wait.assert_called_once_with(5)

    def test_monitor_loop_callback_exception(self):
        """Test monitor loop with callback that raises an exception."""
        # Return a file from scan
        self.monitor._scan_directory.return_value = ["/test/loop/dir/file1.mp4"]
        
        # Make callback raise an exception
        self.mock_callback.side_effect = Exception("Test callback exception")
        
        # Run the monitor loop
        self.monitor._monitor_loop()
        
        # Verify scan was called
        self.monitor._scan_directory.assert_called_once()
        
        # Verify file was queued
        assert self.monitor._file_queue.qsize() == 1
        
        # Verify callback was called despite exception
        self.mock_callback.assert_called_once_with("/test/loop/dir/file1.mp4")
        
        # Verify error was logged
        self.logger_mock.error.assert_called_once()
        
        # Verify loop still waited for poll interval
        self.monitor._stop_event.wait.assert_called_once_with(5)

    @patch('time.sleep')
    def test_monitor_loop_scan_exception(self, mock_sleep):
        """Test monitor loop with scan that raises an exception."""
        # Make scan raise an exception
        self.monitor._scan_directory.side_effect = Exception("Test scan exception")

        # Run the monitor loop
        self.monitor._monitor_loop()

        # Verify scan was attempted
        self.monitor._scan_directory.assert_called_once()

        # Verify no files were processed
        self.mock_callback.assert_not_called()

        # Verify error was logged
        self.logger_mock.error.assert_called_once()

        # Verify sleep was called for error recovery
        mock_sleep.assert_called_once_with(5)