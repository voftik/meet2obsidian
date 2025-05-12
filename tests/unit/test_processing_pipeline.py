"""
Unit tests for the ProcessingPipeline class.

These tests verify that the ProcessingPipeline correctly integrates
the file monitoring, processing queue, and audio extraction components.
"""

import unittest
from unittest.mock import MagicMock, patch, call
import os
import tempfile
import shutil
from pathlib import Path

# Import with try/except to handle missing dependencies in test environment
try:
    from meet2obsidian.processing.pipeline import ProcessingPipeline
    from meet2obsidian.processing.state import ProcessingStatus
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "Required dependencies not available")
class TestProcessingPipeline(unittest.TestCase):
    """Test the ProcessingPipeline class functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.watch_dir = os.path.join(self.temp_dir, "watch")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        os.makedirs(self.watch_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create mock objects
        self.mock_file_monitor = MagicMock()
        self.mock_processing_queue = MagicMock()
        self.mock_audio_extractor = MagicMock()
        self.mock_cache_manager = MagicMock()
        self.mock_logger = MagicMock()
        
        # Patches for the pipeline
        self.file_monitor_patch = patch('meet2obsidian.monitor.FileMonitor')
        self.processing_queue_patch = patch('meet2obsidian.processing.queue.ProcessingQueue')
        self.audio_extractor_patch = patch('meet2obsidian.audio.extractor.AudioExtractor')
        self.cache_manager_patch = patch('meet2obsidian.cache.CacheManager')
        self.get_logger_patch = patch('meet2obsidian.utils.logging.get_logger')
        self.setup_logging_patch = patch('meet2obsidian.utils.logging.setup_component_logging')
        
        # Start patches
        self.mock_file_monitor_class = self.file_monitor_patch.start()
        self.mock_processing_queue_class = self.processing_queue_patch.start()
        self.mock_audio_extractor_class = self.audio_extractor_patch.start()
        self.mock_cache_manager_class = self.cache_manager_patch.start()
        self.mock_get_logger = self.get_logger_patch.start()
        self.mock_setup_logging = self.setup_logging_patch.start()
        
        # Configure mocks
        self.mock_file_monitor_class.return_value = self.mock_file_monitor
        self.mock_processing_queue_class.return_value = self.mock_processing_queue
        self.mock_audio_extractor_class.return_value = self.mock_audio_extractor
        self.mock_cache_manager_class.return_value = self.mock_cache_manager
        self.mock_get_logger.return_value = self.mock_logger
        self.mock_setup_logging.return_value = self.mock_logger
        
        # Configure ProcessingQueue mock to track files
        self.mock_processing_queue.get_stats.return_value = {
            "total": 0, "pending": 0, "processing": 0, 
            "completed": 0, "error": 0, "failed": 0
        }
        
        # Configure FileMonitor mock
        self.mock_file_monitor.start.return_value = True
        self.mock_file_monitor.stop.return_value = True
        
        # Configure AudioExtractor mock
        self.mock_audio_extractor.check_video_file.return_value = (True, None)
        self.mock_audio_extractor.extract_audio_with_profile.return_value = (True, os.path.join(self.output_dir, "test.m4a"))
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop patches
        self.file_monitor_patch.stop()
        self.processing_queue_patch.stop()
        self.audio_extractor_patch.stop()
        self.cache_manager_patch.stop()
        self.get_logger_patch.stop()
        self.setup_logging_patch.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pipeline_initialization(self):
        """Test that the pipeline initializes all components correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Verify component initialization
        self.mock_cache_manager_class.assert_called_once()
        self.mock_audio_extractor_class.assert_called_once()
        self.mock_processing_queue_class.assert_called_once()
        self.mock_file_monitor_class.assert_called_once()
        
        # Verify callback registration
        self.mock_file_monitor.register_file_callback.assert_called_once()
        self.mock_file_monitor.set_validation_function.assert_called_once()
    
    def test_pipeline_start(self):
        """Test that the pipeline starts all components correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Start pipeline
        result = pipeline.start()
        
        # Verify result
        self.assertTrue(result)
        
        # Verify component starts
        self.mock_processing_queue.start.assert_called_once()
        self.mock_file_monitor.start.assert_called_once()
    
    def test_pipeline_stop(self):
        """Test that the pipeline stops all components correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Start then stop pipeline
        pipeline.start()
        result = pipeline.stop()
        
        # Verify result
        self.assertTrue(result)
        
        # Verify component stops
        self.mock_file_monitor.stop.assert_called_once()
        self.mock_processing_queue.stop.assert_called_once()
    
    def test_on_new_file(self):
        """Test that the pipeline handles new files correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Create a test file path
        test_file = os.path.join(self.watch_dir, "test_video.mp4")
        
        # Mock that the file is not already in the queue
        self.mock_processing_queue._queue = {}
        
        # Call the file callback
        pipeline._on_new_file(test_file)
        
        # Verify file was added to the queue
        self.mock_processing_queue.add_file.assert_called_once()
        
        # Check the metadata provided to add_file
        args, kwargs = self.mock_processing_queue.add_file.call_args
        self.assertEqual(args[0], test_file)
        self.assertIn('metadata', kwargs)
        metadata = kwargs['metadata']
        self.assertEqual(metadata['source_path'], test_file)
        self.assertEqual(metadata['output_format'], pipeline.audio_format)
    
    def test_validate_video_file(self):
        """Test that the pipeline validates video files correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Create a test file path
        test_file = os.path.join(self.watch_dir, "test_video.mp4")
        
        # Test validation success
        self.mock_audio_extractor.check_video_file.return_value = (True, None)
        result = pipeline._validate_video_file(test_file)
        self.assertTrue(result)
        
        # Test validation failure
        self.mock_audio_extractor.check_video_file.return_value = (False, "Invalid video file")
        result = pipeline._validate_video_file(test_file)
        self.assertFalse(result)
    
    def test_process_file(self):
        """Test that the pipeline processes files correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Create a test file path
        test_file = os.path.join(self.watch_dir, "test_video.mp4")
        expected_output = os.path.join(self.output_dir, "test_video.m4a")
        
        # Set up metadata
        metadata = {
            "source_path": test_file,
            "output_format": "m4a",
            "quality": "medium",
            "output_directory": self.output_dir
        }
        
        # Configure mock for extract_audio_with_profile
        self.mock_audio_extractor.extract_audio_with_profile.return_value = (True, expected_output)
        
        # Process file
        result = pipeline._process_file(test_file, metadata)
        
        # Verify result
        self.assertTrue(result)
        
        # Verify audio extraction was called
        self.mock_audio_extractor.extract_audio_with_profile.assert_called_once_with(
            video_path=test_file, 
            output_path=expected_output, 
            profile="medium"
        )
        
        # Verify cache was updated
        self.mock_cache_manager.store.assert_called_once()
    
    def test_get_status(self):
        """Test that the pipeline returns correct status information."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Configure queue stats
        self.mock_processing_queue.get_stats.return_value = {
            "total": 5, 
            "pending": 2, 
            "processing": 1, 
            "completed": 1, 
            "error": 1, 
            "failed": 0
        }
        
        # Get status
        status = pipeline.get_status()
        
        # Verify status contains expected information
        self.assertEqual(status["running"], pipeline._is_running)
        self.assertEqual(status["watch_directory"], self.watch_dir)
        self.assertEqual(status["output_directory"], self.output_dir)
        self.assertIn("queue", status)
        self.assertIn("stats", status)
    
    def test_retry_errors(self):
        """Test that the pipeline retries errors correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Configure retry_all_errors
        self.mock_processing_queue.retry_all_errors.return_value = 3
        
        # Call retry_errors
        count = pipeline.retry_errors()
        
        # Verify result
        self.assertEqual(count, 3)
        self.mock_processing_queue.retry_all_errors.assert_called_once()
    
    def test_clear_completed(self):
        """Test that the pipeline clears completed files correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Configure clear_completed
        self.mock_processing_queue.clear_completed.return_value = 2
        
        # Call clear_completed
        count = pipeline.clear_completed()
        
        # Verify result
        self.assertEqual(count, 2)
        self.mock_processing_queue.clear_completed.assert_called_once()
    
    def test_cached_file_processing(self):
        """Test that the pipeline uses cached results correctly."""
        # Create pipeline
        pipeline = ProcessingPipeline(
            watch_directory=self.watch_dir,
            output_directory=self.output_dir,
            cache_directory=self.cache_dir,
            min_file_age_seconds=1,
            logger=self.mock_logger
        )
        
        # Create a test file path
        test_file = os.path.join(self.watch_dir, "test_cache.mp4")
        expected_output = os.path.join(self.output_dir, "test_cache.m4a")
        
        # Set up metadata
        metadata = {
            "source_path": test_file,
            "output_format": "m4a",
            "quality": "medium",
            "output_directory": self.output_dir
        }
        
        # Configure cache hit
        def mock_get(cache_type, key):
            if cache_type == "audio_extraction":
                return expected_output
            return None
        
        self.mock_cache_manager.get.side_effect = mock_get
        
        # Mock file existence checks
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getmtime', return_value=123456789.0):
            
            # Process file
            result = pipeline._process_file(test_file, metadata)
            
            # Verify result
            self.assertTrue(result)
            
            # Verify audio extraction was NOT called
            self.mock_audio_extractor.extract_audio_with_profile.assert_not_called()
            
            # Verify cache was checked
            self.mock_cache_manager.get.assert_called()


if __name__ == '__main__':
    unittest.main()