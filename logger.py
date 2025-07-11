import os
import json
from datetime import datetime

def log_acknowledgment(manifest_time, carrier, status, reason=None):
    # Use configurable path from settings
    from settings_manager import get_settings_manager
    settings = get_settings_manager()
    log_path = settings.get_acknowledgments_path()
    
    # Ensure logs directory exists
    log_dir = os.path.dirname(log_path)
    os.makedirs(log_dir, exist_ok=True)
    
    # Get effective acknowledgment name (custom name or Windows username)
    settings = get_settings_manager()
    username = settings.get_effective_ack_name()
    
    today = datetime.now().date().isoformat()
    entry = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'date': today,
        'manifest_time': manifest_time,
        'carrier': carrier,
        'status': status,
        'acknowledged_by': username,
    }
    if reason:
        entry['reason'] = reason
    # Read existing log
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    else:
        data = []
    # Remove any existing entry for this date, time, and carrier
    data = [d for d in data if not (d.get('date') == today and d.get('manifest_time') == manifest_time and d.get('carrier') == carrier)]
    data.append(entry)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
