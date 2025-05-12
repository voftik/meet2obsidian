"""Integration tests for processing queue persistence and recovery."""

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


class TestProcessingQueuePersistence(unittest.TestCase):
    """Integration tests for processing queue persistence and recovery."""
    
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
    
    def test_basic_persistence_and_recovery(self):
        """Test basic persistence and recovery of queue state."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        # Create a persistence directory
        persistence_dir = os.path.join(self.temp_dir, "persistence")
        Path(persistence_dir).mkdir(exist_ok=True)
        
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )
        
        # Add a file to the queue
        queue.add_file(test_file)
        
        # Force persistence
        queue._persist_state()
        
        # Check that the state file was created
        state_file = os.path.join(persistence_dir, "queue_state.json")
        self.assertTrue(os.path.exists(state_file))
        
        # Create a new queue instance to simulate restart
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )
        
        # Verify that the state was recovered
        self.assertIn(test_file, new_queue.get_all_states())
        self.assertIn(test_file, new_queue.get_files_by_status(ProcessingStatus.PENDING))
        

if __name__ == "__main__":
    unittest.main()