from scheduler import get_manifest_status
from datetime import datetime

now = datetime.now()
print(f"Current time: {now.strftime('%H:%M:%S')}")
print()

manifests = ["11:00", "12:30", "12:36", "12:38", "13:45", "14:30"]
for time_str in manifests:
    status = get_manifest_status(time_str, now)
    print(f"{time_str}: {status}")
