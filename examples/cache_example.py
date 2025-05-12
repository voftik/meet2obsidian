#!/usr/bin/env python3
"""
Example demonstrating the meet2obsidian caching system.

This script shows how to use the CacheManager and how it integrates
with the Rev.ai and Claude API clients.
"""

import os
import time
import tempfile
from pathlib import Path

from meet2obsidian.cache import CacheManager
from meet2obsidian.api.revai import RevAiClient
from meet2obsidian.api.claude import ClaudeClient
from meet2obsidian.utils.logging import setup_logging, get_logger


def main():
    """Run the caching demonstration."""
    # Set up logging
    setup_logging(log_level="INFO")
    logger = get_logger("cache_example")
    
    # Create a temporary directory for the example cache
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary cache directory: {temp_dir}")
        
        # Example 1: Basic CacheManager usage
        example_basic_cache(temp_dir, logger)
        
        # Example 2: RevAi client with caching
        example_revai_caching(temp_dir, logger)
        
        # Example 3: Claude client with caching
        example_claude_caching(temp_dir, logger)
        
        # Example 4: Cache invalidation and cleanup
        example_cache_maintenance(temp_dir, logger)


def example_basic_cache(cache_dir, logger):
    """Demonstrate basic CacheManager usage."""
    logger.info("\n\n--- Example 1: Basic CacheManager Usage ---")
    
    # Create the cache manager
    cache_manager = CacheManager(os.path.join(cache_dir, "basic"), logger=logger)
    
    # Store different types of data
    logger.info("Storing data in cache...")
    cache_manager.store("strings", "key1", "This is a simple string")
    cache_manager.store("dicts", "key2", {"name": "Example", "value": 42})
    cache_manager.store("binary", "key3", b'\x00\x01\x02\x03\x04\x05')
    
    # Retrieve data
    logger.info("Retrieving data from cache...")
    string_data = cache_manager.get("strings", "key1")
    dict_data = cache_manager.get("dicts", "key2")
    binary_data = cache_manager.get("binary", "key3")
    
    # Display results
    logger.info(f"Retrieved string: {string_data}")
    logger.info(f"Retrieved dict: {dict_data}")
    logger.info(f"Retrieved binary: {binary_data!r}")
    
    # Check for non-existent data
    missing_data = cache_manager.get("strings", "nonexistent")
    logger.info(f"Missing data result: {missing_data}")
    
    # Get cache size
    size_info = cache_manager.get_cache_size()
    logger.info(f"Cache size: {size_info}")


def example_revai_caching(cache_dir, logger):
    """Demonstrate RevAi client with caching."""
    logger.info("\n\n--- Example 2: Rev.ai Client with Caching ---")
    
    # Create the cache manager for Rev.ai
    cache_manager = CacheManager(os.path.join(cache_dir, "revai"), logger=logger)
    
    # Create the Rev.ai client
    revai_client = RevAiClient("fake_api_key", cache_manager=cache_manager, logger=logger)
    
    # Create a simulated audio file path
    audio_path = os.path.join(temp_dir, "simulated_audio.mp3")
    
    # First call - should use API
    logger.info("First call - should use API:")
    transcript1, from_cache1 = revai_client.get_transcript_for_file(audio_path)
    logger.info(f"Transcript: {transcript1}")
    logger.info(f"From cache: {from_cache1}")
    
    # Second call - should use cache
    logger.info("\nSecond call - should use cache:")
    transcript2, from_cache2 = revai_client.get_transcript_for_file(audio_path)
    logger.info(f"Transcript: {transcript2}")
    logger.info(f"From cache: {from_cache2}")
    
    # Call with a different file - should use API again
    logger.info("\nCall with different file - should use API:")
    different_path = os.path.join(temp_dir, "different_audio.mp3")
    transcript3, from_cache3 = revai_client.get_transcript_for_file(different_path)
    logger.info(f"Transcript: {transcript3}")
    logger.info(f"From cache: {from_cache3}")


def example_claude_caching(cache_dir, logger):
    """Demonstrate Claude client with caching."""
    logger.info("\n\n--- Example 3: Claude Client with Caching ---")
    
    # Create the cache manager for Claude
    cache_manager = CacheManager(os.path.join(cache_dir, "claude"), logger=logger)
    
    # Create the Claude client
    claude_client = ClaudeClient("fake_api_key", cache_manager=cache_manager, logger=logger)
    
    # Test text for analysis
    test_text = "This is a test sentence to analyze with Claude API. It contains some information about caching and API usage."
    
    # First call - should use API
    logger.info("First call - should use API:")
    summary1, from_cache1 = claude_client.summarize_transcript(test_text)
    logger.info(f"Summary: {summary1}")
    logger.info(f"From cache: {from_cache1}")
    
    # Second call - should use cache
    logger.info("\nSecond call - should use cache:")
    summary2, from_cache2 = claude_client.summarize_transcript(test_text)
    logger.info(f"Summary: {summary2}")
    logger.info(f"From cache: {from_cache2}")
    
    # Different analysis type - should use API again
    logger.info("\nDifferent analysis type - should use API:")
    keywords, from_cache3 = claude_client.analyze_text(test_text, "keywords")
    logger.info(f"Keywords: {keywords}")
    logger.info(f"From cache: {from_cache3}")
    
    # Force refresh (bypass cache)
    logger.info("\nForce refresh (bypass cache):")
    summary3, from_cache4 = claude_client.summarize_transcript(test_text, use_cache=False)
    logger.info(f"Summary: {summary3}")
    logger.info(f"From cache: {from_cache4}")


def example_cache_maintenance(cache_dir, logger):
    """Demonstrate cache invalidation and cleanup."""
    logger.info("\n\n--- Example 4: Cache Maintenance ---")
    
    # Create the cache manager
    cache_manager = CacheManager(os.path.join(cache_dir, "maintenance"), 
                               retention_days=7, logger=logger)
    
    # Store some data
    logger.info("Storing data in cache...")
    for i in range(10):
        cache_manager.store("test_type", f"key_{i}", f"Value {i}")
    
    # Create a file with an old timestamp
    old_cache_type = "old_data"
    cache_manager.store(old_cache_type, "old_key", "This is old data")
    cache_path = os.path.join(cache_manager.cache_dir, old_cache_type)
    for file_name in os.listdir(cache_path):
        file_path = os.path.join(cache_path, file_name)
        # Set modification time to 10 days ago
        mod_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(file_path, (mod_time, mod_time))
    
    # Check size before cleanup
    size_before = cache_manager.get_cache_size()
    logger.info(f"Cache size before cleanup: {size_before}")
    
    # Clean up outdated files
    removed = cache_manager.cleanup()
    logger.info(f"Cleaned up {removed} outdated files")
    
    # Check size after cleanup
    size_after = cache_manager.get_cache_size()
    logger.info(f"Cache size after cleanup: {size_after}")
    
    # Invalidate specific cache type
    removed = cache_manager.invalidate("test_type")
    logger.info(f"Invalidated 'test_type': removed {removed} files")
    
    # Check size after invalidation
    size_after_invalidation = cache_manager.get_cache_size()
    logger.info(f"Cache size after invalidation: {size_after_invalidation}")


if __name__ == "__main__":
    # Create a temp directory at module level for the examples
    temp_dir = tempfile.mkdtemp()
    try:
        main()
    finally:
        # Clean up the temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)