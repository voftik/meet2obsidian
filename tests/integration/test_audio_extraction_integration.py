"""
Integration tests for audio extraction functionality.

This module contains integration tests that verify audio extraction works correctly
with real video files. These tests require actual video files to be present in the
test data directory.
"""

import os
import tempfile
import time
import pytest
import subprocess
from pathlib import Path

from meet2obsidian.audio.extractor import AudioExtractor


class TestAudioExtractionIntegration:
    """Integration tests for audio extraction with real files."""
    
    @pytest.fixture
    def extractor(self):
        """Create AudioExtractor instance for tests."""
        return AudioExtractor()
    
    @pytest.fixture
    def test_videos_dir(self):
        """Path to directory with test video files."""
        test_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'videos')
        if not os.path.exists(test_dir):
            pytest.skip("Test videos directory not found")
        return test_dir
    
    def setup_test_data(self, test_videos_dir):
        """
        Set up test data directory with synthetic video files if needed.
        
        This function checks if the test videos directory has required test files.
        If not, it creates synthetic test files for testing.
        """
        # Check if we need to create test files
        video_files = []
        for ext in ['.mp4', '.mov', '.webm', '.mkv']:
            video_files.extend(
                [f for f in os.listdir(test_videos_dir) if f.lower().endswith(ext)]
            )
        
        if len(video_files) < 3:
            print("Creating synthetic test videos...")
            
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                pytest.skip("FFmpeg not available - can't create test videos")
            
            # Create various test files
            # Short MP4
            self.create_synthetic_video(
                duration=3, 
                has_audio=True,
                output_path=os.path.join(test_videos_dir, 'short.mp4')
            )
            
            # Medium MP4 without audio
            self.create_synthetic_video(
                duration=10, 
                has_audio=False,
                output_path=os.path.join(test_videos_dir, 'medium_no_audio.mp4')
            )
            
            # MKV
            self.create_synthetic_video(
                duration=5, 
                has_audio=True,
                output_format='mkv',
                output_path=os.path.join(test_videos_dir, 'test.mkv')
            )
            
            print(f"Created test videos in {test_videos_dir}")
    
    def create_synthetic_video(self, duration=5, has_audio=True, corrupt=False, 
                               output_format='mp4', output_path=None):
        """
        Create a synthetic test video file.
        
        Args:
            duration: Duration in seconds (default: 5)
            has_audio: Whether to include audio track (default: True)
            corrupt: Whether to corrupt the file (default: False)
            output_format: Format of the output file (default: mp4)
            output_path: Path where to save the video (default: temp file)
            
        Returns:
            Path to created video file
        """
        # Create a temporary file for the video if no output path is provided
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False)
            video_path = temp_file.name
            temp_file.close()
        else:
            video_path = output_path
        
        try:
            # Create a synthetic video using FFmpeg
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-f', 'lavfi',  # Use lavfi input format
                '-i', f'color=c=blue:s=640x480:d={duration}',  # Blue background
            ]
            
            # Add audio if requested
            if has_audio:
                cmd.extend([
                    '-f', 'lavfi',
                    '-i', f'sine=frequency=440:duration={duration}'  # 440Hz tone
                ])
            
            # Add output file
            cmd.extend([
                '-shortest',  # Match shortest input stream
                video_path
            ])
            
            # Run FFmpeg command
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            
            # Corrupt the file if requested
            if corrupt:
                with open(video_path, 'r+b') as f:
                    # Jump to a position that will corrupt the file but still keep it as a file
                    f.seek(100)
                    # Write some random bytes
                    f.write(os.urandom(10))
            
            return video_path
            
        except Exception as e:
            # Clean up if an error occurred
            if os.path.exists(video_path):
                os.unlink(video_path)
            pytest.fail(f"Failed to create synthetic video: {str(e)}")
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    def test_process_real_video_files(self, extractor, test_videos_dir):
        """Test processing several real video files."""
        self.setup_test_data(test_videos_dir)
        
        # Get all video files in test directory
        video_files = []
        for ext in ['.mp4', '.mov', '.webm', '.mkv']:
            video_files.extend(
                [os.path.join(test_videos_dir, f) for f in os.listdir(test_videos_dir)
                 if f.lower().endswith(ext)]
            )
        
        if not video_files:
            pytest.skip("No test video files found even after setup")
        
        # Process each file
        for video_path in video_files:
            # Arrange
            with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
                audio_path = temp_audio.name
            
            try:
                # Act
                result, output = extractor.extract_audio(video_path, audio_path)
                
                # Assert
                assert result is True, f"Failed to process {os.path.basename(video_path)}: {output}"
                assert os.path.exists(audio_path), f"Audio not created for {os.path.basename(video_path)}"
                assert os.path.getsize(audio_path) > 0, f"Audio empty for {os.path.basename(video_path)}"
                
                # Get video info to verify
                video_info = extractor.get_video_info(video_path)
                assert video_info is not None, f"Failed to get video info for {os.path.basename(video_path)}"
                
                # Get audio info to verify
                audio_info = extractor.get_video_info(audio_path)
                assert audio_info is not None, f"Failed to get audio info for {audio_path}"
                
                # Check that audio info has audio streams
                audio_streams = [s for s in audio_info["streams"] if s["codec_type"] == "audio"]
                assert len(audio_streams) > 0, f"No audio streams found in {audio_path}"
                
            finally:
                # Clean up
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    @pytest.mark.parametrize("format_type", ["wav", "mp3", "m4a"])
    def test_format_compatibility(self, extractor, test_videos_dir, format_type):
        """Test compatibility with different output formats."""
        self.setup_test_data(test_videos_dir)
        
        # Find an MP4 file to test with
        mp4_files = [os.path.join(test_videos_dir, f) for f in os.listdir(test_videos_dir)
                     if f.lower().endswith('.mp4')]
        
        if not mp4_files:
            pytest.skip("No MP4 test files found")
        
        video_path = mp4_files[0]
        
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=f'.{format_type}', delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        try:
            # Act
            result, output = extractor.extract_audio(video_path, audio_path, format=format_type)
            
            # Assert
            assert result is True, f"Failed to extract {format_type} format: {output}"
            assert os.path.exists(audio_path), f"{format_type} file not created"
            assert os.path.getsize(audio_path) > 0, f"{format_type} file is empty"
        finally:
            # Clean up
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    @pytest.mark.parametrize("bitrate", ["64k", "128k", "192k", "256k"])
    def test_bitrate_settings(self, extractor, test_videos_dir, bitrate):
        """Test different bitrate settings for audio extraction."""
        self.setup_test_data(test_videos_dir)
        
        # Find an MP4 file to test with
        mp4_files = [os.path.join(test_videos_dir, f) for f in os.listdir(test_videos_dir)
                     if f.lower().endswith('.mp4')]
        
        if not mp4_files:
            pytest.skip("No MP4 test files found")
        
        video_path = mp4_files[0]
        
        # Dictionary to store file sizes
        file_sizes = {}
        
        # Extract audio with different bitrates
        for br in ["64k", "256k"]:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
                audio_path = temp_audio.name
            
            try:
                # Act
                result, output = extractor.extract_audio(video_path, audio_path, 
                                                       format='mp3', bitrate=br)
                
                # Assert
                assert result is True, f"Failed to extract with bitrate {br}: {output}"
                assert os.path.exists(audio_path), f"Audio file not created with bitrate {br}"
                
                # Store file size
                file_sizes[br] = os.path.getsize(audio_path)
            finally:
                # Clean up
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
        
        # Higher bitrate should result in larger file
        if "64k" in file_sizes and "256k" in file_sizes:
            assert file_sizes["256k"] > file_sizes["64k"], \
                "Higher bitrate should result in larger file size"
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    @pytest.mark.slow
    def test_extraction_performance(self, extractor, test_videos_dir):
        """Test extraction performance with a synthetic 30-second video."""
        # Create a 30-second test video
        video_path = self.create_synthetic_video(duration=30, has_audio=True)
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        try:
            # Measure extraction time
            start_time = time.time()
            result, output = extractor.extract_audio(video_path, audio_path)
            processing_time = time.time() - start_time
            
            # Assert
            assert result is True, f"Extraction failed with error: {output}"
            assert os.path.exists(audio_path), "Audio file was not created"
            assert os.path.getsize(audio_path) > 0, "Audio file is empty"
            
            # Log performance info
            video_size = os.path.getsize(video_path)
            audio_size = os.path.getsize(audio_path)
            print(f"Test video size: {video_size/1024:.2f}KB")
            print(f"Extracted audio size: {audio_size/1024:.2f}KB")
            print(f"Processing time: {processing_time:.2f} seconds")
            print(f"Processing speed: {video_size/(processing_time*1024*1024):.2f}MB/s")
            
            # Basic performance assertion (should process faster than real-time)
            assert processing_time < 30, "Processing should be faster than real-time"
            
        finally:
            # Clean up
            if os.path.exists(audio_path):
                os.unlink(audio_path)
            if os.path.exists(video_path):
                os.unlink(video_path)