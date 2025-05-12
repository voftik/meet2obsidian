#!/usr/bin/env python3
"""
Example of using the FileManager with other components.

This example demonstrates how to use the FileManager class to safely process 
audio files in the meet2obsidian application.
"""

import os
import sys
import logging
from typing import Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project components
from meet2obsidian.utils.file_manager import FileManager
from meet2obsidian.utils.logging import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger("file_manager_example")


class AudioProcessor:
    """Example class to demonstrate integration with FileManager."""
    
    def __init__(self, output_dir: str):
        """
        Initialize the AudioProcessor.
        
        Args:
            output_dir: Directory for processed files
        """
        self.file_manager = FileManager(logger=logger)
        self.output_dir = output_dir
        
        # Ensure output directory exists
        success, error = self.file_manager.ensure_directory_exists(output_dir)
        if not success:
            raise RuntimeError(f"Failed to create output directory: {error}")
            
        logger.info(f"AudioProcessor initialized with output directory: {output_dir}")
    
    def process_audio_file(self, audio_path: str, delete_source: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process an audio file and save the result.
        
        Args:
            audio_path: Path to the audio file
            delete_source: Whether to delete the source file after processing
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, error message, output path)
        """
        # Check if file exists
        if not os.path.exists(audio_path):
            return False, f"Audio file not found: {audio_path}", None
            
        # Check for sufficient disk space (assume we need 2x the file size)
        file_size = os.path.getsize(audio_path)
        required_space = file_size * 2
        
        success, error, has_space = self.file_manager.has_sufficient_space(self.output_dir, required_space)
        if not success:
            return False, f"Failed to check disk space: {error}", None
            
        if not has_space:
            return False, f"Insufficient disk space for processing. Need {required_space} bytes.", None
        
        # Generate output filename
        filename = os.path.basename(audio_path)
        base, ext = os.path.splitext(filename)
        processed_filename = f"{base}_processed{ext}"
        output_path = os.path.join(self.output_dir, processed_filename)
        
        # Define processing function (just a simple example)
        def audio_transform(data: bytes) -> bytes:
            # In a real application, this would do actual audio processing
            # This is just a placeholder for demonstration
            logger.info(f"Processing {len(data)} bytes of audio data")
            return data
        
        # Process the file
        return self.file_manager.safe_process_file(
            audio_path,
            output_path,
            processing_function=audio_transform,
            secure_delete=delete_source,
            create_dirs=True,
            overwrite=True
        )


def main():
    """Main function to demonstrate the audio processor."""
    # Create a temporary directory for output
    import tempfile
    output_dir = tempfile.mkdtemp()
    
    try:
        # Create a temporary audio file for testing
        audio_file = os.path.join(output_dir, "test_audio.wav")
        with open(audio_file, 'wb') as f:
            # Write dummy audio data (just for demonstration)
            f.write(b'RIFF' + b'\x00' * 1000)
        
        logger.info(f"Created test audio file: {audio_file}")
        
        # Initialize the audio processor
        processor = AudioProcessor(os.path.join(output_dir, "processed"))
        
        # Process the audio file
        success, error, output_path = processor.process_audio_file(audio_file, delete_source=True)
        
        if success:
            logger.info(f"Successfully processed audio to: {output_path}")
            
            # Verify the output file exists
            assert os.path.exists(output_path), "Output file should exist"
            logger.info("Output file exists and is accessible")
        else:
            logger.error(f"Failed to process audio: {error}")
    
    finally:
        # Clean up
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
        logger.info("Cleaned up temporary files")


if __name__ == "__main__":
    main()