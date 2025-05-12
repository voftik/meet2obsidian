"""File processor for meet2obsidian."""

from typing import Callable, Dict, Any, Optional, List, Tuple
from pathlib import Path
import threading
import logging
from datetime import datetime

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processor for handling file processing operations."""
    
    def __init__(self, processor_func: Callable[[str, Dict[str, Any]], bool]):
        """Initialize the file processor.
        
        Args:
            processor_func: Function that processes a file. Takes file path and metadata dict.
                Returns True if processing was successful, False otherwise.
        """
        self.processor_func = processor_func
        self._lock = threading.RLock()
        self._active_threads: Dict[str, threading.Thread] = {}
        self._callbacks: Dict[ProcessingStatus, List[Callable[[ProcessingState], None]]] = {
            status: [] for status in ProcessingStatus
        }
    
    def register_callback(self, status: ProcessingStatus, 
                          callback: Callable[[ProcessingState], None]) -> None:
        """Register a callback for a specific processing status.
        
        Args:
            status: The processing status to trigger the callback for
            callback: Function to call when a file reaches the given status
        """
        with self._lock:
            self._callbacks[status].append(callback)
    
    def _trigger_callbacks(self, state: ProcessingState) -> None:
        """Trigger callbacks for the current state's status.

        Args:
            state: Current processing state
        """
        try:
            callbacks = self._callbacks.get(state.status, [])
            for callback in callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in callback for {state.file_path}: {e}")
        except Exception as e:
            logger.error(f"Error triggering callbacks for {state.file_path}: {e}")
    
    def process(self, state: ProcessingState, blocking: bool = False) -> None:
        """Process a file based on its state.
        
        Args:
            state: The processing state of the file
            blocking: If True, process synchronously; otherwise process in a thread
        """
        if blocking:
            self._process_file(state)
        else:
            self._start_processing_thread(state)
    
    def _start_processing_thread(self, state: ProcessingState) -> None:
        """Start a new thread to process the file.
        
        Args:
            state: The processing state of the file
        """
        with self._lock:
            # Check if already processing this file
            if state.file_path in self._active_threads:
                if self._active_threads[state.file_path].is_alive():
                    logger.warning(f"Already processing {state.file_path}")
                    return
                else:
                    # Thread is dead, remove it
                    del self._active_threads[state.file_path]
            
            # Create and start new thread
            thread = threading.Thread(
                target=self._process_file,
                args=(state,),
                name=f"processor-{Path(state.file_path).name}"
            )
            thread.daemon = True  # Don't block program exit
            self._active_threads[state.file_path] = thread
            thread.start()
    
    def _process_file(self, state: ProcessingState) -> None:
        """Process a file and update its state.
        
        Args:
            state: The processing state of the file
        """
        if state.status != ProcessingStatus.PENDING:
            logger.warning(f"Cannot process file not in PENDING state: {state.file_path}")
            return
        
        # Update state to processing
        state.mark_processing()
        self._trigger_callbacks(state)
        logger.info(f"Processing file: {state.file_path}")
        
        try:
            # Call the processor function
            success = self.processor_func(state.file_path, state.metadata)
            
            if success:
                state.mark_completed()
                logger.info(f"Successfully processed: {state.file_path}")
            else:
                state.mark_error("Processing function returned False")
                logger.warning(f"Processing failed: {state.file_path}")
                
        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            state.mark_error(error_msg)
            logger.error(f"{error_msg} - File: {state.file_path}")
        
        # Update state and trigger callbacks
        with self._lock:
            if state.file_path in self._active_threads:
                del self._active_threads[state.file_path]
        
        self._trigger_callbacks(state)
    
    def cancel_all(self) -> None:
        """Cancel all running processing threads.
        
        Note: This doesn't actually stop the threads (Python doesn't support
        forceful thread termination), but marks them as canceled for cleanup.
        """
        with self._lock:
            self._active_threads.clear()
    
    def wait_all(self, timeout: Optional[float] = None) -> bool:
        """Wait for all processing threads to complete.
        
        Args:
            timeout: Maximum time to wait in seconds, or None to wait indefinitely
            
        Returns:
            True if all threads completed, False if timeout occurred
        """
        start_time = datetime.now()
        threads_copy = []
        
        with self._lock:
            threads_copy = list(self._active_threads.values())
        
        for thread in threads_copy:
            remaining_time = None
            if timeout is not None:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    return False
                remaining_time = timeout - elapsed
            
            thread.join(remaining_time)
            if timeout is not None and thread.is_alive():
                return False
        
        return True
    
    @property
    def active_count(self) -> int:
        """Get the number of active processing threads."""
        with self._lock:
            return sum(1 for t in self._active_threads.values() if t.is_alive())
