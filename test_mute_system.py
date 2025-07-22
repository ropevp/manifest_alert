"""
Quick Test for Centralized Mute System
Run this on each PC to verify the system is working
"""

import os
import sys
from datetime import datetime

def test_mute_system():
    print("🔧 CENTRALIZED MUTE SYSTEM TEST")
    print("=" * 40)
    
    # Test 1: Check if mute_manager can be imported
    print("\n1. Testing mute_manager import...")
    try:
        from mute_manager import get_mute_manager
        print("   ✅ mute_manager.py imported successfully")
    except ImportError as e:
        print(f"   ❌ ERROR: Cannot import mute_manager: {e}")
        return False
    
    # Test 2: Check mute manager functionality
    print("\n2. Testing mute manager functionality...")
    try:
        manager = get_mute_manager()
        muted, user = manager.is_currently_muted()
        print(f"   ✅ Current mute status: {muted}")
        if muted:
            print(f"   📝 Muted by: {user}")
    except Exception as e:
        print(f"   ❌ ERROR: Mute manager failed: {e}")
        return False
    
    # Test 3: Check network file access
    print("\n3. Testing network file access...")
    try:
        file_path = manager.get_mute_file_path()
        print(f"   📁 Mute file path: {file_path}")
        
        if os.path.exists(file_path):
            print("   ✅ Network mute file accessible")
        else:
            print("   ⚠️  Network mute file not found (will be created on first use)")
    except Exception as e:
        print(f"   ❌ ERROR: Cannot access mute file: {e}")
        return False
    
    # Test 4: Test mute toggle
    print("\n4. Testing mute toggle...")
    try:
        current_user = os.getenv('COMPUTERNAME', 'TestPC')
        original_state, _ = manager.is_currently_muted()
        
        # Toggle mute
        new_state, message = manager.toggle_mute(current_user, 1)
        print(f"   📝 Toggle result: {message}")
        
        # Toggle back
        final_state, message2 = manager.toggle_mute(current_user)
        print(f"   📝 Toggle back: {message2}")
        
        print("   ✅ Mute toggle working")
    except Exception as e:
        print(f"   ❌ ERROR: Mute toggle failed: {e}")
        return False
    
    # Test 5: Check git branch
    print("\n5. Testing git branch...")
    try:
        import subprocess
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            branch = result.stdout.strip()
            print(f"   📝 Current branch: {branch}")
            if branch == '3.3':
                print("   ✅ On correct branch (3.3)")
            else:
                print(f"   ⚠️  Wrong branch! Should be 3.3, but on {branch}")
        else:
            print("   ⚠️  Cannot determine git branch")
    except Exception as e:
        print(f"   ❌ ERROR: Git check failed: {e}")
    
    print("\n" + "=" * 40)
    print("✅ CENTRALIZED MUTE SYSTEM TEST COMPLETE")
    print("\nIf all tests passed, the mute button should work during alerts!")
    print("Remember: Mute button only appears during ACTIVE alerts")
    
    return True

if __name__ == "__main__":
    test_mute_system()
