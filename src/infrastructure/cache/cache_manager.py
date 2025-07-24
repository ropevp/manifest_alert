"""
High-performance cache manager with aggressive caching strategy.

Implements the 30-second network cache and 5-second fast cache required
for optimal performance in the manifest alert system.
"""

from typing import Any, Dict, Optional, List, Callable, TypeVar, Generic
from datetime import datetime, timedelta
import threading
import time
import logging
import sys
from dataclasses import dataclass

from .cache_entry import CacheEntry, CacheStats
from ...infrastructure.exceptions import NetworkAccessException

T = TypeVar('T')


class CacheManager:
    """High-performance cache manager with multi-tier caching.
    
    Provides aggressive caching with:
    - 30-second network cache for expensive operations
    - 5-second fast cache for UI responsiveness  
    - Automatic cache invalidation and refresh
    - Thread-safe operations with performance metrics
    """
    
    # Cache tier configurations
    NETWORK_CACHE_TTL = 30.0  # 30 seconds for network operations
    FAST_CACHE_TTL = 5.0      # 5 seconds for UI updates
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the cache manager.
        
        Args:
            logger: Optional logger for cache operations
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Cache storage
        self._network_cache: Dict[str, CacheEntry] = {}
        self._fast_cache: Dict[str, CacheEntry] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = CacheStats()
        
        # Cleanup tracking
        self._last_cleanup = datetime.now()
        self._cleanup_interval = 60.0  # Clean up every minute
        
        self.logger.info("CacheManager initialized with aggressive caching strategy")
    
    def get_network_cached(self, key: str, loader: Callable[[], T], 
                          force_refresh: bool = False) -> T:
        """Get value from network cache with 30-second TTL.
        
        This is the primary cache for expensive network operations.
        Cache hits here save significant time and prevent network timeouts.
        
        Args:
            key: Cache key identifier
            loader: Function to load data if cache miss
            force_refresh: Force cache refresh even if valid entry exists
            
        Returns:
            Cached or freshly loaded value
            
        Raises:
            NetworkAccessException: When loader fails and no cached data available
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Check for valid cache entry
                if not force_refresh and key in self._network_cache:
                    entry = self._network_cache[key]
                    if not entry.is_expired:
                        value = entry.access()
                        self._stats.record_hit((time.time() - start_time) * 1000)
                        self._stats.record_network_call_saved()
                        
                        self.logger.debug(f"Network cache HIT for '{key}' (age: {entry.age_seconds:.1f}s)")
                        return value
                    else:
                        # Remove expired entry
                        del self._network_cache[key]
                        self.logger.debug(f"Removed expired network cache entry: '{key}'")
                
                # Cache miss - load data
                self.logger.debug(f"Network cache MISS for '{key}' - loading data")
                self._stats.record_miss((time.time() - start_time) * 1000)
                
                try:
                    value = loader()
                    
                    # Store in cache
                    entry = CacheEntry(
                        key=key,
                        value=value,
                        created_at=datetime.now(),
                        ttl_seconds=self.NETWORK_CACHE_TTL
                    )
                    self._network_cache[key] = entry
                    self._stats.total_entries = len(self._network_cache) + len(self._fast_cache)
                    
                    self.logger.debug(f"Cached network data for '{key}' (TTL: {self.NETWORK_CACHE_TTL}s)")
                    return value
                    
                except Exception as e:
                    # Check if we have any cached data as fallback
                    fallback_entry = self._network_cache.get(key)
                    if fallback_entry is not None:
                        self.logger.warning(f"Using expired cache data for '{key}' due to loader error: {e}")
                        return fallback_entry.value
                    
                    error = NetworkAccessException(f"Failed to load data for '{key}': {e}")
                    self.logger.error(str(error))
                    raise error
                    
        finally:
            self._maybe_cleanup()
    
    def get_fast_cached(self, key: str, loader: Callable[[], T], 
                       force_refresh: bool = False) -> T:
        """Get value from fast cache with 5-second TTL.
        
        This cache is optimized for UI responsiveness and frequent access patterns.
        
        Args:
            key: Cache key identifier  
            loader: Function to load data if cache miss
            force_refresh: Force cache refresh even if valid entry exists
            
        Returns:
            Cached or freshly loaded value
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Check for valid cache entry
                if not force_refresh and key in self._fast_cache:
                    entry = self._fast_cache[key]
                    if not entry.is_expired:
                        value = entry.access()
                        self._stats.record_hit((time.time() - start_time) * 1000)
                        
                        self.logger.debug(f"Fast cache HIT for '{key}' (age: {entry.age_seconds:.1f}s)")
                        return value
                    else:
                        # Remove expired entry
                        del self._fast_cache[key]
                        self.logger.debug(f"Removed expired fast cache entry: '{key}'")
                
                # Cache miss - load data
                self.logger.debug(f"Fast cache MISS for '{key}' - loading data")
                self._stats.record_miss((time.time() - start_time) * 1000)
                
                value = loader()
                
                # Store in cache
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    ttl_seconds=self.FAST_CACHE_TTL
                )
                self._fast_cache[key] = entry
                self._stats.total_entries = len(self._network_cache) + len(self._fast_cache)
                
                self.logger.debug(f"Cached fast data for '{key}' (TTL: {self.FAST_CACHE_TTL}s)")
                return value
                
        finally:
            self._maybe_cleanup()
    
    def invalidate(self, key: str, cache_tier: Optional[str] = None) -> bool:
        """Invalidate cache entries for a specific key.
        
        Args:
            key: Cache key to invalidate
            cache_tier: Specific cache tier ('network', 'fast') or None for both
            
        Returns:
            True if any entries were invalidated
        """
        with self._lock:
            invalidated = False
            
            if cache_tier is None or cache_tier == 'network':
                if key in self._network_cache:
                    del self._network_cache[key]
                    invalidated = True
                    self.logger.debug(f"Invalidated network cache entry: '{key}'")
            
            if cache_tier is None or cache_tier == 'fast':
                if key in self._fast_cache:
                    del self._fast_cache[key]
                    invalidated = True
                    self.logger.debug(f"Invalidated fast cache entry: '{key}'")
            
            if invalidated:
                self._stats.total_entries = len(self._network_cache) + len(self._fast_cache)
            
            return invalidated
    
    def clear_all(self) -> None:
        """Clear all cache entries and reset statistics."""
        with self._lock:
            network_count = len(self._network_cache)
            fast_count = len(self._fast_cache)
            
            self._network_cache.clear()
            self._fast_cache.clear()
            self._stats.reset()
            
            self.logger.info(f"Cleared all cache entries (network: {network_count}, fast: {fast_count})")
    
    def get_statistics(self) -> CacheStats:
        """Get current cache statistics.
        
        Returns:
            Current cache statistics
        """
        with self._lock:
            # Update memory usage estimation
            self._stats.memory_usage_bytes = self._estimate_memory_usage()
            return self._stats
    
    def get_cache_info(self, cache_tier: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed cache information.
        
        Args:
            cache_tier: Specific cache tier to report on, or None for both
            
        Returns:
            Dictionary with cache information
        """
        with self._lock:
            info = {
                'timestamp': datetime.now().isoformat(),
                'statistics': self._stats.get_summary(),
            }
            
            if cache_tier is None or cache_tier == 'network':
                network_entries = []
                for key, entry in self._network_cache.items():
                    network_entries.append({
                        'key': key,
                        'age_seconds': entry.age_seconds,
                        'remaining_ttl': entry.remaining_ttl,
                        'access_count': entry.access_count,
                        'is_expired': entry.is_expired,
                    })
                info['network_cache'] = {
                    'ttl_seconds': self.NETWORK_CACHE_TTL,
                    'entry_count': len(self._network_cache),
                    'entries': network_entries,
                }
            
            if cache_tier is None or cache_tier == 'fast':
                fast_entries = []
                for key, entry in self._fast_cache.items():
                    fast_entries.append({
                        'key': key,
                        'age_seconds': entry.age_seconds,
                        'remaining_ttl': entry.remaining_ttl,
                        'access_count': entry.access_count,
                        'is_expired': entry.is_expired,
                    })
                info['fast_cache'] = {
                    'ttl_seconds': self.FAST_CACHE_TTL,
                    'entry_count': len(self._fast_cache),
                    'entries': fast_entries,
                }
            
            return info
    
    def _maybe_cleanup(self) -> None:
        """Perform periodic cleanup of expired entries."""
        now = datetime.now()
        if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        
        # Clean up expired entries
        expired_network = [k for k, v in self._network_cache.items() if v.is_expired]
        expired_fast = [k for k, v in self._fast_cache.items() if v.is_expired]
        
        for key in expired_network:
            del self._network_cache[key]
        
        for key in expired_fast:
            del self._fast_cache[key]
        
        if expired_network or expired_fast:
            self._stats.total_entries = len(self._network_cache) + len(self._fast_cache)
            self.logger.debug(f"Cleaned up expired entries (network: {len(expired_network)}, fast: {len(expired_fast)})")
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage of cached data.
        
        Returns:
            Estimated memory usage in bytes
        """
        try:
            total_size = 0
            
            # Estimate size of cache entries
            for entry in self._network_cache.values():
                total_size += sys.getsizeof(entry.value) + sys.getsizeof(entry)
            
            for entry in self._fast_cache.values():
                total_size += sys.getsizeof(entry.value) + sys.getsizeof(entry)
            
            return total_size
        except Exception:
            return 0
