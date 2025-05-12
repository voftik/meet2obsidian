# Caching System

## Overview

Meet2Obsidian includes a powerful caching system that dramatically improves performance by saving the results of time-consuming operations like API calls, audio transcriptions, and file processing. This means faster response times and reduced API usage.

## How Caching Works

The caching system works behind the scenes to store the results of operations that:

- Take a long time to complete (like transcribing audio)
- Cost money (like API calls to Rev.ai or Claude)
- Use significant processing power

When Meet2Obsidian needs these results again, it first checks the cache to see if it already has a valid copy before performing the operation again.

## Benefits of Caching

- **Faster Processing**: Cached results are retrieved almost instantly
- **Reduced API Costs**: Fewer calls to paid services like Rev.ai and Claude
- **Offline Capability**: Access previously processed content even without internet
- **Lower CPU/Memory Usage**: Less repetitive processing work

## Cache Management

### Storage Location

The cache is stored in your local file system at:

```
~/.cache/meet2obsidian/
```

Or in a custom location if you've configured one in your settings.

### Cache Lifespan

By default, cached data is considered valid for 30 days. This means:

- Cached transcriptions will be reused for 30 days
- API responses are stored and reused for 30 days
- File processing results are kept for 30 days

You can adjust this retention period in the configuration settings if needed.

### Cache Size

The cache may grow over time, especially if you process many files. You can monitor and manage cache size using the CLI:

```bash
# View current cache size
meet2obsidian cache status

# Clean up outdated cache entries
meet2obsidian cache cleanup
```

## Configuration Options

You can customize caching behavior in your configuration file:

```json
{
  "cache": {
    "enabled": true,
    "directory": "~/.cache/meet2obsidian",
    "retention_days": 30,
    "max_size_mb": 1024
  }
}
```

| Option | Description | Default |
|--------|-------------|---------|
| `enabled` | Enable or disable caching | `true` |
| `directory` | Path to cache directory | `~/.cache/meet2obsidian` |
| `retention_days` | Days to keep cached data | `30` |
| `max_size_mb` | Maximum cache size in MB | `1024` (1GB) |

## Common Tasks

### Clearing the Cache

If you need to clear the cache (for example, after updating API settings), you can use the CLI:

```bash
# Clear the entire cache
meet2obsidian cache clear

# Clear a specific type of cache
meet2obsidian cache clear --type transcriptions

# Clear a specific item from the cache
meet2obsidian cache clear --type transcriptions --key video_123
```

### Force Refresh

To force a fresh processing of a file (ignoring cache):

```bash
meet2obsidian process file.mp4 --no-cache
```

## Troubleshooting

### Cache Not Working

If caching seems not to be working:

1. Verify caching is enabled in your configuration
2. Check if you're forcing cache bypass with `--no-cache` flag
3. Ensure you have sufficient disk space 
4. Verify cache directory permissions

### Incorrect or Outdated Results

If you're getting outdated or incorrect results:

1. Clear the specific cache item: `meet2obsidian cache clear --type transcriptions --key your_file`
2. Reduce retention period in configuration
3. Process the file with `--no-cache` flag

## Advanced Usage

For advanced users, the caching system can be monitored and managed with additional commands:

```bash
# View detailed cache information
meet2obsidian cache info --verbose

# Clean up cache with specific retention
meet2obsidian cache cleanup --days 7

# Export cache statistics
meet2obsidian cache stats --output stats.json
```

## Good Practices

- **Regular Cleanup**: Run `meet2obsidian cache cleanup` periodically to free disk space
- **Balance Retention**: Set retention days high enough for your workflow, but not unnecessarily high
- **Monitor Size**: Check cache size occasionally, especially if disk space is limited