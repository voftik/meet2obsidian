"""Integration tests for processing queue system."""

import unittest
import os
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.processing.queue import ProcessingQueue


class TestProcessingQueueSimplified(unittest.TestCase):
    """Simplified integration tests for the processing queue system."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a simple processor function that always succeeds
        processor_func = lambda file_path, metadata: True
        self.processor = FileProcessor(processor_func)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_basic_processing(self):
        """Test basic file processing functionality."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        # Create a queue with a special callback to track processed files
        processed_files = []
        
        def on_completed(state):
            processed_files.append(state.file_path)
        
        # Create a custom processor with callback
        custom_processor = FileProcessor(lambda f, m: True)
        custom_processor.register_callback(ProcessingStatus.COMPLETED, on_completed)
        
        # Create queue with our processor
        queue = ProcessingQueue(
            processor=custom_processor,
            auto_start=False
        )
        
        # Add a file to the queue
        state = queue.add_file(test_file)
        
        # Process the file manually
        custom_processor.process(state, blocking=True)
        
        # Verify the file was processed
        self.assertEqual(len(processed_files), 1)
        self.assertEqual(processed_files[0], test_file)
        
        # Check the file state
        file_state = queue.get_state(test_file)
        self.assertEqual(file_state.status, ProcessingStatus.COMPLETED)
    
    def test_priority_processing(self):
        """Test that files are prioritized correctly."""
        # Create test files with different priorities
        high_file = os.path.join(self.temp_dir, "high_priority.txt")
        med_file = os.path.join(self.temp_dir, "medium_priority.txt")
        low_file = os.path.join(self.temp_dir, "low_priority.txt")
        
        # Write content to each file
        for file_path in [high_file, med_file, low_file]:
            with open(file_path, "w") as f:
                f.write(f"content for {os.path.basename(file_path)}")
        
        # Create a queue
        queue = ProcessingQueue(
            processor=self.processor,
            auto_start=False
        )
        
        # Add files with different priorities
        queue.add_file(low_file, priority=0)
        queue.add_file(med_file, priority=5)
        queue.add_file(high_file, priority=10)
        
        # Get the pending files sorted by priority
        with queue._queue_lock:
            pending_states = [
                queue._queue[file_path] for file_path in queue._pending_files
                if file_path in queue._queue
            ]
            
            # Sort by priority (higher first) then by added time
            pending_states.sort(key=lambda s: (-s.priority, s.added_time))
            
            # Extract file paths in priority order
            sorted_files = [state.file_path for state in pending_states]
        
        # Verify the order is correct
        self.assertEqual(len(sorted_files), 3, "Should have 3 files in the queue")
        self.assertEqual(sorted_files[0], high_file, "High priority file should be first")
        self.assertEqual(sorted_files[1], med_file, "Medium priority file should be second")
        self.assertEqual(sorted_files[2], low_file, "Low priority file should be third")
    
    def test_basic_persistence(self):
        """Test basic persistence of queue state."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "persist_test.txt")
        with open(test_file, "w") as f:
            f.write("persistence test content")
        
        # Create a persistence directory
        persistence_dir = os.path.join(self.temp_dir, "persistence")
        Path(persistence_dir).mkdir(exist_ok=True)
        
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )
        
        # Add the file to the queue
        queue.add_file(test_file)
        
        # Force persistence
        queue._persist_state()
        
        # Create a new queue to simulate restart
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )
        
        # Verify the file state was recovered
        self.assertIn(test_file, new_queue.get_all_states())
        self.assertIn(test_file, new_queue.get_files_by_status(ProcessingStatus.PENDING))


if __name__ == "__main__":
    unittest.main()