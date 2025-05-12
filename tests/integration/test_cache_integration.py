import os
import pytest
import shutil
import tempfile
import time
from unittest.mock import patch, MagicMock

from meet2obsidian.cache import CacheManager


class TestCacheIntegrationWithAPI:
    """Test suite for cache integration with API clients."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a CacheManager instance for tests."""
        return CacheManager(cache_dir=temp_cache_dir, retention_days=30)
    
    def test_mock_revai_client_caching(self, cache_manager, monkeypatch):
        """Test caching with a mocked Rev.ai client."""
        # Create a mock RevAiClient
        class MockRevAiClient:
            def __init__(self, api_key, cache_manager):
                self.api_key = api_key
                self._cache_manager = cache_manager
                self._client = MagicMock()
                self.call_count = 0
            
            def get_transcript_for_file(self, file_path):
                cache_type = "transcriptions"
                cache_key = f"transcript_{file_path}"
                
                # Check if result is in cache
                cached_result = self._cache_manager.get(cache_type, cache_key)
                if cached_result:
                    return cached_result
                
                # If not in cache, call the API (mock implementation)
                self.call_count += 1
                transcript = f"This is a test transcript {self.call_count} for {file_path}"
                
                # Store in cache
                self._cache_manager.store(cache_type, cache_key, transcript)
                return transcript
        
        test_file_path = "/test/video/sample.mp4"
        
        # Create mock client
        client = MockRevAiClient(api_key="fake_api_key", cache_manager=cache_manager)
        
        # First call - should use the API
        transcript1 = client.get_transcript_for_file(test_file_path)
        assert "test transcript 1" in transcript1
        assert client.call_count == 1
        
        # Second call - should use the cache
        transcript2 = client.get_transcript_for_file(test_file_path)
        assert transcript2 == transcript1
        assert client.call_count == 1  # Count shouldn't increase
        
        # Different file - should use the API again
        different_file = "/test/video/different.mp4"
        transcript3 = client.get_transcript_for_file(different_file)
        assert "test transcript 2" in transcript3
        assert transcript3 != transcript1
        assert client.call_count == 2
    
    def test_mock_claude_client_caching(self, cache_manager, monkeypatch):
        """Test caching with a mocked Claude client."""
        # Create a mock ClaudeClient
        class MockClaudeClient:
            def __init__(self, api_key, cache_manager):
                self.api_key = api_key
                self._cache_manager = cache_manager
                self.call_count = 0
            
            def analyze_text(self, text, analysis_type):
                cache_type = "analyses"
                cache_key = f"{analysis_type}_{hash(text)}"
                
                # Check if result is in cache
                cached_result = self._cache_manager.get(cache_type, cache_key)
                if cached_result:
                    return cached_result
                
                # If not in cache, call the API (mock implementation)
                self.call_count += 1
                
                if analysis_type == "summary":
                    result = {
                        "summary": f"Summary {self.call_count} of the text",
                        "confidence": 0.95
                    }
                elif analysis_type == "keywords":
                    result = {
                        "keywords": ["key1", "key2", "key3"],
                        "analysis_id": f"analysis_{self.call_count}"
                    }
                else:
                    result = {"error": "Unknown analysis type"}
                
                # Store in cache
                self._cache_manager.store(cache_type, cache_key, result)
                return result
        
        test_text = "This is a test text to analyze"
        
        # Create mock client
        client = MockClaudeClient(api_key="fake_api_key", cache_manager=cache_manager)
        
        # First call - should use the API
        result1 = client.analyze_text(test_text, "summary")
        assert "Summary 1" in result1["summary"]
        assert client.call_count == 1
        
        # Second call with same parameters - should use the cache
        result2 = client.analyze_text(test_text, "summary")
        assert result2 == result1
        assert client.call_count == 1  # Count shouldn't increase
        
        # Different analysis type - should use the API again
        result3 = client.analyze_text(test_text, "keywords")
        assert "keywords" in result3
        assert result3 != result1
        assert client.call_count == 2
        
        # Different text - should use the API again
        different_text = "This is a different text to analyze"
        result4 = client.analyze_text(different_text, "summary")
        assert "Summary 3" in result4["summary"]
        assert result4 != result1
        assert client.call_count == 3
    
    def test_cache_cleanup_affects_clients(self, cache_manager):
        """Test the effect of cache cleanup on client functionality."""
        # Create mock clients
        class MockClient:
            def __init__(self, cache_manager, cache_type):
                self._cache_manager = cache_manager
                self.cache_type = cache_type
            
            def store_data(self, key, data):
                return self._cache_manager.store(self.cache_type, key, data)
            
            def get_data(self, key):
                return self._cache_manager.get(self.cache_type, key)
        
        # Create clients using different cache types
        client1 = MockClient(cache_manager, "type1")
        client2 = MockClient(cache_manager, "type2")
        
        # Store test data
        client1.store_data("key1", "Data for client 1")
        client2.store_data("key2", "Data for client 2")
        
        # Verify data was stored
        assert client1.get_data("key1") == "Data for client 1"
        assert client2.get_data("key2") == "Data for client 2"
        
        # Invalidate one cache type
        cache_manager.invalidate("type1")
        
        # Check that type1 cache is gone but type2 remains
        assert client1.get_data("key1") is None
        assert client2.get_data("key2") == "Data for client 2"
    
    def test_concurrent_access_simulation(self, cache_manager):
        """Test simulated concurrent access to cache."""
        # This is a simplified simulation of concurrent access
        # For real concurrent testing, multi-threading would be used
        
        # Create a test key and data
        cache_type = "concurrent"
        key = "shared_key"
        initial_data = "Initial data"
        updated_data = "Updated data"
        
        # Store initial data
        cache_manager.store(cache_type, key, initial_data)
        assert cache_manager.get(cache_type, key) == initial_data
        
        # Simulate "concurrent" access by having different instances
        # of CacheManager accessing the same directory
        second_manager = CacheManager(cache_dir=cache_manager.cache_dir)
        
        # Second manager reads the data
        assert second_manager.get(cache_type, key) == initial_data
        
        # First manager updates the data
        cache_manager.store(cache_type, key, updated_data)
        
        # Second manager should see the update
        assert second_manager.get(cache_type, key) == updated_data
        
        # Second manager invalidates the cache
        assert second_manager.invalidate(cache_type, key) == 1
        
        # First manager should see that the data is gone
        assert cache_manager.get(cache_type, key) is None
    
    def test_age_based_invalidation(self, cache_manager):
        """Test age-based cache invalidation across multiple clients."""
        # Create mock clients
        class MockAgeClient:
            def __init__(self, cache_manager, cache_type, max_age_days):
                self._cache_manager = cache_manager
                self.cache_type = cache_type
                self.max_age_days = max_age_days
            
            def store_data(self, key, data):
                return self._cache_manager.store(self.cache_type, key, data)
            
            def has_valid_data(self, key):
                return self._cache_manager.has_valid_cache(
                    self.cache_type, key, self.max_age_days)
            
            def get_data_if_valid(self, key):
                if self.has_valid_data(key):
                    return self._cache_manager.get(self.cache_type, key)
                return None
        
        # Create clients with different age requirements
        client1 = MockAgeClient(cache_manager, "age_test", max_age_days=5)
        client2 = MockAgeClient(cache_manager, "age_test", max_age_days=1)
        
        # Store test data
        client1.store_data("key1", "Test data")
        
        # Modify the file to simulate aging (3 days old)
        cache_path = os.path.join(cache_manager.cache_dir, "age_test")
        three_days_ago = time.time() - (3 * 24 * 60 * 60)
        for file_name in os.listdir(cache_path):
            file_path = os.path.join(cache_path, file_name)
            os.utime(file_path, (three_days_ago, three_days_ago))
        
        # Client1 should still consider the data valid (max age 5 days)
        assert client1.has_valid_data("key1") is True
        assert client1.get_data_if_valid("key1") == "Test data"
        
        # Client2 should consider the data invalid (max age 1 day)
        assert client2.has_valid_data("key1") is False
        assert client2.get_data_if_valid("key1") is None
    
    def test_cache_size_tracking(self, cache_manager):
        """Test tracking cache size across different cache types."""
        # Store data of various types and sizes
        cache_manager.store("type1", "key1", "Small data")
        cache_manager.store("type1", "key2", "Another small data entry")

        # Store larger data
        large_data = "X" * 10000  # 10 KB of data
        cache_manager.store("type2", "large_key", large_data)

        # Get cache sizes
        sizes = cache_manager.get_cache_size()

        # Verify results
        assert "total" in sizes
        assert sizes["total"] > 0
        assert "type1" in sizes
        assert "type2" in sizes

        # Type2 should be significantly larger than type1
        assert sizes["type2"] > sizes["type1"]

        # Invalidate type1 and check sizes again
        cache_manager.invalidate("type1")
        new_sizes = cache_manager.get_cache_size()

        # After invalidation, type1 should either not exist or have size 0
        if "type1" in new_sizes:
            assert new_sizes["type1"] == 0

        assert "type2" in new_sizes
        assert new_sizes["total"] < sizes["total"]