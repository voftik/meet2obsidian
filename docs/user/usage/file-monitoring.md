# File Monitoring

Meet2Obsidian automatically monitors specified directories for new video files and processes them as they appear. This guide explains how the file monitoring system works and how to configure it.

## How File Monitoring Works

Meet2Obsidian uses an advanced event-based file monitoring system to detect when new video files are created in your monitored directories. It efficiently watches for file system events and automatically processes eligible files once they have finished copying.

## Key Features

- **Efficient Monitoring**: Uses system native file system events for immediate detection of new files
- **File Stability Detection**: Ensures files are completely copied before processing begins
- **Pattern Filtering**: Only processes files that match configured patterns (e.g., video files)
- **Persistence**: Remembers which files have been processed to avoid duplicates after restart
- **Low Resource Usage**: Minimal impact on CPU and disk I/O compared to traditional polling approaches

## Configuration Options

You can configure file monitoring through the `meet2obsidian` CLI:

### Setting the Video Directory

```bash
meet2obsidian config set video_directory "~/Videos/Meetings"
```

This sets the directory where Meet2Obsidian will look for new video files.

### Setting File Patterns

```bash
meet2obsidian config set video_patterns '["*.mp4", "*.mov", "*.webm"]'
```

This defines which file types Meet2Obsidian will process. By default, the following patterns are included:
- `*.mp4`
- `*.mov`
- `*.webm`
- `*.mkv`

### Setting Minimum File Age

```bash
meet2obsidian config set min_file_age 10
```

This sets how many seconds a file must be stable (not changing size) before processing begins. The default is 5 seconds.

## Checking Monitoring Status

You can check the status of the file monitoring service using the CLI:

```bash
meet2obsidian status
```

This will show you information including:
- Whether the monitoring service is running
- The directory being monitored
- File patterns being watched
- Number of files processed
- Any pending files

## Viewing Logs

To see detailed logs of file monitoring activity:

```bash
meet2obsidian logs
```

You can also filter logs to see just file monitoring related entries:

```bash
meet2obsidian logs --filter "file monitor"
```

## Stopping and Starting Monitoring

The file monitoring service starts automatically with the Meet2Obsidian service. You can control it with:

```bash
# Start the service
meet2obsidian service start

# Stop the service
meet2obsidian service stop
```

## Troubleshooting

### Files Not Being Detected

If your files aren't being detected, check:

1. **Correct Directory**: Verify the `video_directory` setting points to the correct location
2. **File Patterns**: Make sure your file types are included in the `video_patterns` setting
3. **Permissions**: Ensure Meet2Obsidian has read access to the directory
4. **Service Status**: Check that the service is running with `meet2obsidian status`

### Files Detected But Not Processed

If files are detected but not processed:

1. **File Stability**: Files might still be copying - increase `min_file_age` if necessary
2. **Previous Processing**: Check if the file was already processed (listed in status report)
3. **Check Logs**: Look for any errors in the logs with `meet2obsidian logs`

## Best Practices

For optimal performance:

1. **Use a Dedicated Directory**: Monitor a specific directory rather than a general-purpose one
2. **Limit File Types**: Only include the specific file types you need in `video_patterns`
3. **Sufficient Stability Time**: Set `min_file_age` high enough to ensure complete file copy
4. **Regular Status Checks**: Use `meet2obsidian status` to verify monitoring is working correctly