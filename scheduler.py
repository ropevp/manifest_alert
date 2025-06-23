from datetime import datetime, timedelta
from data_manager import load_config

def get_manifest_status(manifest_time_str, now=None):
    if now is None:
        now = datetime.now()
    today = now.date()
    manifest_time = datetime.strptime(manifest_time_str, "%H:%M").replace(year=today.year, month=today.month, day=today.day)
    active_start = manifest_time - timedelta(minutes=2)
    active_end = manifest_time + timedelta(minutes=30)

    if active_start <= now < active_end:
        return "Active"
    elif now >= active_end:
        return "Missed"
    else:
        return "Pending"

if __name__ == "__main__":
    config = load_config()
    manifests = config.get('manifests', [])
    now = datetime.now()
    print(f"Current time: {now.strftime('%H:%M')}")
    for m in manifests:
        status = get_manifest_status(m['time'], now)
        print(f"Time: {m['time']}, Carrier: {m['carrier']}, Status: {status}")
