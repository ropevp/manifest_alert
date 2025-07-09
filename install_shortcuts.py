#!/usr/bin/env python3
"""
Manifest Alert System - Shortcut Creator
Creates desktop and start menu shortcuts for the application
"""

import os
import sys
import winshell
from win32com.client import Dispatch

def create_shortcuts():
    """Create desktop and start menu shortcuts for Manifest Alert System"""
    
    # Get current directory and paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
    main_script = os.path.join(current_dir, "main.py")
    icon_path = os.path.join(current_dir, "resources", "icon.ico")
    
    # Verify files exist
    if not os.path.exists(python_exe):
        print(f"ERROR: Python executable not found at {python_exe}")
        print("Please ensure the virtual environment is created")
        return False
        
    if not os.path.exists(main_script):
        print(f"ERROR: Main script not found at {main_script}")
        return False
        
    if not os.path.exists(icon_path):
        print(f"WARNING: Icon not found at {icon_path}")
        icon_path = ""  # Will use default icon
    
    try:
        # Create desktop shortcut
        desktop = winshell.desktop()
        desktop_shortcut = os.path.join(desktop, "Manifest Alert System.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(desktop_shortcut)
        shortcut.Targetpath = python_exe
        shortcut.Arguments = f'"{main_script}"'
        shortcut.WorkingDirectory = current_dir
        shortcut.Description = "Manifest Alert System - Monitor and Alert"
        if icon_path:
            shortcut.IconLocation = icon_path
        shortcut.save()
        
        print(f"✅ Desktop shortcut created: {desktop_shortcut}")
        
        # Create start menu shortcut
        start_menu = winshell.start_menu()
        start_menu_folder = os.path.join(start_menu, "Programs", "Manifest Alert System")
        os.makedirs(start_menu_folder, exist_ok=True)
        
        start_menu_shortcut = os.path.join(start_menu_folder, "Manifest Alert System.lnk")
        
        shortcut = shell.CreateShortCut(start_menu_shortcut)
        shortcut.Targetpath = python_exe
        shortcut.Arguments = f'"{main_script}"'
        shortcut.WorkingDirectory = current_dir
        shortcut.Description = "Manifest Alert System - Monitor and Alert"
        if icon_path:
            shortcut.IconLocation = icon_path
        shortcut.save()
        
        print(f"✅ Start menu shortcut created: {start_menu_shortcut}")
        
        # Create uninstall shortcut in start menu
        uninstall_shortcut = os.path.join(start_menu_folder, "Uninstall Manifest Alert System.lnk")
        
        shortcut = shell.CreateShortCut(uninstall_shortcut)
        shortcut.Targetpath = "cmd.exe"
        shortcut.Arguments = f'/c cd /d "{current_dir}" && rmdir /s /q ".venv" && del /q "*.lnk" && echo Uninstalled successfully && pause'
        shortcut.WorkingDirectory = current_dir
        shortcut.Description = "Uninstall Manifest Alert System"
        shortcut.save()
        
        print(f"✅ Uninstall shortcut created: {uninstall_shortcut}")
        
        return True
        
    except Exception as e:
        print(f"ERROR creating shortcuts: {e}")
        return False

def main():
    """Main function"""
    print("Manifest Alert System - Shortcut Creator")
    print("=" * 45)
    
    if create_shortcuts():
        print("\n✅ All shortcuts created successfully!")
        print("\nYou can now launch Manifest Alert System from:")
        print("  • Desktop shortcut")
        print("  • Start Menu → Programs → Manifest Alert System")
        print("  • Windows search (type 'Manifest Alert')")
    else:
        print("\n❌ Failed to create shortcuts")
        sys.exit(1)

if __name__ == "__main__":
    main()
