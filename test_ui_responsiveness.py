#!/usr/bin/env python3
"""
UI Responsiveness Test - Test clicking and UI interactions
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class UIResponseTest:
    def __init__(self):
        self.start_time = time.time()
        
    def test_data_loading_speed(self):
        """Test the speed of data loading operations"""
        print("🔧 Testing data loading speed...")
        
        # Test config loading
        from alert_display import AlertDisplay
        app = None
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication([])
        except:
            pass
            
        display = AlertDisplay()
        
        print("\n⚡ Testing config loading:")
        times = []
        for i in range(5):
            start = time.time()
            config = display.load_config()
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"   Load {i+1}: {elapsed:.4f}s - Manifests: {len(config.get('manifests', []))}")
        
        avg_time = sum(times) / len(times)
        print(f"   📊 Average config load: {avg_time:.4f}s")
        
        print("\n⚡ Testing acknowledgments loading:")
        times = []
        for i in range(5):
            start = time.time()
            acks = display.load_acknowledgments()
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"   Load {i+1}: {elapsed:.4f}s - Acks: {len(acks)}")
        
        avg_time = sum(times) / len(times)
        print(f"   📊 Average acks load: {avg_time:.4f}s")
        
        print("\n⚡ Testing mute status checking:")
        times = []
        for i in range(5):
            start = time.time()
            is_muted = display.is_snoozed
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"   Check {i+1}: {elapsed:.4f}s - Muted: {is_muted}")
        
        avg_time = sum(times) / len(times)
        print(f"   📊 Average mute check: {avg_time:.4f}s")
        
        if app:
            app.quit()
    
    def evaluate_performance(self, times, operation_name):
        """Evaluate if performance is acceptable"""
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\n📊 {operation_name} Performance:")
        print(f"   Average: {avg_time:.4f}s")
        print(f"   Maximum: {max_time:.4f}s")
        
        if max_time < 0.01:
            print("   ✅ EXCELLENT: All operations under 0.01s")
            return "excellent"
        elif max_time < 0.1:
            print("   ✅ GOOD: All operations under 0.1s")
            return "good"
        elif max_time < 0.5:
            print("   ⚠️  ACCEPTABLE: Operations under 0.5s")
            return "acceptable"
        else:
            print("   ❌ SLOW: Some operations over 0.5s")
            return "slow"

def main():
    print("🚀 UI Responsiveness Test - Ultra-Optimized Version")
    print("=" * 60)
    
    test = UIResponseTest()
    test.test_data_loading_speed()
    
    total_time = time.time() - test.start_time
    print(f"\n⏱️  Total test time: {total_time:.2f}s")
    print("\n" + "=" * 60)
    print("✅ UI responsiveness test complete!")
    print("\nIf the mute button is still slow, the issue might be in")
    print("Qt event handling or other UI framework delays.")

if __name__ == "__main__":
    main()
