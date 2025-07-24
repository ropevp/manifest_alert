"""
Cache entry and statistics classes.

Provides the data structures for managing cached data with TTL and statistics tracking.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Union
import time


@dataclass
class CacheEntry:
    """Represents a single cache entry with TTL and metadata.
    
    Stores cached data along with timing information for TTL management
    and access statistics for cache performance monitoring.
    """
    
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: float
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps and validate TTL."""
        if self.ttl_seconds <= 0:
            raise ValueError("TTL must be positive")
        
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired.
        
        Returns:
            True if the entry is past its TTL
        """
        if self.ttl_seconds == float('inf'):
            return False
        
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time
    
    @property
    def remaining_ttl(self) -> float:
        """Get the remaining time-to-live in seconds.
        
        Returns:
            Remaining TTL in seconds, 0 if expired
        """
        if self.ttl_seconds == float('inf'):
            return float('inf')
        
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        remaining = (expiry_time - datetime.now()).total_seconds()
        return max(0, remaining)
    
    @property
    def age_seconds(self) -> float:
        """Get the age of the cache entry in seconds.
        
        Returns:
            Age in seconds since creation
        """
        return (datetime.now() - self.created_at).total_seconds()
    
    def access(self) -> Any:
        """Access the cached value and update statistics.
        
        Returns:
            The cached value
            
        Raises:
            ValueError: If the entry has expired
        """
        if self.is_expired:
            raise ValueError(f"Cache entry '{self.key}' has expired")
        
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value
    
    def refresh(self, new_value: Any, new_ttl: Optional[float] = None) -> None:
        """Refresh the cache entry with new data.
        
        Args:
            new_value: New value to cache
            new_ttl: Optional new TTL, uses existing TTL if not provided
        """
        self.value = new_value
        self.created_at = datetime.now()
        self.last_accessed = self.created_at
        
        if new_ttl is not None:
            if new_ttl <= 0:
                raise ValueError("TTL must be positive")
            self.ttl_seconds = new_ttl


@dataclass
class CacheStats:
    """Cache performance statistics and metrics.
    
    Tracks cache hit/miss ratios, memory usage, and performance metrics
    for monitoring and optimization purposes.
    """
    
    hits: int = 0
    misses: int = 0
    total_entries: int = 0
    memory_usage_bytes: int = 0
    network_calls_saved: int = 0
    average_access_time_ms: float = 0.0
    
    @property
    def hit_ratio(self) -> float:
        """Calculate the cache hit ratio.
        
        Returns:
            Hit ratio as a value between 0.0 and 1.0
        """
        total_accesses = self.hits + self.misses
        if total_accesses == 0:
            return 0.0
        return self.hits / total_accesses
    
    @property
    def miss_ratio(self) -> float:
        """Calculate the cache miss ratio.
        
        Returns:
            Miss ratio as a value between 0.0 and 1.0
        """
        return 1.0 - self.hit_ratio
    
    @property
    def total_accesses(self) -> int:
        """Get total number of cache accesses.
        
        Returns:
            Total hits + misses
        """
        return self.hits + self.misses
    
    def record_hit(self, access_time_ms: float = 0.0) -> None:
        """Record a cache hit with optional timing.
        
        Args:
            access_time_ms: Time taken to access the cached value
        """
        self.hits += 1
        self._update_average_time(access_time_ms)
    
    def record_miss(self, access_time_ms: float = 0.0) -> None:
        """Record a cache miss with optional timing.
        
        Args:
            access_time_ms: Time taken for the cache miss operation
        """
        self.misses += 1
        self._update_average_time(access_time_ms)
    
    def record_network_call_saved(self) -> None:
        """Record that a network call was avoided due to cache hit."""
        self.network_calls_saved += 1
    
    def _update_average_time(self, access_time_ms: float) -> None:
        """Update the average access time with a new measurement.
        
        Args:
            access_time_ms: New access time measurement
        """
        if access_time_ms <= 0:
            return
        
        total_accesses = self.total_accesses
        if total_accesses <= 1:
            self.average_access_time_ms = access_time_ms
        else:
            # Calculate running average
            self.average_access_time_ms = (
                (self.average_access_time_ms * (total_accesses - 1) + access_time_ms) 
                / total_accesses
            )
    
    def reset(self) -> None:
        """Reset all statistics to zero."""
        self.hits = 0
        self.misses = 0
        self.total_entries = 0
        self.memory_usage_bytes = 0
        self.network_calls_saved = 0
        self.average_access_time_ms = 0.0
    
    def get_summary(self) -> Dict[str, Union[int, float, str]]:
        """Get a summary of cache statistics.
        
        Returns:
            Dictionary with formatted statistics
        """
        return {
            'total_accesses': self.total_accesses,
            'hits': self.hits,
            'misses': self.misses,
            'hit_ratio': f"{self.hit_ratio:.2%}",
            'miss_ratio': f"{self.miss_ratio:.2%}",
            'total_entries': self.total_entries,
            'memory_usage_mb': f"{self.memory_usage_bytes / 1024 / 1024:.2f}",
            'network_calls_saved': self.network_calls_saved,
            'avg_access_time_ms': f"{self.average_access_time_ms:.2f}",
        }
