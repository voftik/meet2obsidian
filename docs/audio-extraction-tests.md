# Audio Extraction Testing Guide

This document provides guidance on testing the audio extraction component of Meet2Obsidian.

## Prerequisites

Before running tests, ensure you have:

1. FFmpeg installed and available in your PATH
2. Python environment set up with required dependencies
3. Sufficient disk space for temporary test files

## Running Audio Extraction Tests

### Running Unit Tests

The audio extraction component has two main sets of unit tests:

```bash
# Run standard mock-based tests
python -m pytest tests/unit/test_audio_extractor.py -v

# Run tests with synthetic video generation (requires FFmpeg)
python -m pytest tests/unit/test_synthetic_videos.py -v
```

### Running Integration Tests

These tests check integration with the real system:

```bash
# Run with real videos (skipped by default)
python -m pytest tests/integration/test_audio_extraction_integration.py -v
```

## Testing with Real Video Files

To test with your own video files:

```bash
# Create a test directory
mkdir -p /tmp/meet2obsidian_test_videos

# Copy some test videos
cp path/to/your/videos/*.mp4 /tmp/meet2obsidian_test_videos/

# Process a test file manually
python -c "from meet2obsidian.audio.extractor import AudioExtractor; extractor = AudioExtractor(); result, path = extractor.extract_audio('/tmp/meet2obsidian_test_videos/your_video.mp4', '/tmp/output.wav'); print(f'Success: {result}, Output: {path}')"
```

## Format Testing

Test different output formats:

```python
from meet2obsidian.audio.extractor import AudioExtractor

extractor = AudioExtractor()

# Test different formats
formats = ['wav', 'mp3', 'm4a', 'ogg']
video_path = '/path/to/test/video.mp4'

for fmt in formats:
    output_path = f'/tmp/output.{fmt}'
    result, path = extractor.extract_audio(video_path, output_path, format=fmt)
    print(f'Format {fmt}: Success={result}, Path={path}')
```

## Quality Profile Testing

Test different quality profiles:

```python
from meet2obsidian.audio.extractor import AudioExtractor

extractor = AudioExtractor()

# Test different quality profiles
profiles = ['voice', 'low', 'medium', 'high']
video_path = '/path/to/test/video.mp4'

for profile in profiles:
    output_path = f'/tmp/output_{profile}.m4a'
    result, path = extractor.extract_audio_with_profile(video_path, output_path, profile=profile)
    print(f'Profile {profile}: Success={result}, Path={path}')
```

## Test Scenarios

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Valid video with audio | Test normal extraction | Audio file created successfully |
| Valid video without audio | Test handling of videos with no audio tracks | Silent audio file created |
| Corrupt video | Test handling of corrupt videos | Error reported, no file created |
| Interrupted processing | Stop FFmpeg during extraction | Partial file cleaned up |
| Very large video | Test with a large video file | Audio extracted correctly |
| Multiple formats | Test all supported formats | All formats extracted correctly |
| All quality profiles | Test all quality profiles | All profiles applied correctly |

## Common Issues and Troubleshooting

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| FFmpeg not found | FFmpeg not installed or not in PATH | Install FFmpeg or update PATH |
| Format not supported | Incorrect format mapping | Check format_mapping in extractor.py |
| Extraction fails with error | Codec not available | Install additional FFmpeg codecs |
| Test skipped | FFmpeg not detected in test path | Update test path in test_synthetic_videos.py |
| Empty output file | Video has no audio tracks | Check video with ffprobe -show_streams |

## Performance and Resources

Monitor resource usage during testing:

```bash
# Monitor CPU, memory, and disk usage during extraction
python -m pytest tests/unit/test_synthetic_videos.py::TestSyntheticVideos::test_extract_audio_from_synthetic_video -v & top -pid $!
```