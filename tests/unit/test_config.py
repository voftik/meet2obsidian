import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from meet2obsidian.config import ConfigManager

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
        
        # Mock os.makedirs to do nothing
        mocker.patch('os.makedirs', return_value=None)
        
        # Mock open for writing default config
        mock_open_func = mock_open()
        mocker.patch('builtins.open', mock_open_func)
        
        # Spy on json.dump to check it's called with default config
        json_dump_spy = mocker.patch('json.dump')
        
        # Create instance of ConfigManager
        config_manager = ConfigManager("dummy/path/config.json")
        
        # Load configuration (should create default)
        loaded_config = config_manager.load_config()
        
        # Verify default config was created
        assert json_dump_spy.called
        
        # Verify default values are present
        assert "paths" in loaded_config
        assert "api" in loaded_config
    
    def test_load_config_invalid_json(self, mocker):
        """Test loading configuration with invalid JSON."""
        # Mock os.path.exists to return True
        mocker.patch('os.path.exists', return_value=True)
        
        # Mock open to return invalid JSON
        mock_open_func = mock_open(read_data="{invalid json")
        mocker.patch('builtins.open', mock_open_func)
        
        # Mock logging
        mock_logger = MagicMock()
        
        # Create instance of ConfigManager with mocked logger
        config_manager = ConfigManager("dummy/path/config.json", logger=mock_logger)
        
        # Load configuration (should fall back to default)
        loaded_config = config_manager.load_config()
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        
        # Verify default config was returned
        assert isinstance(loaded_config, dict)
        assert "paths" in loaded_config
    
    def test_load_config_empty_file(self, mocker):
        """Test loading configuration from an empty file."""
        # Mock os.path.exists to return True
        mocker.patch('os.path.exists', return_value=True)
        
        # Mock open to return empty string
        mock_open_func = mock_open(read_data="")
        mocker.patch('builtins.open', mock_open_func)
        
        # Mock logging
        mock_logger = MagicMock()
        
        # Create instance of ConfigManager with mocked logger
        config_manager = ConfigManager("dummy/path/config.json", logger=mock_logger)
        
        # Load configuration (should fall back to default)
        loaded_config = config_manager.load_config()
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        
        # Verify default config was returned
        assert isinstance(loaded_config, dict)
        assert "paths" in loaded_config
    
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
        