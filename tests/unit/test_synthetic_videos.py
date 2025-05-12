"""
Tests for audio extraction using synthetically generated video files.

This module contains tests that use synthetically generated video files to test
the audio extraction functionality. These tests help validate different aspects of
audio extraction without requiring real video files.
"""

import os
import subprocess
import tempfile
import time
import pytest
from pathlib import Path

from meet2obsidian.audio.extractor import AudioExtractor


class TestSyntheticVideos:
    """Tests using synthetically generated video files."""
    
    @pytest.fixture
    def extractor(self):
        """Create AudioExtractor instance for tests."""
        return AudioExtractor()
    
    @pytest.fixture
    def create_synthetic_video(self):
        """Create a synthetic video file for testing."""
        created_files = []
        
        def _create(duration=5, has_audio=True, corrupt=False, output_path=None):
            """
            Create a synthetic video file with specified parameters.
            
            Args:
                duration: Duration in seconds (default: 5)
                has_audio: Whether to include audio (default: True)
                corrupt: Whether to make the file corrupt (default: False)
                output_path: Path where to save the video (default: temp file)
                
            Returns:
                Path to the created file
            """
            # Create a temporary file for the video if no output path is provided
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                video_path = temp_file.name
                temp_file.close()
            else:
                video_path = output_path

            try:
                # Check if ffmpeg is available
                try:
                    subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                except (subprocess.SubprocessError, FileNotFoundError):
                    pytest.skip("FFmpeg not available - skipping test")
                
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
                
                # Track the file for cleanup
                created_files.append(video_path)
                return video_path
                
            except Exception as e:
                # Clean up if an error occurred
                if os.path.exists(video_path):
                    os.unlink(video_path)
                pytest.fail(f"Failed to create synthetic video: {str(e)}")
        
        yield _create
        
        # Clean up any created files
        for file_path in created_files:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    def test_extract_audio_from_synthetic_video(self, extractor, create_synthetic_video):
        """Test audio extraction from a synthetically generated video."""
        # Skip if ffmpeg is not installed
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            pytest.skip("FFmpeg not available - skipping test")
            
        # Arrange - create synthetic video with audio
        video_path = create_synthetic_video(duration=3, has_audio=True)
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        try:
            # Act
            result, output = extractor.extract_audio(video_path, audio_path)
            
            # Assert
            assert result is True, f"Extraction failed with error: {output}"
            assert os.path.exists(audio_path), "Audio file was not created"
            assert os.path.getsize(audio_path) > 0, "Audio file is empty"
        finally:
            # Clean up
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    def test_extract_audio_no_audio_stream(self, extractor, create_synthetic_video):
        """Test extracting audio from a video with no audio stream."""
        # Skip if ffmpeg is not installed
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            pytest.skip("FFmpeg not available - skipping test")
            
        # Arrange - create synthetic video without audio
        video_path = create_synthetic_video(duration=3, has_audio=False)
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        try:
            # Act
            result, output = extractor.extract_audio(video_path, audio_path)
            
            # Assert
            assert result is True, f"Extraction failed with error: {output}"
            assert os.path.exists(audio_path), "Audio file was not created"
            # The file might be very small (or empty) since there's no audio
            # But the operation should not fail
        finally:
            # Clean up
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    def test_validate_corrupt_video(self, extractor, create_synthetic_video):
        """Test validation with a corrupt video file."""
        # Skip if ffmpeg is not installed
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            pytest.skip("FFmpeg not available - skipping test")
            
        # Arrange - create corrupted video
        video_path = create_synthetic_video(corrupt=True)
        
        # Act
        is_valid, error = extractor.check_video_file(video_path)
        
        # Assert
        assert is_valid is False, "Corrupt video should fail validation"
        assert error is not None, "Error should be provided for corrupt file"
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    @pytest.mark.parametrize("expected_duration", [1, 3, 5])
    def test_video_duration_accuracy(self, extractor, create_synthetic_video, expected_duration):
        """Test accuracy of video duration reporting."""
        # Skip if ffmpeg is not installed
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            pytest.skip("FFmpeg not available - skipping test")
            
        # Arrange - create video with specific duration
        video_path = create_synthetic_video(duration=expected_duration)
        
        # Act
        info = extractor.get_video_info(video_path)
        
        # Assert
        assert info is not None, "Failed to get video information"
        # Check duration with 0.1 second tolerance
        assert abs(info["duration"] - expected_duration) < 0.2, \
            f"Expected duration {expected_duration}, got {info['duration']}"
    
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    @pytest.mark.parametrize("format_type", ["wav", "mp3", "m4a"])
    def test_extract_audio_different_formats(self, extractor, create_synthetic_video, format_type):
        """Test audio extraction with different output formats."""
        # Skip if ffmpeg is not installed
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            pytest.skip("FFmpeg not available - skipping test")
            
        # Arrange - create synthetic video
        video_path = create_synthetic_video(duration=2)
        
        with tempfile.NamedTemporaryFile(suffix=f'.{format_type}', delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        try:
            # Act
            result, output = extractor.extract_audio(video_path, audio_path, format=format_type)
            
            # Assert
            assert result is True, f"Extraction to {format_type} failed with error: {output}"
            assert os.path.exists(audio_path), f"{format_type} file was not created"
            assert os.path.getsize(audio_path) > 0, f"{format_type} file is empty"
        finally:
            # Clean up
            if os.path.exists(audio_path):
                os.unlink(audio_path)
                
    @pytest.mark.skipif(not os.path.exists('/usr/bin/ffmpeg') and not os.path.exists('/usr/local/bin/ffmpeg'),
                         reason="FFmpeg not installed")
    @pytest.mark.parametrize("channels", [1, 2])
    def test_extract_audio_channels(self, extractor, create_synthetic_video, channels):
        """Test audio extraction with different channel counts."""
        # Skip if ffmpeg is not installed
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            pytest.skip("FFmpeg not available - skipping test")
            
        # Arrange - create synthetic video
        video_path = create_synthetic_video(duration=2)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        try:
            # Act
            result, output = extractor.extract_audio(video_path, audio_path, channels=channels)
            
            # Assert
            assert result is True, f"Extraction with {channels} channels failed with error: {output}"
            assert os.path.exists(audio_path), "Audio file was not created"
            
            # Verify channels using ffprobe
            info = extractor.get_video_info(audio_path)
            assert info is not None, "Failed to get audio file information"
            
            # Find audio stream
            audio_streams = [s for s in info["streams"] if s["codec_type"] == "audio"]
            assert len(audio_streams) > 0, "No audio streams found in output file"
            
            # Check channels (might be reported as int or string depending on ffprobe version)
            audio_stream = audio_streams[0]
            assert str(audio_stream["channels"]) == str(channels), \
                f"Expected {channels} channels, got {audio_stream['channels']}"
            
        finally:
            # Clean up
            if os.path.exists(audio_path):
                os.unlink(audio_path)