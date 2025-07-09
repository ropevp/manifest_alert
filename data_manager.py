import json
import os

def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
    import shutil
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Config Error", f"Config file not found: {config_path}")
        return {"manifests": []}
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
