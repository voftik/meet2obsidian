# Video Validation Tool

## Overview

The `check_videos.py` script is a utility for validating video files before they are processed by the meet2obsidian application. It checks for common issues such as corrupt files, invalid durations, and unreadable formats, helping to identify problems early in the workflow.

## Features

- **Video File Scanning**: Recursively scans directories for video files
- **Corruption Detection**: Checks if video files are corrupted or unreadable
- **Duration Validation**: Ensures videos have valid duration information
- **Format Inspection**: Provides detailed information about video formats
- **Error Reporting**: Clear reporting of issues found in video files
- **Customizable Extensions**: Support for various video file extensions
- **Verbose Output**: Optional detailed information about each video file

## Architecture

The script uses FFmpeg's ffprobe and ffmpeg commands to analyze video files. It integrates with the meet2obsidian application through similar validation methods used in the `AudioExtractor` class.

```
┌────────────────────┐      ┌─────────────────────────┐
│                    │      │                         │
│  check_videos.py   │─────►│     FFmpeg/FFprobe      │
│                    │      │                         │
└────────────────────┘      └─────────────────────────┘
         │                             │
         │                             │
         ▼                             ▼
┌────────────────────┐      ┌─────────────────────────┐
│                    │      │                         │
│  Validation Logic  │      │      Video Files        │
│                    │      │                         │
└────────────────────┘      └─────────────────────────┘
```

## Usage

### Installation Requirements

The script requires FFmpeg to be installed on the system. On macOS, this can be installed via Homebrew:

```bash
brew install ffmpeg
```

### Command-Line Interface

```bash
# View help
./scripts/check_videos.py --help

# Check a single directory
./scripts/check_videos.py /path/to/videos

# Check multiple directories
./scripts/check_videos.py /path/to/videos1 /path/to/videos2

# Check recursively (includes subdirectories)
./scripts/check_videos.py --recursive /path/to/videos

# Show detailed information about each video
./scripts/check_videos.py --verbose /path/to/videos

# Check specific video extensions
./scripts/check_videos.py --extensions .mp4 .mov .avi /path/to/videos
```

## Validation Checks

The script performs the following validation checks:

1. **File Existence**: Verifies that the file exists
2. **Read Permissions**: Checks if the file is readable
3. **File Size**: Ensures the file is not empty (0 bytes)
4. **Duration Check**: Uses FFprobe to extract and validate the duration
5. **Frame Reading**: Attempts to read video frames to check for corruption
6. **Format Information**: Extracts detailed metadata about the video format

## Integration with meet2obsidian

The video validation functionality in `check_videos.py` mirrors the validation logic used in the `AudioExtractor` class in the meet2obsidian application. This ensures consistent handling of video files across the application.

Key integration points:

1. **Shared Validation Logic**: Uses similar FFprobe commands as the `AudioExtractor.check_video_file` method
2. **Consistent Error Handling**: Error messages match those used in the main application
3. **File Processing**: Adheres to the same file format support as the main application

## Error Reporting

The script provides detailed error messages for different types of issues:

- **File Not Found**: "File does not exist: [path]"
- **Permission Error**: "File is not readable: [path]"
- **Empty File**: "File is empty (0 bytes): [path]"
- **No Duration**: "Unable to determine duration: [path]"
- **Invalid Duration**: "Invalid duration (0s): [path]"
- **Corruption**: "Corrupted video file (frame read error): [path]"
- **FFprobe Error**: "Error analyzing video: [path]"

## Implementation Details

### Video Detection

The script recognizes the following video formats by default:
- `.mp4`: MPEG-4 video files
- `.webm`: WebM video files
- `.mov`: QuickTime video files
- `.mkv`: Matroska video files
- `.avi`: AVI video files

### FFprobe Commands

The script uses the following FFprobe commands for video analysis:

```bash
# For duration check
ffprobe -v error -show_entries format=duration -of json [video_path]

# For detailed video information
ffprobe -v quiet -print_format json -show_format -show_streams [video_path]
```

### FFmpeg Commands

For corruption checking, the script attempts to read frames using FFmpeg:

```bash
# For corruption check
ffmpeg -v error -i [video_path] -t 1 -f null -
```

## Example Output

```
Scanning /path/to/videos...
Found 3 video files.
Checking: meeting1.mp4... OK
  Duration: 00:45:12, Size: 256.5 MB, Resolution: 1920x1080, Format: mp4, Audio: aac (2 channels)
Checking: meeting2.mp4... FAILED
  Corrupted video file (frame read error): /path/to/videos/meeting2.mp4
  Error: Invalid data found when processing input
Checking: interview.mov... OK
  Duration: 01:15:34, Size: 512.3 MB, Resolution: 1280x720, Format: mov, Audio: aac (2 channels)

==================================================
SUMMARY: 3 files checked, 2 valid, 1 with issues

Issues found:
- /path/to/videos/meeting2.mp4
  Corrupted video file (frame read error): /path/to/videos/meeting2.mp4
  Error: Invalid data found when processing input

1 files have issues and may not be processed correctly by meet2obsidian.
```

## Troubleshooting

### Common Issues

1. **FFmpeg Not Found**: Ensure FFmpeg is installed and in the system PATH
2. **Permission Denied**: Check file permissions for the video files
3. **Network Drive Issues**: Validate that network-mounted drives are properly accessible
4. **Large Files**: Very large video files may take longer to analyze

### Solutions

- Install FFmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Ubuntu)
- Fix permissions: `chmod +r /path/to/video.mp4`
- For slow analysis: Use the non-recursive mode and process directories in batches

## Future Improvements

- Add support for parallel processing of multiple files
- Add JSON output format for scripting integration
- Add repair options for fixable video issues
- Add integration with meet2obsidian's CLI commands
- Add threshold configuration for duration and file size checks