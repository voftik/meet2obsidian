# Audio Extraction Component

This document provides a comprehensive guide to the audio extraction component of the meet2obsidian application, including implementation details, testing approach, and best practices.

## Overview

The audio extraction component is responsible for extracting audio from video files, which is a critical first step in the processing pipeline after a file is detected. The extracted audio is later used for transcription by speech recognition services.

## Core Functionality

The `AudioExtractor` class provides the following key functions:

1. **Video Validation** - Checking if a video file is valid and readable
2. **Audio Extraction** - Extracting audio from video files with configurable parameters
3. **Video Information** - Retrieving metadata about video files
4. **Duration Detection** - Determining the length of video files

## Implementation Details

### Dependencies

The audio extraction component has the following dependencies:

- **FFmpeg** - External command-line tool for handling multimedia data
- **Python Standard Library**:
  - `subprocess` - For executing FFmpeg commands
  - `os` - For file system operations
  - `json` - For parsing FFmpeg output

### AudioExtractor Class

The main class is `AudioExtractor`, which is defined in `meet2obsidian/audio/extractor.py`:

```python
class AudioExtractor:
    """
    Class for extracting audio from video files.
    
    Uses ffmpeg to extract audio tracks from video files
    and prepare them for transcription.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the audio extractor.
        
        Args:
            logger: Optional logger. If not provided, a new one will be created.
        """
        self.logger = logger or get_logger('audio.extractor')
    
    def check_video_file(self, video_path):
        """
        Check if a video file is valid and readable.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        # Implementation details...
    
    def extract_audio(self, video_path, output_path=None, 
                     format='wav', bitrate='128k',
                     channels=1, sample_rate=16000):
        """
        Extract an audio track from a video file.
        
        Args:
            video_path: Path to the video file
            output_path: Path for saving the audio. If not specified, will use
                         the video path with a changed extension.
            format: Output audio format (wav, mp3, etc.)
            bitrate: Audio bitrate
            channels: Number of channels (1 for mono, 2 for stereo)
            sample_rate: Sample rate in Hz
            
        Returns:
            Tuple[bool, Optional[str]]: (success, output_path or error_message)
        """
        # Implementation details...
    
    def get_video_info(self, video_path):
        """
        Get metadata about a video file (duration, resolution, codec, etc.).
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary with video information or None on error
        """
        # Implementation details...
```

### FFmpeg Integration

The component uses FFmpeg for all media processing operations. Here's how the integration works:

1. **Commands are executed via subprocess**:
   ```python
   result = subprocess.run(cmd, capture_output=True, text=True)
   ```

2. **Command output is parsed**:
   ```python
   if result.returncode == 0:
       # Success, parse output
       data = json.loads(result.stdout)
   else:
       # Error handling
       error_message = result.stderr
   ```

3. **FFmpeg output is processed and returned in a standardized format**:
   ```python
   processed_info = {
       'filename': os.path.basename(video_path),
       'duration': float(info.get('format', {}).get('duration', 0)),
       'streams': []
   }
   
   # Add stream information
   for stream in info.get('streams', []):
       stream_info = {
           'codec_type': stream.get('codec_type'),
           'codec_name': stream.get('codec_name'),
       }
       # Add type-specific details
       processed_info['streams'].append(stream_info)
   ```

### Error Handling

The component implements comprehensive error handling:

1. **File Existence and Permissions**:
   ```python
   if not os.path.exists(video_path):
       return False, f"File does not exist: {video_path}"
       
   if not os.access(video_path, os.R_OK):
       return False, f"No read permissions for file: {video_path}"
   ```

2. **FFmpeg Process Errors**:
   ```python
   if result.returncode != 0:
       self.logger.error(f"Error extracting audio: {result.stderr}")
       return False, f"Error extracting audio: {result.stderr}"
   ```

3. **Output Validation**:
   ```python
   if not os.path.exists(output_path):
       return False, "Audio file was not created"
   ```

4. **Exception Handling**:
   ```python
   try:
       # FFmpeg operations
   except Exception as e:
       self.logger.exception(f"Exception while extracting audio from {video_path}")
       return False, f"Error extracting audio: {str(e)}"
   ```

## Testing Approach

The audio extraction component has a comprehensive testing strategy with three main types of tests:

### 1. Unit Tests

Unit tests focus on testing the component's functionality with mocked FFmpeg interactions. These tests verify:

- Proper handling of file existence and permissions
- Correct command construction for different extraction options
- Error handling for various scenarios
- Metadata processing and formatting

### 2. Synthetic Video Tests

These tests use small, synthetically generated video files created during the test to verify actual extraction functionality:

- Testing extraction with different output formats
- Testing extraction with different audio codecs and parameters
- Testing with videos with and without audio streams
- Testing validation with corrupt video files
- Testing duration detection accuracy

### 3. Integration Tests

Integration tests verify the component works correctly with real video files:

- Processing different video formats (MP4, MOV, WEBM, MKV)
- Compatibility with various output formats
- Performance testing with larger files
- End-to-end process testing from validation to extraction

## Best Practices

When working with the audio extraction component, follow these best practices:

### 1. File Handling

- Always validate video files before processing
- Use proper error handling and reporting
- Clean up temporary files after processing

### 2. FFmpeg Usage

- Use `-y` flag to overwrite existing files when needed
- Use `-vn` to exclude video streams when extracting audio
- Configure bitrate and sample rate based on the transcription service requirements
- Use `-f` to specify the output format explicitly

### 3. Performance Considerations

- Processing large files can be resource-intensive
- Consider adding a maximum file size limit for processing
- Monitor FFmpeg process memory and CPU usage
- Implement timeouts for long-running processes

### 4. Error Handling

- Always check return codes from FFmpeg processes
- Log both stdout and stderr from FFmpeg for debugging
- Implement retries for transient errors
- Validate output files after processing

## Integration with Other Components

The audio extraction component integrates with other parts of the system as follows:

### 1. File Monitor Integration

The file monitor detects new video files and passes them to the processing pipeline, which initiates audio extraction.

### 2. Processing Queue Integration

Audio extraction is the first step in the processing queue workflow. The extraction task is:

1. Added to the queue when a new file is detected
2. Processed with appropriate priority
3. Marked as completed or failed based on the extraction result
4. Has its output passed to the next step (transcription)

### 3. Config Integration

Audio extraction parameters can be configured in the application config:

```yaml
audio:
  format: m4a
  bitrate: 128k
  channels: 1
  sample_rate: 16000
```

## Reference Implementation

Below is a reference implementation for the key methods of the `AudioExtractor` class:

### Extract Audio Method

```python
def extract_audio(self, video_path, output_path=None, 
                 format='wav', bitrate='128k',
                 channels=1, sample_rate=16000):
    """
    Extract an audio track from a video file.
    
    Args:
        video_path: Path to the video file
        output_path: Path for saving the audio. If not specified, will use
                     the video path with a changed extension.
        format: Output audio format (wav, mp3, etc.)
        bitrate: Audio bitrate
        channels: Number of channels (1 for mono, 2 for stereo)
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple[bool, Optional[str]]: (success, output_path or error_message)
    """
    # Validate the video file first
    is_valid, error_msg = self.check_video_file(video_path)
    if not is_valid:
        self.logger.error(f"Cannot extract audio from invalid video file: {error_msg}")
        return False, error_msg
    
    # If output path is not specified, create one based on the video path
    if output_path is None:
        base_path = os.path.splitext(video_path)[0]
        output_path = f"{base_path}.{format}"
    
    self.logger.info(f"Extracting audio from {video_path} to {output_path}")
    
    try:
        # FFmpeg command for audio extraction
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # Disable video
            '-ar', str(sample_rate),  # Sample rate
            '-ac', str(channels),     # Channels
            '-b:a', bitrate,          # Audio bitrate
            '-f', format,             # Output format
            '-y',                     # Overwrite output file if it exists
            output_path
        ]
        
        # Run the process
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check result
        if result.returncode != 0:
            self.logger.error(f"Error extracting audio: {result.stderr}")
            return False, f"Error extracting audio: {result.stderr}"
            
        # Verify the output file exists
        if not os.path.exists(output_path):
            return False, "Audio file was not created"
            
        self.logger.info(f"Audio successfully extracted: {output_path}")
        return True, output_path
        
    except Exception as e:
        self.logger.exception(f"Exception while extracting audio from {video_path}")
        return False, f"Error extracting audio: {str(e)}"
```

### Get Video Info Method

```python
def get_video_info(self, video_path):
    """
    Get metadata about a video file (duration, resolution, codec, etc.).
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary with video information or None on error
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.logger.error(f"Error getting video info: {result.stderr}")
            return None
            
        # Parse JSON response
        info = json.loads(result.stdout)
        
        # Extract and process important information
        processed_info = {
            'filename': os.path.basename(video_path),
            'full_path': video_path,
            'format_name': info.get('format', {}).get('format_name', 'unknown'),
            'duration': float(info.get('format', {}).get('duration', 0)),
            'size': int(info.get('format', {}).get('size', 0)),
            'bit_rate': int(info.get('format', {}).get('bit_rate', 0)),
            'streams': []
        }
        
        # Process stream information
        for stream in info.get('streams', []):
            stream_info = {
                'codec_type': stream.get('codec_type'),
                'codec_name': stream.get('codec_name'),
            }
            
            # Add video stream info
            if stream.get('codec_type') == 'video':
                stream_info.update({
                    'width': stream.get('width'),
                    'height': stream.get('height'),
                    'display_aspect_ratio': stream.get('display_aspect_ratio'),
                    'fps': stream.get('r_frame_rate')
                })
            
            # Add audio stream info
            elif stream.get('codec_type') == 'audio':
                stream_info.update({
                    'sample_rate': stream.get('sample_rate'),
                    'channels': stream.get('channels'),
                    'channel_layout': stream.get('channel_layout')
                })
            
            processed_info['streams'].append(stream_info)
        
        return processed_info
        
    except Exception as e:
        self.logger.exception(f"Exception getting info for video {video_path}")
        return None
```

## Conclusion

The audio extraction component is a critical part of the meet2obsidian application, serving as the first step in the processing pipeline for converting video files to text notes. By following the implementation details and testing approach outlined in this document, you can ensure the component works reliably and efficiently.