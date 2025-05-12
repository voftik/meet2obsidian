# Meet2Obsidian Technical Overview

## Project Purpose and Structure

Meet2Obsidian is a tool designed to automatically convert video conference recordings into structured Obsidian notes. It processes video files (from sources like Zoom, Google Meet, Microsoft Teams, etc.), extracts audio, transcribes the content, and generates formatted Markdown notes that can be directly used in Obsidian knowledge bases.

### Core System Components

The system is structured using a modular architecture that consists of:

1. **File Monitoring Subsystem**: Watches directories for new video files
2. **File Management System**: Provides robust file operations with error handling
3. **Audio Extraction Subsystem**: Extracts audio from video files
4. **Processing Queue System**: Manages the workflow of file processing
5. **Note Generation**: Creates structured Markdown notes from transcriptions
6. **Obsidian Integration**: Provides templates and utilities for Obsidian compatibility

### Project Directory Structure

```
meet2obsidian/
  ├── docs/                 # Documentation directory
  ├── meet2obsidian/        # Main Python package
  │   ├── __init__.py
  │   ├── api/              # API integrations (e.g., transcription services)
  │   │   ├── __init__.py
  │   │   ├── claude.py     # Claude AI integration
  │   │   └── revai.py      # Rev.ai transcription service
  │   ├── audio/            # Audio processing
  │   │   ├── __init__.py
  │   │   └── extractor.py  # Audio extraction from videos
  │   ├── note/             # Note generation
  │   │   ├── __init__.py
  │   │   ├── generator.py  # Markdown note creation
  │   │   └── obsidian.py   # Obsidian-specific formatting
  │   ├── processing/       # Processing system
  │   │   ├── __init__.py
  │   │   ├── audio_processor.py  # Audio extraction processor
  │   │   └── processor.py        # Base processor interface
  │   ├── utils/            # Utility modules
  │   │   ├── __init__.py
  │   │   ├── file_manager.py # File management utilities
  │   │   ├── logging.py    # Logging utilities
  │   │   ├── security.py   # Security utilities
  │   │   └── status.py     # Status reporting
  │   ├── cli.py            # Command-line interface
  │   ├── config.py         # Configuration management
  │   ├── core.py           # Core application logic
  │   ├── cache.py          # Caching utilities
  │   └── monitor.py        # File monitoring system
  ├── scripts/              # Utility scripts
  │   ├── check_videos.py   # Video validation script
  │   ├── install.sh        # Installation script
  │   ├── setup_api_keys.py # API key setup script
  │   └── setup_launchagent.sh # macOS service setup
  ├── tests/                # Test suite
  │   ├── __init__.py
  │   ├── data/             # Test data
  │   ├── integration/      # Integration tests
  │   │   ├── test_audio_extraction_integration.py  # Audio extraction integration tests
  │   │   └── test_file_manager_integration.py      # File manager integration tests
  │   └── unit/             # Unit tests
  │       ├── test_audio_extractor.py  # Tests for audio extraction
  │       ├── test_file_manager.py     # Tests for file management
  │       ├── test_synthetic_videos.py # Tests with synthetic video files
  │       └── [other test files]
  ├── LICENSE
  ├── README.md
  ├── pyproject.toml       # Python project configuration
  ├── requirements.txt     # Dependencies
  └── setup.py             # Package installation
```

## File Management System

The file management component provides robust and reliable file operations with comprehensive error handling. It ensures that all file operations across the application are performed safely, with proper error recovery and logging.

### File Management Process

The FileManager utility handles all critical file operations:

1. **Safe Deletion**: Removes files with proper error handling
2. **Secure Deletion**: Multi-pass overwriting for sensitive files
3. **Directory Operations**: Creates, moves, and deletes directories
4. **File Movement**: Safely relocates files with fallbacks
5. **Permission Management**: Checks and sets file permissions
6. **Error Recovery**: Handles common file system errors

### Key Component

#### FileManager (`meet2obsidian/utils/file_manager.py`)

The `FileManager` class provides core file management functionality:

- **Safe File Operations**: All operations include comprehensive error handling
- **Status Reporting**: Operations return success/error status with detailed messages
- **Permission Management**: Granular control of file access permissions
- **Recovery Mechanisms**: Automatic retries for temporary errors
- **Cross-Device Support**: Special handling for operations across filesystems

```python
# Key methods of the FileManager class:
- delete_file(file_path)                # Safely delete a file
- secure_delete_file(file_path, passes) # Securely delete with overwriting
- move_file(source, target, ...)        # Move file with error handling
- copy_file(source, target, ...)        # Copy file with metadata preservation
- check_permission(path, perm_type)     # Check file permissions
- set_permissions(path, read, write)    # Modify file permissions
```

### Technical Implementation Details

#### Error Handling Strategy

The system implements a multi-layered error handling approach:

- **Operation Status**: All methods return success/error status
- **Detailed Messages**: Error messages provide context for debugging
- **Error Tracking**: Last error and error code are stored for later retrieval
- **Logging**: Errors are logged with detailed information
- **Recovery**: Automatic retry for transient errors (with configurable attempts)

#### Security Features

Special attention is given to file security:

- **Secure Deletion**: Multi-pass overwriting with zero, ones, and random data
- **Permission Enforcement**: Strict checking of access rights
- **Path Validation**: Verification of path safety before operations

#### Platform Compatibility

The implementation handles platform-specific differences:

- **Cross-Platform Testing**: Tests accommodate different OS behaviors
- **Permission Mapping**: Platform-appropriate permission handling
- **Error Code Translation**: Standardized error reporting across platforms

## Audio Extraction System

The audio extraction component is a critical part of the processing pipeline that converts video conference recordings into audio files suitable for transcription.

### Audio Extraction Process

1. The **FileMonitor** component detects new video files in monitored directories
2. Files are validated to ensure they are proper video files
3. Valid files are added to the **ProcessingQueue**
4. The **AudioExtractionProcessor** extracts audio tracks using the **AudioExtractor**
5. Extracted audio files are stored in a dedicated audio directory
6. The process updates metadata and passes the audio file to subsequent processors (e.g., transcription)

### Key Components

#### AudioExtractor (`meet2obsidian/audio/extractor.py`)

The `AudioExtractor` class provides core audio extraction functionality:

- **Validates video files** using FFmpeg/FFprobe
- **Extracts audio** in multiple formats (wav, mp3, m4a)
- **Supports quality profiles** (voice, low, medium, high)
- **Retrieves metadata** from video files
- **Handles edge cases** such as videos without audio tracks
- **Implements caching** for improved performance
- **Provides robust error handling**

```python
# Key methods of the AudioExtractor class:
- check_video_file(video_path)          # Validates video file
- extract_audio(video_path, output_path) # Extracts audio from video
- get_video_info(video_path)            # Gets video metadata
- extract_audio_with_profile(video_path) # Uses preset quality profiles
- quick_check_video(video_path)         # Fast validation for monitoring
```

#### AudioExtractionProcessor (`meet2obsidian/processing/audio_processor.py`)

The `AudioExtractionProcessor` class integrates with the queue system:

- Implements the **FileProcessor** interface
- **Organizes output files** in the audio directory
- **Updates file metadata** for downstream processors
- **Manages error handling** and logging
- Provides **validation functions** for the file monitor

```python
# Key methods of the AudioExtractionProcessor:
- process_file(file_path, metadata)     # Process a video file
- quick_validate(file_path)             # Fast validation for monitoring
```

#### Application Manager Integration (`meet2obsidian/core.py`)

The ApplicationManager class initializes and integrates the audio extraction system:

- Creates the **audio directory** for storing extracted files
- Initializes the **AudioExtractionProcessor**
- Registers the processor with the **ProcessingQueue**
- Sets up **validation functions** for the FileMonitor
- Handles **error reporting** and status tracking

### Technical Implementation Details

#### Audio Formats and Quality Profiles

The system supports multiple audio formats using FFmpeg codec mapping:

- **wav**: High-quality PCM audio (default for testing)
- **mp3**: Compressed audio using libmp3lame codec
- **m4a**: AAC audio in MPEG-4 container (uses 'ipod' format specifier)
- **ogg**: Vorbis audio in Ogg container

Quality profiles simplify common use cases:

- **voice**: Optimized for speech (mono, 64k bitrate, 22050Hz)
- **low**: Low quality (stereo, 128k bitrate, 44100Hz)
- **medium**: Medium quality (stereo, 192k bitrate, 44100Hz)
- **high**: High quality (stereo, 256k bitrate, 48000Hz)

#### Handling Videos Without Audio

The system can process videos that don't contain audio tracks by:

1. Detecting the absence of audio streams
2. Generating silent audio matching the video duration
3. Creating an appropriately formatted audio file for downstream processing

#### Error Handling and Recovery

The audio extraction system implements robust error handling:

- **Validation errors**: Reports issues with invalid video files
- **Processing errors**: Catches and reports FFmpeg execution errors
- **Output verification**: Ensures output files exist and contain data
- **Metadata handling**: Falls back gracefully if metadata extraction fails
- **Cleanup**: Removes partial files in case of errors

#### Performance Optimization

Several optimizations are implemented:

- **Metadata caching**: Avoids repeated FFprobe calls for the same file
- **Quick validation**: Fast initial video validation for monitoring
- **Format detection**: Proper format/codec mapping for different outputs
- **Parallel processing**: Integration with the queue system for parallel execution

## Integration with Other Components

The audio extraction system integrates with several other components:

### File Monitoring System

- The `FileMonitor` uses the `quick_validate` method from `AudioExtractionProcessor` to quickly filter valid video files
- The monitor calls the `_handle_new_file` method in `ApplicationManager` which adds files to the processing queue

### Processing Queue System

- The `AudioExtractionProcessor` implements the `FileProcessor` interface
- It processes files from the queue and updates metadata
- The processing queue manages concurrency, persistence, and error handling

### Configuration System

- Audio extraction settings can be configured through the configuration system
- Audio directory paths, format preferences, and quality settings are customizable
- Configuration changes take effect without requiring application restart

### Note Generation System

- The audio extraction provides audio files and metadata for transcription
- Duration information helps with timing and synchronization in notes
- File paths and metadata are propagated to the note generation system

## Testing

### Audio Extraction Testing

The audio extraction system has comprehensive test coverage:

- **Unit Tests**: Test individual methods and functionality
  - `test_audio_extractor.py`: Tests core extraction functions
  - `test_synthetic_videos.py`: Tests with programmatically generated videos

- **Integration Tests**: Test system-level interactions
  - `test_audio_extraction_integration.py`: Tests with real video processing

- **Test Types**:
  - Validation tests for video file checking
  - Extraction tests for different formats and parameters
  - Error handling tests for corrupt or invalid files
  - Metadata tests for information extraction

### File Management Testing

The file management system has extensive test coverage:

- **Unit Tests**: Test individual file operations and error scenarios
  - `test_file_manager.py`: Tests all file operations and error handling

- **Integration Tests**: Test end-to-end workflows
  - `test_file_manager_integration.py`: Tests complete workflows with the real file system

- **Test Types**:
  - File operation tests (delete, move, copy)
  - Permission management tests
  - Error handling tests for various scenarios
  - Recovery tests for transient errors

## Dependencies

### Audio Extraction Dependencies

The audio extraction system relies on external dependencies:

- **FFmpeg**: For video processing and audio extraction
- **FFprobe**: For media file analysis and metadata extraction

### File Management Dependencies

The file management system primarily uses Python standard library modules:

- **os**: For basic file operations
- **shutil**: For high-level file operations
- **stat**: For permission handling
- **errno**: For error code standardization

## Future Enhancements

### Audio Extraction Enhancements

Potential enhancements for the audio extraction system:

1. **Enhanced format support**: Additional output formats (FLAC, Opus)
2. **Advanced audio processing**: Noise reduction, normalization
3. **Multi-track support**: Handling videos with multiple audio tracks
4. **Cloud processing**: Offloading processing to cloud services
5. **Progress reporting**: Real-time progress updates during extraction

### File Management Enhancements

Potential enhancements for the file management system:

1. **File ownership management**: Change file ownership and group
2. **Extended attribute support**: Read/write extended file attributes
3. **Checksumming**: File integrity verification
4. **File locking**: Explicit file locking for concurrent access
5. **Asynchronous operations**: Non-blocking file operations
