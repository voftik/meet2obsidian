"""Processing queue system for meet2obsidian."""

import os
import json
import logging
import threading
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from datetime import datetime
from pathlib import Path
import time

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor

logger = logging.getLogger(__name__)


class ProcessingQueue:
    """A queue for managing file processing."""
    
    def __init__(self, processor: FileProcessor, 
                 persistence_dir: Optional[str] = None,
                 max_concurrent: int = 3,
                 auto_start: bool = True):
        """Initialize the processing queue.
        
        Args:
            processor: FileProcessor instance for processing files
            persistence_dir: Directory to store queue state for persistence
            max_concurrent: Maximum number of files to process concurrently
            auto_start: Whether to start the queue processing thread automatically
        """
        self.processor = processor
        self.persistence_dir = persistence_dir
        self.max_concurrent = max_concurrent
        
        # Core queue data structure
        self._queue: Dict[str, ProcessingState] = {}
        self._queue_lock = threading.RLock()
        
        # Processing thread management
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._processing_interval = 1.0  # seconds
        
        # Tracking sets for quick status lookups
        self._pending_files: Set[str] = set()
        self._processing_files: Set[str] = set()
        self._completed_files: Set[str] = set()
        self._error_files: Set[str] = set()
        self._failed_files: Set[str] = set()
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable[[ProcessingState], None]]] = {
            "added": [],
            "status_changed": [],
            "removed": []
        }
        
        # Register for processor callbacks
        for status in ProcessingStatus:
            self.processor.register_callback(status, self._handle_processor_callback)
        
        # Load persisted state if available
        if persistence_dir:
            self._load_state()
        
        # Start processing thread if auto_start is True
        if auto_start:
            self.start()
    
    def start(self) -> None:
        """Start the queue processing thread."""
        with self._queue_lock:
            if self._processing_thread and self._processing_thread.is_alive():
                logger.warning("Processing thread already running")
                return
            
            self._stop_event.clear()
            self._processing_thread = threading.Thread(
                target=self._processing_loop,
                name="processing-queue-thread"
            )
            self._processing_thread.daemon = True
            self._processing_thread.start()
            logger.info("Processing queue started")
    
    def stop(self, wait: bool = True, timeout: Optional[float] = 30.0) -> bool:
        """Stop the queue processing thread.
        
        Args:
            wait: Whether to wait for the processing thread to stop
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if thread stopped successfully, False if timeout occurred
        """
        logger.info("Stopping processing queue")
        self._stop_event.set()
        
        if wait and self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout)
            stopped = not self._processing_thread.is_alive()
            if stopped:
                logger.info("Processing queue stopped")
            else:
                logger.warning("Timeout while stopping processing queue")
            return stopped
        
        return True
    
    def add_file(self, file_path: str, priority: int = 0, 
                metadata: Optional[Dict[str, Any]] = None,
                max_retries: int = 3) -> ProcessingState:
        """Add a file to the processing queue.
        
        Args:
            file_path: Path to the file to process
            priority: Processing priority (higher numbers = higher priority)
            metadata: Additional metadata for the processor
            max_retries: Maximum number of retry attempts on error
            
        Returns:
            The created processing state
        
        Raises:
            ValueError: If the file is already in the queue
        """
        with self._queue_lock:
            if file_path in self._queue:
                raise ValueError(f"File already in queue: {file_path}")
            
            state = ProcessingState(
                file_path=file_path,
                status=ProcessingStatus.PENDING,
                priority=priority,
                added_time=datetime.now(),
                max_retries=max_retries,
                metadata=metadata or {}
            )
            
            self._queue[file_path] = state
            self._pending_files.add(file_path)
            self._persist_state()
            
            # Trigger added callbacks
            for callback in self._callbacks["added"]:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in add_file callback: {e}")
            
            logger.info(f"Added file to queue: {file_path}")
            return state
    
    def remove_file(self, file_path: str) -> Optional[ProcessingState]:
        """Remove a file from the processing queue.
        
        Args:
            file_path: Path to the file to remove
            
        Returns:
            The removed processing state, or None if not found
        """
        with self._queue_lock:
            if file_path not in self._queue:
                return None
            
            state = self._queue.pop(file_path)
            
            # Remove from tracking sets
            self._pending_files.discard(file_path)
            self._processing_files.discard(file_path)
            self._completed_files.discard(file_path)
            self._error_files.discard(file_path)
            self._failed_files.discard(file_path)
            
            self._persist_state()
            
            # Trigger removed callbacks
            for callback in self._callbacks["removed"]:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in remove_file callback: {e}")
            
            logger.info(f"Removed file from queue: {file_path}")
            return state
    
    def get_state(self, file_path: str) -> Optional[ProcessingState]:
        """Get the processing state for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            The processing state, or None if not found
        """
        with self._queue_lock:
            return self._queue.get(file_path)
    
    def get_all_states(self) -> Dict[str, ProcessingState]:
        """Get all processing states.
        
        Returns:
            Dictionary mapping file paths to their processing states
        """
        with self._queue_lock:
            return self._queue.copy()
    
    def get_files_by_status(self, status: ProcessingStatus) -> List[str]:
        """Get all files with the given status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of file paths with the given status
        """
        with self._queue_lock:
            if status == ProcessingStatus.PENDING:
                return list(self._pending_files)
            elif status == ProcessingStatus.PROCESSING:
                return list(self._processing_files)
            elif status == ProcessingStatus.COMPLETED:
                return list(self._completed_files)
            elif status == ProcessingStatus.ERROR:
                return list(self._error_files)
            elif status == ProcessingStatus.FAILED:
                return list(self._failed_files)
            return []
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics.
        
        Returns:
            Dictionary with queue statistics
        """
        with self._queue_lock:
            return {
                "total": len(self._queue),
                "pending": len(self._pending_files),
                "processing": len(self._processing_files),
                "completed": len(self._completed_files),
                "error": len(self._error_files),
                "failed": len(self._failed_files)
            }
    
    def retry_file(self, file_path: str) -> bool:
        """Retry processing a file that encountered an error.
        
        Args:
            file_path: Path to the file to retry
            
        Returns:
            True if the file was reset for retry, False otherwise
        """
        with self._queue_lock:
            if file_path not in self._queue:
                return False
            
            state = self._queue[file_path]
            if not state.can_retry():
                return False
            
            # Reset state for retry
            state.reset_for_retry()
            
            # Update tracking sets
            self._error_files.discard(file_path)
            self._pending_files.add(file_path)
            
            self._persist_state()
            
            # Trigger status changed callbacks
            for callback in self._callbacks["status_changed"]:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in retry_file callback: {e}")
            
            logger.info(f"Reset file for retry: {file_path}")
            return True
    
    def retry_all_errors(self) -> int:
        """Retry all files that encountered errors and can be retried.
        
        Returns:
            Number of files reset for retry
        """
        count = 0
        with self._queue_lock:
            error_files = list(self._error_files)  # Copy to avoid modification during iteration
            
            for file_path in error_files:
                if self.retry_file(file_path):
                    count += 1
            
            logger.info(f"Reset {count} files for retry")
            return count
    
    def clear_completed(self) -> int:
        """Remove all completed files from the queue.
        
        Returns:
            Number of files removed
        """
        count = 0
        with self._queue_lock:
            completed_files = list(self._completed_files)  # Copy to avoid modification during iteration
            
            for file_path in completed_files:
                if self.remove_file(file_path):
                    count += 1
            
            logger.info(f"Cleared {count} completed files")
            return count
    
    def register_callback(self, event_type: str, 
                         callback: Callable[[ProcessingState], None]) -> bool:
        """Register a callback for queue events.
        
        Args:
            event_type: Event type ('added', 'status_changed', 'removed')
            callback: Function to call when the event occurs
            
        Returns:
            True if registered successfully, False otherwise
        """
        if event_type not in self._callbacks:
            return False
        
        self._callbacks[event_type].append(callback)
        return True
    
    def _handle_processor_callback(self, state: ProcessingState) -> None:
        """Handle callbacks from the processor.

        Args:
            state: Updated processing state
        """
        with self._queue_lock:
            if state.file_path not in self._queue:
                return

            # Update our state copy
            current_state = self._queue[state.file_path]
            old_status = current_state.status

            # Copy relevant fields from the updated state
            current_state.status = state.status
            current_state.start_time = state.start_time
            current_state.end_time = state.end_time
            current_state.error_count = state.error_count
            current_state.last_error = state.last_error

            # Update tracking sets if status changed
            if old_status != state.status:
                self._update_tracking_sets(state.file_path, old_status, state.status)

                # Trigger status changed callbacks
                for callback in self._callbacks["status_changed"]:
                    try:
                        callback(current_state)
                    except Exception as e:
                        logger.error(f"Error in status_changed callback: {e}")

            self._persist_state()
    
    def _update_tracking_sets(self, file_path: str,
                             old_status: ProcessingStatus,
                             new_status: ProcessingStatus) -> None:
        """Update tracking sets when a file's status changes.

        Args:
            file_path: Path to the file
            old_status: Previous status
            new_status: New status
        """
        # Get the appropriate set for the old status
        old_set = None
        if old_status == ProcessingStatus.PENDING:
            old_set = self._pending_files
        elif old_status == ProcessingStatus.PROCESSING:
            old_set = self._processing_files
        elif old_status == ProcessingStatus.COMPLETED:
            old_set = self._completed_files
        elif old_status == ProcessingStatus.ERROR:
            old_set = self._error_files
        elif old_status == ProcessingStatus.FAILED:
            old_set = self._failed_files

        # Get the appropriate set for the new status
        new_set = None
        if new_status == ProcessingStatus.PENDING:
            new_set = self._pending_files
        elif new_status == ProcessingStatus.PROCESSING:
            new_set = self._processing_files
        elif new_status == ProcessingStatus.COMPLETED:
            new_set = self._completed_files
        elif new_status == ProcessingStatus.ERROR:
            new_set = self._error_files
        elif new_status == ProcessingStatus.FAILED:
            new_set = self._failed_files

        # Remove from old set and add to new set
        if old_set is not None:
            old_set.discard(file_path)

        if new_set is not None:
            new_set.add(file_path)

        # Log the update for debugging
        logger.debug(f"Updated tracking sets for {file_path}: {old_status.value} -> {new_status.value}")
    
    def _processing_loop(self) -> None:
        """Main processing loop that processes pending files."""
        while not self._stop_event.is_set():
            try:
                self._process_pending_files()
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
            
            # Wait for the next processing interval
            if not self._stop_event.wait(self._processing_interval):
                continue
            else:
                break
    
    def _process_pending_files(self) -> None:
        """Process pending files based on priority and available slots."""
        with self._queue_lock:
            # Check if we have capacity to process more files
            active_count = self.processor.active_count
            available_slots = max(0, self.max_concurrent - active_count)
            
            if available_slots <= 0 or not self._pending_files:
                return
            
            # Get pending files ordered by priority (highest first)
            pending_states = [
                self._queue[file_path] for file_path in self._pending_files
                if file_path in self._queue
            ]
            
            # Sort by priority (higher first) then by added time (older first)
            pending_states.sort(key=lambda s: (-s.priority, s.added_time))
            
            # Process up to available_slots files
            for state in pending_states[:available_slots]:
                try:
                    # Update status to mark as processing
                    file_path = state.file_path
                    
                    # Start processing in a thread via the processor
                    self.processor.process(state)
                    
                    logger.debug(f"Started processing file: {file_path}")
                except Exception as e:
                    logger.error(f"Error starting processing for {state.file_path}: {e}")
    
    def _persist_state(self) -> None:
        """Persist the queue state to disk."""
        if not self.persistence_dir:
            return

        try:
            # Create directory with parents if it doesn't exist
            Path(self.persistence_dir).mkdir(parents=True, exist_ok=True)

            # Create a serializable representation of the queue
            state_data = {
                "queue": {path: state.to_dict() for path, state in self._queue.items()},
                "saved_at": datetime.now().isoformat()
            }

            # Write to file atomically using a temporary file
            state_file = os.path.join(self.persistence_dir, "queue_state.json")
            temp_file = f"{state_file}.tmp"

            with open(temp_file, "w") as f:
                json.dump(state_data, f, indent=2)

            # Rename temp file to actual file (atomic operation)
            os.replace(temp_file, state_file)

            logger.debug("Queue state persisted")
        except Exception as e:
            logger.error(f"Error persisting queue state: {e}")
    
    def _load_state(self) -> None:
        """Load the queue state from disk."""
        if not self.persistence_dir:
            return
        
        state_file = os.path.join(self.persistence_dir, "queue_state.json")
        
        if not os.path.exists(state_file):
            logger.info("No queue state file found, starting with empty queue")
            return
        
        try:
            with open(state_file, "r") as f:
                state_data = json.load(f)
            
            if "queue" not in state_data:
                logger.warning("Invalid queue state file, missing 'queue' key")
                return
            
            # Clear current queue
            self._queue.clear()
            self._pending_files.clear()
            self._processing_files.clear()
            self._completed_files.clear()
            self._error_files.clear()
            self._failed_files.clear()
            
            # Load queue states
            for file_path, state_dict in state_data["queue"].items():
                # Skip non-existent files
                if not os.path.exists(file_path):
                    logger.warning(f"Skipping non-existent file: {file_path}")
                    continue
                
                try:
                    state = ProcessingState.from_dict(state_dict)
                    self._queue[file_path] = state
                    
                    # Reset any PROCESSING states to PENDING
                    if state.status == ProcessingStatus.PROCESSING:
                        state.status = ProcessingStatus.PENDING
                        state.start_time = None
                        state.end_time = None
                    
                    # Update tracking sets
                    if state.status == ProcessingStatus.PENDING:
                        self._pending_files.add(file_path)
                    elif state.status == ProcessingStatus.COMPLETED:
                        self._completed_files.add(file_path)
                    elif state.status == ProcessingStatus.ERROR:
                        self._error_files.add(file_path)
                    elif state.status == ProcessingStatus.FAILED:
                        self._failed_files.add(file_path)
                        
                except Exception as e:
                    logger.error(f"Error loading state for {file_path}: {e}")
            
            logger.info(f"Loaded queue state with {len(self._queue)} files")
        except Exception as e:
            logger.error(f"Error loading queue state: {e}")
