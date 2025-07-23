#!/usr/bin/env python3
"""
Simple cache performance test - no GUI
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MockMuteManager:
    """Mock mute manager for testing cache performance"""
    def __init__(self):
        self.call_count = 0
        
    def is_currently_muted(self):
        """Simulate slow network call"""
        self.call_count += 1
        print(f"      [NETWORK CALL #{self.call_count}] Simulating 1.5s network delay...")
        time.sleep(1.5)  # Simulate slow network
        return False, None

class CacheTestObject:
    """Test object with same caching logic as AlertDisplay"""
    def __init__(self):
        self.mute_manager = MockMuteManager()
        self._cached_mute_status = False
        self._last_mute_check = 0
        self._mute_check_interval = 30
        self._fast_cache_duration = 5
        
    @property
    def is_snoozed(self):
        """Same caching logic as AlertDisplay"""
        import time
        current_time = time.time()
        
        # Ultra-fast response for frequent UI calls - use cache for 5 seconds
        if current_time - self._last_mute_check < self._fast_cache_duration:
            return self._cached_mute_status
        
        # Only do network calls every 30 seconds max
        if current_time - self._last_mute_check > self._mute_check_interval:
            try:
                # Use a timeout for network calls to prevent hanging
                import threading
                result = [None]
                
                def check_network():
                    try:
                        muted, _ = self.mute_manager.is_currently_muted()
                        result[0] = muted
                    except:
                        result[0] = self._cached_mute_status
                
                thread = threading.Thread(target=check_network)
                thread.daemon = True
                thread.start()
                thread.join(1.0)  # 1 second timeout
                
                if result[0] is not None:
                    old_status = self._cached_mute_status
                    self._cached_mute_status = result[0]
                    
                    if old_status != self._cached_mute_status:
                        print(f"      🔔 Mute state changed: {old_status} → {self._cached_mute_status}")
                
                self._last_mute_check = current_time
            except Exception:
                pass
        
        return self._cached_mute_status

def test_cache_performance():
    """Test the caching performance"""
    print("🔧 Testing mute status caching performance...")
    
    test_obj = CacheTestObject()
    
    print("\n⚡ Testing rapid UI calls (should be cached):")
    times = []
    
    for i in range(8):
        start_time = time.time()
        is_muted = test_obj.is_snoozed
        elapsed = time.time() - start_time
        times.append(elapsed)
        print(f"   Call {i+1}: {elapsed:.4f}s - Muted: {is_muted}")
        time.sleep(0.2)  # Small UI update delay
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print(f"\n📊 Rapid UI Calls Summary:")
    print(f"   Average: {avg_time:.4f}s")
    print(f"   Max:     {max_time:.4f}s")
    print(f"   Network calls made: {test_obj.mute_manager.call_count}")
    
    if max_time < 0.01:
        print("   ✅ EXCELLENT: All calls under 0.01s")
    elif max_time < 0.1:
        print("   ✅ GOOD: All calls under 0.1s") 
    else:
        print("   ⚠️  NEEDS IMPROVEMENT: Some calls over 0.1s")
    
    # Test cache expiration
    print(f"\n⏰ Waiting for cache to expire (6 seconds)...")
    time.sleep(6)
    
    print("\n🔄 Testing cache refresh:")
    start_time = time.time()
    is_muted = test_obj.is_snoozed
    elapsed = time.time() - start_time
    print(f"   Cache refresh call: {elapsed:.4f}s - Muted: {is_muted}")
    print(f"   Total network calls: {test_obj.mute_manager.call_count}")
    
    # Test fast follow-up calls
    print("\n⚡ Testing fast follow-up calls:")
    for i in range(3):
        start_time = time.time()
        is_muted = test_obj.is_snoozed
        elapsed = time.time() - start_time
        print(f"   Fast call {i+1}: {elapsed:.4f}s - Muted: {is_muted}")

def main():
    print("🚀 Cache Performance Test - No GUI")
    print("=" * 50)
    
    test_cache_performance()
    
    print("\n" + "=" * 50)
    print("✅ Cache test complete!")

if __name__ == "__main__":
    main()
