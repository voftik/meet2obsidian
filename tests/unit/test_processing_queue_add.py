"""Tests for adding files to the processing queue."""

import unittest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from datetime import datetime
import time

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.processing.queue import ProcessingQueue


class TestProcessingQueueAdd(unittest.TestCase):
    """Test cases for adding files to the processing queue."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file
        self.test_file = os.path.join(self.temp_dir, "test_file.mp4")
        with open(self.test_file, "w") as f:
            f.write("test content")
        
        # Create a mock processor function
        self.mock_processor_func = MagicMock(return_value=True)
        
        # Create processor and queue
        self.processor = FileProcessor(self.mock_processor_func)
        self.queue = ProcessingQueue(
            processor=self.processor,
            auto_start=False  # Don't start processing automatically
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop the queue if it's running
        self.queue.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_add_single_file(self):
        """Test adding a single file to the queue."""
        # Add a file to the queue
        state = self.queue.add_file(self.test_file)
        
        # Check that the file was added to the queue
        self.assertIn(self.test_file, self.queue.get_all_states())
        
        # Check that the state was initialized correctly
        self.assertEqual(state.file_path, self.test_file)
        self.assertEqual(state.status, ProcessingStatus.PENDING)
        self.assertEqual(state.priority, 0)  # Default priority
        self.assertEqual(state.error_count, 0)
        self.assertEqual(state.max_retries, 3)  # Default max retries
        self.assertIsNone(state.start_time)
        self.assertIsNone(state.end_time)
        self.assertIsNotNone(state.added_time)
        self.assertIsInstance(state.added_time, datetime)
        
        # Check that the file is in the pending list
        pending_files = self.queue.get_files_by_status(ProcessingStatus.PENDING)
        self.assertIn(self.test_file, pending_files)
        
        # Check queue stats
        stats = self.queue.get_stats()
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["processing"], 0)
        self.assertEqual(stats["completed"], 0)
        self.assertEqual(stats["error"], 0)
        self.assertEqual(stats["failed"], 0)
    
    def test_add_file_with_priority(self):
        """Test adding a file with a specific priority."""
        # Add a file with high priority
        priority = 10
        state = self.queue.add_file(self.test_file, priority=priority)
        
        # Check that the priority was set correctly
        self.assertEqual(state.priority, priority)
        
        # Verify through queue state lookup too
        queue_state = self.queue.get_state(self.test_file)
        self.assertEqual(queue_state.priority, priority)
    
    def test_add_file_with_metadata(self):
        """Test adding a file with metadata."""
        # Add a file with metadata
        metadata = {"key1": "value1", "key2": 42}
        state = self.queue.add_file(self.test_file, metadata=metadata)
        
        # Check that the metadata was set correctly
        self.assertEqual(state.metadata, metadata)
        
        # Verify through queue state lookup too
        queue_state = self.queue.get_state(self.test_file)
        self.assertEqual(queue_state.metadata, metadata)
    
    def test_add_file_with_max_retries(self):
        """Test adding a file with custom max retries."""
        # Add a file with custom max retries
        max_retries = 5
        state = self.queue.add_file(self.test_file, max_retries=max_retries)
        
        # Check that max_retries was set correctly
        self.assertEqual(state.max_retries, max_retries)
        
        # Verify through queue state lookup too
        queue_state = self.queue.get_state(self.test_file)
        self.assertEqual(queue_state.max_retries, max_retries)
    
    def test_add_duplicate_file(self):
        """Test adding a duplicate file raises an error."""
        # Add a file to the queue
        self.queue.add_file(self.test_file)
        
        # Try to add the same file again
        with self.assertRaises(ValueError):
            self.queue.add_file(self.test_file)
    
    def test_add_multiple_files(self):
        """Test adding multiple files to the queue."""
        # Create multiple test files
        files = []
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f"test_file_{i}.mp4")
            with open(file_path, "w") as f:
                f.write(f"test content {i}")
            files.append(file_path)
        
        # Add each file to the queue
        for file_path in files:
            self.queue.add_file(file_path)
        
        # Check that all files were added to the queue
        states = self.queue.get_all_states()
        self.assertEqual(len(states), len(files))
        for file_path in files:
            self.assertIn(file_path, states)
        
        # Check queue stats
        stats = self.queue.get_stats()
        self.assertEqual(stats["total"], len(files))
        self.assertEqual(stats["pending"], len(files))
    
    def test_add_file_with_callback(self):
        """Test that callbacks are triggered when adding a file."""
        # Create a mock callback
        mock_callback = MagicMock()
        
        # Register the callback
        self.queue.register_callback("added", mock_callback)
        
        # Add a file to the queue
        state = self.queue.add_file(self.test_file)
        
        # Check that the callback was called with the correct state
        mock_callback.assert_called_once()
        callback_state = mock_callback.call_args[0][0]
        self.assertEqual(callback_state.file_path, self.test_file)
        self.assertEqual(callback_state.status, ProcessingStatus.PENDING)
    
    def test_add_file_persistence(self):
        """Test that adding a file persists the queue state."""
        # Create a queue with persistence
        persistence_dir = os.path.join(self.temp_dir, "queue_state")
        os.makedirs(persistence_dir, exist_ok=True)
        
        queue_with_persistence = ProcessingQueue(
            processor=self.processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )
        
        # Add a file to the queue
        queue_with_persistence.add_file(self.test_file)
        
        # Check that the state file was created
        state_file = os.path.join(persistence_dir, "queue_state.json")
        self.assertTrue(os.path.exists(state_file))
        
        # Create a new queue with the same persistence directory
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )
        
        # Check that the state was loaded
        self.assertIn(self.test_file, new_queue.get_all_states())
        pending_files = new_queue.get_files_by_status(ProcessingStatus.PENDING)
        self.assertIn(self.test_file, pending_files)


if __name__ == "__main__":
    unittest.main()