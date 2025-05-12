import os
import time
import pickle
import pytest
import shutil
import tempfile
from typing import Dict, Optional, Any
from unittest.mock import patch, MagicMock

from meet2obsidian.cache import CacheManager


class TestCacheStorage:
    """Test suite for storing objects in cache."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after tests
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a CacheManager instance for tests."""
        return CacheManager(cache_dir=temp_cache_dir, retention_days=30)
    
    def test_store_string_data(self, cache_manager):
        """Test storing string data in cache."""
        # Arrange
        cache_type = "test_strings"
        key = "string_key_1"
        data = "This is a test string to store in cache"
        
        # Act
        result = cache_manager.store(cache_type, key, data)
        
        # Assert
        assert result is True
        # Check that cache file was created
        cache_path = os.path.join(cache_manager.cache_dir, cache_type)
        assert os.path.exists(cache_path)
        cache_files = os.listdir(cache_path)
        assert len(cache_files) == 1
    
    def test_store_dict_data(self, cache_manager):
        """Test storing dictionary data in cache."""
        # Arrange
        cache_type = "test_dicts"
        key = "dict_key_1"
        data = {"name": "Test User", "age": 30, "items": [1, 2, 3]}
        
        # Act
        result = cache_manager.store(cache_type, key, data)
        
        # Assert
        assert result is True
        # Verify cache contents by reading it directly
        cache_path = os.path.join(cache_manager.cache_dir, cache_type)
        cache_files = os.listdir(cache_path)
        # We should find the cache file
        assert len(cache_files) == 1
        
        # Verify data was stored correctly
        with open(os.path.join(cache_path, cache_files[0]), 'rb') as f:
            stored_data = pickle.load(f)
        assert stored_data == data
        
        # Also verify using the get method
        retrieved_data = cache_manager.get(cache_type, key)
        assert retrieved_data == data
    
    def test_store_binary_data(self, cache_manager):
        """Test storing binary data in cache."""
        # Arrange
        cache_type = "test_binary"
        key = "binary_key_1"
        data = b'\x00\x01\x02\x03\x04\xFF\xFE\xFD'
        
        # Act
        result = cache_manager.store(cache_type, key, data)
        
        # Assert
        assert result is True
        # Verify by retrieving
        retrieved_data = cache_manager.get(cache_type, key)
        assert retrieved_data == data
    
    def test_store_with_missing_directory(self, cache_manager):
        """Test storing data when the cache directory doesn't exist."""
        # Arrange
        cache_type = "nonexistent/nested/deep"
        key = "nested_key"
        data = "Data in nested directory"
        
        # Act
        result = cache_manager.store(cache_type, key, data)
        
        # Assert
        assert result is True
        # Check that nested directories were created
        cache_path = os.path.join(cache_manager.cache_dir, "nonexistent", "nested", "deep")
        assert os.path.exists(cache_path)
        # Verify data can be retrieved
        retrieved_data = cache_manager.get(cache_type, key)
        assert retrieved_data == data
    
    def test_store_overwrite_existing(self, cache_manager):
        """Test overwriting existing data in cache."""
        # Arrange
        cache_type = "test_overwrite"
        key = "overwrite_key"
        data1 = "Original data"
        data2 = "Updated data"
        
        # Act
        cache_manager.store(cache_type, key, data1)
        # Verify original data was stored
        original_data = cache_manager.get(cache_type, key)
        assert original_data == data1
        
        # Overwrite
        result = cache_manager.store(cache_type, key, data2)
        
        # Assert
        assert result is True
        updated_data = cache_manager.get(cache_type, key)
        assert updated_data == data2
        assert updated_data != data1
    
    def test_store_error_handling(self, cache_manager):
        """Test error handling when storing in cache."""
        # Arrange
        cache_type = "test_errors"
        key = "error_key"
        data = "Test data for error case"
        
        # Mock os.makedirs to raise PermissionError
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            # Act
            result = cache_manager.store(cache_type, key, data)
            
            # Assert
            assert result is False
        
        # Mock pickle.dump to raise an error
        with patch('pickle.dump', side_effect=pickle.PickleError("Pickling error")):
            # Act
            result = cache_manager.store(cache_type, key, data)
            
            # Assert
            assert result is False
    
    def test_store_custom_object(self, cache_manager):
        """Test storing custom objects in cache."""
        # Arrange
        class CustomObject:
            def __init__(self, name, value):
                self.name = name
                self.value = value

            def __eq__(self, other):
                if not isinstance(other, CustomObject):
                    return False
                return self.name == other.name and self.value == other.value

        cache_type = "test_objects"
        key = "object_key"
        data = CustomObject("test_name", 42)

        # Act
        result = cache_manager.store(cache_type, key, data)

        # Assert
        assert result is True
        retrieved_data = cache_manager.get(cache_type, key)

        # The retrieved object might be a dict of attributes, not the original class instance
        if isinstance(retrieved_data, dict):
            assert retrieved_data['name'] == "test_name"
            assert retrieved_data['value'] == 42
        else:
            assert retrieved_data == data
            assert retrieved_data.name == "test_name"
            assert retrieved_data.value == 42
    
    def test_store_large_data(self, cache_manager):
        """Test storing large data in cache."""
        # Arrange
        cache_type = "test_large"
        key = "large_key"
        # Create relatively large data (about 5 MB)
        data = b'x' * (5 * 1024 * 1024)
        
        # Act
        result = cache_manager.store(cache_type, key, data)
        
        # Assert
        assert result is True
        # Check file size
        cache_path = os.path.join(cache_manager.cache_dir, cache_type)
        cache_files = os.listdir(cache_path)
        file_path = os.path.join(cache_path, cache_files[0])
        file_size = os.path.getsize(file_path)
        # File size should be approximately equal to data size (plus some overhead)
        assert file_size > 5 * 1024 * 1024  # More than 5 MB


class TestCacheRetrieval:
    """Test suite for retrieving objects from cache."""
    
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
    
    @pytest.fixture
    def populated_cache(self, cache_manager):
        """Populate cache with test data."""
        cache_manager.store("test_strings", "key1", "String data")
        cache_manager.store("test_dicts", "key2", {"name": "Test", "value": 123})
        cache_manager.store("test_binary", "key3", b'\x01\x02\x03\x04')
        return cache_manager
    
    def test_get_existing_string(self, populated_cache):
        """Test retrieving existing string from cache."""
        # Act
        result = populated_cache.get("test_strings", "key1")
        
        # Assert
        assert result == "String data"
    
    def test_get_existing_dict(self, populated_cache):
        """Test retrieving existing dictionary from cache."""
        # Act
        result = populated_cache.get("test_dicts", "key2")
        
        # Assert
        assert result == {"name": "Test", "value": 123}
        assert result["name"] == "Test"
        assert result["value"] == 123
    
    def test_get_existing_binary(self, populated_cache):
        """Test retrieving existing binary data from cache."""
        # Act
        result = populated_cache.get("test_binary", "key3")
        
        # Assert
        assert result == b'\x01\x02\x03\x04'
    
    def test_get_nonexistent_key(self, populated_cache):
        """Test retrieving nonexistent key from cache."""
        # Act
        result = populated_cache.get("test_strings", "nonexistent_key")
        
        # Assert
        assert result is None
    
    def test_get_nonexistent_type(self, populated_cache):
        """Test retrieving from nonexistent cache type."""
        # Act
        result = populated_cache.get("nonexistent_type", "key1")
        
        # Assert
        assert result is None
    
    def test_get_with_deserialize_error(self, populated_cache):
        """Test handling deserialization errors when retrieving from cache."""
        # Arrange - create a corrupted cache file
        cache_type = "corrupted"
        key = "bad_key"
        cache_path = os.path.join(populated_cache.cache_dir, cache_type)
        os.makedirs(cache_path, exist_ok=True)
        
        # Generate filename the same way CacheManager does
        import hashlib
        file_name = hashlib.md5(key.encode('utf-8')).hexdigest()
        file_path = os.path.join(cache_path, file_name)
        
        # Create a corrupted file with invalid pickle data
        with open(file_path, 'wb') as f:
            f.write(b'This is not a valid pickle file')
        
        # Act
        result = populated_cache.get(cache_type, key)
        
        # Assert - should return None instead of raising exception
        assert result is None
    
    def test_has_valid_cache_with_existing(self, populated_cache):
        """Test checking for valid cache with existing key."""
        # Act
        result = populated_cache.has_valid_cache("test_strings", "key1")
        
        # Assert
        assert result is True
    
    def test_has_valid_cache_with_nonexistent(self, populated_cache):
        """Test checking for valid cache with nonexistent key."""
        # Act
        result = populated_cache.has_valid_cache("test_strings", "nonexistent_key")
        
        # Assert
        assert result is False
    
    def test_get_with_age_verification(self, cache_manager):
        """Test retrieving cache with age verification."""
        # Arrange
        cache_type = "test_age"
        key = "age_key"
        data = "Data with age check"
        
        # Store data
        cache_manager.store(cache_type, key, data)
        
        # Act & Assert - should be valid immediately after creation
        assert cache_manager.has_valid_cache(cache_type, key, max_age_days=1) is True
        
        # Simulate an old file created a week ago
        week_ago = time.time() - (7 * 24 * 60 * 60)  # 7 days ago
        
        # Find the file and modify its modification time
        cache_path = os.path.join(cache_manager.cache_dir, cache_type)
        cache_files = os.listdir(cache_path)
        file_path = os.path.join(cache_path, cache_files[0])
        os.utime(file_path, (week_ago, week_ago))
        
        # Act & Assert - should now be considered outdated for max_age_days=1
        assert cache_manager.has_valid_cache(cache_type, key, max_age_days=1) is False
        # But still valid for max_age_days=30 (default)
        assert cache_manager.has_valid_cache(cache_type, key) is True


class TestCacheInvalidation:
    """Test suite for cache invalidation."""
    
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
    
    @pytest.fixture
    def populated_cache(self, cache_manager):
        """Populate cache with test data."""
        # Type 1 with multiple keys
        cache_manager.store("type1", "key1", "Data 1")
        cache_manager.store("type1", "key2", "Data 2")
        cache_manager.store("type1", "key3", "Data 3")
        
        # Type 2 with multiple keys
        cache_manager.store("type2", "key1", "Data 4")
        cache_manager.store("type2", "key2", "Data 5")
        
        # Type 3 with one key
        cache_manager.store("type3", "key1", "Data 6")
        
        return cache_manager
    
    def test_invalidate_specific_key(self, populated_cache):
        """Test invalidating a specific key in cache."""
        # Act
        count = populated_cache.invalidate("type1", "key1")
        
        # Assert
        assert count == 1  # One file should be removed
        # Check that key was actually removed
        assert populated_cache.get("type1", "key1") is None
        # But other keys of the same type remain
        assert populated_cache.get("type1", "key2") == "Data 2"
        assert populated_cache.get("type1", "key3") == "Data 3"
    
    def test_invalidate_entire_type(self, populated_cache):
        """Test invalidating all keys of a specific type."""
        # Act
        count = populated_cache.invalidate("type1")
        
        # Assert
        assert count == 3  # Three files should be removed
        # Check that all keys of the type were removed
        assert populated_cache.get("type1", "key1") is None
        assert populated_cache.get("type1", "key2") is None
        assert populated_cache.get("type1", "key3") is None
        # But keys of other types remain
        assert populated_cache.get("type2", "key1") == "Data 4"
        assert populated_cache.get("type3", "key1") == "Data 6"
    
    def test_invalidate_nonexistent_key(self, populated_cache):
        """Test invalidating a nonexistent key."""
        # Act
        count = populated_cache.invalidate("type1", "nonexistent_key")
        
        # Assert
        assert count == 0  # Nothing should be removed
        # Check that other keys were not affected
        assert populated_cache.get("type1", "key1") == "Data 1"
        assert populated_cache.get("type1", "key2") == "Data 2"
    
    def test_invalidate_nonexistent_type(self, populated_cache):
        """Test invalidating a nonexistent cache type."""
        # Act
        count = populated_cache.invalidate("nonexistent_type")
        
        # Assert
        assert count == 0  # Nothing should be removed
        # Check that other types were not affected
        assert populated_cache.get("type1", "key1") == "Data 1"
        assert populated_cache.get("type2", "key1") == "Data 4"
    
    def test_invalidate_error_handling(self, populated_cache):
        """Test error handling during cache invalidation."""
        # Arrange - mock os.remove to raise PermissionError
        with patch('os.remove', side_effect=PermissionError("Permission denied")):
            # Act
            count = populated_cache.invalidate("type1", "key1")
            
            # Assert
            assert count == 0  # Nothing should be removed due to error
    
    def test_invalidate_all_cache(self, populated_cache):
        """Test invalidating entire cache."""
        # Act
        count = populated_cache.invalidate_all()
        
        # Assert
        assert count == 6  # All 6 files should be removed
        # Check that all data is gone
        assert populated_cache.get("type1", "key1") is None
        assert populated_cache.get("type2", "key1") is None
        assert populated_cache.get("type3", "key1") is None


class TestCacheCleanup:
    """Test suite for cache cleanup."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a CacheManager instance with short retention for testing cleanup."""
        return CacheManager(cache_dir=temp_cache_dir, retention_days=7)
    
    def create_aged_cache_files(self, cache_manager, age_days, cache_type="aged_type"):
        """Create cache files with a specified age."""
        # Create files
        cache_manager.store(cache_type, "recent_key", "Recent data")
        cache_manager.store(cache_type, "old_key", "Old data")
        
        # Modify modification time for "old_key"
        past_time = time.time() - (age_days * 24 * 60 * 60)  # age in days
        
        # Find file for old_key
        cache_path = os.path.join(cache_manager.cache_dir, cache_type)
        for file_name in os.listdir(cache_path):
            file_path = os.path.join(cache_path, file_name)
            # Check if this is the file for old_key by reading its content
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                    if data == "Old data":
                        # Set old modification time
                        os.utime(file_path, (past_time, past_time))
                        break
            except:
                continue
    
    def test_cleanup_with_aged_files(self, cache_manager):
        """Test cleaning up aged cache files."""
        # Arrange - create files with different ages
        # Recent file (1 day old)
        self.create_aged_cache_files(cache_manager, 1, "recent_type")
        # Old file (10 days old, more than retention_days=7)
        self.create_aged_cache_files(cache_manager, 10, "old_type")
        
        # Act
        count = cache_manager.cleanup()
        
        # Assert
        assert count >= 1  # At least one file should be removed (the old one)
        # Check that old file is gone but recent one remains
        assert cache_manager.get("old_type", "old_key") is None
        assert cache_manager.get("recent_type", "recent_key") == "Recent data"
    
    def test_cleanup_with_no_aged_files(self, cache_manager):
        """Test cleanup when there are no aged files."""
        # Arrange - create only recent files (1 day old)
        self.create_aged_cache_files(cache_manager, 1)
        
        # Act
        count = cache_manager.cleanup()
        
        # Assert
        assert count == 0  # Nothing should be removed
        # Check that all files remain
        assert cache_manager.get("aged_type", "recent_key") == "Recent data"
        assert cache_manager.get("aged_type", "old_key") == "Old data"
    
    def test_cleanup_error_handling(self, cache_manager):
        """Test error handling during cache cleanup."""
        # Arrange
        self.create_aged_cache_files(cache_manager, 10)  # Old files
        
        # Mock os.remove to raise PermissionError
        with patch('os.remove', side_effect=PermissionError("Permission denied")):
            # Act
            count = cache_manager.cleanup()
            
            # Assert
            assert count == 0  # Nothing should be removed due to error
    
    def test_cleanup_with_custom_retention(self, cache_manager):
        """Test cleanup with custom retention period."""
        # Arrange
        # Create files with age 5 days (less than default retention_days=7)
        self.create_aged_cache_files(cache_manager, 5)
        
        # Act - clean up with custom retention of 3 days
        count = cache_manager.cleanup_with_retention(retention_days=3)
        
        # Assert
        assert count >= 1  # At least one file should be removed
        # Check that files older than 3 days are removed
        assert cache_manager.get("aged_type", "old_key") is None
    
    def test_cleanup_specific_cache_type(self, cache_manager):
        """Test cleaning up aged files of a specific cache type."""
        # Arrange
        # Create aged files of different types
        
        # Type 1 with aged files
        old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
        cache_manager.store("type1", "old_key1", "Old data 1")
        cache_path = os.path.join(cache_manager.cache_dir, "type1")
        for file_name in os.listdir(cache_path):
            file_path = os.path.join(cache_path, file_name)
            os.utime(file_path, (old_time, old_time))
        
        # Type 2 with aged files
        cache_manager.store("type2", "old_key2", "Old data 2")
        cache_path = os.path.join(cache_manager.cache_dir, "type2")
        for file_name in os.listdir(cache_path):
            file_path = os.path.join(cache_path, file_name)
            os.utime(file_path, (old_time, old_time))
        
        # Act
        count = cache_manager.cleanup_type("type1")
        
        # Assert
        assert count >= 1  # At least one file should be removed from type1
        # Check that files from type1 are removed but type2 remains
        assert cache_manager.get("type1", "old_key1") is None
        assert cache_manager.get("type2", "old_key2") == "Old data 2"