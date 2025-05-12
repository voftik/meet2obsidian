"""Processing pipeline for meet2obsidian.

This module connects the file monitoring, processing queue, and audio extraction
components to create a complete processing pipeline.
"""

import os
import logging
import threading
from typing import Optional, Dict, Any, Callable, List, Set

from meet2obsidian.utils.logging import get_logger, setup_component_logging
from meet2obsidian.monitor import FileMonitor
from meet2obsidian.processing.queue import ProcessingQueue
from meet2obsidian.processing.state import ProcessingState, ProcessingStatus
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.audio.extractor import AudioExtractor
from meet2obsidian.cache import CacheManager


class ProcessingPipeline:
    """
    Connects file monitoring, processing queue, and audio extraction components.
    
    This class integrates the various components of the meet2obsidian system:
    - FileMonitor: Detects new video files in a directory
    - ProcessingQueue: Manages the queue of files to be processed
    - AudioExtractor: Extracts audio from video files
    - CacheManager: Handles caching of results
    """
    
    def __init__(self, 
                 watch_directory: str,
                 output_directory: str,
                 cache_directory: Optional[str] = None,
                 audio_format: str = 'm4a',
                 audio_quality: str = 'medium',
                 file_patterns: Optional[List[str]] = None,
                 max_concurrent: int = 3,
                 min_file_age_seconds: int = 5,
                 log_dir: Optional[str] = None,
                 log_level: str = "info",
                 logger = None):
        """
        Initialize the processing pipeline.

        Args:
            watch_directory: Directory to monitor for new video files
            output_directory: Directory to store processed output files
            cache_directory: Directory for caching results (optional)
            audio_format: Format for extracted audio files
            audio_quality: Quality profile for audio extraction
            file_patterns: Patterns of video files to monitor
            max_concurrent: Maximum number of concurrent processing tasks
            min_file_age_seconds: Minimum age of file before processing
            log_dir: Directory to store log files
            log_level: Logging level (debug, info, warning, error, critical)
            logger: Optional logger instance
        """
        self.watch_directory = os.path.abspath(os.path.expanduser(watch_directory))
        self.output_directory = os.path.abspath(os.path.expanduser(output_directory))
        self.audio_format = audio_format
        self.audio_quality = audio_quality
        self.file_patterns = file_patterns or ["*.mp4", "*.mov", "*.webm", "*.mkv"]

        # Set up centralized logging
        if not logger:
            pipeline_context = {
                "watch_dir": self.watch_directory,
                "output_dir": self.output_directory,
                "max_concurrent": max_concurrent
            }
            logger = setup_component_logging("processing.pipeline", log_dir, log_level, pipeline_context)

        self.logger = logger
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Initialize cache manager if cache directory is provided
        self.cache_manager = None
        if cache_directory:
            cache_dir = os.path.abspath(os.path.expanduser(cache_directory))
            self.cache_manager = CacheManager(cache_dir, logger=self.logger)
            self.logger.info(f"Initialized cache manager with directory: {cache_dir}")
        
        # Create component loggers with shared configuration
        audio_extractor_logger = get_logger("audio.extractor", component="audio_extractor",
                                          pipeline=id(self))
        processor_logger = get_logger("processing.processor", component="processor",
                                   pipeline=id(self))
        queue_logger = get_logger("processing.queue", component="queue",
                                pipeline=id(self), max_concurrent=max_concurrent)
        monitor_logger = get_logger("monitoring.file_monitor", component="file_monitor",
                                 pipeline=id(self), watch_dir=self.watch_directory)

        # Initialize audio extractor
        self.audio_extractor = AudioExtractor(logger=audio_extractor_logger)

        # Initialize file processor with appropriate logger
        self.processor = FileProcessor(self._process_file)
        # Update the processor's logger
        self.processor.logger = processor_logger

        # Initialize processing queue
        queue_persistence_dir = os.path.join(self.output_directory, ".queue") if self.output_directory else None
        self.processing_queue = ProcessingQueue(
            processor=self.processor,
            persistence_dir=queue_persistence_dir,
            max_concurrent=max_concurrent,
            auto_start=False  # We'll start it manually
        )
        # Update the queue's logger
        self.processing_queue.logger = queue_logger

        # Initialize file monitor
        self.file_monitor = FileMonitor(
            directory=self.watch_directory,
            file_patterns=self.file_patterns,
            min_file_age_seconds=min_file_age_seconds,
            logger=monitor_logger
        )
        
        # Set up the callback chain
        self.file_monitor.register_file_callback(self._on_new_file)
        self.file_monitor.set_validation_function(self._validate_video_file)
        
        # Processing state
        self._is_running = False
        self._lock = threading.RLock()
        
        # Stats
        self._stats = {
            "files_detected": 0,
            "files_processed": 0,
            "errors": 0,
            "cached_hits": 0
        }
        
        self.logger.info(f"Initialized processing pipeline:")
        self.logger.info(f" - Watch directory: {self.watch_directory}")
        self.logger.info(f" - Output directory: {self.output_directory}")
        self.logger.info(f" - File patterns: {', '.join(self.file_patterns)}")
        self.logger.info(f" - Audio format: {self.audio_format}")
        self.logger.info(f" - Audio quality: {self.audio_quality}")
    
    def start(self) -> bool:
        """
        Start the processing pipeline.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        with self._lock:
            if self._is_running:
                self.logger.info("Processing pipeline is already running")
                return True
            
            self.logger.info("Starting processing pipeline")
            
            # Start the processing queue
            self.processing_queue.start()
            
            # Start the file monitor
            if not self.file_monitor.start():
                self.logger.error("Failed to start file monitor")
                self.processing_queue.stop()
                return False
            
            self._is_running = True
            self.logger.info("Processing pipeline started successfully")
            return True
    
    def stop(self) -> bool:
        """
        Stop the processing pipeline.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self._lock:
            if not self._is_running:
                self.logger.info("Processing pipeline is not running")
                return True
            
            self.logger.info("Stopping processing pipeline")
            
            # Stop the file monitor
            file_monitor_stopped = self.file_monitor.stop()
            
            # Stop the processing queue
            queue_stopped = self.processing_queue.stop(wait=True, timeout=30.0)
            
            self._is_running = False
            
            if file_monitor_stopped and queue_stopped:
                self.logger.info("Processing pipeline stopped successfully")
                return True
            else:
                self.logger.warning("Issues occurred while stopping processing pipeline")
                return False
    
    def _on_new_file(self, file_path: str) -> None:
        """
        Handle new files detected by the file monitor.
        
        Args:
            file_path: Path to the new file
        """
        try:
            self.logger.info(f"New file detected: {os.path.basename(file_path)}")
            
            with self._lock:
                self._stats["files_detected"] += 1
            
            # Check if we've already processed this file in the queue
            with self.processing_queue._queue_lock:
                if file_path in self.processing_queue._queue:
                    self.logger.info(f"File already in queue, skipping: {os.path.basename(file_path)}")
                    return
            
            # Add the file to the processing queue
            try:
                # Create metadata for the file
                metadata = {
                    "source_path": file_path,
                    "output_format": self.audio_format,
                    "quality": self.audio_quality,
                    "output_directory": self.output_directory
                }
                
                # Add to the queue
                self.processing_queue.add_file(file_path, metadata=metadata)
                self.logger.info(f"Added file to processing queue: {os.path.basename(file_path)}")
                
            except Exception as e:
                self.logger.error(f"Error adding file to queue: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error handling new file: {str(e)}")
    
    def _validate_video_file(self, file_path: str) -> bool:
        """
        Validate a video file before processing.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            bool: True if the file is valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Use AudioExtractor to validate the file
            valid, error_msg = self.audio_extractor.check_video_file(file_path)
            
            if not valid:
                self.logger.warning(f"Invalid video file {os.path.basename(file_path)}: {error_msg}")
            
            return valid
            
        except Exception as e:
            self.logger.error(f"Error validating video file {file_path}: {str(e)}")
            return False
    
    def _process_file(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Process a video file by extracting its audio.
        
        This is the main processing function called by the FileProcessor.
        
        Args:
            file_path: Path to the video file
            metadata: Additional metadata for processing
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            self.logger.info(f"Processing file: {os.path.basename(file_path)}")
            
            # Extract metadata
            output_format = metadata.get("output_format", self.audio_format)
            quality = metadata.get("quality", self.audio_quality)
            output_dir = metadata.get("output_directory", self.output_directory)
            
            # Generate output path
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            output_path = os.path.join(output_dir, f"{base_name}.{output_format}")
            
            # Check cache if available
            if self.cache_manager:
                cache_key = f"{file_path}_{os.path.getmtime(file_path)}_{quality}_{output_format}"
                cache_result = self.cache_manager.get("audio_extraction", cache_key)
                
                if cache_result and os.path.exists(cache_result):
                    self.logger.info(f"Using cached audio file: {os.path.basename(cache_result)}")
                    with self._lock:
                        self._stats["cached_hits"] += 1
                        self._stats["files_processed"] += 1
                    return True
            
            # Extract audio
            success, result = self.audio_extractor.extract_audio_with_profile(
                video_path=file_path,
                output_path=output_path,
                profile=quality
            )
            
            if success:
                self.logger.info(f"Audio extraction successful: {os.path.basename(file_path)} -> {os.path.basename(output_path)}")
                
                # Store in cache if available
                if self.cache_manager:
                    cache_key = f"{file_path}_{os.path.getmtime(file_path)}_{quality}_{output_format}"
                    self.cache_manager.store("audio_extraction", cache_key, output_path)
                
                with self._lock:
                    self._stats["files_processed"] += 1
                
                return True
            else:
                self.logger.error(f"Audio extraction failed: {result}")
                with self._lock:
                    self._stats["errors"] += 1
                return False
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            with self._lock:
                self._stats["errors"] += 1
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the processing pipeline.
        
        Returns:
            dict: Status information
        """
        monitor_status = self.file_monitor.get_status()
        queue_stats = self.processing_queue.get_stats()
        
        with self._lock:
            status = {
                "running": self._is_running,
                "watch_directory": self.watch_directory,
                "output_directory": self.output_directory,
                "stats": self._stats.copy(),
                "monitor": monitor_status,
                "queue": queue_stats
            }
            
            return status
    
    def retry_errors(self) -> int:
        """
        Retry files that encountered errors.
        
        Returns:
            int: Number of files reset for retry
        """
        count = self.processing_queue.retry_all_errors()
        self.logger.info(f"Reset {count} files for retry")
        return count
    
    def clear_completed(self) -> int:
        """
        Clear completed files from the queue.
        
        Returns:
            int: Number of files removed
        """
        count = self.processing_queue.clear_completed()
        self.logger.info(f"Cleared {count} completed files from queue")
        return count
    
    @property
    def is_running(self) -> bool:
        """Get the running state of the pipeline."""
        with self._lock:
            return self._is_running