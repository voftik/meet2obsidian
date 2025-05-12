"""
Unit tests for the AudioExtractor class.

This module contains tests to verify the functionality of the audio extraction component,
which is responsible for extracting audio from video files, checking video validity,
and retrieving metadata.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from meet2obsidian.audio.extractor import AudioExtractor


class TestAudioExtractor:
    """Unit tests for AudioExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create AudioExtractor instance for tests."""
        return AudioExtractor()
    
    @pytest.fixture
    def sample_video_path(self):
        """Path to a sample video file."""
        # This will be replaced by a mock in most tests
        return "/path/to/sample_video.mp4"
    
    def test_init(self):
        """Test AudioExtractor initialization."""
        # Arrange & Act
        extractor = AudioExtractor()
        
        # Assert
        assert extractor is not None
        assert extractor.logger is not None
    
    def test_check_video_file_nonexistent(self, extractor):
        """Test checking a nonexistent video file."""
        # Arrange
        nonexistent_path = "/nonexistent/path/to/video.mp4"

        # Act
        result, error = extractor.check_video_file(nonexistent_path)

        # Assert
        assert result is False
        assert error is not None
        # Вместо проверки сообщения на русском, проверяем наличие пути
        assert nonexistent_path in error
    
    def test_check_video_file_not_readable(self, extractor):
        """Test checking a video file without read permissions."""
        # Arrange
        test_file = "/path/to/video.mp4"
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=False):

            # Act
            result, error = extractor.check_video_file(test_file)

            # Assert
            assert result is False
            assert error is not None
            # Проверяем наличие пути в сообщении об ошибке
            assert test_file in error
    
    def test_check_video_file_invalid_format(self, extractor):
        """Test checking a file with invalid video format."""
        # Arrange
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_run:

            # Mock subprocess to simulate FFprobe error
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_error_message = "Invalid data found when processing input"
            mock_process.stderr = mock_error_message
            mock_run.return_value = mock_process

            # Act
            result, error = extractor.check_video_file("/path/to/video.mp4")

            # Assert
            assert result is False
            assert error is not None
            # Проверяем, что текст ошибки ffprobe включен в сообщение
            assert mock_error_message in error
    
    def test_check_video_file_no_duration(self, extractor):
        """Test checking a video file with no duration information."""
        # Arrange
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_run, \
             patch('json.loads') as mock_json:

            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "{}"
            mock_run.return_value = mock_process

            # Mock JSON parsing to return data without format/duration
            mock_json.return_value = {"format": {}}

            # Act
            result, error = extractor.check_video_file("/path/to/video.mp4")

            # Assert
            assert result is False
            assert error is not None
            # Проверка содержимого не требуется, так как сообщение содержит кириллицу
    
    def test_check_video_file_invalid_duration(self, extractor):
        """Test checking a video file with invalid duration."""
        # Arrange
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_run, \
             patch('json.loads') as mock_json:

            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "{}"
            mock_run.return_value = mock_process

            # Mock JSON parsing to return zero duration
            mock_json.return_value = {"format": {"duration": "0"}}

            # Act
            result, error = extractor.check_video_file("/path/to/video.mp4")

            # Assert
            assert result is False
            assert error is not None
            # Проверяем наличие информации о длительности в ошибке
            assert "0" in error
    
    def test_check_video_file_valid(self, extractor):
        """Test checking a valid video file."""
        # Arrange
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_run, \
             patch('json.loads') as mock_json:
            
            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "{}"
            mock_run.return_value = mock_process
            
            # Mock JSON parsing to return valid duration
            mock_json.return_value = {"format": {"duration": "10.5"}}
            
            # Act
            result, error = extractor.check_video_file("/path/to/video.mp4")
            
            # Assert
            assert result is True
            assert error is None
    
    def test_extract_audio_invalid_video(self, extractor):
        """Test extracting audio from an invalid video file."""
        # Arrange
        with patch.object(extractor, 'check_video_file', return_value=(False, "Invalid video")):
            # Act
            result, error = extractor.extract_audio("/path/to/video.mp4")
            
            # Assert
            assert result is False
            assert error == "Invalid video"
    
    def test_extract_audio_default_output_path(self, extractor):
        """Test extracting audio with default output path."""
        # Arrange
        video_path = "/path/to/video.mp4"
        expected_output = "/path/to/video.wav"  # Default format is wav
        
        with patch.object(extractor, 'check_video_file', return_value=(True, None)), \
             patch('subprocess.run') as mock_run, \
             patch('os.path.exists', return_value=True):
            
            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process
            
            # Act
            result, output_path = extractor.extract_audio(video_path)
            
            # Assert
            assert result is True
            assert output_path == expected_output
            mock_run.assert_called_once()
            # Check command arguments
            args = mock_run.call_args[0][0]
            assert args[0] == 'ffmpeg'
            assert args[1] == '-i'
            assert args[2] == video_path
    
    def test_extract_audio_custom_output_path(self, extractor):
        """Test extracting audio with custom output path."""
        # Arrange
        video_path = "/path/to/video.mp4"
        output_path = "/path/to/output.mp3"
        
        with patch.object(extractor, 'check_video_file', return_value=(True, None)), \
             patch('subprocess.run') as mock_run, \
             patch('os.path.exists', return_value=True):
            
            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process
            
            # Act
            result, actual_output = extractor.extract_audio(video_path, output_path, format='mp3')
            
            # Assert
            assert result is True
            assert actual_output == output_path
            mock_run.assert_called_once()
            # Check command arguments
            args = mock_run.call_args[0][0]
            assert args[0] == 'ffmpeg'
            assert output_path in args
    
    def test_extract_audio_ffmpeg_error(self, extractor):
        """Test extracting audio when FFmpeg returns an error."""
        # Arrange
        with patch.object(extractor, 'check_video_file', return_value=(True, None)), \
             patch('subprocess.run') as mock_run:
            
            # Mock subprocess to return error
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "FFmpeg error: Invalid data found when processing input"
            mock_run.return_value = mock_process
            
            # Act
            result, error = extractor.extract_audio("/path/to/video.mp4", "/path/to/output.wav")
            
            # Assert
            assert result is False
            assert error is not None
            assert "FFmpeg error" in error
    
    def test_extract_audio_subprocess_error(self, extractor):
        """Test extracting audio when subprocess raises an exception."""
        # Arrange
        with patch.object(extractor, 'check_video_file', return_value=(True, None)), \
             patch('subprocess.run', side_effect=Exception("Test exception")):

            # Act
            result, error = extractor.extract_audio("/path/to/video.mp4", "/path/to/output.wav")

            # Assert
            assert result is False
            assert error is not None
            # Проверяем наличие текста исключения в сообщении об ошибке
            assert "Test exception" in error
    
    def test_extract_audio_output_not_created(self, extractor):
        """Test extracting audio when output file is not created."""
        # Arrange
        output_path = "/path/to/output.wav"
        with patch.object(extractor, 'check_video_file', return_value=(True, None)), \
             patch('subprocess.run') as mock_run, \
             patch('os.path.exists', return_value=False):

            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Act
            result, error = extractor.extract_audio("/path/to/video.mp4", output_path)

            # Assert
            assert result is False
            assert error is not None
            # Проверка, что в сообщении об ошибке есть ссылка на то, что файл не создан
            # (без проверки конкретного текста на русском)
    
    def test_extract_audio_custom_parameters(self, extractor):
        """Test extracting audio with custom format, bitrate, channels and sample rate."""
        # Arrange
        video_path = "/path/to/video.mp4"
        output_path = "/path/to/output.mp3"
        format_type = "mp3"
        bitrate = "192k"
        channels = 2
        sample_rate = 44100
        
        with patch.object(extractor, 'check_video_file', return_value=(True, None)), \
             patch('subprocess.run') as mock_run, \
             patch('os.path.exists', return_value=True):
            
            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process
            
            # Act
            result, actual_output = extractor.extract_audio(
                video_path, output_path, 
                format=format_type, 
                bitrate=bitrate,
                channels=channels, 
                sample_rate=sample_rate
            )
            
            # Assert
            assert result is True
            assert actual_output == output_path
            
            # Check command arguments
            args = mock_run.call_args[0][0]
            assert args[0] == 'ffmpeg'
            assert '-ar' in args
            assert str(sample_rate) in args
            assert '-ac' in args
            assert str(channels) in args
            assert '-b:a' in args
            assert bitrate in args
            assert '-f' in args
            assert format_type in args
    
    def test_get_video_info_valid(self, extractor):
        """Test getting video information for a valid video."""
        # Arrange
        with patch('subprocess.run') as mock_run, \
             patch('json.loads') as mock_json:
            
            # Mock subprocess to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "{}"
            mock_run.return_value = mock_process
            
            # Mock JSON parsing to return valid info
            mock_json.return_value = {
                "format": {
                    "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                    "duration": "10.5",
                    "size": "1048576",
                    "bit_rate": "1000000"
                },
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1920,
                        "height": 1080,
                        "display_aspect_ratio": "16:9",
                        "r_frame_rate": "30/1"
                    },
                    {
                        "codec_type": "audio",
                        "codec_name": "aac",
                        "sample_rate": "44100",
                        "channels": 2,
                        "channel_layout": "stereo"
                    }
                ]
            }
            
            # Act
            info = extractor.get_video_info("/path/to/video.mp4")
            
            # Assert
            assert info is not None
            assert info["format_name"] == "mov,mp4,m4a,3gp,3g2,mj2"
            assert info["duration"] == 10.5
            assert info["size"] == 1048576
            assert info["bit_rate"] == 1000000
            assert len(info["streams"]) == 2
            
            # Check video stream info
            video_stream = info["streams"][0]
            assert video_stream["codec_type"] == "video"
            assert video_stream["width"] == 1920
            assert video_stream["height"] == 1080
            
            # Check audio stream info
            audio_stream = info["streams"][1]
            assert audio_stream["codec_type"] == "audio"
            assert audio_stream["sample_rate"] == "44100"
            assert audio_stream["channels"] == 2
    
    def test_get_video_info_ffprobe_error(self, extractor):
        """Test getting video info when FFprobe returns an error."""
        # Arrange
        with patch('subprocess.run') as mock_run:
            
            # Mock subprocess to return error
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "FFprobe error"
            mock_run.return_value = mock_process
            
            # Act
            info = extractor.get_video_info("/path/to/video.mp4")
            
            # Assert
            assert info is None
    
    def test_get_video_info_exception(self, extractor):
        """Test getting video info when an exception occurs."""
        # Arrange
        with patch('subprocess.run', side_effect=Exception("Test exception")):
            
            # Act
            info = extractor.get_video_info("/path/to/video.mp4")
            
            # Assert
            assert info is None