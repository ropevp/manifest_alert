#!/usr/bin/env python3
"""
Quick test script to verify mute button responsiveness
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mute_button_speed():
    """Test mute button response speed using the optimized approach"""
    print("🔧 Testing optimized mute button performance...")
    
    # Import the application's mute checking logic
    try:
        from alert_display import AlertDisplay
        from mute_manager import get_mute_manager
        
        # Create a minimal test instance
        app = None
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication([])
        except:
            pass
            
        display = AlertDisplay()
        mute_manager = get_mute_manager()
        
        print("✅ Application components loaded successfully")
        
        # Test cached mute status calls (what the UI actually does)
        print("\n🚀 Testing cached mute status calls (UI simulation):")
        times = []
        
        for i in range(10):
            start_time = time.time()
            is_muted = display.is_snoozed  # This should use the cached version
            elapsed = time.time() - start_time
            times.append(elapsed)
            print(f"   Call {i+1:2d}: {elapsed:.4f}s - Muted: {is_muted}")
            
            if i < 9:  # Small delay between calls except the last
                time.sleep(0.1)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n📊 Performance Summary:")
        print(f"   Average: {avg_time:.4f}s")
        print(f"   Min:     {min_time:.4f}s") 
        print(f"   Max:     {max_time:.4f}s")
        
        if max_time < 0.01:
            print("   ✅ EXCELLENT: All calls under 0.01s")
        elif max_time < 0.1:
            print("   ✅ GOOD: All calls under 0.1s")
        elif max_time < 0.5:
            print("   ⚠️  ACCEPTABLE: Some calls under 0.5s")
        else:
            print("   ❌ SLOW: Some calls over 0.5s")
        
        # Test what happens when cache expires
        print(f"\n⏰ Testing cache expiration (waiting 6 seconds)...")
        time.sleep(6)
        
        start_time = time.time()
        is_muted = display.is_snoozed  # This should trigger a network refresh
        elapsed = time.time() - start_time
        print(f"   Cache refresh: {elapsed:.4f}s - Muted: {is_muted}")
        
        # Test immediate follow-up calls (should be fast again)
        print("\n⚡ Testing post-refresh cached calls:")
        for i in range(3):
            start_time = time.time()
            is_muted = display.is_snoozed
            elapsed = time.time() - start_time
            print(f"   Fast call {i+1}: {elapsed:.4f}s - Muted: {is_muted}")
        
        if app:
            app.quit()
            
    except Exception as e:
        print(f"❌ Error testing: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 Mute Button Performance Test - Optimized Version")
    print("=" * 60)
    
    test_mute_button_speed()
    
    print("\n" + "=" * 60)
    print("✅ Performance test complete!")

if __name__ == "__main__":
    main()
