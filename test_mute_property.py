#!/usr/bin/env python3
"""
Minimal test to check if the issue is in the mute property checking
"""

import sys
import os

def test_mute_property():
    print("🔧 TESTING MUTE PROPERTY")
    print("=" * 40)
    
    try:
        print("1. Testing imports...")
        from alert_display import AlertDisplay
        from mute_manager import get_mute_manager
        print("   ✅ Imports successful")
        
        print("\n2. Testing mute manager...")
        manager = get_mute_manager()
        is_muted, muted_by = manager.is_currently_muted()
        print(f"   📝 Current mute status: {is_muted} by {muted_by}")
        
        print("\n3. Testing AlertDisplay instance creation...")
        app = AlertDisplay()
        print("   ✅ AlertDisplay created")
        
        print("\n4. Testing is_snoozed property...")
        snoozed = app.is_snoozed
        print(f"   📝 is_snoozed: {snoozed}")
        
        print("\n5. Testing mute_manager property...")
        app_manager = app.mute_manager
        print(f"   📝 app.mute_manager: {app_manager}")
        
        print("\n6. Testing toggle_snooze method exists...")
        if hasattr(app, 'toggle_snooze'):
            print("   ✅ toggle_snooze method exists")
        else:
            print("   ❌ toggle_snooze method missing")
            
        print("\n7. Simulating mute button click...")
        app.alert_active = True  # Simulate active alert
        print("   📝 Set alert_active = True")
        
        # Test the toggle_snooze method
        app.toggle_snooze()
        print("   ✅ toggle_snooze completed without crash")
        
        print("\n" + "=" * 40)
        print("✅ MUTE PROPERTY TEST COMPLETE")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mute_property()
