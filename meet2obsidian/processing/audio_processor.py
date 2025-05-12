"""
Module containing the processor for extracting audio from video files.
"""

import os
import logging
from typing import Dict, Any, Optional

from meet2obsidian.audio.extractor import AudioExtractor
from meet2obsidian.processing.processor import FileProcessor
from meet2obsidian.utils.logging import get_logger


class AudioExtractionProcessor(FileProcessor):
    """
    Processor for extracting audio from video files.
    
    Implements the FileProcessor interface for use in the queue processing system.
    """
    
    def __init__(self, output_dir: Optional[str] = None, logger=None):
        """
        Initialize the processor.
        
        Args:
            output_dir: Directory for saving audio files
            logger: Logger object for message logging
        """
        self.logger = logger or get_logger('processing.audio')
        self.extractor = AudioExtractor(logger=self.logger)
        self.output_dir = output_dir

        # Create a processor function to pass to FileProcessor
        def processor_func(file_path, metadata):
            return self.process_file(file_path, metadata)

        # Initialize the FileProcessor with processor function
        super().__init__(processor_func)
    
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Process file - extract audio from video.
        
        Args:
            file_path: Path to file for processing
            metadata: File metadata
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            self.logger.info(f"Starting file processing: {file_path}")
            
            # Check that file exists and is a valid video file
            is_valid, error = self.extractor.check_video_file(file_path)
            if not is_valid:
                self.logger.error(f"Invalid video file: {error}")
                return False
            
            # Determine output path
            if self.output_dir:
                # Use specified directory while preserving the filename
                filename = os.path.basename(file_path)
                name, _ = os.path.splitext(filename)
                output_path = os.path.join(self.output_dir, f"{name}.m4a")
            else:
                # Create file next to the original
                base, _ = os.path.splitext(file_path)
                output_path = f"{base}.m4a"
            
            # Extract audio with optimized settings for transcription
            success, result = self.extractor.extract_audio_with_profile(
                file_path, 
                output_path, 
                profile='voice'  # Optimized for speech
            )
            
            if success:
                self.logger.info(f"Audio successfully extracted: {output_path}")
                
                # Update metadata for passing to next stages
                if metadata is None:
                    metadata = {}
                
                metadata['audio_path'] = output_path
                metadata['original_video_path'] = file_path
                
                # Get video duration
                duration, duration_success = self.extractor.get_video_duration(file_path)
                if duration_success:
                    metadata['duration'] = duration
                
                # Get detailed video info
                video_info = self.extractor.get_video_info(file_path)
                if video_info:
                    metadata['video_info'] = video_info
                
                return True
            else:
                self.logger.error(f"Failed to extract audio: {result}")
                return False
                
        except Exception as e:
            self.logger.exception(f"Unexpected error processing file: {str(e)}")
            return False
    
    def quick_validate(self, file_path: str) -> bool:
        """
        Quickly validate a file to see if it's a processable video.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            bool: True if the file appears to be a valid video
        """
        return self.extractor.quick_check_video(file_path)