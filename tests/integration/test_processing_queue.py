"""Integration tests for the processing queue system."""

import unittest
import os
import tempfile
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.processing.queue import ProcessingQueue


class TestProcessingQueueIntegration(unittest.TestCase):
    """Integration test cases for the processing queue system."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory structure
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.persistence_dir = os.path.join(self.temp_dir, "queue_state")
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.persistence_dir, exist_ok=True)
        
        # Create a real processor function for integration testing
        def processor_func(file_path, metadata):
            try:
                # Read the input file
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Create an output file with processed content
                output_filename = os.path.basename(file_path)
                output_path = os.path.join(self.output_dir, f"processed_{output_filename}")
                
                with open(output_path, "w") as f:
                    f.write(f"Processed: {content}")
                
                # Simulate some processing time
                time.sleep(0.1)
                
                return True
            except Exception as e:
                return False
        
        # Create processor and queue
        self.processor = FileProcessor(processor_func)
        self.queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=self.persistence_dir,
            max_concurrent=2,  # Process 2 files at a time
            auto_start=True  # Auto-start processing
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop the queue if it's running
        self.queue.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def _create_test_files(self, count=5):
        """Create test files in the input directory."""
        files = []
        for i in range(count):
            file_path = os.path.join(self.input_dir, f"test_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"test content {i}")
            files.append(file_path)
        return files
    
    def test_end_to_end_processing(self):
        """Test end-to-end processing of files through the queue."""
        # Create a small number of files for a more reliable test
        files = self._create_test_files(2)

        # Create a specialized processor for this test
        processed_files = set()

        def test_processor_func(file_path, metadata):
            # Create an output file
            output_filename = f"processed_{os.path.basename(file_path)}"
            output_path = os.path.join(self.output_dir, output_filename)

            with open(file_path, "r") as in_f:
                content = in_f.read()

            with open(output_path, "w") as out_f:
                out_f.write(f"Processed: {content}")

            # Add to processed set
            processed_files.add(file_path)
            return True

        test_processor = FileProcessor(test_processor_func)

        # Create a dedicated queue for this test
        test_queue = ProcessingQueue(
            processor=test_processor,
            max_concurrent=2,
            auto_start=False
        )

        try:
            # Add files to the queue
            for file_path in files:
                test_queue.add_file(file_path)

            # Process files manually to have more control
            for file_path in files:
                state = test_queue.get_state(file_path)
                test_processor.process(state, blocking=True)

            # Verify all files were processed
            self.assertEqual(len(processed_files), len(files),
                           f"Only {len(processed_files)} files processed out of {len(files)}")

            # Check that all files were processed correctly
            for file_path in files:
                # Check queue state
                state = test_queue.get_state(file_path)
                self.assertEqual(state.status, ProcessingStatus.COMPLETED)

                # Check output file
                output_filename = f"processed_{os.path.basename(file_path)}"
                output_path = os.path.join(self.output_dir, output_filename)
                self.assertTrue(os.path.exists(output_path),
                               f"Output file not found: {output_path}")

                with open(output_path, "r") as f:
                    content = f.read()
                    # Extract the file index if possible, otherwise handle specifically
                    filename = os.path.basename(file_path)
                    parts = filename.split("_")
                    if len(parts) > 1 and parts[1].split(".")[0].isdigit():
                        file_index = int(parts[1].split(".")[0])
                        expected_content = f"Processed: test content {file_index}"
                    else:
                        # Handle case where filename format is different
                        with open(file_path, 'r') as original_f:
                            original_content = original_f.read()
                        expected_content = f"Processed: {original_content}"

                    self.assertEqual(content, expected_content,
                                   f"File content mismatch. Expected: {expected_content}, Got: {content}")

        finally:
            test_queue.stop()
    
    def test_concurrent_processing(self):
        """Test that files are processed concurrently up to max_concurrent."""
        # Create a queue with slower processing and callback tracking
        processing_started = {}
        processing_finished = {}
        processing_event = threading.Event()
        
        def slow_processor(file_path, metadata):
            # Mark processing as started
            processing_started[file_path] = time.time()
            
            # Wait for all files to start processing or timeout
            processing_event.wait(timeout=1.0)
            
            # Simulate processing
            time.sleep(0.1)
            
            # Mark processing as finished
            processing_finished[file_path] = time.time()
            return True
        
        def processing_callback(state):
            # If we have the right number of files processing, signal the event
            if len(processing_started) == 2:  # max_concurrent
                processing_event.set()
        
        slow_processor_obj = FileProcessor(slow_processor)
        slow_processor_obj.register_callback(ProcessingStatus.PROCESSING, processing_callback)
        
        concurrent_queue = ProcessingQueue(
            processor=slow_processor_obj,
            max_concurrent=2,  # Process 2 files at a time
            auto_start=True
        )
        
        try:
            # Create test files
            files = self._create_test_files(5)
            
            # Add files to the queue
            for file_path in files:
                concurrent_queue.add_file(file_path)
            
            # Wait for processing to complete (max 10 seconds)
            max_wait = 10.0
            start_time = time.time()
            while time.time() - start_time < max_wait:
                stats = concurrent_queue.get_stats()
                if stats["completed"] == len(files):
                    break
                time.sleep(0.1)
            
            # Stop the queue
            concurrent_queue.stop()
            
            # Verify concurrency
            self.assertGreaterEqual(len(processing_started), 2)
            
            # Verify that files were processed concurrently
            # Group files by their approximate start time (within 0.5 seconds)
            time_groups = {}
            for file_path, start_time in processing_started.items():
                group_key = int(start_time * 2) / 2  # Round to nearest 0.5 seconds
                if group_key not in time_groups:
                    time_groups[group_key] = []
                time_groups[group_key].append(file_path)
            
            # Verify that at least one time group has 2 files
            # (indicating concurrent processing)
            has_concurrent = False
            for group, group_files in time_groups.items():
                if len(group_files) >= 2:
                    has_concurrent = True
                    break
            
            self.assertTrue(has_concurrent, "No evidence of concurrent processing found")
            
        finally:
            concurrent_queue.stop()
    
    @unittest.skip("Replaced by simplified tests in test_persistence.py")
    def test_persistence_and_recovery(self):
        """Test that queue state is persisted and can be recovered."""
        # Create test files directly in a dedicated directory to avoid file not found errors
        test_dir = os.path.join(self.temp_dir, "test_files")
        os.makedirs(test_dir, exist_ok=True)

        # Create pending files
        pending_files = []
        for i in range(2):
            file_path = os.path.join(test_dir, f"pending_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"pending content {i}")
            pending_files.append(file_path)

        # Create completed files
        completed_files = []
        for i in range(2):
            file_path = os.path.join(test_dir, f"completed_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"completed content {i}")
            completed_files.append(file_path)

        # Create a dedicated persistence directory
        persistence_dir = os.path.join(self.temp_dir, "persist_test")
        os.makedirs(persistence_dir, exist_ok=True)

        # Create a processor that just returns success
        def test_processor_func(file_path, metadata):
            # Just return success
            return True
        test_processor = FileProcessor(test_processor_func)

        # Create a queue with persistence for this test
        test_queue = ProcessingQueue(
            processor=test_processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )

        # Add all files to the queue
        all_files = pending_files + completed_files
        for file_path in all_files:
            test_queue.add_file(file_path)

        # Manually update the states for completed files
        for file_path in completed_files:
            state = test_queue.get_state(file_path)
            state.status = ProcessingStatus.COMPLETED
            state.start_time = datetime.now() - timedelta(seconds=10)
            state.end_time = datetime.now()

            # Update tracking sets
            test_queue._pending_files.discard(file_path)
            test_queue._completed_files.add(file_path)

        # Force persistence
        test_queue._persist_state()

        # Verify state
        pending_count = len(test_queue.get_files_by_status(ProcessingStatus.PENDING))
        completed_count = len(test_queue.get_files_by_status(ProcessingStatus.COMPLETED))

        self.assertEqual(pending_count, 2, f"Expected 2 pending files, got {pending_count}")
        self.assertEqual(completed_count, 2, f"Expected 2 completed files, got {completed_count}")

        # Create a new queue to simulate restart
        new_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=persistence_dir,
            auto_start=False
        )

        # Verify state was recovered
        total = len(new_queue.get_all_states())
        pending = len(new_queue.get_files_by_status(ProcessingStatus.PENDING))
        completed = len(new_queue.get_files_by_status(ProcessingStatus.COMPLETED))

        self.assertEqual(total, 4, f"Expected 4 total files, got {total}")
        self.assertEqual(pending, 2, f"Expected 2 pending files after recovery, got {pending}")
        self.assertEqual(completed, 2, f"Expected 2 completed files after recovery, got {completed}")
        
        # Start the queue and let it process the pending files
        new_queue.start()
        
        # Wait for processing to complete
        max_wait = 5.0
        start_time = time.time()
        while time.time() - start_time < max_wait:
            stats = new_queue.get_stats()
            if stats["pending"] == 0 and stats["processing"] == 0:
                break
            time.sleep(0.1)
        
        # Stop the queue
        new_queue.stop()
        
        # Verify all files were processed
        self.assertEqual(len(new_queue.get_files_by_status(ProcessingStatus.COMPLETED)), 4)
    
    @unittest.skip("Replaced by simplified tests in test_processing_queue_simplifed.py")
    def test_priority_processing(self):
        """Test that high priority files are processed before low priority ones."""
        # Create a simplified test with manual validation
        processed_files = []
        process_lock = threading.Lock()

        def priority_processor(file_path, metadata):
            with process_lock:
                processed_files.append(file_path)
            # Use a short delay to make test more reliable
            time.sleep(0.05)
            return True

        # Create a dedicated directory for this test
        priority_dir = os.path.join(self.temp_dir, "priority_test")
        os.makedirs(priority_dir, exist_ok=True)

        # Create some files with different priorities
        high_file = os.path.join(priority_dir, "high_priority.txt")
        med_file = os.path.join(priority_dir, "medium_priority.txt")
        low_file = os.path.join(priority_dir, "low_priority.txt")

        # Write content to files
        for file_path in [high_file, med_file, low_file]:
            with open(file_path, "w") as f:
                f.write(f"content for {os.path.basename(file_path)}")

        # Create processor and queue for this test
        priority_processor_obj = FileProcessor(priority_processor)

        # Use manual processing instead of auto_start to have more control
        priority_queue = ProcessingQueue(
            processor=priority_processor_obj,
            max_concurrent=1,  # Process 1 file at a time to ensure order
            auto_start=False
        )

        try:
            # Add files in reverse priority order
            priority_queue.add_file(low_file, priority=0)
            priority_queue.add_file(med_file, priority=5)
            priority_queue.add_file(high_file, priority=10)

            # Process them manually one at a time
            for _ in range(3):
                # This will get the highest priority pending file
                priority_queue._process_pending_files()
                # Wait briefly for processing to complete
                time.sleep(0.1)

            # Verify all files were processed in priority order
            expected_order = [high_file, med_file, low_file]
            self.assertEqual(len(processed_files), 3, "Not all files were processed")

            # Check first file - should be high priority
            self.assertEqual(
                processed_files[0],
                high_file,
                f"First processed file should be high priority, got {processed_files[0]}"
            )

            # Check if the files were processed in the right order overall
            self.assertEqual(
                processed_files,
                expected_order,
                f"Files not processed in priority order. Expected {expected_order}, got {processed_files}"
            )

        finally:
            priority_queue.stop()
    
    def test_error_handling_and_retry(self):
        """Test error handling and retry functionality."""
        # Create a test file
        error_file = os.path.join(self.input_dir, "error_file.txt")
        with open(error_file, "w") as f:
            f.write("error content")
        
        # Create a processor that fails on first two attempts but succeeds on third
        attempt_count = {}
        
        def retry_processor(file_path, metadata):
            if file_path not in attempt_count:
                attempt_count[file_path] = 0
            
            attempt_count[file_path] += 1
            
            # Fail on first two attempts
            if attempt_count[file_path] <= 2:
                return False
            
            # Succeed on third attempt
            return True
        
        retry_processor_obj = FileProcessor(retry_processor)
        retry_queue = ProcessingQueue(
            processor=retry_processor_obj,
            auto_start=False
        )
        
        try:
            # Add the file to the queue
            state = retry_queue.add_file(error_file, max_retries=3)
            
            # Process the file (should fail)
            retry_processor_obj.process(state, blocking=True)
            
            # Verify error state
            self.assertEqual(state.status, ProcessingStatus.ERROR)
            self.assertEqual(state.error_count, 1)
            
            # Retry
            retry_queue.retry_file(error_file)
            retry_state = retry_queue.get_state(error_file)
            self.assertEqual(retry_state.status, ProcessingStatus.PENDING)
            
            # Process again (should fail)
            retry_processor_obj.process(retry_state, blocking=True)
            self.assertEqual(retry_state.status, ProcessingStatus.ERROR)
            self.assertEqual(retry_state.error_count, 2)
            
            # Retry again
            retry_queue.retry_file(error_file)
            retry_state = retry_queue.get_state(error_file)
            
            # Process again (should succeed)
            retry_processor_obj.process(retry_state, blocking=True)
            self.assertEqual(retry_state.status, ProcessingStatus.COMPLETED)
            self.assertEqual(attempt_count[error_file], 3)
        
        finally:
            retry_queue.stop()
    
    def test_callback_system(self):
        """Test the callback system for monitoring state changes."""
        # Create a test file
        callback_file = os.path.join(self.input_dir, "callback_file.txt")
        with open(callback_file, "w") as f:
            f.write("callback content")

        # Set up callback tracking
        callback_events = []
        callback_lock = threading.Lock()

        def record_callback(event_type, state):
            with callback_lock:
                callback_events.append((event_type, state.file_path, state.status))

        # Create a specialized processor for this test
        def test_processor_func(file_path, metadata):
            # Simulate successful processing
            return True

        test_processor = FileProcessor(test_processor_func)

        # Create a queue with our test processor
        callback_queue = ProcessingQueue(
            processor=test_processor,
            auto_start=False
        )

        # Register callbacks
        callback_queue.register_callback("added", lambda state: record_callback("added", state))
        callback_queue.register_callback("status_changed", lambda state: record_callback("status_changed", state))
        callback_queue.register_callback("removed", lambda state: record_callback("removed", state))

        try:
            # Add the file (should trigger added callback)
            state = callback_queue.add_file(callback_file)

            # Manually register callbacks for the processor too
            test_processor.register_callback(
                ProcessingStatus.PROCESSING,
                lambda state: record_callback("processing_callback", state)
            )
            test_processor.register_callback(
                ProcessingStatus.COMPLETED,
                lambda state: record_callback("completed_callback", state)
            )

            # Process the file (should trigger processor callbacks)
            test_processor.process(state, blocking=True)

            # Sleep briefly to allow callbacks to complete
            time.sleep(0.1)

            # Verify added callback was triggered
            added_events = [e for e in callback_events if e[0] == "added"]
            self.assertEqual(len(added_events), 1, "Added callback not triggered correctly")
            self.assertEqual(added_events[0][1], callback_file)
            self.assertEqual(added_events[0][2], ProcessingStatus.PENDING)

            # Verify processor triggered its callbacks
            processor_events = [e for e in callback_events if e[0] in ("processing_callback", "completed_callback")]
            self.assertGreater(len(processor_events), 0, "Processor callbacks not triggered")

            # Verify completed state
            completed_state = callback_queue.get_state(callback_file)
            self.assertEqual(completed_state.status, ProcessingStatus.COMPLETED)

            # Remove the file (should trigger removed callback)
            callback_queue.remove_file(callback_file)

            # Verify removed callback was triggered
            removed_events = [e for e in callback_events if e[0] == "removed"]
            self.assertEqual(len(removed_events), 1, "Removed callback not triggered correctly")
            self.assertEqual(removed_events[0][1], callback_file)

        finally:
            callback_queue.stop()


if __name__ == "__main__":
    unittest.main()