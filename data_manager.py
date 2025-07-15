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
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Config Error", f"Config file is invalid and was backed up as {config_path}.bak: {e}")
        return {"manifests": []}

def load_reasons(reasons_path=None):
    """Load reasons from shared folder reasons.json"""
    if reasons_path is None:
        # Use settings manager to get data folder path
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        reasons_path = os.path.join(data_folder, 'reasons.json')
    
    try:
        with open(reasons_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default reasons file
        default_reasons = {
            "reasons": [
                "Truck Arrived Late",
                "Manifest Cancelled",
                "Manifest Not Working",
                "Manifest Done",
                "System Issue"
            ]
        }
        try:
            os.makedirs(os.path.dirname(reasons_path), exist_ok=True)
            with open(reasons_path, 'w', encoding='utf-8') as f:
                json.dump(default_reasons, f, indent=2)
            print(f"Created default reasons file: {reasons_path}")
        except Exception as e:
            print(f"Could not create default reasons file: {e}")
        return default_reasons
    except Exception as e:
        print(f"Error loading reasons: {e}")
        return {"reasons": []}

def save_reasons(reasons_data, reasons_path=None):
    """Save reasons to shared folder reasons.json"""
    if reasons_path is None:
        # Use settings manager to get data folder path
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        reasons_path = os.path.join(data_folder, 'reasons.json')
    
    try:
        os.makedirs(os.path.dirname(reasons_path), exist_ok=True)
        with open(reasons_path, 'w', encoding='utf-8') as f:
            json.dump(reasons_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving reasons: {e}")
        return False

def add_new_reason(new_reason, reasons_path=None):
    """Add a new reason to the reasons.json file"""
    reasons_data = load_reasons(reasons_path)
    if new_reason not in reasons_data.get('reasons', []):
        reasons_data['reasons'].append(new_reason)
        return save_reasons(reasons_data, reasons_path)
    return True  # Already exists

def save_acknowledgment_with_reason(date, manifest_time, carrier, user, reason, timestamp, ack_path=None):
    """Save acknowledgment with reason and reason_history support"""
    if ack_path is None:
        # Use settings manager to get data folder path
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        ack_path = os.path.join(data_folder, 'ack.json')
    
    # Load existing acknowledgments
    try:
        with open(ack_path, 'r', encoding='utf-8') as f:
            ack_data = json.load(f)
    except FileNotFoundError:
        ack_data = []
    except Exception as e:
        print(f"Error loading acknowledgments: {e}")
        ack_data = []
    
    # Find existing acknowledgment for this carrier
    existing_ack = None
    for ack in ack_data:
        if (ack.get('date') == date and 
            ack.get('manifest_time') == manifest_time and 
            ack.get('carrier') == carrier):
            existing_ack = ack
            break
    
    if existing_ack:
        # Update existing acknowledgment
        if 'reason_history' not in existing_ack:
            existing_ack['reason_history'] = []
        
        # Add new reason to history
        reason_entry = {
            'reason': reason,
            'timestamp': timestamp,
            'user': user
        }
        existing_ack['reason_history'].append(reason_entry)
        
        # Update main fields
        existing_ack['reason'] = reason
        existing_ack['timestamp'] = timestamp
        existing_ack['user'] = user
    else:
        # Create new acknowledgment
        ack_entry = {
            'date': date,
            'manifest_time': manifest_time,
            'carrier': carrier,
            'user': user,
            'reason': reason,
            'timestamp': timestamp,
            'reason_history': [{
                'reason': reason,
                'timestamp': timestamp,
                'user': user
            }] if reason else []
        }
        ack_data.append(ack_entry)
    
    # Save to file
    try:
        with open(ack_path, 'w', encoding='utf-8') as f:
            json.dump(ack_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving acknowledgment: {e}")
        return False

def migrate_existing_acknowledgments(ack_path=None):
    """Migrate existing acknowledgments to new structure with reason_history"""
    if ack_path is None:
        # Use settings manager to get data folder path
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        ack_path = os.path.join(data_folder, 'ack.json')
    
    try:
        with open(ack_path, 'r', encoding='utf-8') as f:
            ack_data = json.load(f)
    except FileNotFoundError:
        return True  # No file to migrate
    except Exception as e:
        print(f"Error loading acknowledgments for migration: {e}")
        return False
    
    # Migrate each acknowledgment
    for ack in ack_data:
        if 'reason_history' not in ack:
            # Create reason_history from existing reason
            reason = ack.get('reason', '')
            timestamp = ack.get('timestamp', '')
            user = ack.get('user', '')
            
            if reason:
                ack['reason_history'] = [{
                    'reason': reason,
                    'timestamp': timestamp,
                    'user': user
                }]
            else:
                ack['reason_history'] = []
    
    # Save migrated data
    try:
        with open(ack_path, 'w', encoding='utf-8') as f:
            json.dump(ack_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving migrated acknowledgments: {e}")
        return False

if __name__ == "__main__":
    config = load_config()
    manifests = config.get('manifests', [])
    print("Loaded manifests:")
    for m in manifests:
        print(f"Time: {m['time']}, Carrier: {m['carrier']}")
