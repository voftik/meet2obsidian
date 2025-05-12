import os
import json
import pytest
import logging
import tempfile
from unittest.mock import patch, MagicMock, call
import structlog

# Путь к тестируемому модулю, который будет создан в следующем эпике
# В стиле "сначала тесты", мы пишем тесты перед реализацией
from meet2obsidian.utils.logging import setup_logging, get_logger


class TestLoggingSetup:
    """Тесты для настройки системы логирования."""

    def test_setup_logging_default_parameters(self):
        """Тест настройки логирования с параметрами по умолчанию."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_stream_handler, \
             patch('logging.FileHandler') as mock_file_handler:
            
            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger
            
            # Вызываем функцию настройки логирования
            logger = setup_logging()
            
            # Проверяем, что структурированное логирование настроено
            mock_configure.assert_called_once()
            
            # Проверяем, что корневой логгер получен и настроен
            mock_get_logger.assert_called_once_with('')  # Корневой логгер
            mock_root_logger.setLevel.assert_called_once()
            
            # Проверяем, что создан хотя бы один обработчик (консольный)
            mock_stream_handler.assert_called_once()
            
            # Проверяем, что функция вернула валидный логгер
            assert logger is not None
    
    def test_setup_logging_with_file_output(self):
        """Тест настройки логирования с выводом в файл."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.handlers.RotatingFileHandler') as mock_file_handler, \
             patch('os.makedirs') as mock_makedirs:
            
            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger
            
            # Создаем временную директорию для тестов
            with tempfile.TemporaryDirectory() as temp_dir:
                log_file = os.path.join(temp_dir, "meet2obsidian.log")
                
                # Вызываем функцию настройки логирования с путем к файлу логов
                logger = setup_logging(log_file=log_file)
                
                # Проверяем, что директория для логов создана
                mock_makedirs.assert_called_once_with(os.path.dirname(log_file), exist_ok=True)
                
                # Проверяем, что создан обработчик для файла
                mock_file_handler.assert_called_once()
                
                # Проверяем, что обработчик добавлен к корневому логгеру
                assert mock_root_logger.addHandler.called
    
    def test_setup_logging_with_custom_level(self):
        """Тест настройки логирования с указанием уровня логирования."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger:
            
            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger
            
            # Вызываем функцию настройки логирования с кастомным уровнем
            logger = setup_logging(log_level="DEBUG")
            
            # Проверяем, что уровень логирования установлен правильно
            mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)
    
    def test_setup_logging_with_invalid_level(self):
        """Тест настройки логирования с неправильным уровнем логирования."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger:
            
            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger
            
            # Вызываем функцию настройки логирования с некорректным уровнем
            # Ожидаем, что будет использован уровень по умолчанию (INFO)
            logger = setup_logging(log_level="INVALID_LEVEL")
            
            # Проверяем, что уровень логирования установлен на INFO
            mock_root_logger.setLevel.assert_called_once_with(logging.INFO)
    
    def test_setup_logging_with_rotation(self):
        """Тест настройки логирования с ротацией файлов."""
        with patch('structlog.configure'), \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.handlers.RotatingFileHandler') as mock_rotating_handler, \
             patch('os.makedirs'):
            
            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger
            
            # Вызываем функцию настройки логирования с параметрами ротации
            log_file = "/tmp/meet2obsidian.log"
            max_bytes = 10 * 1024 * 1024  # 10 MB
            backup_count = 5
            
            logger = setup_logging(
                log_file=log_file,
                max_bytes=max_bytes,
                backup_count=backup_count
            )
            
            # Проверяем, что RotatingFileHandler создан с правильными параметрами
            mock_rotating_handler.assert_called_once_with(
                log_file, 
                maxBytes=max_bytes, 
                backupCount=backup_count,
                encoding='utf-8'
            )
    
    def test_setup_logging_processors_configuration(self):
        """Тест настройки процессоров structlog."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger'):
            
            # Вызываем функцию настройки логирования
            logger = setup_logging()
            
            # Получаем аргументы вызова configure
            configure_args = mock_configure.call_args[1]
            
            # Проверяем наличие необходимых ключей в конфигурации
            assert 'processors' in configure_args
            assert 'formatters' in configure_args or 'renderer' in configure_args
            
            # Проверяем, что для формата JSON настроены соответствующие процессоры
            processors = configure_args['processors']
            assert any('TimeStamper' in str(p) for p in processors) or \
                   any(hasattr(p, 'processor') and 'TimeStamper' in str(p.processor) for p in processors)
            
            # Проверяем, что JSON рендерер присутствует
            assert any('JSONRenderer' in str(p) for p in processors) or \
                   any('format_json' in str(p) for p in processors)


class TestLoggerFunctions:
    """Тесты для функций создания и использования логгеров."""

    def test_get_logger_returns_configured_logger(self):
        """Тест получения настроенного логгера."""
        with patch('structlog.getLogger') as mock_structlog_get_logger:
            # Настраиваем мок
            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Вызываем функцию получения логгера
            logger = get_logger("test_module")

            # Проверяем, что логгер был получен с правильным именем
            mock_structlog_get_logger.assert_called_once_with("test_module")

            # Проверяем, что логгер является валидным объектом
            assert logger is mock_logger

    def test_get_logger_with_context(self):
        """Тест получения логгера с контекстными данными."""
        with patch('structlog.getLogger') as mock_structlog_get_logger:
            # Настраиваем мок с методом bind
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_structlog_get_logger.return_value = mock_logger

            # Контекстные данные
            context = {"component": "auth", "user_id": "12345"}

            # Вызываем функцию получения логгера с контекстом
            logger = get_logger("test_module", **context)

            # Проверяем, что bind был вызван с правильными аргументами
            mock_logger.bind.assert_called_once_with(**context)

            # Проверяем, что возвращен привязанный логгер
            assert logger is mock_bound_logger

    def test_log_message_formatting(self):
        """Тест форматирования сообщений логов."""
        # Так как structlog обычно настраивается с форматированием в конфигурации,
        # используем mock для проверки вызова методов

        with patch('structlog.getLogger') as mock_structlog_get_logger:
            # Настраиваем мок
            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Получаем логгер
            logger = get_logger("test_module")

            # Логируем сообщение
            logger.info("Test message", extra_field="extra_value")

            # Проверяем, что info был вызван с правильными аргументами
            mock_logger.info.assert_called_once_with("Test message", extra_field="extra_value")


class TestLoggingLevels:
    """Тесты для проверки различных уровней логирования."""

    def test_debug_level_logging(self):
        """Тест логирования на уровне DEBUG."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('structlog.getLogger') as mock_structlog_get_logger:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Настраиваем логирование на уровне DEBUG
            setup_logging(log_level="DEBUG")

            # Получаем логгер и выполняем логирование
            logger = get_logger("test_module")
            logger.debug("Debug message")

            # Проверяем, что debug был вызван
            mock_logger.debug.assert_called_once_with("Debug message")

            # Проверяем, что корневой логгер установлен на DEBUG
            mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)

    def test_info_level_logging(self):
        """Тест логирования на уровне INFO."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('structlog.getLogger') as mock_structlog_get_logger:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Настраиваем логирование на уровне INFO (по умолчанию)
            setup_logging()

            # Получаем логгер и выполняем логирование
            logger = get_logger("test_module")
            logger.info("Info message")
            logger.debug("This should not be logged")

            # Проверяем, что info был вызван
            mock_logger.info.assert_called_once_with("Info message")

            # Проверяем, что корневой логгер установлен на INFO
            mock_root_logger.setLevel.assert_called_once_with(logging.INFO)

    def test_warning_level_logging(self):
        """Тест логирования на уровне WARNING."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('structlog.getLogger') as mock_structlog_get_logger:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Настраиваем логирование на уровне WARNING
            setup_logging(log_level="WARNING")

            # Получаем логгер и выполняем логирование
            logger = get_logger("test_module")
            logger.warning("Warning message")
            logger.info("This should not be logged")

            # Проверяем, что warning был вызван
            mock_logger.warning.assert_called_once_with("Warning message")

            # Проверяем, что корневой логгер установлен на WARNING
            mock_root_logger.setLevel.assert_called_once_with(logging.WARNING)

    def test_error_level_logging(self):
        """Тест логирования на уровне ERROR."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('structlog.getLogger') as mock_structlog_get_logger:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Настраиваем логирование на уровне ERROR
            setup_logging(log_level="ERROR")

            # Получаем логгер и выполняем логирование
            logger = get_logger("test_module")
            logger.error("Error message")
            logger.warning("This should not be logged")

            # Проверяем, что error был вызван
            mock_logger.error.assert_called_once_with("Error message")

            # Проверяем, что корневой логгер установлен на ERROR
            mock_root_logger.setLevel.assert_called_once_with(logging.ERROR)

    def test_critical_level_logging(self):
        """Тест логирования на уровне CRITICAL."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('structlog.getLogger') as mock_structlog_get_logger:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Настраиваем логирование на уровне CRITICAL
            setup_logging(log_level="CRITICAL")

            # Получаем логгер и выполняем логирование
            logger = get_logger("test_module")
            logger.critical("Critical message")
            logger.error("This should not be logged")

            # Проверяем, что critical был вызван
            mock_logger.critical.assert_called_once_with("Critical message")

            # Проверяем, что корневой логгер установлен на CRITICAL
            mock_root_logger.setLevel.assert_called_once_with(logging.CRITICAL)

    def test_log_level_inheritance(self):
        """Тест наследования уровней логирования для вложенных логгеров."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger:

            # Настраиваем моки для корневого логгера
            mock_root_logger = MagicMock()

            # Настраиваем моки для вложенных логгеров
            mock_child_logger = MagicMock()

            # Словарь для хранения созданных логгеров
            loggers = {
                '': mock_root_logger,
                'meet2obsidian': mock_child_logger
            }

            # Мокаем getLogger, чтобы возвращать разные логгеры в зависимости от имени
            def mock_get_logger_func(name=''):
                return loggers.get(name, MagicMock())

            mock_get_logger.side_effect = mock_get_logger_func

            # Настраиваем логирование
            setup_logging(log_level="INFO")

            # Проверяем, что корневой логгер установлен на INFO
            mock_root_logger.setLevel.assert_called_once_with(logging.INFO)

            # Получаем логгер для модуля и проверяем, что он наследует уровень логирования
            # В реальной реализации такое наследование происходит автоматически через иерархию логгеров,
            # но в мокируемом окружении мы просто проверяем взаимодействие с API логирования


class TestLogRotation:
    """Тесты для проверки ротации логов."""

    def test_log_rotation_setup(self):
        """Тест настройки ротации логов."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.handlers.RotatingFileHandler') as mock_rotating_handler, \
             patch('os.makedirs') as mock_makedirs:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger
            mock_handler = MagicMock()
            mock_rotating_handler.return_value = mock_handler

            # Параметры ротации
            log_file = "/tmp/test/meet2obsidian.log"
            max_bytes = 5 * 1024 * 1024  # 5 MB
            backup_count = 3

            # Настраиваем логирование с ротацией
            setup_logging(
                log_file=log_file,
                max_bytes=max_bytes,
                backup_count=backup_count
            )

            # Проверяем, что директория для логов создана
            mock_makedirs.assert_called_once_with(os.path.dirname(log_file), exist_ok=True)

            # Проверяем, что создан RotatingFileHandler с правильными параметрами
            mock_rotating_handler.assert_called_once_with(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )

            # Проверяем, что обработчик добавлен к корневому логгеру
            mock_root_logger.addHandler.assert_called_with(mock_handler)

    def test_log_rotation_default_values(self):
        """Тест настройки ротации логов со значениями по умолчанию."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.handlers.RotatingFileHandler') as mock_rotating_handler, \
             patch('os.makedirs') as mock_makedirs:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            # Настраиваем логирование с файлом, но без явных параметров ротации
            log_file = "/tmp/meet2obsidian.log"
            setup_logging(log_file=log_file)

            # Проверяем, что RotatingFileHandler создан с параметрами по умолчанию
            # (предполагаем, что значения по умолчанию будут 10MB и 5 файлов)
            mock_rotating_handler.assert_called_once()
            args, kwargs = mock_rotating_handler.call_args

            # Проверяем путь к файлу
            assert args[0] == log_file

            # Проверяем, что параметры ротации присутствуют
            assert 'maxBytes' in kwargs
            assert 'backupCount' in kwargs

    def test_log_rotation_with_no_rotation(self):
        """Тест настройки логирования без ротации."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.FileHandler') as mock_file_handler, \
             patch('logging.handlers.RotatingFileHandler') as mock_rotating_handler, \
             patch('os.makedirs') as mock_makedirs:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger
            mock_handler = MagicMock()
            mock_file_handler.return_value = mock_handler

            # Настраиваем логирование с явным отключением ротации
            log_file = "/tmp/meet2obsidian.log"
            setup_logging(log_file=log_file, rotate_logs=False)

            # Проверяем, что создан обычный FileHandler вместо RotatingFileHandler
            mock_file_handler.assert_called_once_with(log_file, encoding='utf-8')
            mock_rotating_handler.assert_not_called()

            # Проверяем, что обработчик добавлен к корневому логгеру
            mock_root_logger.addHandler.assert_called_with(mock_handler)

    def test_log_rotation_large_file_size(self):
        """Тест настройки ротации логов с большим размером файла."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger') as mock_get_logger, \
             patch('logging.handlers.RotatingFileHandler') as mock_rotating_handler, \
             patch('os.makedirs') as mock_makedirs:

            # Настраиваем моки
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            # Параметры ротации с большим размером файла
            log_file = "/tmp/meet2obsidian.log"
            max_bytes = 1024 * 1024 * 1024  # 1 GB
            backup_count = 2

            # Настраиваем логирование с ротацией
            setup_logging(
                log_file=log_file,
                max_bytes=max_bytes,
                backup_count=backup_count
            )

            # Проверяем, что RotatingFileHandler создан с правильными параметрами
            mock_rotating_handler.assert_called_once_with(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )


class TestStructuredLogging:
    """Тесты для проверки структурированного логирования."""

    def test_structured_logging_format(self):
        """Тест формата структурированных логов (JSON)."""
        with patch('structlog.configure') as mock_configure, \
             patch('logging.getLogger'), \
             patch('structlog.getLogger') as mock_structlog_get_logger:

            # Настраиваем моки
            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Настраиваем логирование
            setup_logging()

            # Получаем аргументы вызова configure
            configure_args = mock_configure.call_args[1]

            # Проверяем наличие процессора JSON
            assert 'processors' in configure_args
            processors = configure_args['processors']
            assert any('JSONRenderer' in str(p) for p in processors) or \
                   any('json' in str(p).lower() for p in processors)

    def test_structured_log_with_context(self):
        """Тест логирования с контекстными данными."""
        with patch('structlog.getLogger') as mock_structlog_get_logger:
            # Настраиваем моки
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_structlog_get_logger.return_value = mock_logger

            # Контекстные данные
            context = {
                "request_id": "abc123",
                "user_id": 42,
                "component": "api"
            }

            # Получаем логгер с контекстом
            logger = get_logger("test_module", **context)

            # Логируем сообщение с дополнительными данными
            logger.info("API request received", path="/api/users", method="GET")

            # Проверяем, что логгер был привязан к контексту
            mock_logger.bind.assert_called_once_with(**context)

            # Проверяем, что info был вызван с дополнительными данными
            mock_bound_logger.info.assert_called_once_with(
                "API request received", path="/api/users", method="GET"
            )

    def test_nested_context_binding(self):
        """Тест добавления вложенных контекстов."""
        with patch('structlog.getLogger') as mock_structlog_get_logger:
            # Настраиваем моки для имитации цепочки bind
            mock_logger = MagicMock()
            mock_bound_logger1 = MagicMock()
            mock_bound_logger2 = MagicMock()

            mock_logger.bind.return_value = mock_bound_logger1
            mock_bound_logger1.bind.return_value = mock_bound_logger2

            mock_structlog_get_logger.return_value = mock_logger

            # Получаем логгер с первым контекстом
            logger1 = get_logger("test_module", request_id="abc123")

            # Добавляем второй контекст
            logger2 = logger1.bind(user_id=42)

            # Логируем сообщение
            logger2.info("User authenticated")

            # Проверяем, что первый bind был вызван с первым контекстом
            mock_logger.bind.assert_called_once_with(request_id="abc123")

            # Проверяем, что второй bind был вызван со вторым контекстом
            mock_bound_logger1.bind.assert_called_once_with(user_id=42)

            # Проверяем, что info был вызван на финальном логгере
            mock_bound_logger2.info.assert_called_once_with("User authenticated")

    def test_structured_error_logging(self):
        """Тест структурированного логирования ошибок с контекстом исключения."""
        with patch('structlog.getLogger') as mock_structlog_get_logger:
            # Настраиваем моки
            mock_logger = MagicMock()
            mock_structlog_get_logger.return_value = mock_logger

            # Получаем логгер
            logger = get_logger("test_module")

            # Создаем исключение для логирования
            try:
                raise ValueError("Test error")
            except ValueError as e:
                # Логируем ошибку со структурированным контекстом
                logger.error(
                    "Error occurred",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=True  # В реальной реализации здесь будет строка трассировки
                )

            # Проверяем правильность вызова метода error
            mock_logger.error.assert_called_once()
            args, kwargs = mock_logger.error.call_args

            # Проверяем сообщение
            assert args[0] == "Error occurred"

            # Проверяем контекст ошибки
            assert kwargs["error_type"] == "ValueError"
            assert kwargs["error_message"] == "Test error"
            assert kwargs["traceback"] is True


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])