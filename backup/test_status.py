#!/usr/bin/env python3
"""Test manifest status calculation"""

from scheduler import get_manifest_status
from datetime import datetime, timedelta

# Test the status calculation
test_time = datetime.now().replace(hour=12, minute=9, second=0, microsecond=0)
print(f"Testing at time: {test_time.strftime('%H:%M:%S')}")

# Test various manifest times
test_manifests = ["11:00", "12:10", "12:30", "13:45"]

for manifest_time in test_manifests:
    status = get_manifest_status(manifest_time, test_time)
    print(f"Manifest {manifest_time}: {status}")

print("\nDetailed timing analysis:")
print(f"Current test time: {test_time.strftime('%H:%M:%S')}")

# For 12:10 manifest at 12:09
manifest_dt = datetime.strptime("12:10", "%H:%M").replace(
    year=test_time.year, month=test_time.month, day=test_time.day
)
print(f"12:10 manifest datetime: {manifest_dt}")
print(f"Active window: {(manifest_dt - timedelta(minutes=2)).strftime('%H:%M')} to {(manifest_dt + timedelta(minutes=30)).strftime('%H:%M')}")
print(f"Time difference: {(test_time - manifest_dt).total_seconds()} seconds")
