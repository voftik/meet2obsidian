# Cache System Component

## Overview

The Cache System provides a reliable and thread-safe mechanism to store and retrieve data, significantly improving performance by reducing redundant processing and API calls. It's particularly valuable for caching expensive operations like API requests, audio transcriptions, and file processing results.

## Key Features

- Thread-safe operations using reentrant locks
- Support for different data types (strings, dictionaries, binary data, objects)
- Age-based cache validation
- Multiple invalidation strategies (by key, by type, or entire cache)
- Automatic cleanup of outdated cache entries
- Size tracking for monitoring cache usage

## Component Structure

The Cache System is implemented as a single `CacheManager` class in the `meet2obsidian/cache.py` file with comprehensive unit and integration tests.

### Class Structure

```python
class CacheManager:
    def __init__(self, cache_dir: str, retention_days: int = 30, logger=None)
    def get(self, cache_type: str, key: str) -> Optional[Any]
    def store(self, cache_type: str, key: str, data: Any) -> bool
    def has_valid_cache(self, cache_type: str, key: str, max_age_days: Optional[int] = None) -> bool
    def invalidate(self, cache_type: str, key: Optional[str] = None) -> int
    def cleanup(self) -> int
    def invalidate_all(self) -> int
    def cleanup_type(self, cache_type: str) -> int
    def cleanup_with_retention(self, retention_days: int) -> int
    def get_cache_size(self) -> Dict[str, int]
```

## Implementation Details

### Cache Organization

The cache is organized hierarchically on disk:
- Base directory: `cache_dir` provided during initialization
- Subdirectories: Created per `cache_type` (e.g., "transcriptions", "analyses")
- Files: Each cached item is stored as a serialized file with MD5-hashed key as filename

```
/cache_dir/
├── transcriptions/
│   ├── 8d5e957f297893487bd98fa830fa6413  # MD5 hash of key
│   └── c4ca4238a0b923820dcc509a6f75849b  # MD5 hash of key
├── analyses/
│   └── d3d9446802a44259755d38e6d163e820  # MD5 hash of key
└── api_responses/
    └── 6512bd43d9caa6e02c990b0a82652dca  # MD5 hash of key
```

### Thread Safety

The `CacheManager` uses a reentrant lock (`threading.RLock`) to ensure thread safety for all operations, making it suitable for multi-threaded environments. Critical sections include:

- File reading/writing operations
- Cache invalidation and cleanup
- Size tracking operations

### Serialization

Data is serialized using Python's built-in `pickle` module, which allows storage of complex Python objects. Special handling has been implemented for custom objects defined in test functions.

### Error Handling

The cache system includes comprehensive error handling for:
- File system access issues (permission errors, missing directories)
- Serialization/deserialization errors
- Concurrent access conflicts
- Custom object serialization challenges

All errors are logged but do not raise exceptions to the caller, ensuring fault tolerance.

## Usage Patterns

### Basic Usage

```python
# Initialize cache manager
cache_manager = CacheManager(cache_dir="/path/to/cache", retention_days=30)

# Store data
cache_manager.store("transcriptions", "video_123", "Transcription text")

# Retrieve data with age verification
if cache_manager.has_valid_cache("transcriptions", "video_123", max_age_days=7):
    transcription = cache_manager.get("transcriptions", "video_123")
    # Use cached transcription
else:
    # Generate new transcription
    transcription = generate_transcription("video_123")
    cache_manager.store("transcriptions", "video_123", transcription)
```

### Integration with API Clients

```python
class RevAiClient:
    def __init__(self, api_key, cache_manager=None):
        self.api_key = api_key
        self._cache_manager = cache_manager or CacheManager("~/.cache/meet2obsidian")
        
    def get_transcript_for_file(self, file_path):
        cache_type = "transcriptions"
        cache_key = f"transcript_{file_path}"
        
        # Try to get from cache first
        cached_result = self._cache_manager.get(cache_type, cache_key)
        if cached_result:
            return cached_result
        
        # If not in cache, call API
        transcript = self._call_rev_ai_api(file_path)
        
        # Store result in cache
        self._cache_manager.store(cache_type, cache_key, transcript)
        return transcript
```

### Periodic Cleanup

```python
# In a maintenance task or scheduled job
def perform_cache_maintenance():
    cache_manager = CacheManager("/path/to/cache")
    
    # Get current cache size
    sizes = cache_manager.get_cache_size()
    logger.info(f"Cache size before cleanup: {sizes['total']} bytes")
    
    # Clean up old files
    removed_files = cache_manager.cleanup()
    logger.info(f"Removed {removed_files} outdated cache files")
    
    # Get updated size
    new_sizes = cache_manager.get_cache_size()
    logger.info(f"Cache size after cleanup: {new_sizes['total']} bytes")
```

## Testing

The cache system has comprehensive tests including:

### Unit Tests (`tests/unit/test_cache_manager.py`)
- `TestCacheStorage`: Tests for storing different types of data
- `TestCacheRetrieval`: Tests for retrieving cached data
- `TestCacheInvalidation`: Tests for invalidating cache entries
- `TestCacheCleanup`: Tests for cleaning up outdated cache entries

### Integration Tests (`tests/integration/test_cache_integration.py`)
- `TestCacheIntegrationWithAPI`: Tests for integration with API clients
- Tests for concurrent access simulation
- Tests for age-based invalidation across components

## Implementation Considerations

### Performance

The cache system is designed for optimal performance:
- Uses MD5 hashing for quick key lookup
- Implements efficient invalidation strategies
- Provides size tracking for monitoring cache growth

### Security

While the cache is not intended for sensitive data, it implements basic safeguards:
- No sensitive API keys or credentials should be stored in the cache
- File paths are sanitized to prevent path traversal
- Error messages don't expose internal system details

### Future Enhancements

Potential future improvements include:
- Memory-based caching layer for highest-frequency access items
- Compression options for large cached objects
- Encryption option for moderately sensitive data
- Cache statistics for monitoring hit/miss ratios

## Related Components

- **API Clients**: Primary consumers of cache for storing API responses
- **Audio Processing**: Uses cache for storing transcription results
- **Note Generator**: May use cache for intermediate processing results

## Best Practices

When using the cache system:

1. Use meaningful cache types to organize data (e.g., "transcriptions", "analyses")
2. Create unique and consistent keys for cache items
3. Implement age-based validation for time-sensitive data
4. Periodically clean up the cache in maintenance tasks
5. Monitor cache size to prevent disk space issues
6. Handle cache misses gracefully

## Configuration

The cache system is configurable through:
- `cache_dir`: Base directory for cache storage
- `retention_days`: Default retention period for cached items (30 days by default)
- Custom retention periods can be specified per operation

## Troubleshooting

Common issues and solutions:

1. **Cache misses when expected hit**: Check if invalidation occurred or if max_age_days is set too low
2. **Performance not improving**: Ensure the cache is actually being used and cache keys are consistent
3. **Disk space issues**: Implement more frequent cleanup or shorter retention periods
4. **Thread safety problems**: Ensure the same CacheManager instance is shared across threads

## References

- [Python pickle documentation](https://docs.python.org/3/library/pickle.html)
- [Python threading documentation](https://docs.python.org/3/library/threading.html)
- [Hash functions in Python](https://docs.python.org/3/library/hashlib.html)