"""
File monitoring module for meet2obsidian.

This module is responsible for monitoring directories for new files
and triggering processing when new files appear.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import threading
import queue

from meet2obsidian.utils.logging import get_logger


class FileMonitor:
    """
    Monitors a directory for new files and starts processing when they appear.
    Uses a separate thread to watch for file changes.
    """

    def __init__(self, directory: str, file_patterns: Optional[List[str]] = None,
                 poll_interval: int = 60, logger=None):
        """
        Initialize a file monitor.

        Args:
            directory: Directory to monitor
            file_patterns: Optional list of file patterns to watch for (e.g., ["*.mp4", "*.mov"])
            poll_interval: Interval in seconds between directory scans (default: 60)
            logger: Optional logger. If not provided, a new one will be created
        """
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.file_patterns = file_patterns or ["*.mp4", "*.mov", "*.webm", "*.mkv"]
        self.poll_interval = max(5, poll_interval)  # Ensure at least 5 seconds interval
        self.logger = logger or get_logger("monitor.file_monitor")

        self._stop_event = threading.Event()
        self._monitor_thread = None
        self._file_queue = queue.Queue()
        self._processed_files = set()
        self.observed_files = set()
        self.last_scan_time = None
        self.is_monitoring = False

        # Callback to notify when new files are found
        self._file_callback = None
        
    def start(self) -> bool:
        """
        Start the file monitoring thread.

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            if not os.path.exists(self.directory):
                self.logger.error(f"Directory does not exist: {self.directory}")
                return False

            # Check if already monitoring
            if self.is_monitoring:
                self.logger.info("File monitor is already running")
                return True

            self.logger.info(f"Starting file monitor for directory: {self.directory}")
            self.logger.info(f"Watching for files matching: {', '.join(self.file_patterns)}")

            # Initialize set of files already in directory
            self._scan_directory()

            # Start monitoring thread
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="FileMonitorThread",
                daemon=True
            )
            self._monitor_thread.start()

            self.is_monitoring = True
            self.logger.info("File monitoring thread started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error starting file monitor: {str(e)}")
            return False

    def stop(self) -> bool:
        """
        Stop the file monitoring thread.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if not self.is_monitoring:
                self.logger.info("File monitor is not running")
                return True

            self.logger.info("Stopping file monitor")

            # Signal thread to stop
            self._stop_event.set()

            # Wait for thread to finish (with timeout)
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5)
                if self._monitor_thread.is_alive():
                    self.logger.warning("File monitor thread did not stop gracefully")

            self.is_monitoring = False
            self.logger.info("File monitor stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping file monitor: {str(e)}")
            return False
    
    def register_file_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback function to be called when a new file is found.
        
        Args:
            callback: Function to call with the file path when a new file is found
        """
        self._file_callback = callback
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the file monitor.
        
        Returns:
            dict: Status information
        """
        return {
            "directory": self.directory,
            "patterns": self.file_patterns,
            "running": self._monitor_thread is not None and self._monitor_thread.is_alive(),
            "files_processed": len(self._processed_files),
            "pending_files": self._file_queue.qsize() if self._file_queue else 0
        }
    
    def _scan_directory(self) -> List[str]:
        """
        Scan the directory for files matching patterns.

        Files are only considered for processing if they meet the following criteria:
        1. They match one of the file patterns
        2. They have not been observed before
        3. They have not been modified for a certain period (to avoid processing files still being written)

        Returns:
            List[str]: List of new files found ready for processing
        """
        try:
            import glob

            # Set minimum age for a file to be considered stable (seconds)
            # This helps prevent processing files that are still being written
            min_file_age_seconds = 5  # Default to 5 seconds

            # Get current time for age calculations
            current_time = time.time()

            # Get all files matching patterns
            all_files = set()
            for pattern in self.file_patterns:
                pattern_path = os.path.join(self.directory, pattern)
                matching_files = glob.glob(pattern_path)
                # Add to the set of all files
                all_files.update(matching_files)

            # Find new files (those not in observed_files)
            new_files_set = all_files - self.observed_files
            new_files = []

            # Check each new file to see if it's ready for processing
            for file_path in new_files_set:
                try:
                    # Get file modification time
                    file_mod_time = os.path.getmtime(file_path)
                    file_age = current_time - file_mod_time

                    # Make sure the file is stable (hasn't been modified recently)
                    if file_age >= min_file_age_seconds:
                        # Get file size
                        file_size = os.path.getsize(file_path)

                        # Skip empty files
                        if file_size == 0:
                            self.logger.warning(f"Skipping empty file: {os.path.basename(file_path)}")
                            continue

                        # Add to the list of files ready for processing
                        new_files.append(file_path)
                    else:
                        # File is too new, will be processed in a future scan
                        self.logger.debug(f"File too recent, waiting for stability: {os.path.basename(file_path)}")
                except Exception as e:
                    self.logger.warning(f"Error checking file {os.path.basename(file_path)}: {str(e)}")

            # Update observed files to include all matching files
            self.observed_files = all_files

            # Update scan time
            self.last_scan_time = time.time()

            # Return new files ready for processing
            return new_files

        except Exception as e:
            self.logger.error(f"Error scanning directory: {str(e)}")
            return []

    def _monitor_loop(self) -> None:
        """Main loop for monitoring directory for new files."""
        self.logger.info("Monitoring loop started")

        # poll_interval is already a property of the class

        while not self._stop_event.is_set():
            try:
                # Scan for new files
                new_files = self._scan_directory()

                # Process new files
                for file_path in new_files:
                    self.logger.info(f"Found new file: {os.path.basename(file_path)}")

                    # Put in queue for processing
                    self._file_queue.put(file_path)

                    # Call callback if registered
                    if self._file_callback:
                        try:
                            self._file_callback(file_path)
                        except Exception as e:
                            self.logger.error(f"Error in file callback: {str(e)}")

                # Sleep for poll interval
                self._stop_event.wait(self.poll_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                # Sleep a bit before retrying to avoid tight loops in case of repeated errors
                time.sleep(5)

        self.logger.info("Monitoring loop stopped")