"""
Integration tests for LaunchAgent functionality.

These tests verify the real-world interaction with macOS LaunchAgents,
including creating plist files, loading/unloading agents, and checking status.

IMPORTANT: These tests interact with the actual LaunchAgents system and are
marked with 'integration' to allow them to be skipped in CI/CD environments.
"""

import os
import sys
import pytest
import tempfile
import subprocess
from pathlib import Path

# Skip all tests if not on macOS
pytestmark = [
    pytest.mark.skipif(sys.platform != 'darwin', reason="LaunchAgent tests only run on macOS"),
    pytest.mark.integration
]


class TestLaunchAgentIntegration:
    """Integration tests for LaunchAgent functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_plist_path = os.path.join(self.temp_dir.name, "com.test.meet2obsidian.plist")
        
        # Create LaunchAgent using LaunchAgentManager
        from meet2obsidian.launchagent import LaunchAgentManager
        self.manager = LaunchAgentManager(
            plist_path=self.test_plist_path,
            label="com.test.meet2obsidian",
            args=["--test"]
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        # Ensure the test LaunchAgent is unloaded and removed
        if os.path.exists(self.test_plist_path):
            try:
                # Try to unload the agent
                subprocess.run(
                    ["launchctl", "unload", self.test_plist_path],
                    capture_output=True,
                    text=True
                )
                # Remove the plist file
                os.remove(self.test_plist_path)
            except:
                pass
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_generate_plist_file_real(self):
        """Test generating a real plist file."""
        # Generate the plist file
        result = self.manager.generate_plist_file()
        
        # Verify the file was created
        assert result is True
        assert os.path.exists(self.test_plist_path)
        
        # Check file permissions (should be 644 for plist files)
        file_mode = os.stat(self.test_plist_path).st_mode & 0o777
        assert file_mode == 0o644 or file_mode == 0o664, f"Expected file mode 644 or 664, got {file_mode:o}"
        
        # Check content format with plutil (validates plist syntax)
        validation = subprocess.run(
            ["plutil", "-lint", self.test_plist_path],
            capture_output=True,
            text=True
        )
        assert validation.returncode == 0, f"Plist validation failed: {validation.stderr}"
    
    def test_launchagent_lifecycle(self):
        """Test the full lifecycle of a LaunchAgent."""
        # Generate the plist file
        result = self.manager.generate_plist_file()
        assert result is True
        
        # Before we install, check status should be inactive
        is_active, _ = self.manager.get_status()
        assert is_active is False
        
        # Install but don't actually load the agent, mock the loading
        original_run = subprocess.run
        
        def mock_run(cmd, **kwargs):
            if "load" in cmd:
                # Return success without actually loading
                return type('MockCompletedProcess', (), {
                    'returncode': 0,
                    'stdout': '',
                    'stderr': ''
                })
            # For any other command, use the real subprocess.run
            return original_run(cmd, **kwargs)
        
        try:
            # Patch subprocess.run to prevent real loading
            subprocess.run = mock_run
            
            # Install the LaunchAgent
            result = self.manager.install()
            assert result is True
            
        finally:
            # Restore original subprocess.run
            subprocess.run = original_run
    
    def test_check_real_system_agents(self):
        """
        Test checking real system LaunchAgents.
        
        This test demonstrates how to check existing system LaunchAgents
        without modifying them, to verify the status checking functionality.
        """
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Create a manager to check status of a system agent (Finder)
        system_manager = LaunchAgentManager(label="com.apple.Finder")
        
        # Get status of a system agent
        is_active, info = system_manager.get_status()
        
        # The test passes either way - we're just checking the function works
        if is_active:
            assert isinstance(info, dict)
            assert "pid" in info
        else:
            assert info is None
    
    def test_real_plist_directories(self):
        """Test validation of LaunchAgent directories in the system."""
        from meet2obsidian.launchagent import LaunchAgentManager
        
        # Check if the standard LaunchAgents directories exist
        user_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        system_agents_dir = "/Library/LaunchAgents"
        
        # User LaunchAgents directory should exist or be creatable
        if not os.path.exists(user_agents_dir):
            try:
                os.makedirs(user_agents_dir, exist_ok=True)
                assert os.path.exists(user_agents_dir)
                os.rmdir(user_agents_dir)  # Clean up if we created it
            except:
                pytest.skip("Cannot create user LaunchAgents directory")
        
        # System LaunchAgents directory should exist
        assert os.path.exists(system_agents_dir)
        
        # Test creating a manager with the user directory
        user_plist_path = os.path.join(user_agents_dir, "com.test.meet2obsidian.plist")
        user_manager = LaunchAgentManager(plist_path=user_plist_path)
        
        # Ensure we're only checking, not creating
        assert not os.path.exists(user_plist_path)
        assert user_manager.plist_exists() is False