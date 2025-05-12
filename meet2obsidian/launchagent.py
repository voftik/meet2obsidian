"""
LaunchAgent management for meet2obsidian on macOS.

This module provides functionality for creating, installing, uninstalling, and 
checking the status of LaunchAgents for meet2obsidian on macOS.
"""

import os
import sys
import json
import logging
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union

# Skip import if not on macOS
if sys.platform != 'darwin':
    raise ImportError("LaunchAgent is only supported on macOS")


class LaunchAgentManager:
    """
    Manages LaunchAgent creation, installation, and status for meet2obsidian.
    
    This class provides methods to:
    - Generate plist files for LaunchAgents
    - Install (load) LaunchAgents
    - Uninstall (unload) LaunchAgents
    - Check LaunchAgent status
    """
    
    def __init__(
        self,
        plist_path: Optional[str] = None,
        label: str = "com.user.meet2obsidian",
        program: Optional[str] = None,
        args: Optional[List[str]] = None,
        run_at_load: bool = True,
        keep_alive: bool = True,
        stdout_path: Optional[str] = None,
        stderr_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the LaunchAgent manager.

        Args:
            plist_path: Path to the plist file. If None, uses default path.
            label: Label for the LaunchAgent.
            program: Path to the program to run. If None, uses sys.executable.
            args: Arguments to pass to the program. Default is meet2obsidian service start.
            run_at_load: Whether to run the agent when loaded.
            keep_alive: Whether to keep the agent alive.
            stdout_path: Path to redirect stdout. If None, uses default.
            stderr_path: Path to redirect stderr. If None, uses default.
            logger: Logger instance. If None, creates a new one.
        """
        # Set default plist path if not provided
        if plist_path is None:
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.meet2obsidian.plist")

        # Store parameters
        self.plist_path = plist_path
        self.label = label
        self.program = program or sys.executable
        self.args = args or ["-m", "meet2obsidian", "service", "start"]
        self.run_at_load = run_at_load
        self.keep_alive = keep_alive

        # Set default log paths if not provided
        log_dir = os.path.expanduser("~/Library/Logs/meet2obsidian")
        self.stdout_path = stdout_path or os.path.join(log_dir, "stdout.log")
        self.stderr_path = stderr_path or os.path.join(log_dir, "stderr.log")

        # Create logger if not provided
        self.logger = logger or logging.getLogger(__name__)
        
    def generate_plist_file(self) -> bool:
        """
        Generate a plist file for the LaunchAgent.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create directory for plist file if it doesn't exist
            plist_dir = os.path.dirname(self.plist_path)
            os.makedirs(plist_dir, exist_ok=True)

            # Format program arguments as XML array items
            args_xml = ""
            for arg in self.args:
                args_xml += f"        <string>{arg}</string>\n"

            # Generate plist XML content
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.program}</string>
{args_xml}    </array>
    <key>RunAtLoad</key>
    <{'true' if self.run_at_load else 'false'}/>
    <key>KeepAlive</key>
    <{'true' if self.keep_alive else 'false'}/>
    <key>StandardOutPath</key>
    <string>{self.stdout_path}</string>
    <key>StandardErrorPath</key>
    <string>{self.stderr_path}</string>
</dict>
</plist>
"""
            # Write plist content to file
            with open(self.plist_path, 'w') as f:
                f.write(plist_content)

            # Set permissions to 644 (rw-r--r--)
            os.chmod(self.plist_path, 0o644)

            self.logger.info(f"LaunchAgent plist file generated: {self.plist_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error generating LaunchAgent plist file: {str(e)}")
            return False

    def install(self) -> bool:
        """
        Install (load) the LaunchAgent.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Generate plist file if it doesn't exist
            if not os.path.exists(self.plist_path):
                if not self.generate_plist_file():
                    self.logger.error("Failed to generate plist file before installation")
                    return False

            # Load the LaunchAgent
            result = subprocess.run(
                ["launchctl", "load", self.plist_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.logger.error(f"Error loading LaunchAgent: {result.stderr}")
                return False

            self.logger.info(f"LaunchAgent loaded: {self.plist_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error installing LaunchAgent: {str(e)}")
            return False

    def uninstall(self) -> bool:
        """
        Uninstall (unload) the LaunchAgent.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if plist file exists
            if not os.path.exists(self.plist_path):
                self.logger.info(f"LaunchAgent plist file does not exist: {self.plist_path}")
                return True

            # Unload the LaunchAgent
            result = subprocess.run(
                ["launchctl", "unload", self.plist_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.logger.error(f"Error unloading LaunchAgent: {result.stderr}")
                return False

            # Remove the plist file
            os.remove(self.plist_path)

            self.logger.info(f"LaunchAgent unloaded and removed: {self.plist_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error uninstalling LaunchAgent: {str(e)}")
            return False

    def get_status(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if the LaunchAgent is active.

        Returns:
            Tuple containing:
                bool: True if active, False otherwise.
                Optional[Dict]: Agent information if active, None otherwise.
        """
        try:
            # Run launchctl list with the label to check if it's loaded
            result = subprocess.run(
                ["launchctl", "list", self.label],
                capture_output=True,
                text=True
            )

            # If non-zero return code, the agent is not running
            if result.returncode != 0:
                return False, None

            # Parse the output to get information about the running agent
            try:
                # Try to parse as JSON (newer macOS versions)
                info = json.loads(result.stdout)
                return True, {
                    "pid": info.get("PID"),
                    "label": info.get("Label"),
                    "status": info.get("Status", 0)
                }
            except json.JSONDecodeError:
                # Parse as text (older macOS versions)
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 3:
                        return True, {
                            "pid": int(parts[0]) if parts[0] != "-" else None,
                            "status": int(parts[1]),
                            "label": parts[2]
                        }
                # Return minimal info if we can't parse the output
                return True, {"label": self.label}

        except Exception as e:
            self.logger.error(f"Error checking LaunchAgent status: {str(e)}")
            return False, None

    def plist_exists(self) -> bool:
        """
        Check if the plist file exists.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return os.path.exists(self.plist_path)