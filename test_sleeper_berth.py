#!/usr/bin/env python
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trucklog.settings')
django.setup()

from core.models import Trip
from core.services import calculate_route_and_logs

def test_sleeper_berth():
    # Create a test trip with sleeper berth enabled
    trip = Trip.objects.create(
        current_location='Green Bay, WI',
        pickup_location='Fond du Lac, WI',
        dropoff_location='Edwardsville, IL',
        current_cycle_hours=60.0,
        use_sleeper_berth=True
    )

    # Calculate logs
    result = calculate_route_and_logs(trip)

    # Print some key logs to verify sleeper berth splitting
    print('Trip created with sleeper berth enabled.')
    print('Logs with sleeper berth:')
    berth_logs = []
    for log in result['logs']:
        if log['status'] == 'Sleeper Berth' or 'Off-Duty after Berth' in log['remarks']:
            berth_logs.append(log)
            print(f"{log['status']}: {log['remarks']} - {log['start_time']} to {log['end_time']}")

    if berth_logs:
        print(f"Found {len(berth_logs)} sleeper berth related logs.")
    else:
        print("No sleeper berth logs found - check if 10-hour break triggered splitting.")

    print('Test completed.')

if __name__ == '__main__':
    test_sleeper_berth()
