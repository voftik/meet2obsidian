"""Tests for queue recovery after application restart."""

import unittest
import os
import tempfile
import shutil
import json
import time
from unittest.mock import MagicMock, patch
from datetime import datetime

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.processing.queue import ProcessingQueue


class TestProcessingQueueRecovery(unittest.TestCase):
    """Test cases for recovering the processing queue after a restart."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory structure
        self.temp_dir = tempfile.mkdtemp()
        self.persistence_dir = os.path.join(self.temp_dir, "queue_state")
        os.makedirs(self.persistence_dir, exist_ok=True)
        
        # Create test files
        self.test_files = []
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f"test_file_{i}.mp4")
            with open(file_path, "w") as f:
                f.write(f"test content {i}")
            self.test_files.append(file_path)
        
        # Create a mock processor function
        self.mock_processor_func = MagicMock(return_value=True)
        
        # Create processor
        self.processor = FileProcessor(self.mock_processor_func)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_basic_queue_persistence(self):
        """Test that the queue state is properly persisted and can be loaded."""
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Add test files to the queue
        for i, file_path in enumerate(self.test_files):
            priority = i  # Different priority for each file
            queue.add_file(file_path, priority=priority)
        
        # Verify state file was created
        state_file = os.path.join(self.persistence_dir, "queue_state.json")
        self.assertTrue(os.path.exists(state_file))
        
        # Create a new queue to simulate restart
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Verify all files were loaded
        for file_path in self.test_files:
            self.assertIn(file_path, new_queue.get_all_states())
        
        # Verify priorities were preserved
        for i, file_path in enumerate(self.test_files):
            state = new_queue.get_state(file_path)
            self.assertEqual(state.priority, i)
    
    def test_queue_recovery_with_different_states(self):
        """Test recovery with files in different states."""
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Add test files to the queue
        for file_path in self.test_files:
            queue.add_file(file_path)
        
        # Process some files to create different states
        # First file: completed
        state1 = queue.get_state(self.test_files[0])
        state1.mark_processing()
        state1.mark_completed()
        
        # Second file: processing (should be reset to pending on load)
        state2 = queue.get_state(self.test_files[1])
        state2.mark_processing()
        
        # Third file: error
        state3 = queue.get_state(self.test_files[2])
        state3.mark_processing()
        state3.mark_error("Test error")
        
        # Fourth file: failed
        state4 = queue.get_state(self.test_files[3])
        for i in range(4):  # Exceed max_retries
            state4.mark_processing()
            state4.mark_error(f"Error {i}")
        
        # Fifth file: pending (unchanged)
        
        # Update tracking sets manually (normally this is done by callback)
        queue._update_tracking_sets(self.test_files[0], ProcessingStatus.PENDING, ProcessingStatus.COMPLETED)
        queue._update_tracking_sets(self.test_files[1], ProcessingStatus.PENDING, ProcessingStatus.PROCESSING)
        queue._update_tracking_sets(self.test_files[2], ProcessingStatus.PENDING, ProcessingStatus.ERROR)
        queue._update_tracking_sets(self.test_files[3], ProcessingStatus.PENDING, ProcessingStatus.FAILED)
        
        # Force persistence
        queue._persist_state()
        
        # Create a new queue to simulate restart
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Verify all files were loaded
        self.assertEqual(len(new_queue.get_all_states()), len(self.test_files))
        
        # Verify status was preserved correctly
        # Completed file should still be completed
        self.assertEqual(
            new_queue.get_state(self.test_files[0]).status,
            ProcessingStatus.COMPLETED
        )
        
        # Processing file should be reset to pending
        self.assertEqual(
            new_queue.get_state(self.test_files[1]).status,
            ProcessingStatus.PENDING
        )
        
        # Error file should still be in error state
        self.assertEqual(
            new_queue.get_state(self.test_files[2]).status,
            ProcessingStatus.ERROR
        )
        
        # Failed file should still be failed
        self.assertEqual(
            new_queue.get_state(self.test_files[3]).status,
            ProcessingStatus.FAILED
        )
        
        # Pending file should still be pending
        self.assertEqual(
            new_queue.get_state(self.test_files[4]).status,
            ProcessingStatus.PENDING
        )
        
        # Check tracking sets
        completed_files = new_queue.get_files_by_status(ProcessingStatus.COMPLETED)
        self.assertIn(self.test_files[0], completed_files)
        
        pending_files = new_queue.get_files_by_status(ProcessingStatus.PENDING)
        self.assertIn(self.test_files[1], pending_files)
        self.assertIn(self.test_files[4], pending_files)
        
        error_files = new_queue.get_files_by_status(ProcessingStatus.ERROR)
        self.assertIn(self.test_files[2], error_files)
        
        failed_files = new_queue.get_files_by_status(ProcessingStatus.FAILED)
        self.assertIn(self.test_files[3], failed_files)
    
    def test_recovery_with_removed_files(self):
        """Test recovery when some files no longer exist on disk."""
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Add test files to the queue
        for file_path in self.test_files:
            queue.add_file(file_path)
        
        # Force persistence
        queue._persist_state()
        
        # Delete some of the files
        os.remove(self.test_files[1])
        os.remove(self.test_files[3])
        
        # Create a new queue to simulate restart
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Verify only existing files were loaded
        states = new_queue.get_all_states()
        self.assertEqual(len(states), len(self.test_files) - 2)
        
        # Check which files were loaded
        self.assertIn(self.test_files[0], states)
        self.assertNotIn(self.test_files[1], states)
        self.assertIn(self.test_files[2], states)
        self.assertNotIn(self.test_files[3], states)
        self.assertIn(self.test_files[4], states)
    
    def test_recovery_with_invalid_state_file(self):
        """Test recovery with an invalid state file."""
        # Create an invalid state file
        state_file = os.path.join(self.persistence_dir, "queue_state.json")
        with open(state_file, "w") as f:
            f.write("invalid json content")
        
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Queue should initialize empty
        self.assertEqual(len(queue.get_all_states()), 0)
    
    def test_recovery_with_missing_queue_key(self):
        """Test recovery with a state file missing the 'queue' key."""
        # Create a state file with a missing queue key
        state_file = os.path.join(self.persistence_dir, "queue_state.json")
        with open(state_file, "w") as f:
            json.dump({"saved_at": datetime.now().isoformat()}, f)
        
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Queue should initialize empty
        self.assertEqual(len(queue.get_all_states()), 0)
    
    def test_recovery_with_processing_restart(self):
        """Test that processing resumes after recovery."""
        # Create a queue with persistence and auto_start=False
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )

        # Add test files to the queue
        for file_path in self.test_files:
            queue.add_file(file_path)

        # Force persistence
        queue._persist_state()

        # Create a custom processor function that marks completion even without
        # calling the original function, so we know it's our new instance running
        processing_count = [0]

        def test_processor_func(file_path, metadata):
            processing_count[0] += 1
            return True  # Always succeed

        test_processor = FileProcessor(test_processor_func)

        # Create a new queue with auto_start=True and our test processor
        new_queue = ProcessingQueue(
            processor=test_processor,
            persistence_dir=self.persistence_dir,
            auto_start=True
        )

        # Wait for processing to begin
        max_wait = 5.0
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # If at least one file is being processed, we're good
            if processing_count[0] > 0:
                break
            time.sleep(0.1)

        # Stop the queue
        new_queue.stop()

        # Verify that at least one file was processed
        self.assertGreater(processing_count[0], 0,
                         "No files were processed after recovery")
    
    def test_recovery_with_metadata(self):
        """Test that metadata is preserved during recovery."""
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Add test files to the queue with metadata
        metadata_values = [
            {"key1": "value1"},
            {"key2": 42, "nested": {"subkey": True}},
            {"list": [1, 2, 3]},
            {"complex": {"a": 1, "b": [2, 3, 4]}},
            {"empty": {}}
        ]
        
        for i, file_path in enumerate(self.test_files):
            queue.add_file(file_path, metadata=metadata_values[i])
        
        # Force persistence
        queue._persist_state()
        
        # Create a new queue to simulate restart
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Verify metadata was preserved
        for i, file_path in enumerate(self.test_files):
            state = new_queue.get_state(file_path)
            self.assertEqual(state.metadata, metadata_values[i])
    
    def test_persistence_update_after_state_change(self):
        """Test that the persisted state is updated after state changes."""
        # Create a queue with persistence
        queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Add a test file
        queue.add_file(self.test_files[0])
        
        # Process the file to completion
        state = queue.get_state(self.test_files[0])
        
        # Use processor directly to simulate processing
        self.processor.process(state, blocking=True)
        
        # Verify state was updated
        updated_state = queue.get_state(self.test_files[0])
        self.assertEqual(updated_state.status, ProcessingStatus.COMPLETED)
        
        # Create a new queue to verify persistence
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            auto_start=False
        )
        
        # Verify state was persisted
        loaded_state = new_queue.get_state(self.test_files[0])
        self.assertEqual(loaded_state.status, ProcessingStatus.COMPLETED)


if __name__ == "__main__":
    unittest.main()