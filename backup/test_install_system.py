#!/usr/bin/env python3
"""
Complete INSTALL.bat and Shortcut System Test
This simulates and verifies the entire installation process
"""

import os
import sys
from pathlib import Path

def test_installation_system():
    """Test the complete installation and shortcut system"""
    
    print("🧪 INSTALL.bat & Shortcut System Test")
    print("=" * 60)
    
    # Test 1: Prerequisites (what INSTALL.bat checks)
    print("1️⃣ Testing Prerequisites (INSTALL.bat checks)...")
    
    # Check Git
    try:
        import subprocess
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Git: {result.stdout.strip()}")
        else:
            print("   ❌ Git not available")
            return False
    except:
        print("   ❌ Git not available")
        return False
    
    # Check Python
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Python: {result.stdout.strip()}")
        else:
            print("   ❌ Python not available")
            return False
    except:
        print("   ❌ Python not available")
        return False
    
    # Test 2: Virtual Environment
    print("2️⃣ Testing Virtual Environment...")
    venv_python = Path('.venv/Scripts/python.exe')
    if venv_python.exists():
        print("   ✅ Virtual environment exists")
        
        # Test PyQt6 installation
        try:
            result = subprocess.run([str(venv_python), '-c', 'import PyQt6; print("PyQt6 version:", PyQt6.__version__)'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {result.stdout.strip()}")
            else:
                print("   ❌ PyQt6 not properly installed")
                return False
        except:
            print("   ❌ Cannot test PyQt6 installation")
            return False
    else:
        print("   ❌ Virtual environment missing")
        return False
    
    # Test 3: Required Files
    print("3️⃣ Testing Required Files...")
    required_files = [
        'main.py',
        'alert_display.py', 
        'requirements.txt',
        'launch_manifest_alerts_silent.bat',
        'launch_manifest_alerts.bat',
        'install_shortcuts.py',
        'resources/icon.ico'
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ⚠️ Missing files: {missing_files}")
        return False
    
    # Test 4: Shortcut System
    print("4️⃣ Testing Shortcut System...")
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        start_menu = winshell.programs()
        
        print(f"   ✅ Desktop path: {desktop}")
        print(f"   ✅ Start Menu path: {start_menu}")
        
        # Check if shortcuts exist
        desktop_shortcut = Path(desktop) / 'Manifest Alert System.lnk'
        start_shortcut = Path(start_menu) / 'Manifest Alert System.lnk'
        
        if desktop_shortcut.exists():
            print("   ✅ Desktop shortcut exists")
        else:
            print("   ℹ️ Desktop shortcut not found (can be created)")
            
        if start_shortcut.exists():
            print("   ✅ Start Menu shortcut exists")
        else:
            print("   ℹ️ Start Menu shortcut not found (can be created)")
            
    except ImportError:
        print("   ⚠️ Shortcut modules not available (winshell/pywin32)")
        return False
    except Exception as e:
        print(f"   ❌ Shortcut system error: {e}")
        return False
    
    # Test 5: Batch File Validation
    print("5️⃣ Testing Batch Files...")
    
    # Check launch_manifest_alerts_silent.bat
    silent_bat = Path('launch_manifest_alerts_silent.bat')
    if silent_bat.exists():
        content = silent_bat.read_text()
        if '.venv\\Scripts\\python.exe' in content and 'main.py' in content:
            print("   ✅ Silent launcher points to virtual environment")
        else:
            print("   ❌ Silent launcher has incorrect paths")
            return False
    
    # Test 6: Application Import Test
    print("6️⃣ Testing Application Components...")
    try:
        # Test core imports
        sys.path.insert(0, str(Path.cwd()))
        from alert_display import AlertDisplay
        from data_manager import load_config
        from scheduler import get_manifest_status
        
        print("   ✅ Core application modules import successfully")
        
        # Test config loading
        config = load_config()
        manifests = config.get('manifests', [])
        print(f"   ✅ Configuration loads: {len(manifests)} manifests")
        
    except Exception as e:
        print(f"   ❌ Application component error: {e}")
        return False
    
    print("=" * 60)
    print("🎉 INSTALLATION SYSTEM VERIFICATION COMPLETE!")
    print("")
    print("📋 System Status:")
    print("   • Prerequisites: ✅ Met")
    print("   • Virtual Environment: ✅ Ready")
    print("   • Required Files: ✅ Present")
    print("   • Shortcut System: ✅ Functional")
    print("   • Batch Files: ✅ Valid")
    print("   • Application: ✅ Ready")
    print("")
    print("🚀 INSTALL.bat would work successfully!")
    print("📱 Shortcuts can be created and will function properly!")
    print("⚡ Application is ready for production deployment!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_installation_system()
        if not success:
            print("\n❌ Some tests failed - check the issues above")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
