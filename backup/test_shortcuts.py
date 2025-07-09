#!/usr/bin/env python3
"""Test shortcut creation functionality"""

import os
import sys
from pathlib import Path

def test_shortcut_creation():
    """Test the shortcut creation process"""
    print("🧪 Testing Shortcut Creation")
    print("=" * 50)
    
    # Test 1: Check required modules
    print("1️⃣ Testing required modules...")
    try:
        import winshell
        print(f"   ✅ winshell imported - Desktop: {winshell.desktop()}")
    except ImportError:
        print("   ❌ winshell not available")
        return False
        
    try:
        from win32com.client import Dispatch
        print("   ✅ win32com.client imported")
    except ImportError:
        print("   ❌ win32com.client not available")
        return False
    
    # Test 2: Check required files
    print("2️⃣ Testing required files...")
    script_dir = Path(__file__).parent.absolute()
    
    batch_file = script_dir / 'launch_manifest_alerts_silent.bat'
    if batch_file.exists():
        print(f"   ✅ Batch file found: {batch_file}")
    else:
        print(f"   ❌ Batch file missing: {batch_file}")
        return False
    
    icon_file = script_dir / 'resources' / 'icon.ico'
    if icon_file.exists():
        print(f"   ✅ Icon file found: {icon_file}")
    else:
        print(f"   ⚠️  Icon file missing: {icon_file}")
    
    # Test 3: Create test shortcut
    print("3️⃣ Testing shortcut creation...")
    try:
        desktop = winshell.desktop()
        test_shortcut_path = os.path.join(desktop, 'TEST_Manifest_Alert.lnk')
        
        # Clean up any existing test shortcut
        if os.path.exists(test_shortcut_path):
            os.remove(test_shortcut_path)
        
        # Create test shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(test_shortcut_path)
        
        shortcut.Targetpath = str(batch_file)
        shortcut.WorkingDirectory = str(script_dir)
        if icon_file.exists():
            shortcut.IconLocation = str(icon_file)
        shortcut.Description = 'TEST - Manifest Alert System'
        
        shortcut.save()
        
        # Verify creation
        if os.path.exists(test_shortcut_path):
            print(f"   ✅ Test shortcut created: {test_shortcut_path}")
            
            # Clean up test shortcut
            os.remove(test_shortcut_path)
            print("   ✅ Test shortcut cleaned up")
            return True
        else:
            print("   ❌ Test shortcut creation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Shortcut creation error: {e}")
        return False
    
    return True

def test_actual_installer():
    """Test the actual install_shortcuts.py functionality"""
    print("\n4️⃣ Testing actual installer...")
    try:
        # Import the installer functions
        from install_shortcuts import create_desktop_shortcut, create_start_menu_shortcut
        
        print("   📋 Testing desktop shortcut creation...")
        desktop_result = create_desktop_shortcut()
        
        print("   📋 Testing start menu shortcut creation...")
        start_menu_result = create_start_menu_shortcut()
        
        if desktop_result and start_menu_result:
            print("   ✅ Both shortcuts created successfully!")
            return True
        else:
            print(f"   ⚠️  Partial success: Desktop={desktop_result}, StartMenu={start_menu_result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Installer test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        # Run basic tests
        basic_test = test_shortcut_creation()
        
        if basic_test:
            # Run actual installer test
            installer_test = test_actual_installer()
            
            print("\n" + "=" * 50)
            if basic_test and installer_test:
                print("🎉 ALL SHORTCUT TESTS PASSED!")
                print("\nShortcuts should now be available:")
                print("   • Desktop: 'Manifest Alert System.lnk'")
                print("   • Start Menu: 'Manifest Alert System.lnk'")
            else:
                print("⚠️  SOME TESTS FAILED")
        else:
            print("\n❌ Basic tests failed - shortcut creation not possible")
            
    except Exception as e:
        print(f"\n💥 Test script error: {e}")
        import traceback
        traceback.print_exc()
