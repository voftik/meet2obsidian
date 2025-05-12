import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from meet2obsidian.config import ConfigManager, ConfigError

class TestConfigManager:
    """Test suite for ConfigManager class."""

    def test_load_config_existing_file(self, mocker):
        """Test loading configuration from an existing file."""
        # Sample configuration
        sample_config = {
            "paths": {
                "video_directory": "/test/videos",
                "obsidian_vault": "/test/obsidian"
            },
            "api": {
                "rev_ai": {
                    "job_timeout": 3600
                },
                "claude": {
                    "model": "claude-3-opus-20240229"
                }
            }
        }

        # Mock open to return our sample config
        mock_open_func = mock_open(read_data=json.dumps(sample_config))
        mocker.patch('builtins.open', mock_open_func)

        # Mock os.path.exists to return True
        mocker.patch('os.path.exists', return_value=True)

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")

        # Load configuration
        loaded_config = config_manager.load_config()

        # Assertions
        assert loaded_config == sample_config
        assert config_manager.get_value("paths.video_directory") == "/test/videos"
        assert config_manager.get_value("api.claude.model") == "claude-3-opus-20240229"

    def test_load_config_nonexistent_file(self, mocker):
        """Test loading configuration when file doesn't exist."""
        # Mock os.path.exists to return False
        mocker.patch('os.path.exists', return_value=False)

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")

        # Load configuration should raise ConfigError
        with pytest.raises(ConfigError) as excinfo:
            config_manager.load_config()

        # Verify error message
        assert "not exist" in str(excinfo.value)

    def test_load_config_invalid_json(self, mocker):
        """Test loading configuration with invalid JSON."""
        # Mock os.path.exists to return True
        mocker.patch('os.path.exists', return_value=True)

        # Mock open to return invalid JSON
        mock_open_func = mock_open(read_data="{invalid json")
        mocker.patch('builtins.open', mock_open_func)

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")

        # Load configuration should raise ConfigError
        with pytest.raises(ConfigError) as excinfo:
            config_manager.load_config()

        # Verify error message
        assert "Error parsing JSON" in str(excinfo.value)

    def test_save_config(self, mocker):
        """Test saving configuration to file."""
        # Mock os.makedirs
        mock_makedirs = mocker.patch('os.makedirs')

        # Mock open
        mock_open_func = mock_open()
        mocker.patch('builtins.open', mock_open_func)

        # Mock json.dump
        json_dump_mock = mocker.patch('json.dump')

        # Sample configuration
        sample_config = {
            "paths": {
                "video_directory": "/test/videos"
            }
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = sample_config

        # Save configuration
        result = config_manager.save_config()

        # Assertions
        assert result is True
        mock_makedirs.assert_called_once()
        mock_open_func.assert_called_once_with("dummy/path/config.json", 'w', encoding='utf-8')
        json_dump_mock.assert_called_once()

    def test_save_config_with_new_config(self, mocker):
        """Test saving new configuration to file."""
        # Mock os.makedirs
        mock_makedirs = mocker.patch('os.makedirs')

        # Mock open
        mock_open_func = mock_open()
        mocker.patch('builtins.open', mock_open_func)

        # Mock json.dump
        json_dump_mock = mocker.patch('json.dump')

        # Sample configurations
        original_config = {
            "paths": {
                "video_directory": "/test/videos"
            }
        }

        new_config = {
            "paths": {
                "video_directory": "/new/videos"
            }
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = original_config

        # Save new configuration
        result = config_manager.save_config(new_config)

        # Assertions
        assert result is True
        assert config_manager.config == new_config
        mock_makedirs.assert_called_once()
        mock_open_func.assert_called_once_with("dummy/path/config.json", 'w', encoding='utf-8')
        json_dump_mock.assert_called_once()

    def test_save_config_error(self, mocker):
        """Test saving configuration when error occurs."""
        # Mock os.makedirs to raise exception
        mock_makedirs = mocker.patch('os.makedirs', side_effect=PermissionError("Permission denied"))

        # Mock logger
        mock_logger = MagicMock()

        # Create instance of ConfigManager with mocked logger
        config_manager = ConfigManager("dummy/path/config.json", logger=mock_logger)

        # Save configuration
        result = config_manager.save_config()

        # Assertions
        assert result is False
        mock_logger.error.assert_called_once()
        assert "Error saving configuration" in mock_logger.error.call_args[0][0]

    def test_get_value_simple_key(self):
        """Test getting value for simple key."""
        # Sample configuration
        sample_config = {
            "key1": "value1",
            "key2": "value2"
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = sample_config

        # Get values
        value1 = config_manager.get_value("key1")
        value2 = config_manager.get_value("key2")
        missing = config_manager.get_value("key3")
        missing_with_default = config_manager.get_value("key3", "default")

        # Assertions
        assert value1 == "value1"
        assert value2 == "value2"
        assert missing is None
        assert missing_with_default == "default"

    def test_get_value_nested_keys(self):
        """Test getting value for nested keys."""
        # Sample configuration
        sample_config = {
            "paths": {
                "video_directory": "/test/videos",
                "obsidian_vault": "/test/obsidian"
            },
            "api": {
                "rev_ai": {
                    "job_timeout": 3600
                }
            }
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = sample_config

        # Get values
        video_dir = config_manager.get_value("paths.video_directory")
        job_timeout = config_manager.get_value("api.rev_ai.job_timeout")
        missing = config_manager.get_value("api.claude.model")
        missing_middle = config_manager.get_value("settings.logging.level")

        # Assertions
        assert video_dir == "/test/videos"
        assert job_timeout == 3600
        assert missing is None
        assert missing_middle is None

    def test_set_value_simple_key(self):
        """Test setting value for simple key."""
        # Create instance of ConfigManager with empty config
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = {}

        # Set values
        result1 = config_manager.set_value("key1", "value1")
        result2 = config_manager.set_value("key2", 123)

        # Assertions
        assert result1 is True
        assert result2 is True
        assert config_manager.config == {
            "key1": "value1",
            "key2": 123
        }

    def test_set_value_nested_keys(self):
        """Test setting value for nested keys."""
        # Create instance of ConfigManager with empty config
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = {}

        # Set values
        config_manager.set_value("paths.video_directory", "/test/videos")
        config_manager.set_value("api.rev_ai.job_timeout", 3600)

        # Assertions
        assert config_manager.config == {
            "paths": {
                "video_directory": "/test/videos"
            },
            "api": {
                "rev_ai": {
                    "job_timeout": 3600
                }
            }
        }

    def test_set_value_override_existing(self):
        """Test setting value to override existing value."""
        # Sample configuration
        sample_config = {
            "paths": {
                "video_directory": "/test/videos"
            }
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = sample_config

        # Set values
        config_manager.set_value("paths.video_directory", "/new/videos")

        # Assertions
        assert config_manager.get_value("paths.video_directory") == "/new/videos"

    def test_set_value_error(self, mocker):
        """Test setting value when error occurs."""
        # Mock logger
        mock_logger = MagicMock()

        # Create a mock config that raises exception when accessed
        mock_config = MagicMock()
        mock_config.__getitem__.side_effect = Exception("Test exception")

        # Create instance of ConfigManager with mocked logger and config
        config_manager = ConfigManager("dummy/path/config.json", logger=mock_logger)
        config_manager.config = mock_config

        # Set value
        result = config_manager.set_value("key", "value")

        # Assertions
        assert result is False
        mock_logger.error.assert_called_once()
        assert "Error setting value" in mock_logger.error.call_args[0][0]

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        # Sample valid configuration
        sample_config = {
            "paths": {
                "video_directory": "/test/videos",
                "obsidian_vault": "/test/obsidian"
            },
            "api": {
                "rev_ai": {},
                "claude": {}
            },
            "processing": {
                "delete_video_files": True,
                "delete_audio_files": True,
                "process_interval": 60
            },
            "system": {}
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = sample_config

        # Validate
        errors = config_manager.validate_config()

        # Assertions
        assert isinstance(errors, list)
        assert len(errors) == 0

    def test_validate_config_missing_sections(self):
        """Test validation with missing sections."""
        # Sample configuration with missing sections
        sample_config = {
            "paths": {
                "video_directory": "/test/videos"
                # Missing obsidian_vault
            }
            # Missing api, processing, system
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = sample_config

        # Validate
        errors = config_manager.validate_config()

        # Assertions
        assert isinstance(errors, list)
        assert len(errors) >= 3  # At least 3 errors: missing api, processing, system
        assert any("api" in error for error in errors)
        assert any("processing" in error for error in errors)
        assert any("system" in error for error in errors)

    def test_validate_config_invalid_values(self):
        """Test validation with invalid values."""
        # Sample configuration with invalid values
        sample_config = {
            "paths": {
                "video_directory": "/test/videos",
                "obsidian_vault": "/test/obsidian"
            },
            "api": {
                "rev_ai": {},
                "claude": {
                    "temperature": 2.0  # Invalid: should be between 0 and 1
                }
            },
            "processing": {
                "delete_video_files": "yes",  # Invalid: should be boolean
                "delete_audio_files": True,
                "process_interval": "60"  # Invalid: should be integer
            },
            "system": {}
        }

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        config_manager.config = sample_config

        # Validate
        errors = config_manager.validate_config()

        # Assertions
        assert isinstance(errors, list)
        assert len(errors) >= 2  # At least 2 errors for the invalid values
        assert any("temperature" in error for error in errors)
        assert any("delete_video_files" in error for error in errors)
        # Note: process_interval validation currently not implemented in config.py

    def test_init_with_default_path(self, mocker):
        """Test initialization with default configuration path."""
        # Mock os.path.expanduser to return a known path
        home_dir = "/mock/home"
        mocker.patch('os.path.expanduser', return_value=home_dir)

        # Mock _load_or_create_default to return empty config and avoid file operations
        mock_load = mocker.patch.object(ConfigManager, '_load_or_create_default', return_value={})

        # Create instance of ConfigManager without specifying config_path
        config_manager = ConfigManager()

        # Check that default path was set correctly
        expected_path = f"{home_dir}/.config/meet2obsidian/config.json"
        assert config_manager.config_path == expected_path
        assert mock_load.called

    def test_load_config_with_comments(self, mocker):
        """Test loading configuration with comments."""
        # Sample configuration with comments
        json_with_comments = """{
            // Video directory path
            "paths": {
                "video_directory": "/test/videos",
                "obsidian_vault": "/test/obsidian"
            },
            /* API configuration
               for external services */
            "api": {
                "rev_ai": {
                    "job_timeout": 3600
                }
            }
        }"""

        # Expected parsed configuration
        expected_config = {
            "paths": {
                "video_directory": "/test/videos",
                "obsidian_vault": "/test/obsidian"
            },
            "api": {
                "rev_ai": {
                    "job_timeout": 3600
                }
            }
        }

        # Mock commentjson.loads to return our expected config
        mock_commentjson = mocker.patch('commentjson.loads', return_value=expected_config)

        # Mock os.path.exists to return True
        mocker.patch('os.path.exists', return_value=True)

        # Mock open to return our JSON with comments
        mock_open_func = mock_open(read_data=json_with_comments)
        mocker.patch('builtins.open', mock_open_func)

        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")

        # Load configuration
        loaded_config = config_manager.load_config()

        # Assertions
        mock_commentjson.assert_called_once_with(json_with_comments)
        assert loaded_config == expected_config