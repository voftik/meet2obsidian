import os
import json
import logging
import commentjson
from typing import Dict, Any, List, Optional, Union

class ConfigError(Exception):
    """Исключение для ошибок конфигурации."""
    pass

class ConfigManager:
    """
    Управляет конфигурацией приложения meet2obsidian.
    Предоставляет методы для загрузки, сохранения и доступа к настройкам.
    """
    
    def __init__(self, config_path: str, logger=None):
        """
        Инициализирует ConfigManager с путем к файлу конфигурации.
        
        Args:
            config_path (str): Путь к файлу конфигурации
            logger (logging.Logger): Опциональный объект логгера
        """
        self.config_path = config_path
        self.logger = logger or logging.getLogger(__name__)
        self.config = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        Загружает конфигурацию из файла. Если файл не существует или 
        содержит ошибки, создает и возвращает конфигурацию по умолчанию.
        
        Returns:
            dict: Загруженная конфигурация или конфигурация по умолчанию
        """
        try:
            # Проверяем существование файла конфигурации
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Файл конфигурации не существует: {self.config_path}")
                # Создаем директории для файла конфигурации, если они не существуют
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                # Создаем конфигурацию по умолчанию и сохраняем ее
                default_config = self._create_default_config()
                self.save_config(default_config)
                self.config = default_config
                return default_config
            
            # Загружаем конфигурацию из файла
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
                # Проверяем наличие содержимого
                if not file_content.strip():
                    self.logger.warning(f"Файл конфигурации пуст: {self.config_path}")
                    default_config = self._create_default_config()
                    self.save_config(default_config)
                    self.config = default_config
                    return default_config
                
                # Используем commentjson для поддержки комментариев в JSON
                try:
                    config = commentjson.loads(file_content)
                    self.logger.debug(f"Конфигурация успешно загружена из {self.config_path}")
                    self.config = config
                    return config
                except json.JSONDecodeError as e:
                    self.logger.error(f"Ошибка при разборе JSON: {str(e)}")
                    default_config = self._create_default_config()
                    self.config = default_config
                    return default_config
                
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке конфигурации: {str(e)}")
            default_config = self._create_default_config()
            self.config = default_config
            return default_config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохраняет конфигурацию в файл.
        
        Args:
            config (dict, optional): Конфигурация для сохранения. 
                                    Если None, сохраняет текущую конфигурацию.
            
        Returns:
            bool: True в случае успеха, False при ошибке
        """
        config_to_save = config if config is not None else self.config
        
        if config_to_save is None:
            self.logger.error("Нет конфигурации для сохранения")
            return False
        
        try:
            # Создаем директории для файла конфигурации, если они не существуют
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Сохраняем конфигурацию в файл
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            
            self.logger.debug(f"Конфигурация успешно сохранена в {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении конфигурации: {str(e)}")
            return False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Получает значение конфигурации по ключу. Ключ может быть вложенным путем с точками.
        Например: "paths.video_directory"
        
        Args:
            key (str): Ключ конфигурации
            default: Значение по умолчанию, возвращаемое если ключ не найден
            
        Returns:
            Значение конфигурации или значение по умолчанию, если ключ не найден
        """
        if self.config is None:
            self.load_config()
        
        # Разбиваем ключ на части
        key_parts = key.split('.')
        
        # Начинаем с корня конфигурации
        current = self.config
        
        # Проходим по частям ключа
        for part in key_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def set_value(self, key: str, value: Any) -> bool:
        """
        Устанавливает значение конфигурации по ключу. Ключ может быть вложенным путем с точками.
        Например: "paths.video_directory" = "/path/to/videos"
        
        Args:
            key (str): Ключ конфигурации
            value: Значение для установки
            
        Returns:
            bool: True в случае успеха, False при ошибке
        """
        if self.config is None:
            self.load_config()
        
        # Разбиваем ключ на части
        key_parts = key.split('.')
        
        # Начинаем с корня конфигурации
        current = self.config
        
        # Проходим по всем частям ключа кроме последней
        for part in key_parts[:-1]:
            # Если текущая часть не существует, создаем пустой словарь
            if part not in current:
                current[part] = {}
            # Если текущая часть не является словарем, не можем продолжить
            elif not isinstance(current[part], dict):
                self.logger.error(f"Невозможно установить значение для {key}: путь содержит не-словарь")
                return False
            
            current = current[part]
        
        # Устанавливаем значение для последней части ключа
        current[key_parts[-1]] = value
        
        # Сохраняем обновленную конфигурацию
        return self.save_config()
    
    def validate_config(self) -> List[str]:
        """
        Проверяет конфигурацию на наличие необходимых полей и корректность значений.
        
        Returns:
            list: Список сообщений об ошибках, пустой список если ошибок нет
        """
        if self.config is None:
            self.load_config()
        
        errors = []
        
        # Проверяем наличие основных разделов
        required_sections = ['paths', 'api', 'processing', 'system']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Отсутствует обязательный раздел: {section}")
        
        # Проверяем наличие и типы необходимых полей
        # Пути
        if 'paths' in self.config:
            if 'video_directory' not in self.config['paths']:
                errors.append("Отсутствует обязательное поле: paths.video_directory")
            if 'obsidian_vault' not in self.config['paths']:
                errors.append("Отсутствует обязательное поле: paths.obsidian_vault")
        
        # API
        if 'api' in self.config:
            # Rev.ai
            if 'rev_ai' not in self.config['api']:
                errors.append("Отсутствует обязательный раздел: api.rev_ai")
            else:
                if 'job_timeout' not in self.config['api']['rev_ai']:
                    errors.append("Отсутствует обязательное поле: api.rev_ai.job_timeout")
                elif not isinstance(self.config['api']['rev_ai']['job_timeout'], (int, float)):
                    errors.append("Поле api.rev_ai.job_timeout должно быть числом")
            
            # Claude
            if 'claude' not in self.config['api']:
                errors.append("Отсутствует обязательный раздел: api.claude")
            else:
                if 'model' not in self.config['api']['claude']:
                    errors.append("Отсутствует обязательное поле: api.claude.model")
                elif not isinstance(self.config['api']['claude']['model'], str):
                    errors.append("Поле api.claude.model должно быть строкой")
        
        # Проверяем типы других важных полей
        if 'processing' in self.config:
            if 'delete_video_files' in self.config['processing'] and not isinstance(self.config['processing']['delete_video_files'], bool):
                errors.append("Поле processing.delete_video_files должно быть логическим")
            if 'delete_audio_files' in self.config['processing'] and not isinstance(self.config['processing']['delete_audio_files'], bool):
                errors.append("Поле processing.delete_audio_files должно быть логическим")
        
        if 'system' in self.config:
            if 'autostart' in self.config['system'] and not isinstance(self.config['system']['autostart'], bool):
                errors.append("Поле system.autostart должно быть логическим")
        
        return errors
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Создает конфигурацию по умолчанию.
        
        Returns:
            dict: Конфигурация по умолчанию
        """
        # Значения по умолчанию
        return {
            "paths": {
                "video_directory": "",
                "obsidian_vault": ""
            },
            "api": {
                "rev_ai": {
                    "job_timeout": 3600,
                    "max_retries": 3
                },
                "claude": {
                    "model": "claude-3-opus-20240229",
                    "temperature": 0.1
                }
            },
            "processing": {
                "delete_video_files": True,
                "delete_audio_files": True,
                "max_video_duration": 14400  # 4 часа в секундах
            },
            "system": {
                "autostart": False,
                "loglevel": "info",
                "notifications": True
            }
        }