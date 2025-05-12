"""Tests for tracking processing state in the processing queue."""

import unittest
import os
import tempfile
import shutil
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus


class TestProcessingState(unittest.TestCase):
    """Test cases for the ProcessingState class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file path
        self.test_file = os.path.join(self.temp_dir, "test_file.mp4")
        with open(self.test_file, "w") as f:
            f.write("test content")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_state_initialization(self):
        """Test that ProcessingState initializes correctly."""
        # Create a basic state
        state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.PENDING
        )
        
        # Check basic initialization
        self.assertEqual(state.file_path, self.test_file)
        self.assertEqual(state.status, ProcessingStatus.PENDING)
        self.assertEqual(state.priority, 0)  # Default priority
        self.assertEqual(state.error_count, 0)
        self.assertEqual(state.max_retries, 3)  # Default max retries
        self.assertIsNone(state.start_time)
        self.assertIsNone(state.end_time)
        self.assertIsNotNone(state.added_time)
        self.assertIsInstance(state.added_time, datetime)
        self.assertIsNotNone(state.metadata)
        self.assertEqual(state.metadata, {})
        
        # Create a state with custom values
        custom_time = datetime.now() - timedelta(hours=1)
        metadata = {"key1": "value1", "key2": 42}
        
        state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.PENDING,
            priority=10,
            added_time=custom_time,
            max_retries=5,
            metadata=metadata
        )
        
        # Check custom initialization
        self.assertEqual(state.priority, 10)
        self.assertEqual(state.max_retries, 5)
        self.assertEqual(state.added_time, custom_time)
        self.assertEqual(state.metadata, metadata)
    
    def test_state_transitions(self):
        """Test state transition methods."""
        # Create a state
        state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.PENDING
        )
        
        # Test mark_processing
        state.mark_processing()
        self.assertEqual(state.status, ProcessingStatus.PROCESSING)
        self.assertIsNotNone(state.start_time)
        self.assertIsNone(state.end_time)
        
        # Test mark_completed
        state.mark_completed()
        self.assertEqual(state.status, ProcessingStatus.COMPLETED)
        self.assertIsNotNone(state.start_time)
        self.assertIsNotNone(state.end_time)
        
        # Create a new state for error testing
        state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.PENDING
        )
        
        # Test mark_processing first
        state.mark_processing()
        
        # Test mark_error
        error_message = "Test error message"
        state.mark_error(error_message)
        self.assertEqual(state.status, ProcessingStatus.ERROR)
        self.assertEqual(state.error_count, 1)
        self.assertEqual(state.last_error, error_message)
        self.assertIsNotNone(state.end_time)
        
        # Test can_retry
        self.assertTrue(state.can_retry())
        
        # Test reset_for_retry
        state.reset_for_retry()
        self.assertEqual(state.status, ProcessingStatus.PENDING)
        self.assertIsNone(state.start_time)
        self.assertIsNone(state.end_time)
        
        # Start fresh with a new state for the error tests
        state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.PENDING,
            max_retries=3
        )

        # Add first error
        state.mark_processing()
        state.mark_error("Error 1")
        self.assertEqual(state.error_count, 1)

        # Reset for retry
        state.reset_for_retry()

        # Add second error
        state.mark_processing()
        state.mark_error("Error 2")
        self.assertEqual(state.error_count, 2)

        # Reset for retry again
        state.reset_for_retry()

        # Add third error, which should put us at max_retries (3 is the default)
        # and change status to FAILED
        state.mark_processing()
        state.mark_error("Error 3")

        # Should now be in FAILED state due to max retries
        self.assertEqual(state.status, ProcessingStatus.FAILED)
        self.assertEqual(state.error_count, 3)
        self.assertFalse(state.can_retry())
        
        # reset_for_retry should not change the state now
        state.reset_for_retry()
        self.assertEqual(state.status, ProcessingStatus.FAILED)  # Still failed
    
    def test_is_terminal(self):
        """Test the is_terminal property."""
        # Create a state
        state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.PENDING
        )
        
        # Pending is not terminal
        self.assertFalse(state.is_terminal)
        
        # Processing is not terminal
        state.status = ProcessingStatus.PROCESSING
        self.assertFalse(state.is_terminal)
        
        # Error is not terminal
        state.status = ProcessingStatus.ERROR
        self.assertFalse(state.is_terminal)
        
        # Completed is terminal
        state.status = ProcessingStatus.COMPLETED
        self.assertTrue(state.is_terminal)
        
        # Failed is terminal
        state.status = ProcessingStatus.FAILED
        self.assertTrue(state.is_terminal)
    
    def test_processing_time(self):
        """Test the processing_time property."""
        # Create a state
        state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.PENDING
        )
        
        # No times set yet
        self.assertIsNone(state.processing_time)
        
        # Set start time only
        state.start_time = datetime.now()
        self.assertIsNone(state.processing_time)
        
        # Set both start and end time
        state.start_time = datetime.now() - timedelta(seconds=10)
        state.end_time = datetime.now()
        self.assertIsNotNone(state.processing_time)
        self.assertGreaterEqual(state.processing_time, 10.0)
        self.assertLess(state.processing_time, 11.0)  # Allow for small timing differences
    
    def test_serialization(self):
        """Test serialization and deserialization of states."""
        # Create a state with various fields set
        original_state = ProcessingState(
            file_path=self.test_file,
            status=ProcessingStatus.COMPLETED,
            priority=5,
            added_time=datetime.now() - timedelta(minutes=10),
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now(),
            error_count=1,
            max_retries=5,
            last_error="Test error",
            metadata={"key1": "value1", "nested": {"subkey": 42}}
        )
        
        # Serialize to dict
        state_dict = original_state.to_dict()
        
        # Check fields
        self.assertEqual(state_dict["file_path"], original_state.file_path)
        self.assertEqual(state_dict["status"], original_state.status.value)
        self.assertEqual(state_dict["priority"], original_state.priority)
        self.assertEqual(state_dict["error_count"], original_state.error_count)
        self.assertEqual(state_dict["max_retries"], original_state.max_retries)
        self.assertEqual(state_dict["last_error"], original_state.last_error)
        self.assertEqual(state_dict["metadata"], original_state.metadata)
        
        # Check JSON serialization
        json_str = json.dumps(state_dict)
        loaded_dict = json.loads(json_str)
        
        # Deserialize back to state
        deserialized_state = ProcessingState.from_dict(loaded_dict)
        
        # Compare with original state
        self.assertEqual(deserialized_state.file_path, original_state.file_path)
        self.assertEqual(deserialized_state.status, original_state.status)
        self.assertEqual(deserialized_state.priority, original_state.priority)
        self.assertEqual(deserialized_state.error_count, original_state.error_count)
        self.assertEqual(deserialized_state.max_retries, original_state.max_retries)
        self.assertEqual(deserialized_state.last_error, original_state.last_error)
        self.assertEqual(deserialized_state.metadata, original_state.metadata)
        
        # Check that datetime fields were properly converted
        self.assertIsInstance(deserialized_state.added_time, datetime)
        self.assertIsInstance(deserialized_state.start_time, datetime)
        self.assertIsInstance(deserialized_state.end_time, datetime)


if __name__ == "__main__":
    unittest.main()