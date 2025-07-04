import sys
import os
import subprocess
from pathlib import Path

def create_desktop_shortcut():
    """Create a desktop shortcut for the Manifest Alert System"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # Get paths
        desktop = winshell.desktop()
        script_dir = Path(__file__).parent.absolute()
        shortcut_path = os.path.join(desktop, 'Manifest Alert System.lnk')
        
        # Check if shortcut already exists
        if os.path.exists(shortcut_path):
            print(f"ℹ️  Updating existing desktop shortcut...")
        else:
            print(f"✅ Creating new desktop shortcut...")
        
        # Create shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        
        # Set shortcut properties
        shortcut.Targetpath = str(script_dir / 'launch_manifest_alerts_silent.bat')
        shortcut.WorkingDirectory = str(script_dir)
        shortcut.IconLocation = str(script_dir / 'resources' / 'icon.ico')
        shortcut.Description = 'Manifest Alert System - Warehouse Alert Monitor'
        
        # Save shortcut
        shortcut.save()
        
        print("✅ Desktop shortcut ready!")
        print(f"Shortcut location: {desktop}")
        return True
        
    except ImportError:
        print("❌ Missing required modules for shortcut creation")
        print("Run: pip install pywin32 winshell")
        return False
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        return False

def create_start_menu_shortcut():
    """Create a Start Menu shortcut"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # Get Start Menu programs folder
        start_menu = winshell.programs()
        script_dir = Path(__file__).parent.absolute()
        shortcut_path = os.path.join(start_menu, 'Manifest Alert System.lnk')
        
        # Check if shortcut already exists
        if os.path.exists(shortcut_path):
            print(f"ℹ️  Updating existing Start Menu shortcut...")
        else:
            print(f"✅ Creating new Start Menu shortcut...")
        
        # Create shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        
        # Set shortcut properties
        shortcut.Targetpath = str(script_dir / 'launch_manifest_alerts_silent.bat')
        shortcut.WorkingDirectory = str(script_dir)
        shortcut.IconLocation = str(script_dir / 'resources' / 'icon.ico')
        shortcut.Description = 'Manifest Alert System - Warehouse Alert Monitor'
        
        # Save shortcut
        shortcut.save()
        
        print("✅ Start Menu shortcut ready!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating Start Menu shortcut: {e}")
        return False

def install_shortcuts(silent_mode=False):
    """Install both desktop and start menu shortcuts"""
    if not silent_mode:
        print("🚀 Manifest Alert System - Shortcut Installer")
        print("=" * 50)
    
    # Check if required modules are available
    try:
        import winshell
        import win32com.client
    except ImportError:
        print("Installing required modules for shortcut creation...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pywin32', 'winshell'])
        print("✅ Modules installed successfully!")
    
    success_count = 0
    
    # Create desktop shortcut
    if not silent_mode:
        print("\n📋 Creating desktop shortcut...")
    if create_desktop_shortcut():
        success_count += 1
    
    # Create start menu shortcut
    if not silent_mode:
        print("\n📋 Creating Start Menu shortcut...")
    if create_start_menu_shortcut():
        success_count += 1
    
    if not silent_mode:
        print("\n" + "=" * 50)
        if success_count == 2:
            print("🎉 Installation complete!")
            print("\nYou can now launch Manifest Alert System from:")
            print("   • Desktop shortcut")
            print("   • Start Menu")
            print("   • Windows Search (type 'Manifest Alert')")
        else:
            print(f"⚠️  Partial installation: {success_count}/2 shortcuts created")
        
        input("\nPress Enter to exit...")
    else:
        # Silent mode - just return status
        return success_count == 2

if __name__ == "__main__":
    # Check if we're being called from command line or installer
    import sys
    silent = len(sys.argv) > 1 and sys.argv[1] == "--silent"
    install_shortcuts(silent_mode=silent)
