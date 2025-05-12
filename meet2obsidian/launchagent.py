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
        
    def generate_plist_file(self, working_directory: Optional[str] = None,
                         env_vars: Optional[Dict[str, str]] = None) -> bool:
        """
        Generate a plist file for the LaunchAgent.

        Args:
            working_directory: Optional working directory for the LaunchAgent
            env_vars: Optional environment variables to include in the plist

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create directory for plist file if it doesn't exist
            plist_dir = os.path.dirname(self.plist_path)
            os.makedirs(plist_dir, exist_ok=True)

            # Create logs directory for stdout/stderr
            logs_dir = os.path.dirname(self.stdout_path)
            os.makedirs(logs_dir, exist_ok=True)

            # Format program arguments as XML array items
            args_xml = ""
            for arg in self.args:
                args_xml += f"        <string>{arg}</string>\n"

            # Base plist content
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
"""
            # Add working directory if specified
            if working_directory:
                plist_content += f"""    <key>WorkingDirectory</key>
    <string>{working_directory}</string>
"""

            # Add environment variables if specified
            if env_vars and len(env_vars) > 0:
                plist_content += "    <key>EnvironmentVariables</key>\n"
                plist_content += "    <dict>\n"

                for key, value in env_vars.items():
                    plist_content += f"        <key>{key}</key>\n"
                    plist_content += f"        <string>{value}</string>\n"

                plist_content += "    </dict>\n"

            # Close the main dictionary and plist
            plist_content += "</dict>\n</plist>\n"

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
            # Check if plist file exists first
            if not self.plist_exists():
                self.logger.debug(f"LaunchAgent plist file does not exist: {self.plist_path}")
                return False, None

            # Run launchctl list with the label to check if it's loaded
            result = subprocess.run(
                ["launchctl", "list", self.label],
                capture_output=True,
                text=True
            )

            # If non-zero return code, the agent is not running
            if result.returncode != 0:
                return False, {"installed": True, "running": False, "label": self.label, "plist_path": self.plist_path}

            # Parse the output to get information about the running agent
            agent_info = {"installed": True, "running": True, "label": self.label, "plist_path": self.plist_path}

            try:
                # Try to parse as JSON (newer macOS versions)
                info = json.loads(result.stdout)
                agent_info.update({
                    "pid": info.get("PID"),
                    "status": info.get("Status", 0),
                    "last_exit_status": info.get("LastExitStatus", None),
                })
                return True, agent_info
            except json.JSONDecodeError:
                # Parse as text (older macOS versions)
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 3:
                        agent_info.update({
                            "pid": int(parts[0]) if parts[0] != "-" else None,
                            "status": int(parts[1]),
                        })
                return True, agent_info

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

    def get_full_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status information about the LaunchAgent.

        This method provides detailed information about the LaunchAgent including:
        - Whether it's installed (plist exists)
        - Whether it's running
        - Detailed configuration information
        - Path information
        - Runtime information if available

        Returns:
            Dict[str, Any]: Comprehensive status information
        """
        # Base status information
        status = {
            "installed": self.plist_exists(),
            "label": self.label,
            "plist_path": self.plist_path
        }

        if not status["installed"]:
            return status

        # Check if the agent is running
        is_running, agent_info = self.get_status()
        status["running"] = is_running

        # If we have agent information, include it
        if agent_info:
            status.update(agent_info)

        # Get plist file modification time
        try:
            mtime = os.path.getmtime(self.plist_path)
            status["last_modified"] = mtime
        except:
            pass

        # If we can read the plist file, get its content
        try:
            with open(self.plist_path, 'r') as f:
                plist_content = f.read()

            # Try to extract key information from the plist content
            import re

            # Extract RunAtLoad value
            run_at_load_match = re.search(r'<key>RunAtLoad</key>\s*<(true|false)/>', plist_content)
            if run_at_load_match:
                status["run_at_load"] = run_at_load_match.group(1) == 'true'

            # Extract KeepAlive value
            keep_alive_match = re.search(r'<key>KeepAlive</key>\s*<(true|false)/>', plist_content)
            if keep_alive_match:
                status["keep_alive"] = keep_alive_match.group(1) == 'true'

            # Extract StandardOutPath and StandardErrorPath
            stdout_match = re.search(r'<key>StandardOutPath</key>\s*<string>(.*?)</string>', plist_content)
            if stdout_match:
                status["stdout_path"] = stdout_match.group(1)

            stderr_match = re.search(r'<key>StandardErrorPath</key>\s*<string>(.*?)</string>', plist_content)
            if stderr_match:
                status["stderr_path"] = stderr_match.group(1)

            # Extract program information (first string in ProgramArguments array)
            program_match = re.search(r'<key>ProgramArguments</key>\s*<array>\s*<string>(.*?)</string>', plist_content)
            if program_match:
                status["program"] = program_match.group(1)

            # Extract WorkingDirectory if present
            working_dir_match = re.search(r'<key>WorkingDirectory</key>\s*<string>(.*?)</string>', plist_content)
            if working_dir_match:
                status["working_directory"] = working_dir_match.group(1)

            # Extract EnvironmentVariables if present
            env_vars_match = re.search(r'<key>EnvironmentVariables</key>', plist_content)
            if env_vars_match:
                status["has_environment_variables"] = True
        except Exception as e:
            self.logger.debug(f"Could not extract detailed plist information: {str(e)}")

        # Try to get extended status using the new domain-target format (macOS 10.10+)
        try:
            # Try the new domain-target format that's available in newer macOS versions
            result = subprocess.run(
                ["launchctl", "print", f"gui/{os.getuid()}/{self.label}"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Parse the detailed output
                output = result.stdout

                # Check if service is enabled
                if "state = disabled" in output:
                    status["enabled"] = False
                else:
                    status["enabled"] = True

                # Extract PID if running
                pid_match = re.search(r'pid = (\d+)', output)
                if pid_match:
                    status["pid"] = int(pid_match.group(1))

                # Extract status code
                status_match = re.search(r'status = (\d+)', output)
                if status_match:
                    status["status_code"] = int(status_match.group(1))

                # Extract last exit status
                exit_status_match = re.search(r'last exit status = (\d+)', output)
                if exit_status_match:
                    status["last_exit_status"] = int(exit_status_match.group(1))

                # Check for additional properties
                if "path =" in output:
                    status["verified_path"] = True
        except Exception as e:
            self.logger.debug(f"Could not get extended status information: {str(e)}")

        return status