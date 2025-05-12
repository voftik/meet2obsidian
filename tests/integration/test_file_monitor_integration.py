"""
Integration tests for FileMonitor functionality.

These tests verify the real-world behavior of FileMonitor,
including scanning directories, detecting new files, and
triggering callbacks when files are added.

IMPORTANT: These tests interact with the actual filesystem and are
marked with 'integration' to allow them to be skipped in CI/CD environments.
"""

import os
import time
import shutil
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from meet2obsidian.monitor import FileMonitor

# Mark as integration test
pytestmark = [
    pytest.mark.integration
]


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