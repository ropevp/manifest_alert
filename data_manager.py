import json
import os

def load_config(config_path=None):
    if config_path is None:
        # Use settings manager to get configurable path
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        config_path = settings.get_config_path()
    
    import shutil
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default config file on first run
        default_config = {"manifests": []}
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config file: {config_path}")
        except Exception as e:
            print(f"Could not create default config file: {e}")
        return default_config
    except Exception as e:
        # Backup the corrupted file
        try:
            backup_path = config_path + ".bak"
            shutil.copyfile(config_path, backup_path)
        except Exception:
            pass
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Config Error", f"Config file is invalid and was backed up as {config_path}.bak: {e}")
        return {"manifests": []}

if __name__ == "__main__":
    config = load_config()
    manifests = config.get('manifests', [])
    print("Loaded manifests:")
    for m in manifests:
        print(f"Time: {m['time']}, Carrier: {m['carrier']}")
