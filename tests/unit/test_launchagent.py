"""
Unit tests for LaunchAgent integration.

These tests verify the functionality of creating, installing, uninstalling
and checking the status of LaunchAgents in macOS for meet2obsidian.
"""

import os
import sys
import pytest
import tempfile
import subprocess
from unittest.mock import patch, MagicMock

# Skip all tests if not on macOS
pytestmark = pytest.mark.skipif(sys.platform != 'darwin', reason="LaunchAgent tests only run on macOS")


class TestLaunchAgentGenerator:
    """Tests for generating LaunchAgent plist files."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plist_path = os.path.join(self.temp_dir.name, "com.user.meet2obsidian.plist")
    
    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_generate_plist_file_with_defaults(self):
        """Test generating a plist file with default values."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Create LaunchAgentManager with test paths
        manager = LaunchAgentManager(plist_path=self.plist_path)
        
        # Generate plist file
        result = manager.generate_plist_file()
        
        # Check result
        assert result is True
        assert os.path.exists(self.plist_path)
        
        # Check content
        with open(self.plist_path, 'r') as f:
            content = f.read()
            assert '<?xml version="1.0" encoding="UTF-8"?>' in content
            assert '<key>Label</key>' in content
            assert '<string>com.user.meet2obsidian</string>' in content
            assert '<key>ProgramArguments</key>' in content
            assert '<string>-m</string>' in content
            assert '<string>meet2obsidian</string>' in content
            assert '<string>service</string>' in content
            assert '<string>start</string>' in content
            assert '<key>RunAtLoad</key>' in content
            assert '<true/>' in content
            assert '<key>KeepAlive</key>' in content
            assert '<key>StandardOutPath</key>' in content
            assert '<key>StandardErrorPath</key>' in content
    
    def test_generate_plist_file_with_custom_values(self):
        """Test generating a plist file with custom values."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Create LaunchAgentManager with test paths
        manager = LaunchAgentManager(
            plist_path=self.plist_path,
            label="com.test.custom",
            program="/usr/bin/python3",
            args=["-m", "meet2obsidian", "--verbose"],
            run_at_load=False,
            keep_alive=False,
            stdout_path="/tmp/stdout.log",
            stderr_path="/tmp/stderr.log"
        )
        
        # Generate plist file
        result = manager.generate_plist_file()
        
        # Check result
        assert result is True
        assert os.path.exists(self.plist_path)
        
        # Check content
        with open(self.plist_path, 'r') as f:
            content = f.read()
            assert '<string>com.test.custom</string>' in content
            assert '<string>/usr/bin/python3</string>' in content
            assert '<string>--verbose</string>' in content
            assert '<false/>' in content
            assert '<string>/tmp/stdout.log</string>' in content
            assert '<string>/tmp/stderr.log</string>' in content
    
    def test_generate_plist_file_error_handling(self):
        """Test error handling when generating plist file."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Create LaunchAgentManager with invalid path (directory that doesn't exist)
        manager = LaunchAgentManager(plist_path="/nonexistent/directory/file.plist")
        
        # Generate plist file should fail
        result = manager.generate_plist_file()
        assert result is False


class TestLaunchAgentInstallation:
    """Tests for installing and uninstalling LaunchAgents."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plist_path = os.path.join(self.temp_dir.name, "com.user.meet2obsidian.plist")
        
        # Create a dummy plist file
        with open(self.plist_path, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n')
            f.write('<plist version="1.0">\n')
            f.write('<dict>\n')
            f.write('    <key>Label</key>\n')
            f.write('    <string>com.user.meet2obsidian</string>\n')
            f.write('</dict>\n')
            f.write('</plist>\n')
    
    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    @patch('subprocess.run')
    def test_install_launchagent(self, mock_run):
        """Test installing a LaunchAgent."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Mock subprocess.run to return success
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        # Create LaunchAgentManager with test path
        manager = LaunchAgentManager(plist_path=self.plist_path)
        
        # Install LaunchAgent
        result = manager.install()
        
        # Check result
        assert result is True
        
        # Check subprocess.run was called with correct arguments
        mock_run.assert_called_once_with(
            ["launchctl", "load", self.plist_path],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_install_launchagent_error(self, mock_run):
        """Test error handling when installing LaunchAgent."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Mock subprocess.run to return an error
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error loading agent")
        
        # Create LaunchAgentManager with test path
        manager = LaunchAgentManager(plist_path=self.plist_path)
        
        # Install LaunchAgent should fail
        result = manager.install()
        assert result is False
    
    @patch('subprocess.run')
    def test_uninstall_launchagent(self, mock_run):
        """Test uninstalling a LaunchAgent."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Mock subprocess.run to return success
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        # Create LaunchAgentManager with test path
        manager = LaunchAgentManager(plist_path=self.plist_path)
        
        # Uninstall LaunchAgent
        result = manager.uninstall()
        
        # Check result
        assert result is True
        
        # Check subprocess.run was called with correct arguments
        mock_run.assert_called_once_with(
            ["launchctl", "unload", self.plist_path],
            capture_output=True,
            text=True
        )
        
        # Check that plist file was removed
        assert not os.path.exists(self.plist_path)
    
    @patch('subprocess.run')
    def test_uninstall_launchagent_error(self, mock_run):
        """Test error handling when uninstalling LaunchAgent."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Mock subprocess.run to return an error
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error unloading agent")
        
        # Create LaunchAgentManager with test path
        manager = LaunchAgentManager(plist_path=self.plist_path)
        
        # Uninstall LaunchAgent should fail
        result = manager.uninstall()
        assert result is False


class TestLaunchAgentStatus:
    """Tests for checking LaunchAgent status."""
    
    def setup_method(self):
        """Setup test environment."""
        self.plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.meet2obsidian.plist")
    
    @patch('subprocess.run')
    def test_check_launchagent_status_active(self, mock_run):
        """Test checking status of an active LaunchAgent."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Mock subprocess.run to return a running agent
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        {
            "Label": "com.user.meet2obsidian",
            "PID": 12345,
            "Status": 0
        }
        """
        mock_run.return_value = mock_process
        
        # Create LaunchAgentManager
        manager = LaunchAgentManager(plist_path=self.plist_path)
        
        # Check status
        is_active, info = manager.get_status()
        
        # Check result
        assert is_active is True
        assert isinstance(info, dict)
        assert info.get("pid") == 12345
    
    @patch('subprocess.run')
    def test_check_launchagent_status_inactive(self, mock_run):
        """Test checking status of an inactive LaunchAgent."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Mock subprocess.run to return a not-found error
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="No such process")
        
        # Create LaunchAgentManager
        manager = LaunchAgentManager(plist_path=self.plist_path)
        
        # Check status
        is_active, info = manager.get_status()
        
        # Check result
        assert is_active is False
        assert info is None
    
    def test_plist_exists(self):
        """Test checking if plist file exists."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Create LaunchAgentManager with non-existent plist path
        manager = LaunchAgentManager(plist_path="/tmp/nonexistent.plist")
        
        # Check plist exists
        assert manager.plist_exists() is False
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create LaunchAgentManager with existing plist path
            manager = LaunchAgentManager(plist_path=temp_path)
            
            # Check plist exists
            assert manager.plist_exists() is True
        finally:
            # Clean up
            os.unlink(temp_path)