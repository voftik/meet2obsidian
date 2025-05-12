# Video Troubleshooting

If you're experiencing issues with processing video files in meet2obsidian, this guide will help you diagnose and resolve common problems.

## Common Video Issues

- **Corrupt video files** - Video files may become corrupted during recording or transfer
- **Incompatible formats** - Some video codecs may not be properly supported
- **Missing audio tracks** - Videos without audio cannot be transcribed
- **Invalid duration** - Some recording software may produce files with incorrect duration metadata
- **Very large files** - Extremely large files may timeout during processing

## Using the Video Validation Tool

Meet2obsidian includes a dedicated tool for checking video files before attempting to process them. This can save time and help identify issues early.

### Running the Video Checker

1. Open a terminal
2. Navigate to your meet2obsidian installation directory
3. Run the check_videos.py script:

```bash
# Basic usage - check all videos in a directory
./scripts/check_videos.py /path/to/your/videos

# Check multiple directories
./scripts/check_videos.py /path/to/dir1 /path/to/dir2

# Include subdirectories (recursive)
./scripts/check_videos.py --recursive /path/to/your/videos

# Show detailed video information
./scripts/check_videos.py --verbose /path/to/your/videos

# Specify certain file extensions to check
./scripts/check_videos.py --extensions .mp4 .mov /path/to/your/videos
```

### Understanding the Results

The tool will check each video file and report any issues found:

```
Scanning /Documents/meet_records...
Found 3 video files.
Checking: meeting1.mp4... OK
Checking: meeting2.mp4... FAILED
  Corrupted video file (frame read error): /Documents/meet_records/meeting2.mp4
  Error: Invalid data found when processing input
Checking: interview.mov... OK

==================================================
SUMMARY: 3 files checked, 2 valid, 1 with issues

Issues found:
- /Documents/meet_records/meeting2.mp4
  Corrupted video file (frame read error): /Documents/meet_records/meeting2.mp4
  Error: Invalid data found when processing input
```

## Fixing Common Issues

### Corrupt Video Files

If the tool reports that a video file is corrupted:

1. **Try re-exporting** the video from your recording software
2. **Use video repair tools** like VLC or FFmpeg to attempt recovery
3. **Convert the file** to another format using a tool like HandBrake

### Missing Audio Track

If your video files don't have an audio track:

1. Make sure your recording software is configured to record audio
2. Check that your microphone was working during the recording
3. Ensure the correct audio input device was selected

### Format Issues

If you have format compatibility issues:

1. Convert your videos to standard MP4 format using H.264/AAC encoding
2. Use HandBrake or FFmpeg for conversion:

```bash
# Example FFmpeg command to convert a video to compatible format
ffmpeg -i input_video.webm -c:v libx264 -c:a aac output_video.mp4
```

### File Size Issues

For very large files:

1. Split long recordings into smaller segments
2. Compress videos to reduce file size:

```bash
# Example FFmpeg command to compress a video
ffmpeg -i input_video.mp4 -vcodec libx264 -crf 24 compressed_video.mp4
```

## Preventative Measures

To avoid video issues in the future:

1. **Test your recording setup** with short recordings first
2. **Use standard formats** like MP4 with H.264 video and AAC audio
3. **Keep recordings under 2 hours** when possible
4. **Run the video checker** on important recordings before processing
5. **Regularly clean up** your video directory

## When to Contact Support

If you continue to experience issues after trying these solutions:

1. Run the video checker with the `--verbose` flag
2. Save the complete output
3. Contact support with:
   - The checker's output
   - Details about your recording software
   - The specific commands you've tried for fixing the issue