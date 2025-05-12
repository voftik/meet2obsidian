"""
File watcher module based on watchdog library.

This module provides a FileWatcher class that uses the watchdog library to monitor
directories for file system events and detect when files are stable and ready for processing.
"""

import os
import time
import logging
import fnmatch
from typing import List, Optional, Callable, Dict, Set
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent, FileModifiedEvent


class FileWatcherEventHandler(FileSystemEventHandler):
    """Custom event handler for FileWatcher."""
    
    def __init__(self, watcher):
        """
        Initialize with a reference to the parent FileWatcher.
        
        Args:
            watcher: The FileWatcher instance that created this handler
        """
        self.watcher = watcher
        self.logger = watcher.logger
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        file_path = event.src_path
        self.logger.debug(f"File created: {file_path}")
        self.watcher._add_pending_file(file_path)
    
    def on_moved(self, event):
        """Handle file move events (often used by applications when saving files)."""
        if event.is_directory:
            return
            
        file_path = event.dest_path
        self.logger.debug(f"File moved: {file_path}")
        self.watcher._add_pending_file(file_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = event.src_path
        self.logger.debug(f"File modified: {file_path}")
        
        # If the file is already in pending files, update its modify time
        self.watcher._update_pending_file(file_path)


class FileWatcher:
    """
    File watcher based on watchdog for monitoring directories for new files.

    This class monitors directories for new files, tracks when files are done
    being copied, and filters files based on extension patterns.
    """

    # Constants for stability detection
    MIN_STABLE_COUNT = 2  # Minimum number of checks with stable size

    def __init__(self,
                 directory: str,
                 file_patterns: Optional[List[str]] = None,
                 min_file_age_seconds: int = 5,
                 stability_check_interval: int = 2,
                 logger = None):
        """
        Initialize FileWatcher.

        Args:
            directory: Directory to monitor
            file_patterns: List of glob patterns to match files against (e.g., "*.mp4")
            min_file_age_seconds: Minimum age of a file in seconds before it's considered stable
            stability_check_interval: Interval in seconds between stability checks
            logger: Optional logger instance

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if min_file_age_seconds < 0:
            raise ValueError("min_file_age_seconds must be non-negative")
        if stability_check_interval <= 0:
            raise ValueError("stability_check_interval must be positive")

        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.file_patterns = file_patterns or ["*.mp4", "*.mov", "*.webm", "*.mkv"]
        self.min_file_age_seconds = min_file_age_seconds
        self.stability_check_interval = stability_check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize internal state
        self.is_watching = False
        self._file_callback = None
        self._observer = None
        self._event_handler = None
        
        # Pending files dictionary: path -> {first_seen, last_modified, size, size_stable_count}
        self._pending_files: Dict[str, Dict] = {}
        self._processed_files: Set[str] = set()
        
        # Thread for checking file stability
        self._stability_thread = None
        self._stop_event = threading.Event()
    
    def start(self, callback: Callable[[str], None] = None) -> bool:
        """
        Start watching the directory.
        
        Args:
            callback: Function to call when a stable file is detected
            
        Returns:
            bool: True if watching started successfully, False otherwise
        """
        if self.is_watching:
            self.logger.info("FileWatcher is already running")
            return True
        
        if not os.path.exists(self.directory):
            self.logger.error(f"Directory does not exist: {self.directory}")
            return False
        
        try:
            # Store callback
            self._file_callback = callback
            
            # Create and start the watchdog observer
            self._event_handler = FileWatcherEventHandler(self)
            self._observer = Observer()
            self._observer.schedule(
                self._event_handler,
                self.directory,
                recursive=False
            )
            self._observer.start()
            
            # Reset the stop event
            self._stop_event.clear()
            
            # Start the stability check thread
            self._stability_thread = threading.Thread(
                target=self._stability_check_loop,
                name="FileWatcherStabilityCheck",
                daemon=True
            )
            self._stability_thread.start()
            
            self.is_watching = True
            self.logger.info(f"Started watching directory: {self.directory}")
            self.logger.info(f"Watching for files matching: {', '.join(self.file_patterns)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting file watcher: {str(e)}")
            self._cleanup()
            return False
    
    def stop(self) -> bool:
        """
        Stop watching the directory.
        
        Returns:
            bool: True if watching stopped successfully, False otherwise
        """
        if not self.is_watching:
            self.logger.info("FileWatcher is not running")
            return True
        
        try:
            # Signal threads to stop
            self._stop_event.set()
            
            # Stop and join the observer
            if self._observer:
                self._observer.stop()
                self._observer.join(timeout=5.0)
            
            # Join the stability thread (if it exists)
            if self._stability_thread and self._stability_thread.is_alive():
                self._stability_thread.join(timeout=5.0)
            
            self._cleanup()
            self.logger.info("Stopped watching directory")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping file watcher: {str(e)}")
            self._cleanup()  # Still try to clean up
            return False
    
    def _cleanup(self):
        """Clean up resources."""
        self.is_watching = False
        self._observer = None
        self._event_handler = None
        self._stability_thread = None
        self._file_callback = None
    
    def _add_pending_file(self, file_path: str):
        """
        Add a file to the pending files dictionary if it matches patterns.
        
        Args:
            file_path: Path to the file
        """
        # Check if the file matches the patterns
        if not self._matches_patterns(file_path):
            return
        
        # Check if we've already processed this file
        if file_path in self._processed_files:
            return
        
        # Get current time
        current_time = time.time()
        
        # Add or update in pending files
        if file_path not in self._pending_files:
            self._pending_files[file_path] = {
                'first_seen': current_time,
                'last_modified': current_time,
                'size': self._get_file_size(file_path),
                'size_stable_count': 0
            }
            self.logger.debug(f"Added file to pending: {file_path}")
        else:
            # Already in pending, just update last_modified
            self._update_pending_file(file_path)
    
    def _update_pending_file(self, file_path: str):
        """
        Update the last modified time of a pending file.
        
        Args:
            file_path: Path to the file
        """
        if file_path in self._pending_files:
            current_time = time.time()
            current_size = self._get_file_size(file_path)
            
            # Update the file info
            self._pending_files[file_path]['last_modified'] = current_time
            
            # Check if size changed
            if current_size != self._pending_files[file_path]['size']:
                self._pending_files[file_path]['size'] = current_size
                self._pending_files[file_path]['size_stable_count'] = 0
            
            self.logger.debug(f"Updated pending file: {file_path}")
    
    def _stability_check_loop(self):
        """
        Background thread to periodically check file stability.
        """
        self.logger.debug("Starting stability check loop")
        
        while not self._stop_event.is_set():
            try:
                # Find stable files
                stable_files = self._check_for_stable_files()
                
                # Process stable files
                for file_path in stable_files:
                    self._process_stable_file(file_path)
                
                # Wait for next check, but allow interruption
                self._stop_event.wait(self.stability_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in stability check loop: {str(e)}")
                # Don't exit the loop on error, just try again after the interval
                self._stop_event.wait(self.stability_check_interval)
        
        self.logger.debug("Stability check loop stopped")
    
    def _check_for_stable_files(self) -> List[str]:
        """
        Check for files that have stabilized.

        Returns:
            List[str]: List of stable file paths
        """
        current_time = time.time()
        stable_files = []
        files_to_remove = []

        for file_path, info in self._pending_files.items():
            # Skip if file is deleted
            if not os.path.exists(file_path):
                files_to_remove.append(file_path)
                continue

            # Get current file size
            current_size = self._get_file_size(file_path)

            # Reject empty files immediately
            if current_size == 0:
                self.logger.warning(f"Rejecting empty file: {file_path}")
                files_to_remove.append(file_path)
                continue

            # Update size if changed
            if current_size != info['size']:
                info['size'] = current_size
                info['last_modified'] = current_time
                info['size_stable_count'] = 0
                continue

            # Count periods where size is stable
            info['size_stable_count'] += 1

            # Calculate age in seconds
            age_seconds = current_time - info['first_seen']

            # Check if file is stable
            is_old_enough = age_seconds >= self.min_file_age_seconds
            is_size_stable = info['size_stable_count'] >= self.MIN_STABLE_COUNT

            if is_old_enough and is_size_stable:
                # File is stable
                stable_files.append(file_path)
                files_to_remove.append(file_path)

        # Clean up files that are stable or deleted
        for file_path in files_to_remove:
            self._pending_files.pop(file_path, None)

        return stable_files
    
    def _process_stable_file(self, file_path: str):
        """
        Process a stable file by calling the callback function.
        
        Args:
            file_path: Path to the stable file
        """
        self.logger.info(f"File is stable and ready for processing: {file_path}")
        
        # Remember this file as processed
        self._processed_files.add(file_path)
        
        # Call the callback if set
        if self._file_callback:
            try:
                self._file_callback(file_path)
            except Exception as e:
                self.logger.error(f"Error in file callback: {str(e)}")
    
    def _matches_patterns(self, file_path: str) -> bool:
        """
        Check if the file matches one of the patterns.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if the file matches a pattern, False otherwise
        """
        if not self.file_patterns:
            return True

        filename = os.path.basename(file_path).lower()

        for pattern in self.file_patterns:
            if fnmatch.fnmatch(filename, pattern.lower()):
                return True

        return False
    
    def _get_file_size(self, file_path: str) -> int:
        """
        Get the size of a file.

        Args:
            file_path: Path to the file

        Returns:
            int: Size of the file in bytes, or 0 if the file doesn't exist
        """
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError) as e:
            self.logger.debug(f"Error getting file size for {file_path}: {str(e)}")
            return 0