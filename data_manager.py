import json
import os

def get_config_path():
    """Get the correct path for config.json using main settings"""
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                data_folder = settings.get('data_folder', '')
                
                if data_folder and os.path.exists(data_folder):
                    return os.path.join(data_folder, 'config.json')
                else:
                    print(f"WARNING: data_folder '{data_folder}' not found")
    except Exception as e:
        print(f"Error loading settings: {e}")
    
    # Fallback - should not happen in normal operation
    return os.path.join(os.path.dirname(__file__), 'config.json')

def load_config(config_path=None):
    if config_path is None:
        config_path = get_config_path()
    
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
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Config Error", f"Config file is invalid and was backed up as {config_path}.bak: {e}")
        return {"manifests": []}

if __name__ == "__main__":
    config = load_config()
    manifests = config.get('manifests', [])
    print("Loaded manifests:")
    for m in manifests:
        print(f"Time: {m['time']}, Carrier: {m['carrier']}")
