"""
Integration tests for the meet2obsidian CLI interface.

This module contains integration tests that verify CLI interaction
with real system components such as the API key storage.
"""

import os
import uuid
import pytest
from click.testing import CliRunner

from meet2obsidian.cli import cli
from meet2obsidian.utils.security import KeychainManager


@pytest.mark.integration
class TestCliApikeysIntegration:
    """Integration tests for the apikeys commands."""

    def setup_method(self):
        """Test setup - create unique keys."""
        self.test_key_name = f"test_key_{uuid.uuid4().hex[:8]}"
        self.test_key_value = f"test_value_{uuid.uuid4().hex}"
        
        # Create keychain manager and save test key
        self.keychain = KeychainManager()
        self.keychain.store_api_key(self.test_key_name, self.test_key_value)

    def teardown_method(self):
        """Test cleanup - remove test keys."""
        self.keychain.delete_api_key(self.test_key_name)
    
    def test_apikeys_get_command(self):
        """Test retrieving API key via CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ['apikeys', 'get', self.test_key_name])
        
        assert result.exit_code == 0
        assert self.test_key_name in result.output
        # Проверяем, что ключ маскируется в выводе
        assert self.test_key_value not in result.output
        assert self.test_key_value[:4] in result.output
    
    def test_apikeys_get_with_show_flag(self):
        """Test retrieving API key with --show flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ['apikeys', 'get', self.test_key_name, '--show'])
        
        assert result.exit_code == 0
        assert self.test_key_name in result.output
        assert self.test_key_value in result.output
    
    def test_apikeys_list_command(self):
        """Test displaying list of API keys via CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ['apikeys', 'list'])
        
        assert result.exit_code == 0
        # Check output (may need adjustment depending on format)
        assert "API" in result.output
    
    def test_apikeys_set_and_delete(self):
        """Test setting and deleting API key via CLI."""
        runner = CliRunner()
        temp_key_name = f"temp_key_{uuid.uuid4().hex[:8]}"
        temp_key_value = f"temp_value_{uuid.uuid4().hex}"
        
        # Set key
        result_set = runner.invoke(cli, ['apikeys', 'set', temp_key_name], input=temp_key_value)
        assert result_set.exit_code == 0

        # Verify key was set
        assert self.keychain.key_exists(temp_key_name)

        # Delete key with confirmation
        result_delete = runner.invoke(cli, ['apikeys', 'delete', temp_key_name], input="y")
        assert result_delete.exit_code == 0

        # Verify deletion
        assert not self.keychain.key_exists(temp_key_name)


@pytest.mark.integration
@pytest.mark.skip(reason="Config command not yet implemented")
class TestCliConfigIntegration:
    """Integration tests for config commands (to be implemented later)."""

    def setup_method(self):
        """Test setup - create temporary config file."""
        # This section will be implemented when the config command is available
        pass

    def teardown_method(self):
        """Test cleanup - remove temporary config file."""
        # This section will be implemented when the config command is available
        pass
    
    def test_config_show_command(self):
        """Test displaying configuration via CLI."""
        # This test will be implemented when the config command is available
        pass

    def test_config_set_command(self):
        """Test setting configuration parameters via CLI."""
        # This test will be implemented when the config command is available
        pass