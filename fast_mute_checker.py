#!/usr/bin/env python3
"""
Lightweight mute status checker with local caching
"""

import json
import os
import time
from datetime import datetime, timedelta

class FastMuteChecker:
    def __init__(self):
        self.local_cache_file = os.path.join(os.path.dirname(__file__), 'app_data', 'mute_cache.json')
        self.network_file = r'\\Prddpkmitlgt004\ManifestPC\mute_status.json'
        self.cache_duration = 30  # Cache for 30 seconds
        self._cached_status = None
        self._cache_time = 0
        
    def is_muted_fast(self):
        """Fast mute check using local cache"""
        current_time = time.time()
        
        # Check if cache is still valid
        if self._cached_status and (current_time - self._cache_time) < self.cache_duration:
            return self._cached_status.get('is_muted', False)
        
        # Try to update cache from network (with timeout)
        try:
            status = self._get_network_status_with_timeout()
            if status:
                self._cached_status = status
                self._cache_time = current_time
                self._save_local_cache(status)
                return status.get('is_muted', False)
        except:
            pass
        
        # Fallback to local cache file
        try:
            local_status = self._load_local_cache()
            if local_status:
                self._cached_status = local_status
                return local_status.get('is_muted', False)
        except:
            pass
            
        # Ultimate fallback
        return False
    
    def _get_network_status_with_timeout(self, timeout=2):
        """Get status from network with timeout"""
        import threading
        
        result = [None]
        exception = [None]
        
        def read_network():
            try:
                if os.path.exists(self.network_file):
                    with open(self.network_file, 'r') as f:
                        result[0] = json.load(f)
                else:
                    result[0] = {'is_muted': False, 'last_updated': time.time()}
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=read_network)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Timeout occurred
            return None
            
        if exception[0]:
            raise exception[0]
            
        return result[0]
    
    def _save_local_cache(self, status):
        """Save status to local cache"""
        try:
            os.makedirs(os.path.dirname(self.local_cache_file), exist_ok=True)
            with open(self.local_cache_file, 'w') as f:
                json.dump(status, f)
        except:
            pass
    
    def _load_local_cache(self):
        """Load status from local cache"""
        try:
            if os.path.exists(self.local_cache_file):
                with open(self.local_cache_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None

# Global fast checker instance
_fast_checker = None

def get_fast_mute_status():
    """Get mute status quickly using caching"""
    global _fast_checker
    if not _fast_checker:
        _fast_checker = FastMuteChecker()
    return _fast_checker.is_muted_fast()

if __name__ == "__main__":
    # Test the fast checker
    print("🚀 Testing fast mute checker...")
    
    for i in range(5):
        start = time.time()
        is_muted = get_fast_mute_status()
        elapsed = time.time() - start
        print(f"Call {i+1}: {elapsed:.3f}s - Muted: {is_muted}")
        time.sleep(1)
