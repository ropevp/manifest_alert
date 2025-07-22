import json
import os
from datetime import datetime

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

def get_individual_carrier_status(carrier, manifest_time, date=None):
    """
    Returns individual acknowledgment status for a specific carrier
    Returns: dict with status info or None if not acknowledged
    """
    try:
        if date is None:
            date = datetime.now().date().isoformat()
        
        # Get ack.json path from settings
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        
        if data_folder and os.path.exists(data_folder):
            ack_path = os.path.join(data_folder, 'ack.json')
        else:
            ack_path = os.path.join(os.path.dirname(__file__), 'app_data', 'ack.json')
        
        if not os.path.exists(ack_path):
            return None
            
        with open(ack_path, 'r', encoding='utf-8') as f:
            ack_data = json.load(f)
        
        # Look for individual carrier acknowledgment
        for ack in ack_data:
            if (ack.get('date') == date and 
                ack.get('manifest_time') == manifest_time and 
                ack.get('carrier') == carrier):
                return {
                    'acknowledged': True,
                    'user': ack.get('user', 'Unknown'),
                    'reason': ack.get('reason', 'Done'),
                    'timestamp': ack.get('timestamp', '')
                }
        
        return None
        
    except Exception as e:
        print(f"Error getting individual carrier status: {e}")
        return None

def get_individual_carrier_ack_info(carrier, manifest_time, date=None):
    """
    Returns detailed acknowledgment information for a specific carrier
    Returns: dict with full acknowledgment details or None
    """
    try:
        if date is None:
            date = datetime.now().date().isoformat()
        
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        
        if data_folder and os.path.exists(data_folder):
            ack_path = os.path.join(data_folder, 'ack.json')
        else:
            ack_path = os.path.join(os.path.dirname(__file__), 'app_data', 'ack.json')
        
        if not os.path.exists(ack_path):
            return None
            
        with open(ack_path, 'r', encoding='utf-8') as f:
            ack_data = json.load(f)
        
        # Find the specific acknowledgment
        for ack in ack_data:
            if (ack.get('date') == date and 
                ack.get('manifest_time') == manifest_time and 
                ack.get('carrier') == carrier):
                return ack
        
        return None
        
    except Exception as e:
        print(f"Error getting individual carrier ack info: {e}")
        return None

def validate_individual_acknowledgment_data():
    """
    Validates that acknowledgment data structure supports individual operations
    Returns: dict with validation results
    """
    try:
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        
        if data_folder and os.path.exists(data_folder):
            ack_path = os.path.join(data_folder, 'ack.json')
        else:
            ack_path = os.path.join(os.path.dirname(__file__), 'app_data', 'ack.json')
        
        if not os.path.exists(ack_path):
            return {
                'valid': True,
                'message': 'No ack.json file exists yet - ready for individual acknowledgments',
                'individual_entries': 0,
                'sample_entry': None
            }
            
        with open(ack_path, 'r', encoding='utf-8') as f:
            ack_data = json.load(f)
        
        if not ack_data:
            return {
                'valid': True,
                'message': 'Empty ack.json - ready for individual acknowledgments',
                'individual_entries': 0,
                'sample_entry': None
            }
        
        # Check if entries have required fields for individual acknowledgments
        required_fields = ['date', 'manifest_time', 'carrier', 'user']
        sample_entry = ack_data[0] if ack_data else None
        
        valid = True
        missing_fields = []
        
        if sample_entry:
            for field in required_fields:
                if field not in sample_entry:
                    valid = False
                    missing_fields.append(field)
        
        return {
            'valid': valid,
            'message': f'Validation {"passed" if valid else "failed"}',
            'individual_entries': len(ack_data),
            'sample_entry': sample_entry,
            'missing_fields': missing_fields
        }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'Error validating acknowledgment data: {e}',
            'individual_entries': 0,
            'sample_entry': None
        }

def get_all_individual_acknowledgments_for_today(date=None):
    """
    Gets all individual acknowledgments for a specific date
    Returns: list of acknowledgment entries
    """
    try:
        if date is None:
            date = datetime.now().date().isoformat()
        
        from settings_manager import get_settings_manager
        settings = get_settings_manager()
        data_folder = settings.get_data_folder()
        
        if data_folder and os.path.exists(data_folder):
            ack_path = os.path.join(data_folder, 'ack.json')
        else:
            ack_path = os.path.join(os.path.dirname(__file__), 'app_data', 'ack.json')
        
        if not os.path.exists(ack_path):
            return []
            
        with open(ack_path, 'r', encoding='utf-8') as f:
            ack_data = json.load(f)
        
        # Filter for today's acknowledgments
        today_acks = []
        for ack in ack_data:
            if ack.get('date') == date:
                today_acks.append(ack)
        
        return today_acks
        
    except Exception as e:
        print(f"Error getting today's individual acknowledgments: {e}")
        return []

def test_individual_acknowledgment_system():
    """
    Comprehensive test of individual acknowledgment system
    Tests all Phase 1 methods and functionality
    """
    print("🔬 TESTING INDIVIDUAL ACKNOWLEDGMENT SYSTEM (Phase 1)")
    print("=" * 60)
    
    # Test 1: Validate data structure
    print("\n1. Testing data structure validation...")
    validation = validate_individual_acknowledgment_data()
    print(f"   ✅ Valid: {validation['valid']}")
    print(f"   📊 Individual entries: {validation['individual_entries']}")
    print(f"   💬 Message: {validation['message']}")
    
    # Test 2: Get all acknowledgments for today
    print("\n2. Testing today's acknowledgment retrieval...")
    today_acks = get_all_individual_acknowledgments_for_today()
    print(f"   📅 Found {len(today_acks)} acknowledgments for today")
    
    if today_acks:
        sample_ack = today_acks[0]
        print(f"   📋 Sample: {sample_ack.get('carrier')} at {sample_ack.get('manifest_time')} by {sample_ack.get('user')}")
    
    # Test 3: Test individual carrier status lookup
    print("\n3. Testing individual carrier status lookup...")
    if today_acks:
        test_carrier = today_acks[0].get('carrier')
        test_time = today_acks[0].get('manifest_time')
        
        status = get_individual_carrier_status(test_carrier, test_time)
        if status:
            print(f"   ✅ Found status for {test_carrier}")
            print(f"   👤 User: {status['user']}")
            print(f"   📝 Reason: {status['reason']}")
        else:
            print(f"   ❌ No status found for {test_carrier}")
    else:
        print("   ⏭️  No acknowledgments available for testing")
    
    # Test 4: Test detailed acknowledgment info
    print("\n4. Testing detailed acknowledgment info retrieval...")
    if today_acks:
        test_carrier = today_acks[0].get('carrier')
        test_time = today_acks[0].get('manifest_time')
        
        ack_info = get_individual_carrier_ack_info(test_carrier, test_time)
        if ack_info:
            print(f"   ✅ Found detailed info for {test_carrier}")
            print(f"   🕒 Timestamp: {ack_info.get('timestamp', 'N/A')}")
        else:
            print(f"   ❌ No detailed info found for {test_carrier}")
    else:
        print("   ⏭️  No acknowledgments available for testing")
    
    print("\n" + "=" * 60)
    print("🎯 PHASE 1 TESTING COMPLETE")
    print("=" * 60)
