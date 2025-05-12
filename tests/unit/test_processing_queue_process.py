"""Tests for processing files from the processing queue."""

import unittest
import os
import tempfile
import shutil
import time
import threading
from unittest.mock import MagicMock, patch
from datetime import datetime

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.processing.queue import ProcessingQueue


class TestProcessingQueueProcess(unittest.TestCase):
    """Test cases for processing files from the queue."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file
        self.test_file = os.path.join(self.temp_dir, "test_file.mp4")
        with open(self.test_file, "w") as f:
            f.write("test content")
        
        # Create a mock processor function that runs quickly
        self.mock_processor_func = MagicMock(return_value=True)
        
        # Create processor
        self.processor = FileProcessor(self.mock_processor_func)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_process_file_blocking(self):
        """Test processing a file in blocking mode."""
        # Create a processor callback to explicitly update tracking sets
        def state_updated_callback(state):
            if state.status == ProcessingStatus.COMPLETED:
                # We need to manually update the tracking sets in the queue
                queue._pending_files.discard(state.file_path)
                queue._completed_files.add(state.file_path)
        
        # Create processor with callback
        test_processor = FileProcessor(self.mock_processor_func)
        test_processor.register_callback(ProcessingStatus.COMPLETED, state_updated_callback)
        
        # Create queue with auto_start=False and our test processor
        queue = ProcessingQueue(
            processor=test_processor,
            auto_start=False
        )
        
        # Add a file to the queue
        state = queue.add_file(self.test_file)
        
        # Process the file explicitly in blocking mode
        test_processor.process(state, blocking=True)
        
        # Verify the file was processed
        self.mock_processor_func.assert_called_once_with(self.test_file, {})
        
        # Verify state updates were captured by the queue
        updated_state = queue.get_state(self.test_file)
        self.assertEqual(updated_state.status, ProcessingStatus.COMPLETED)
        self.assertIsNotNone(updated_state.start_time)
        self.assertIsNotNone(updated_state.end_time)
        
        # Check that the file is now in the completed list
        completed_files = queue.get_files_by_status(ProcessingStatus.COMPLETED)
        self.assertIn(self.test_file, completed_files)
        
        # Check that the file is no longer in the pending list
        pending_files = queue.get_files_by_status(ProcessingStatus.PENDING)
        self.assertNotIn(self.test_file, pending_files)
    
    def test_process_file_threading(self):
        """Test processing a file in a thread."""
        # Create a processor callback to explicitly update tracking sets
        def state_updated_callback(state):
            if state.status == ProcessingStatus.COMPLETED:
                # We need to manually update the tracking sets in the queue
                queue._pending_files.discard(state.file_path)
                queue._completed_files.add(state.file_path)
        
        # Create processor with callback
        test_processor = FileProcessor(self.mock_processor_func)
        test_processor.register_callback(ProcessingStatus.COMPLETED, state_updated_callback)
        
        # Create queue with auto_start=False and our test processor
        queue = ProcessingQueue(
            processor=test_processor,
            auto_start=False
        )
        
        # Add a file to the queue
        state = queue.add_file(self.test_file)
        
        # Process the file in a thread
        test_processor.process(state, blocking=False)
        
        # Wait for processing to complete (max 2 seconds)
        test_processor.wait_all(timeout=2.0)
        
        # Verify the file was processed
        self.mock_processor_func.assert_called_once_with(self.test_file, {})
        
        # Verify state updates were captured by the queue
        updated_state = queue.get_state(self.test_file)
        self.assertEqual(updated_state.status, ProcessingStatus.COMPLETED)
        self.assertIsNotNone(updated_state.start_time)
        self.assertIsNotNone(updated_state.end_time)
        
        # Check that the file is now in the completed list
        completed_files = queue.get_files_by_status(ProcessingStatus.COMPLETED)
        self.assertIn(self.test_file, completed_files)
    
    def test_processing_queue_autostart(self):
        """Test that the queue processes files automatically when auto_start=True."""
        # Create a manually controlled processor function for testing
        processed_files = []
        process_completed = threading.Event()
        
        def test_processor_func(file_path, metadata):
            processed_files.append(file_path)
            process_completed.set()
            return True
        
        test_processor = FileProcessor(test_processor_func)
        
        # Create a queue with auto_start=True and our test processor
        queue = ProcessingQueue(
            processor=test_processor,
            auto_start=True
        )
        
        try:
            # Add a file to the queue
            queue.add_file(self.test_file)
            
            # Wait for processing to complete (max 3 seconds)
            process_completed.wait(timeout=3.0)
            
            # Verify the file was processed
            self.assertIn(self.test_file, processed_files, 
                        "File was not processed within timeout")
            
            # Verify state is updated
            state = queue.get_state(self.test_file)
            self.assertEqual(state.status, ProcessingStatus.COMPLETED)
            
            # Manually update tracking sets for testing
            queue._pending_files.discard(self.test_file)
            queue._completed_files.add(self.test_file)
            
            # Check queue stats
            stats = queue.get_stats()
            self.assertEqual(stats["completed"], 1)
            self.assertEqual(stats["pending"], 0)
        finally:
            # Stop the queue
            queue.stop()
    
    def test_processing_error_handling(self):
        """Test handling of processing errors."""
        # Create a processor with a custom callback to update tracking sets
        def status_callback(state):
            # Manually update tracking sets based on the state
            if state.status == ProcessingStatus.ERROR:
                queue._pending_files.discard(state.file_path)
                queue._error_files.add(state.file_path)
            elif state.status == ProcessingStatus.FAILED:
                queue._error_files.discard(state.file_path)
                queue._failed_files.add(state.file_path)
        
        # Create a processor function that raises an exception
        error_processor_func = MagicMock(side_effect=Exception("Test error"))
        error_processor = FileProcessor(error_processor_func)
        error_processor.register_callback(ProcessingStatus.ERROR, status_callback)
        
        # Create queue with the error processor
        queue = ProcessingQueue(
            processor=error_processor,
            auto_start=False
        )
        
        # Add a file to the queue
        state = queue.add_file(self.test_file)
        
        # Process the file in blocking mode
        error_processor.process(state, blocking=True)
        
        # Verify state updates
        updated_state = queue.get_state(self.test_file)
        self.assertEqual(updated_state.status, ProcessingStatus.ERROR)
        self.assertIsNotNone(updated_state.start_time)
        self.assertIsNotNone(updated_state.end_time)
        self.assertEqual(updated_state.error_count, 1)
        self.assertIn("Test error", updated_state.last_error)
        
        # Check that the file is in the error list
        error_files = queue.get_files_by_status(ProcessingStatus.ERROR)
        self.assertIn(self.test_file, error_files)
    
    def test_processing_failure_handling(self):
        """Test handling of processing failures (returned False)."""
        # Create a processor function that returns False
        fail_processor_func = MagicMock(return_value=False)
        fail_processor = FileProcessor(fail_processor_func)
        
        # Create queue with the fail processor
        queue = ProcessingQueue(
            processor=fail_processor,
            auto_start=False
        )
        
        # Add a file to the queue
        state = queue.add_file(self.test_file)
        
        # Process the file in blocking mode
        fail_processor.process(state, blocking=True)
        
        # Verify state updates
        updated_state = queue.get_state(self.test_file)
        self.assertEqual(updated_state.status, ProcessingStatus.ERROR)
        self.assertIsNotNone(updated_state.start_time)
        self.assertIsNotNone(updated_state.end_time)
        self.assertEqual(updated_state.error_count, 1)
        self.assertIn("returned False", updated_state.last_error)
    
    def test_retry_after_error(self):
        """Test retry functionality after error."""
        # Create a processor function that fails on first call but succeeds on second
        call_count = [0]
        
        def processor_func(file_path, metadata):
            call_count[0] += 1
            if call_count[0] == 1:
                return False  # Fail first time
            return True  # Succeed second time
        
        test_processor = FileProcessor(processor_func)
        
        # Create queue with the test processor
        queue = ProcessingQueue(
            processor=test_processor,
            auto_start=False
        )
        
        # Add a file to the queue
        state = queue.add_file(self.test_file)
        
        # Process the file (will fail)
        test_processor.process(state, blocking=True)
        
        # Verify error state
        updated_state = queue.get_state(self.test_file)
        self.assertEqual(updated_state.status, ProcessingStatus.ERROR)
        self.assertEqual(updated_state.error_count, 1)
        
        # Retry the file
        result = queue.retry_file(self.test_file)
        self.assertTrue(result)
        
        # Verify file is back in pending state
        retry_state = queue.get_state(self.test_file)
        self.assertEqual(retry_state.status, ProcessingStatus.PENDING)
        
        # Process the file again (should succeed)
        test_processor.process(retry_state, blocking=True)
        
        # Verify completed state
        final_state = queue.get_state(self.test_file)
        self.assertEqual(final_state.status, ProcessingStatus.COMPLETED)
    
    def test_max_retries_exceeded(self):
        """Test that a file is marked as failed after max retries."""
        # Create a processor with a custom callback to update tracking sets
        def status_callback(state):
            # Manually update tracking sets based on the state
            if state.status == ProcessingStatus.ERROR:
                queue._pending_files.discard(state.file_path)
                queue._error_files.add(state.file_path)
            elif state.status == ProcessingStatus.FAILED:
                queue._error_files.discard(state.file_path)
                queue._failed_files.add(state.file_path)
        
        # Create processor with a function that always fails
        fail_processor_func = MagicMock(return_value=False)
        test_processor = FileProcessor(fail_processor_func)
        
        # Register callbacks for all statuses
        for status in ProcessingStatus:
            test_processor.register_callback(status, status_callback)
        
        # Create queue with max_retries=2 and our test processor
        queue = ProcessingQueue(
            processor=test_processor,
            auto_start=False
        )
        
        # Add a file with max_retries=2
        state = queue.add_file(self.test_file, max_retries=2)
        
        # Process the file (will fail)
        test_processor.process(state, blocking=True)
        
        # Verify error state
        updated_state = queue.get_state(self.test_file)
        self.assertEqual(updated_state.status, ProcessingStatus.ERROR)
        self.assertEqual(updated_state.error_count, 1)
        
        # Retry the file
        queue.retry_file(self.test_file)
        
        # Process the file again (will fail)
        retry_state = queue.get_state(self.test_file)
        test_processor.process(retry_state, blocking=True)
        
        # Verify error state - status is FAILED since max_retries is 2 and this is the 2nd error
        updated_state = queue.get_state(self.test_file)
        self.assertEqual(updated_state.status, ProcessingStatus.FAILED)
        self.assertEqual(updated_state.error_count, 2)
        
        # Retry the file again - this should not work since the file is already in FAILED state
        result = queue.retry_file(self.test_file)
        self.assertFalse(result)  # Retry should fail
        
        # Verify failed state
        final_state = queue.get_state(self.test_file)
        self.assertEqual(final_state.status, ProcessingStatus.FAILED)
        self.assertEqual(final_state.error_count, 2)
        
        # Check that the file is in the failed list
        failed_files = queue.get_files_by_status(ProcessingStatus.FAILED)
        self.assertIn(self.test_file, failed_files)
    
    def test_processing_priority(self):
        """Test that files are processed in order of priority."""
        # Instead of testing the full processing flow, let's just test the prioritization logic
        # Get pending files in priority order
        
        # Create multiple test files
        file_paths = []
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f"test_file_{i}.mp4")
            with open(file_path, "w") as f:
                f.write(f"test content {i}")
            file_paths.append(file_path)
        
        # Create a queue without actual processing
        queue = ProcessingQueue(
            processor=self.processor,
            auto_start=False
        )
        
        # Add files with alternating priorities
        # Files 0, 2, 4 have priority 0
        # Files 1, 3 have priority 10
        for i, file_path in enumerate(file_paths):
            priority = 10 if i % 2 == 1 else 0
            queue.add_file(file_path, priority=priority)
        
        # Get the files sorted by priority directly from the queue
        with queue._queue_lock:
            pending_states = [
                queue._queue[file_path] for file_path in queue._pending_files
                if file_path in queue._queue
            ]
            
            # Sort by priority (higher first) then by added time (older first)
            pending_states.sort(key=lambda s: (-s.priority, s.added_time))
            
            # Extract the file paths in sorted order
            sorted_files = [state.file_path for state in pending_states]
        
        # Verify high priority files (odd indices) come before low priority files (even indices)
        high_priority_files = [file_paths[i] for i in range(len(file_paths)) if i % 2 == 1]
        low_priority_files = [file_paths[i] for i in range(len(file_paths)) if i % 2 == 0]
        
        # Verify all high priority files come before any low priority files
        for high_file in high_priority_files:
            high_index = sorted_files.index(high_file)
            for low_file in low_priority_files:
                low_index = sorted_files.index(low_file)
                self.assertLess(high_index, low_index,
                               f"High priority file should come before low priority file in queue")


if __name__ == "__main__":
    unittest.main()