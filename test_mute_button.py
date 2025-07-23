#!/usr/bin/env python3
"""
Debug script for mute button functionality
Tests the mute system in isolation
"""

import sys
import os

def test_mute_button():
    print("🔧 MUTE BUTTON DEBUG TEST")
    print("=" * 40)
    
    try:
        print("1. Testing mute_manager import...")
        from mute_manager import get_mute_manager
        print("   ✅ mute_manager imported successfully")
        
        print("\n2. Testing mute manager instance...")
        manager = get_mute_manager()
        print("   ✅ MuteManager instance created")
        
        print("\n3. Testing current mute status...")
        is_muted, muted_by = manager.is_currently_muted()
        print(f"   📝 Current status: muted={is_muted}, by={muted_by}")
        
        print("\n4. Testing mute toggle...")
        current_user = os.getenv('USERNAME', 'TestUser')
        new_state, message = manager.toggle_mute(current_user, 5)
        print(f"   📝 Toggle result: {message}")
        print(f"   📝 New state: {new_state}")
        
        print("\n5. Testing mute time remaining...")
        remaining = manager.get_mute_time_remaining()
        print(f"   📝 Time remaining: {remaining} minutes")
        
        print("\n6. Testing datetime import (used in countdown)...")
        import datetime as dt
        now = dt.datetime.now()
        end_time = now + dt.timedelta(minutes=5)
        print(f"   📝 Current time: {now}")
        print(f"   📝 End time: {end_time}")
        
        remaining_time = end_time - now
        total_seconds = int(remaining_time.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        print(f"   📝 Countdown: {minutes}m {seconds}s")
        
        print("\n7. Testing unmute...")
        new_state, message = manager.toggle_mute(current_user, 5)
        print(f"   📝 Unmute result: {message}")
        
        print("\n" + "=" * 40)
        print("✅ MUTE BUTTON DEBUG COMPLETE")
        print("\nIf all tests passed, the issue might be:")
        print("- QTimer conflicts in the main app")
        print("- Audio playback issues")
        print("- UI update conflicts")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mute_button()
