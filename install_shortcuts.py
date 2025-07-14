import os
import sys
from pathlib import Path

try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    print("Required modules not found. Please install 'winshell' and 'pywin32'.")
    sys.exit(1)

def create_shortcut(target_path, target_args, shortcut_path, icon=None):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = target_path
    shortcut.Arguments = target_args
    shortcut.WorkingDirectory = str(Path(target_path).parent)
    if icon:
        shortcut.IconLocation = str(icon)
    shortcut.save()

def main():
    app_name = "Manifest Alert"
    target = Path(__file__).parent / "main.py"
    python_exe = Path(sys.executable)
    shortcut_dir = Path(os.path.expanduser(r"~\Desktop"))
    shortcut_path = shortcut_dir / f"{app_name}.lnk"
    icon_path = Path(__file__).parent / "resources" / "icon.ico"  # Use the application icon

    # Shortcut will run: python main.py
    create_shortcut(str(python_exe), f'"{target}"', shortcut_path, icon=icon_path)
    print(f"Shortcut created at {shortcut_path}")

if __name__ == "__main__":
    main()
