# CacheManager 

## Overview

The `CacheManager` class provides a robust and thread-safe caching mechanism for the `meet2obsidian` application. It allows for efficient caching of various data types including strings, dictionaries, binary data, and custom objects.

## Features

- Store and retrieve any serializable data
- Thread-safe operations with locking mechanism
- Automatic directory creation
- Cache invalidation (by key, by type, or all)
- Age-based cache validation
- Automated cleanup of outdated cache entries
- Size tracking for monitoring cache usage

## Usage Examples

### Basic Usage

```python
from meet2obsidian.cache import CacheManager

# Initialize a cache manager with default retention of 30 days
cache_manager = CacheManager(cache_dir="/path/to/cache", retention_days=30)

# Store data in cache
cache_manager.store("transcriptions", "video_123", "Transcription text content...")

# Retrieve data from cache
transcription = cache_manager.get("transcriptions", "video_123")

# Check if valid cache exists (with age verification)
if cache_manager.has_valid_cache("transcriptions", "video_123", max_age_days=7):
    # Use cached data
    pass
else:
    # Generate new data
    pass
```

### Integrating with API Clients

```python
class RevAiClient:
    def __init__(self, api_key, cache_manager=None):
        self.api_key = api_key
        self._cache_manager = cache_manager or CacheManager("~/.cache/meet2obsidian")
        
    def get_transcript_for_file(self, file_path):
        cache_type = "transcriptions"
        cache_key = f"transcript_{file_path}"
        
        # Check if result is in cache
        cached_result = self._cache_manager.get(cache_type, cache_key)
        if cached_result:
            return cached_result
        
        # If not in cache, call the API
        transcript = self._call_rev_ai_api(file_path)
        
        # Store in cache
        self._cache_manager.store(cache_type, cache_key, transcript)
        return transcript
```

### Cache Maintenance

```python
# Invalidate specific cache item
cache_manager.invalidate("transcriptions", "video_123")

# Invalidate all items of a type
cache_manager.invalidate("analyses")

# Clean up outdated items (older than retention_days)
cache_manager.cleanup()

# Clean up with custom retention
cache_manager.cleanup_with_retention(retention_days=1)

# Get cache size statistics
sizes = cache_manager.get_cache_size()
print(f"Total cache size: {sizes['total']} bytes")
```

## API Reference

### Constructor

- `__init__(cache_dir: str, retention_days: int = 30, logger=None)`: 
  Initialize the cache manager with a cache directory, retention period, and optional logger.

### Main Methods

- `get(cache_type: str, key: str) -> Optional[Any]`: 
  Retrieve an object from cache by type and key.

- `store(cache_type: str, key: str, data: Any) -> bool`: 
  Store an object in cache.

- `has_valid_cache(cache_type: str, key: str, max_age_days: Optional[int] = None) -> bool`: 
  Check if valid cache exists, optionally verifying age.

- `invalidate(cache_type: str, key: Optional[str] = None) -> int`: 
  Invalidate cache entry by key, or all entries of a type if key is None.

- `cleanup() -> int`: 
  Clean up outdated cache data older than the configured retention period.

- `invalidate_all() -> int`: 
  Invalidate all cache entries.

- `cleanup_type(cache_type: str) -> int`: 
  Clean up outdated data of a specific cache type.

- `cleanup_with_retention(retention_days: int) -> int`: 
  Clean up with a custom retention period.

- `get_cache_size() -> Dict[str, int]`: 
  Get total cache size and sizes by type.

## Thread Safety

All operations in CacheManager are thread-safe, using a reentrant lock to protect access to the cache. This allows for concurrent cache operations from multiple threads.

## Error Handling

The CacheManager contains robust error handling for various scenarios:

- Permission errors when creating directories or files
- Serialization/deserialization errors
- File system access errors
- Concurrent access issues

All errors are logged and operations gracefully fail without raising exceptions to the caller.

## Implementation Notes

- Uses Python's pickle module for serialization
- MD5 hashing is used to create safe filenames from cache keys
- Empty directories are automatically created as needed
- Cache is organized by type in separate subdirectories