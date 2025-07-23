#!/usr/bin/env python3
"""
Performance test for mute system - check response times
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mute_manager import get_mute_manager

def test_mute_performance():
    """Test performance of mute operations"""
    print("🔧 Testing mute system performance...")
    
    mute_manager = get_mute_manager()
    
    # Test basic mute status check
    print("\n1. Testing basic mute status check:")
    start_time = time.time()
    try:
        is_muted, end_time = mute_manager.is_currently_muted()
        elapsed = time.time() - start_time
        print(f"   ✅ Mute status check: {elapsed:.3f}s (Muted: {is_muted})")
        if elapsed > 1.0:
            print(f"   ⚠️  WARNING: Slow response time: {elapsed:.3f}s")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ Error: {e} (took {elapsed:.3f}s)")
    
    # Test multiple rapid calls (simulate button clicks)
    print("\n2. Testing rapid mute status calls (simulating UI updates):")
    total_time = 0
    num_calls = 5
    
    for i in range(num_calls):
        start_time = time.time()
        try:
            is_muted, end_time = mute_manager.is_currently_muted()
            elapsed = time.time() - start_time
            total_time += elapsed
            print(f"   Call {i+1}: {elapsed:.3f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            total_time += elapsed
            print(f"   Call {i+1}: ERROR - {e} ({elapsed:.3f}s)")
    
    avg_time = total_time / num_calls
    print(f"   📊 Average time per call: {avg_time:.3f}s")
    
    if avg_time > 0.5:
        print("   ❌ PERFORMANCE ISSUE: Average > 0.5s per call")
    elif avg_time > 0.2:
        print("   ⚠️  SLOW: Average > 0.2s per call")
    else:
        print("   ✅ GOOD: Fast response times")
    
    # Test toggle operation
    print("\n3. Testing toggle mute operation:")
    start_time = time.time()
    try:
        original_state, _ = mute_manager.is_currently_muted()
        print(f"   Original state: {'Muted' if original_state else 'Unmuted'}")
        
        # Toggle mute
        if original_state:
            mute_manager.unmute()
            print("   🔊 Unmuted")
        else:
            mute_manager.mute(5)  # 5 minute mute
            print("   🔇 Muted for 5 minutes")
        
        elapsed = time.time() - start_time
        print(f"   ✅ Toggle operation: {elapsed:.3f}s")
        
        # Restore original state
        time.sleep(1)
        if original_state:
            mute_manager.mute(5)
        else:
            mute_manager.unmute()
        print("   🔄 Restored original state")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ Toggle error: {e} (took {elapsed:.3f}s)")

def main():
    print("🚀 Manifest Alert Performance Test")
    print("=" * 50)
    
    test_mute_performance()
    
    print("\n" + "=" * 50)
    print("✅ Performance test complete!")

if __name__ == "__main__":
    main()
