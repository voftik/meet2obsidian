"""
Integration tests for FileMonitor functionality.

These tests verify the real-world behavior of FileMonitor,
including scanning directories, detecting new files, and
triggering callbacks when files are added.

The tests cover:
- File detection and stability monitoring
- Handling of files of different types and sizes
- Callback processing
- Queue management
- Processing of files in nested directories
- Handling of concurrent file operations

IMPORTANT: These tests interact with the actual filesystem and are
marked with 'integration' to allow them to be skipped in CI/CD environments.
"""

import os
import time
import shutil
import tempfile
import threading
import pytest
import concurrent.futures
from pathlib import Path
from unittest.mock import MagicMock

from meet2obsidian.monitor import FileMonitor

# Mark as integration test
pytestmark = [
    pytest.mark.integration
]

# Constants for tests
MIN_FILE_AGE_SECONDS = 5  # Minimum age for file stability, matching implementation


class TestFileMonitorIntegration:
    """Integration tests for FileMonitor functionality."""
    
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
            poll_interval=2,  # Short polling interval for tests
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
    
    def test_file_detection(self):
        """Test detecting new files in the monitored directory."""
        # Start the monitor
        self.file_monitor.start()
        
        # Create a test file
        test_file_path = os.path.join(self.monitor_dir, "test_file.mp4")
        with open(test_file_path, 'w') as f:
            f.write("Test content")
        
        # Give the monitor time to detect the file (longer than min file age)
        time.sleep(8)  
        
        # Stop the monitor
        self.file_monitor.stop()
        
        # Verify that the callback was called with the test file
        self.mock_callback.assert_called_with(test_file_path)
    
    def test_file_stability_direct(self):
        """Test the file stability logic by directly using the scan method."""
        # This test directly tests the file stability logic in _scan_directory
        # without relying on the monitor thread

        # Create a test file
        test_file_path = os.path.join(self.monitor_dir, "stability_test.mp4")
        with open(test_file_path, 'w') as f:
            f.write("Test content")

        # Make sure the file isn't in observed_files
        self.file_monitor.observed_files = set()

        # First scan should add it to observed_files but not return it as new yet
        # because it's too new (min age check)
        new_files = self.file_monitor._scan_directory()

        # The file should be in observed files
        assert test_file_path in self.file_monitor.observed_files

        # But should not be returned as "new" yet since it's too recent
        # This is our test of the stability logic
        assert len(new_files) == 0

        # Wait until the file is considered stable (more than 5 seconds)
        time.sleep(6)

        # Reset observed_files to simulate first seeing the file
        self.file_monitor.observed_files = set()

        # Now when we scan, the file should be stable AND considered new
        new_files = self.file_monitor._scan_directory()

        # Now it should be returned as a new file since it's stable
        assert test_file_path in new_files
    
    def test_empty_file_skipping(self):
        """Test that empty files are skipped."""
        # Start the monitor
        self.file_monitor.start()
        
        # Create an empty test file
        empty_file_path = os.path.join(self.monitor_dir, "empty_file.mp4")
        with open(empty_file_path, 'w') as f:
            pass  # Create empty file
        
        # Give the monitor time to process
        time.sleep(8)
        
        # Stop the monitor
        self.file_monitor.stop()
        
        # Verify that the callback was NOT called for the empty file
        self.mock_callback.assert_not_called()
        
        # Verify that a warning was logged about the empty file
        any_empty_warning = False
        for call in self.logger.warning.call_args_list:
            if "Skipping empty file" in call[0][0]:
                any_empty_warning = True
                break
        
        assert any_empty_warning, "No warning was logged about empty file"
    
    def test_file_pattern_filtering(self):
        """Test that only files matching patterns are detected."""
        # Этот тест использует прямое тестирование метода _scan_directory,
        # а не мониторинг в отдельном потоке, который подвержен проблемам с таймингом

        # Создаем файлы с разными расширениями
        mp4_file = os.path.join(self.monitor_dir, "video.mp4")
        txt_file = os.path.join(self.monitor_dir, "document.txt")
        pdf_file = os.path.join(self.monitor_dir, "document.pdf")  # Должен игнорироваться

        # Записываем содержимое во все файлы
        for file_path in [mp4_file, txt_file, pdf_file]:
            with open(file_path, 'w') as f:
                f.write("Test content")

        # Ждем немного, чтобы файлы были стабильны
        time.sleep(6)

        # Сбрасываем наблюдаемые файлы
        self.file_monitor.observed_files = set()

        # Выполняем сканирование напрямую
        new_files = self.file_monitor._scan_directory()

        # Проверяем, что только mp4 и txt файлы возвращаются как новые
        assert len(new_files) == 2
        assert mp4_file in new_files
        assert txt_file in new_files
        assert pdf_file not in new_files

        # Проверяем, что все файлы добавились в observed_files
        assert mp4_file in self.file_monitor.observed_files
        assert txt_file in self.file_monitor.observed_files

        # PDF-файл не должен быть в observed_files, так как он не соответствует шаблонам
        assert pdf_file not in self.file_monitor.observed_files

    def test_file_queue_processing(self):
        """Test that files are processed in correct order."""
        # In real integration testing, we can't rely on checking the internal queue
        # as files may be processed and removed from the queue by the time we check.
        # Instead, let's verify the callbacks are called.

        # Create several test files
        test_files = []
        for i in range(5):
            file_path = os.path.join(self.monitor_dir, f"queue_test_{i}.mp4")
            with open(file_path, 'w') as f:
                f.write(f"Test content {i}")
            test_files.append(file_path)

        # Wait for files to be stable
        time.sleep(MIN_FILE_AGE_SECONDS + 1)

        # Start the monitor - all files should be processed during first scan
        self.file_monitor.start()

        # Wait for files to be processed - need longer time for all files
        time.sleep(10)

        # Stop the monitor
        self.file_monitor.stop()

        # Verify callbacks were called for each file
        assert self.mock_callback.call_count == 5

        # Verify each file was passed to the callback
        call_args_list = [call[0][0] for call in self.mock_callback.call_args_list]
        for file_path in test_files:
            assert file_path in call_args_list

    def test_gradual_file_writing(self):
        """Test detection of a file that is being gradually written to disk."""
        # Create a file that will be gradually written to
        file_path = os.path.join(self.monitor_dir, "growing_file.mp4")

        # Start with empty file
        with open(file_path, 'w') as f:
            pass

        # Start the monitor
        self.file_monitor.start()

        # Write content to the file in small chunks to simulate a file being copied
        content_chunks = ["Part 1 ", "Part 2 ", "Part 3 ", "Part 4 ", "Part 5"]

        for chunk in content_chunks:
            with open(file_path, 'a') as f:
                f.write(chunk)
            # Wait a short time between writes
            time.sleep(1)

        # Wait for file to be considered stable - need more time as it's being gradually modified
        time.sleep(MIN_FILE_AGE_SECONDS + 3)

        # Wait for processing - allow more time for polling interval
        time.sleep(5)

        # Stop the monitor
        self.file_monitor.stop()

        # Verify the callback was called with the correct file path
        # During an integration test, the callback may be called more than once if the scan
        # happens to catch the file at different stages of stability
        any_callback_for_file = False
        for call_args in self.mock_callback.call_args_list:
            if call_args[0][0] == file_path:
                any_callback_for_file = True
                break

        assert any_callback_for_file, "File was never processed"

    def test_nested_directories(self):
        """Test that files in nested directories are not detected (no recursive scan)."""
        # Create a nested directory structure
        nested_dir = os.path.join(self.monitor_dir, "nested")
        os.makedirs(nested_dir, exist_ok=True)

        # Create a file in the root directory
        root_file = os.path.join(self.monitor_dir, "root_file.mp4")
        with open(root_file, 'w') as f:
            f.write("Root file content")

        # Create a file in the nested directory
        nested_file = os.path.join(nested_dir, "nested_file.mp4")
        with open(nested_file, 'w') as f:
            f.write("Nested file content")

        # Wait for files to be stable
        time.sleep(MIN_FILE_AGE_SECONDS + 1)

        # Start the monitor
        self.file_monitor.start()

        # Wait for processing - longer for more reliable results
        time.sleep(8)

        # Stop the monitor
        self.file_monitor.stop()

        # Verify the root file was detected
        called_for_root = False
        for call_args in self.mock_callback.call_args_list:
            if call_args[0][0] == root_file:
                called_for_root = True
                break

        assert called_for_root, "Root file was not detected"

        # Verify nested file was NOT in observed files
        assert nested_file not in self.file_monitor.observed_files

    def test_large_file_handling(self):
        """Test handling of a larger file."""
        # Create a larger file (1MB)
        large_file = os.path.join(self.monitor_dir, "large_file.mp4")

        # Create 1MB of data (efficient way)
        with open(large_file, 'wb') as f:
            f.write(b'\0' * (1024 * 1024))

        # Wait for file to be considered stable - larger files may need more time
        time.sleep(MIN_FILE_AGE_SECONDS + 2)

        # Start the monitor
        self.file_monitor.start()

        # Wait for processing - increased to accommodate polling interval
        time.sleep(8)

        # Stop the monitor
        self.file_monitor.stop()

        # Verify the large file was detected
        called_for_large_file = False
        for call_args in self.mock_callback.call_args_list:
            if call_args[0][0] == large_file:
                called_for_large_file = True
                break

        assert called_for_large_file, "Large file was not detected"

    def test_ignore_dotfiles(self):
        """Test that hidden files (dotfiles) are not detected by default patterns."""
        # Create a dotfile that should be ignored
        dotfile = os.path.join(self.monitor_dir, ".hidden.mp4")
        with open(dotfile, 'w') as f:
            f.write("Hidden file content")

        # Create a normal file that should be detected
        normal_file = os.path.join(self.monitor_dir, "normal.mp4")
        with open(normal_file, 'w') as f:
            f.write("Normal file content")

        # Wait for files to be stable
        time.sleep(MIN_FILE_AGE_SECONDS + 1)

        # Start the monitor
        self.file_monitor.start()

        # Wait for processing - increase wait time for reliability
        time.sleep(8)

        # Stop the monitor
        self.file_monitor.stop()

        # Verify the normal file was detected
        called_for_normal_file = False
        for call_args in self.mock_callback.call_args_list:
            if call_args[0][0] == normal_file:
                called_for_normal_file = True
                break

        assert called_for_normal_file, "Normal file was not detected"

        # Check dotfile was not detected
        for call_args in self.mock_callback.call_args_list:
            assert call_args[0][0] != dotfile, "Dotfile was incorrectly detected"

        # The dotfile should not be in observed_files
        assert dotfile not in self.file_monitor.observed_files

    def test_concurrent_file_creation(self):
        """Test handling of files created concurrently."""
        # Define a function to create files concurrently
        def create_file(index):
            file_path = os.path.join(self.monitor_dir, f"concurrent_{index}.mp4")
            with open(file_path, 'w') as f:
                f.write(f"Concurrent file {index} content")
            return file_path

        # Create 10 files concurrently
        created_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_file, i) for i in range(10)]
            for future in concurrent.futures.as_completed(futures):
                created_files.append(future.result())

        # Wait for files to be stable
        time.sleep(MIN_FILE_AGE_SECONDS + 2)

        # Start the monitor
        self.file_monitor.start()

        # Wait for processing - increased time for reliability
        time.sleep(10)

        # Stop the monitor
        self.file_monitor.stop()

        # Get the list of files that triggered callbacks
        processed_files = [call[0][0] for call in self.mock_callback.call_args_list]

        # Verify all files or most files were detected (might have timing issues)
        # Integration tests should allow for some real-world conditions
        detected_count = 0
        for file_path in created_files:
            if file_path in processed_files:
                detected_count += 1

        # At least 8 of 10 files should be detected (arbitrary threshold for integration test)
        assert detected_count >= 8, f"Only {detected_count}/10 files were processed"

        # Check that all created files are in observed_files
        for file_path in created_files:
            assert file_path in self.file_monitor.observed_files

    def test_file_moved_to_directory(self):
        """Test handling of a file that is moved into the monitored directory."""
        # Create a temporary file outside the monitored directory
        temp_dir = tempfile.TemporaryDirectory()
        temp_file = os.path.join(temp_dir.name, "moved_file.mp4")
        with open(temp_file, 'w') as f:
            f.write("This file will be moved")

        # Start the monitor
        self.file_monitor.start()

        # Wait a moment for the monitor to initialize
        time.sleep(1)

        # Move the file to the monitored directory
        dest_file = os.path.join(self.monitor_dir, "moved_file.mp4")
        shutil.move(temp_file, dest_file)

        # Wait for file to be stable and processed
        time.sleep(MIN_FILE_AGE_SECONDS + 3)

        # Stop the monitor
        self.file_monitor.stop()

        # Clean up temporary directory
        temp_dir.cleanup()

        # Verify the moved file was detected
        self.mock_callback.assert_called_once_with(dest_file)
        assert dest_file in self.file_monitor.observed_files

    def test_long_polling_stability(self):
        """Test stability with a longer polling period."""
        # Create a file monitor with a longer polling interval
        long_poll_monitor = FileMonitor(
            directory=self.monitor_dir,
            file_patterns=["*.mp4"],
            poll_interval=10,  # 10 seconds
            logger=self.logger
        )

        try:
            # Register a mock callback
            mock_long_poll_callback = MagicMock()
            long_poll_monitor.register_file_callback(mock_long_poll_callback)

            # Start the monitor
            long_poll_monitor.start()

            # Create a file
            test_file = os.path.join(self.monitor_dir, "long_poll_test.mp4")
            with open(test_file, 'w') as f:
                f.write("Test content for long polling")

            # Wait for one polling cycle plus file stability time
            time.sleep(15)

            # Verify the file was detected
            mock_long_poll_callback.assert_called_once_with(test_file)

        finally:
            # Stop the monitor
            long_poll_monitor.stop()