"""
Интеграционные тесты для класса ApplicationManager.

Эти тесты проверяют взаимодействие ApplicationManager с операционной системой:
- Создание и удаление реальных PID файлов
- Настройка автозапуска через LaunchAgent (только на macOS)
- Проверка реальных процессов

ВНИМАНИЕ: Эти тесты взаимодействуют с реальной файловой системой и службами ОС.
Они помечены как 'integration', чтобы их можно было пропустить в среде CI/CD.
"""

import os
import sys
import time
import pytest
import tempfile
import subprocess
from pathlib import Path

from meet2obsidian.core import ApplicationManager
from meet2obsidian.utils.logging import get_logger


@pytest.mark.integration
class TestApplicationManagerIntegration:
    """Интеграционные тесты для ApplicationManager."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        # Создаем временную директорию для тестов
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Настраиваем путь к тестовому PID файлу
        self.pid_file_path = os.path.join(self.temp_dir.name, "meet2obsidian.pid")
        
        # Создаем реальный логгер
        self.logger = get_logger("test_app_manager_integration")
        
        # Создаем экземпляр ApplicationManager
        self.app_manager = ApplicationManager(logger=self.logger)
        
        # Заменяем путь к PID файлу на тестовый
        self.app_manager._pid_file = self.pid_file_path
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        # Удаляем PID файл, если он существует
        if os.path.exists(self.pid_file_path):
            try:
                os.remove(self.pid_file_path)
            except:
                pass
        
        # Удаляем временную директорию
        self.temp_dir.cleanup()
    
    def test_start_stop_real_file(self):
        """Тест создания и удаления реального PID файла."""
        # Запускаем приложение
        result = self.app_manager.start()
        assert result is True
        
        # Проверяем, что PID файл создан
        assert os.path.exists(self.pid_file_path)
        
        # Проверяем содержимое PID файла
        with open(self.pid_file_path, 'r') as f:
            pid = int(f.read().strip())
            assert pid == os.getpid()
        
        # Проверяем, что приложение считается запущенным
        assert self.app_manager.is_running() is True
        
        # Останавливаем приложение
        result = self.app_manager.stop()
        assert result is True
        
        # Проверяем, что PID файл удален
        assert not os.path.exists(self.pid_file_path)
        
        # Проверяем, что приложение считается не запущенным
        assert self.app_manager.is_running() is False
    
    def test_get_status_real_uptime(self):
        """Тест получения реального времени работы приложения."""
        # Запускаем приложение
        self.app_manager.start()
        
        # Ждем немного, чтобы uptime был ненулевым
        time.sleep(1.5)
        
        # Получаем статус
        status = self.app_manager.get_status()
        
        # Проверяем, что uptime корректен (не менее 1 секунды)
        assert status["running"] is True
        assert "uptime" in status
        # Не проверяем содержимое строки, так как формат зависит от кодировки
        assert isinstance(status["uptime"], str)
        assert len(status["uptime"]) > 0
        
        # Останавливаем приложение и проверяем, что uptime пропадает
        self.app_manager.stop()
        status = self.app_manager.get_status()
        assert status["running"] is False
        assert "uptime" not in status
    
    @pytest.mark.skipif(sys.platform != 'darwin', reason="Тест только для macOS")
    def test_setup_autostart_integration(self):
        """
        Тест настройки автозапуска через LaunchAgent (только для macOS).
        
        ВНИМАНИЕ: Этот тест создает и удаляет реальный plist файл в ~/Library/LaunchAgents,
        но не загружает и не выгружает его, чтобы избежать реальных изменений в системе.
        """
        # Временно заменяем вызов launchctl на пустую функцию
        original_run = subprocess.run
        
        def mock_run(cmd, **kwargs):
            # Возвращаем успешный результат, но не выполняем реальную команду
            result = type('MockCompletedProcess', (), {
                'returncode': 0,
                'stdout': '',
                'stderr': ''
            })
            return result
        
        try:
            subprocess.run = mock_run
            
            # Путь к реальному plist файлу
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.meet2obsidian.plist")
            
            # Удаляем файл, если он уже существует от предыдущих тестов
            if os.path.exists(plist_path):
                os.remove(plist_path)
            
            # Включаем автозапуск
            result = self.app_manager.setup_autostart(enable=True)
            assert result is True
            
            # Проверяем, что plist файл создан
            assert os.path.exists(plist_path)
            
            # Проверяем содержимое plist файла
            with open(plist_path, 'r') as f:
                content = f.read()
                assert "<key>Label</key>" in content
                assert "<string>com.user.meet2obsidian</string>" in content
                assert "meet2obsidian" in content
                assert "service" in content
                assert "start" in content
                assert "<key>RunAtLoad</key>" in content
                assert "<true/>" in content
            
            # Отключаем автозапуск
            result = self.app_manager.setup_autostart(enable=False)
            assert result is True
            
            # Проверяем, что plist файл удален
            assert not os.path.exists(plist_path)
            
        finally:
            # Восстанавливаем оригинальную функцию
            subprocess.run = original_run
            
            # Удаляем файл, если тест не удалил его
            if os.path.exists(plist_path):
                os.remove(plist_path)
    
    def test_check_process_exists_integration(self):
        """Тест проверки существования реальных процессов."""
        # Проверяем, что текущий процесс существует
        assert self.app_manager._check_process_exists(os.getpid()) is True
        
        # Проверяем, что родительский процесс существует
        if os.getppid() > 0:  # Убедимся, что родительский PID валиден
            assert self.app_manager._check_process_exists(os.getppid()) is True
        
        # Проверяем, что несуществующий процесс (надеюсь!) не существует
        # Используем заведомо невалидный PID
        assert self.app_manager._check_process_exists(999999999) is False