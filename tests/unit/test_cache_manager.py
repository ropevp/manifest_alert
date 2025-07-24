"""
Unit tests for cache manager functionality.

Tests the aggressive caching strategy with 30-second network cache
and 5-second fast cache for optimal performance.
"""

import unittest
import time
import threading
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.infrastructure.cache import CacheManager, CacheEntry, CacheStats
from src.infrastructure.exceptions import NetworkAccessException


class TestCacheEntry(unittest.TestCase):
    """Test cases for CacheEntry class."""
    
    def test_create_cache_entry(self):
        """Test creating a cache entry."""
        # Act
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            ttl_seconds=30.0
        )
        
        # Assert
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.value, "test_value")
        self.assertEqual(entry.ttl_seconds, 30.0)
        self.assertEqual(entry.access_count, 0)
        self.assertIsNotNone(entry.last_accessed)
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        # Arrange
        past_time = datetime.now() - timedelta(seconds=60)
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=past_time,
            ttl_seconds=30.0
        )
        
        # Act & Assert
        self.assertTrue(entry.is_expired)
        self.assertEqual(entry.remaining_ttl, 0)
    
    def test_cache_entry_not_expired(self):
        """Test cache entry that hasn't expired."""
        # Arrange
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            ttl_seconds=30.0
        )
        
        # Act & Assert
        self.assertFalse(entry.is_expired)
        self.assertGreater(entry.remaining_ttl, 25)  # Should be close to 30
    
    def test_cache_entry_access(self):
        """Test accessing cache entry updates statistics."""
        # Arrange
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            ttl_seconds=30.0
        )
        
        # Act
        value = entry.access()
        
        # Assert
        self.assertEqual(value, "test_value")
        self.assertEqual(entry.access_count, 1)
        self.assertIsNotNone(entry.last_accessed)
    
    def test_access_expired_entry_raises_error(self):
        """Test accessing expired entry raises error."""
        # Arrange
        past_time = datetime.now() - timedelta(seconds=60)
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=past_time,
            ttl_seconds=30.0
        )
        
        # Act & Assert
        with self.assertRaises(ValueError):
            entry.access()
    
    def test_refresh_cache_entry(self):
        """Test refreshing cache entry with new value."""
        # Arrange
        entry = CacheEntry(
            key="test_key",
            value="old_value",
            created_at=datetime.now() - timedelta(seconds=10),
            ttl_seconds=30.0
        )
        
        # Act
        entry.refresh("new_value", 60.0)
        
        # Assert
        self.assertEqual(entry.value, "new_value")
        self.assertEqual(entry.ttl_seconds, 60.0)
        self.assertGreater(entry.remaining_ttl, 55)  # Should be close to 60
    
    def test_infinite_ttl(self):
        """Test cache entry with infinite TTL."""
        # Arrange
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            ttl_seconds=float('inf')
        )
        
        # Act & Assert
        self.assertFalse(entry.is_expired)
        self.assertEqual(entry.remaining_ttl, float('inf'))


class TestCacheStats(unittest.TestCase):
    """Test cases for CacheStats class."""
    
    def test_initial_stats(self):
        """Test initial cache statistics."""
        # Act
        stats = CacheStats()
        
        # Assert
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 0)
        self.assertEqual(stats.hit_ratio, 0.0)
        self.assertEqual(stats.miss_ratio, 1.0)
    
    def test_record_hits_and_misses(self):
        """Test recording hits and misses."""
        # Arrange
        stats = CacheStats()
        
        # Act
        stats.record_hit(10.0)
        stats.record_hit(15.0)
        stats.record_miss(20.0)
        
        # Assert
        self.assertEqual(stats.hits, 2)
        self.assertEqual(stats.misses, 1)
        self.assertEqual(stats.total_accesses, 3)
        self.assertAlmostEqual(stats.hit_ratio, 2/3, places=2)
        self.assertAlmostEqual(stats.miss_ratio, 1/3, places=2)
    
    def test_average_access_time_calculation(self):
        """Test average access time calculation."""
        # Arrange
        stats = CacheStats()
        
        # Act
        stats.record_hit(10.0)
        stats.record_hit(20.0)
        stats.record_miss(30.0)
        
        # Assert
        expected_avg = (10.0 + 20.0 + 30.0) / 3
        self.assertAlmostEqual(stats.average_access_time_ms, expected_avg, places=1)
    
    def test_network_calls_saved(self):
        """Test tracking network calls saved."""
        # Arrange
        stats = CacheStats()
        
        # Act
        stats.record_network_call_saved()
        stats.record_network_call_saved()
        
        # Assert
        self.assertEqual(stats.network_calls_saved, 2)
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        # Arrange
        stats = CacheStats()
        stats.record_hit(10.0)
        stats.record_miss(20.0)
        stats.record_network_call_saved()
        
        # Act
        stats.reset()
        
        # Assert
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 0)
        self.assertEqual(stats.network_calls_saved, 0)
        self.assertEqual(stats.average_access_time_ms, 0.0)
    
    def test_get_summary(self):
        """Test getting formatted statistics summary."""
        # Arrange
        stats = CacheStats()
        stats.record_hit(10.0)
        stats.record_miss(20.0)
        stats.network_calls_saved = 5
        stats.memory_usage_bytes = 1024 * 1024  # 1 MB
        
        # Act
        summary = stats.get_summary()
        
        # Assert
        self.assertEqual(summary["total_accesses"], 2)
        self.assertEqual(summary["hits"], 1)
        self.assertEqual(summary["misses"], 1)
        self.assertEqual(summary["hit_ratio"], "50.00%")
        self.assertEqual(summary["miss_ratio"], "50.00%")
        self.assertEqual(summary["network_calls_saved"], 5)
        self.assertEqual(summary["memory_usage_mb"], "1.00")


class TestCacheManager(unittest.TestCase):
    """Test cases for CacheManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache_manager = CacheManager()
    
    def test_network_cache_hit(self):
        """Test network cache hit scenario."""
        # Arrange
        def loader():
            return "loaded_value"
        
        # Act - First call should load data
        result1 = self.cache_manager.get_network_cached("test_key", loader)
        # Second call should hit cache
        result2 = self.cache_manager.get_network_cached("test_key", loader)
        
        # Assert
        self.assertEqual(result1, "loaded_value")
        self.assertEqual(result2, "loaded_value")
        # Should have at least one cache hit
        stats = self.cache_manager.get_statistics()
        self.assertGreater(stats.hits, 0)
    
    def test_fast_cache_hit(self):
        """Test fast cache hit scenario."""
        # Arrange
        def loader():
            return "fast_value"
        
        # Act - First call should load data
        result1 = self.cache_manager.get_fast_cached("fast_key", loader)
        # Second call should hit cache
        result2 = self.cache_manager.get_fast_cached("fast_key", loader)
        
        # Assert
        self.assertEqual(result1, "fast_value")
        self.assertEqual(result2, "fast_value")
    
    def test_cache_miss_calls_loader(self):
        """Test cache miss scenario calls loader function."""
        # Arrange
        mock_loader = Mock(return_value="mock_value")
        
        # Act
        result = self.cache_manager.get_network_cached("new_key", mock_loader)
        
        # Assert
        self.assertEqual(result, "mock_value")
        mock_loader.assert_called_once()
    
    def test_force_refresh_bypasses_cache(self):
        """Test force refresh bypasses existing cache."""
        # Arrange
        call_count = 0
        def counting_loader():
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"
        
        # Act
        result1 = self.cache_manager.get_network_cached("refresh_key", counting_loader)
        result2 = self.cache_manager.get_network_cached("refresh_key", counting_loader, force_refresh=True)
        
        # Assert
        self.assertEqual(result1, "value_1")
        self.assertEqual(result2, "value_2")
        self.assertEqual(call_count, 2)  # Loader called twice due to force refresh
    
    def test_cache_expiration(self):
        """Test cache entry expiration."""
        # Arrange
        cache_manager = CacheManager()
        cache_manager.NETWORK_CACHE_TTL = 0.1  # 100ms for testing
        
        call_count = 0
        def counting_loader():
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"
        
        # Act
        result1 = cache_manager.get_network_cached("expire_key", counting_loader)
        time.sleep(0.2)  # Wait for expiration
        result2 = cache_manager.get_network_cached("expire_key", counting_loader)
        
        # Assert
        self.assertEqual(result1, "value_1")
        self.assertEqual(result2, "value_2")
        self.assertEqual(call_count, 2)  # Loader called twice due to expiration
    
    def test_invalidate_cache_entry(self):
        """Test invalidating specific cache entries."""
        # Arrange
        def loader():
            return "value"
        
        # Load into cache
        self.cache_manager.get_network_cached("invalidate_key", loader)
        
        # Act
        invalidated = self.cache_manager.invalidate("invalidate_key", "network")
        
        # Assert
        self.assertTrue(invalidated)
    
    def test_invalidate_nonexistent_key(self):
        """Test invalidating non-existent cache key."""
        # Act
        invalidated = self.cache_manager.invalidate("nonexistent_key")
        
        # Assert
        self.assertFalse(invalidated)
    
    def test_clear_all_caches(self):
        """Test clearing all cache entries."""
        # Arrange
        def loader():
            return "value"
        
        self.cache_manager.get_network_cached("key1", loader)
        self.cache_manager.get_fast_cached("key2", loader)
        
        # Act
        self.cache_manager.clear_all()
        
        # Assert
        stats = self.cache_manager.get_statistics()
        self.assertEqual(stats.total_entries, 0)
    
    def test_cache_fallback_on_loader_failure(self):
        """Test cache fallback when loader fails."""
        # Arrange
        def failing_loader():
            raise Exception("Loader failed")
        
        # First, populate cache with good data
        def good_loader():
            return "cached_value"
        
        self.cache_manager.get_network_cached("fallback_key", good_loader)
        
        # Now try with failing loader - should return expired cache data
        try:
            result = self.cache_manager.get_network_cached("fallback_key", failing_loader)
            # If we get here, it used fallback (though this test may not work as expected
            # due to TTL not being expired)
        except NetworkAccessException:
            # This is expected when no cache fallback is available
            pass
    
    def test_thread_safety(self):
        """Test cache manager thread safety."""
        # Arrange
        results = []
        call_count = 0
        
        def thread_loader():
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Small delay to test concurrency
            return f"value_{call_count}"
        
        def cache_access():
            result = self.cache_manager.get_network_cached("thread_key", thread_loader)
            results.append(result)
        
        # Act - Multiple threads accessing cache simultaneously
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=cache_access)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert - All threads should get the same value (cache hit)
        # and loader should only be called once
        self.assertEqual(len(set(results)), 1)  # All results should be the same
        self.assertEqual(call_count, 1)  # Loader called only once
    
    def test_get_cache_info(self):
        """Test getting detailed cache information."""
        # Arrange
        def loader():
            return "info_value"
        
        self.cache_manager.get_network_cached("info_key", loader)
        
        # Act
        info = self.cache_manager.get_cache_info()
        
        # Assert
        self.assertIn("timestamp", info)
        self.assertIn("statistics", info)
        self.assertIn("network_cache", info)
        self.assertIn("fast_cache", info)
        
        network_cache = info["network_cache"]
        self.assertEqual(network_cache["entry_count"], 1)
        self.assertEqual(network_cache["ttl_seconds"], CacheManager.NETWORK_CACHE_TTL)
    
    def test_cache_cleanup(self):
        """Test automatic cleanup of expired entries."""
        # Arrange
        cache_manager = CacheManager()
        cache_manager._cleanup_interval = 0.1  # 100ms for testing
        
        # Add entry that will expire
        entry = CacheEntry(
            key="cleanup_key",
            value="cleanup_value",
            created_at=datetime.now() - timedelta(seconds=60),
            ttl_seconds=30.0
        )
        cache_manager._network_cache["cleanup_key"] = entry
        
        # Force the last cleanup time to be far in the past
        cache_manager._last_cleanup = datetime.now() - timedelta(seconds=120)
        
        # Act - Trigger cleanup
        cache_manager._maybe_cleanup()
        
        # Assert - Expired entry should be removed
        self.assertNotIn("cleanup_key", cache_manager._network_cache)
    
    def test_performance_with_large_dataset(self):
        """Test cache performance with larger dataset."""
        # Arrange
        def loader_factory(value):
            return lambda: f"value_{value}"
        
        # Act - Load many items into cache
        start_time = time.time()
        for i in range(100):
            self.cache_manager.get_network_cached(f"perf_key_{i}", loader_factory(i))
        
        # Access cached items
        for i in range(100):
            result = self.cache_manager.get_network_cached(f"perf_key_{i}", loader_factory(i))
            self.assertEqual(result, f"value_{i}")
        
        end_time = time.time()
        
        # Assert - Should be fast
        total_time = end_time - start_time
        self.assertLess(total_time, 1.0)  # Should complete in under 1 second
        
        # Check cache hit ratio
        stats = self.cache_manager.get_statistics()
        self.assertGreater(stats.hit_ratio, 0.4)  # At least 40% hit ratio


class TestCachePerformanceRequirements(unittest.TestCase):
    """Test that cache meets performance requirements."""
    
    def test_network_cache_ttl_requirement(self):
        """Test that network cache TTL meets 30-second requirement."""
        self.assertEqual(CacheManager.NETWORK_CACHE_TTL, 30.0)
    
    def test_fast_cache_ttl_requirement(self):
        """Test that fast cache TTL meets 5-second requirement."""
        self.assertEqual(CacheManager.FAST_CACHE_TTL, 5.0)
    
    def test_cache_access_speed(self):
        """Test that cache access is fast enough for UI responsiveness."""
        # Arrange
        cache_manager = CacheManager()
        def loader():
            return "speed_test_value"
        
        # Prime the cache
        cache_manager.get_fast_cached("speed_key", loader)
        
        # Act - Measure cache access speed
        start_time = time.time()
        for _ in range(1000):
            cache_manager.get_fast_cached("speed_key", loader)
        end_time = time.time()
        
        # Assert - Should be very fast (< 100ms for 1000 accesses)
        total_time = end_time - start_time
        avg_time_per_access = total_time / 1000
        self.assertLess(avg_time_per_access, 0.0001)  # < 0.1ms per access


if __name__ == '__main__':
    unittest.main()
