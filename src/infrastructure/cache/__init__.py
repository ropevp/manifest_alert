"""
Cache package for high-performance data caching.

Implements aggressive caching with 30-second network cache and 5-second fast cache
to meet the performance requirements of the manifest alert system.
"""

from .cache_manager import CacheManager
from .cache_entry import CacheEntry, CacheStats

__all__ = ['CacheManager', 'CacheEntry', 'CacheStats']
