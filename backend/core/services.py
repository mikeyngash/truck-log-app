from geopy.distance import geodesic
from datetime import datetime, timedelta, time, date
import random
from .models import LogEntry
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from collections import defaultdict
from .routing import router

THIRTY_MIN = 30

ELEVEN_HOURS_MIN = 11 * 60
FOURTEEN_HOURS_MIN = 14 * 60

STATUS_KEYS = {
    "Off-Duty": "off",
    "Sleeper Berth": "sleeper",
    "Driving": "driving",
    "On-Duty": "onduty",
    "On-Duty (Not Driving)": "onduty",
}

def _min_to_hours(m):
    return round(m / 60.0, 2)

def _min_between(start, end):
    H,M,S = map(int, start.split(":"))
    h2,m2,s2 = map(int, end.split(":"))
    return (h2*60 + m2 + s2/60) - (H*60 + M + S/60)

def _as_hms(v):
    return v if isinstance(v, str) else v.strftime("%H:%M:%S")

def _merge_off_blocks(entries):
    entries = sorted(entries, key=lambda e: (e['date'], _as_hms(e['start_time'] or "00:00:00")))
    out = []
    for e in entries:
        st = _as_hms(e['start_time']) if e['start_time'] else "00:00:00"
        en = _as_hms(e['end_time']) if e['end_time'] else "00:00:00"

        if not out:
            out.append({**e, 'start_time': st, 'end_time': en})
            continue

        prev = out[-1]
        pst, pen = _as_hms(prev['start_time']), _as_hms(prev['end_time'])

        mergeable = (
            e['status'] in ('Off-Duty','Sleeper Berth') and
            prev['status'] in ('Off-Duty','Sleeper Berth') and
            prev['date'] == e['date'] and
            st <= pen  # overlapping or touching
        )

        if mergeable:
            # extend end time
            if en > pen:
                prev['end_time'] = en
            # combine remarks neatly (avoid exact duplicates)
            if e.get('remarks'):
                if prev.get('remarks') and e['remarks'] not in prev['remarks']:
                    prev['remarks'] = f"{prev['remarks']} / {e['remarks']}"
                elif not prev.get('remarks'):
                    prev['remarks'] = e['remarks']
            # miles remain 0 for off-duty/sleeper
        else:
            out.append({**e, 'start_time': st, 'end_time': en})
    return out

def _ensure_full_day(day, items):
    """Guarantee 00:00–24:00 coverage with Off-Duty fillers if needed, and merge overlapping off-duty periods."""
    items.sort(key=lambda x: x["start_time"])
    
    # First, merge overlapping off-duty/sleeper berth entries
    merged = []
    for item in items:
        if not merged:
            merged.append(item)
            continue
        
        last = merged[-1]
        # Check if current item overlaps with last item and both are off-duty/sleeper
        if (item["status"] in ("Off-Duty", "Sleeper Berth") and 
            last["status"] in ("Off-Duty", "Sleeper Berth") and
            item["start_time"] <= last["end_time"]):
            # Merge: extend the end time and combine remarks
            if item["end_time"] > last["end_time"]:
                last["end_time"] = item["end_time"]
            # Combine remarks if different
            if item.get("remarks") and item["remarks"] not in last.get("remarks", ""):
                if last.get("remarks"):
                    last["remarks"] = f"{last['remarks']} / {item['remarks']}"
                else:
                    last["remarks"] = item["remarks"]
        else:
            merged.append(item)
    
    items = merged
    
    # Fill gaps at start and end
    if items[0]["start_time"] != "00:00:00":
        items.insert(0, {
            "date": day, "status": "Off-Duty",
            "start_time": "00:00:00", "end_time": items[0]["start_time"],
            "remarks": "Home terminal time base", "miles": 0
        })
    if items[-1]["end_time"] not in ("23:59:59", "24:00:00"):
        items.append({
            "date": day, "status": "Off-Duty",
            "start_time": items[-1]["end_time"], "end_time": "23:59:59",
            "remarks": "", "miles": 0
        })
    return items

def _hos_flags(entries):
    """Return list of HOS violations using MINUTES thresholds."""
    flags = []
    driving_since_reset = 0
    first_on_duty_after_reset = None
    driving_since_break = 0

    for e in entries:
        dur = int(round(_min_between(e["start_time"], e["end_time"])))
        is_break = e["status"] in ("Off-Duty", "Sleeper Berth")

        if e["status"].startswith("On-Duty") and first_on_duty_after_reset is None:
            first_on_duty_after_reset = e["start_time"]

        if e["status"] == "Driving":
            driving_since_reset += dur
            driving_since_break += dur
            if driving_since_reset > ELEVEN_HOURS_MIN:
                flags.append("Exceeded 11-hour driving limit")
        else:
            if driving_since_break >= 8*60 and is_break and dur >= THIRTY_MIN:
                driving_since_break = 0
            if is_break and dur >= 10*60:
                driving_since_reset = 0
                driving_since_break = 0
                first_on_duty_after_reset = None

        if first_on_duty_after_reset:
            H,M,S = map(int, first_on_duty_after_reset.split(":"))
            endH,endM,endS = map(int, e["end_time"].split(":"))
            window = (endH*60 + endM) - (H*60 + M)
            if window > FOURTEEN_HOURS_MIN:
                flags.append("Exceeded 14-hour on-duty window")
                first_on_duty_after_reset = None

    return sorted(set(flags))

def compute_daily_totals(logs):
    daily_totals = {}
    for log in logs:
        if log['status'] == 'Total':
            continue
        day = log['date']
        if day not in daily_totals:
            daily_totals[day] = {'totals': {'driving': 0, 'on_duty_not_driving': 0, 'off_duty': 0, 'sleeper': 0, 'lines_3_4_total': 0}}
        status = log['status']
        start = log['start_time']
        end = log['end_time']
        if isinstance(start, str):
            start = datetime.strptime(start, "%H:%M:%S").time()
        if isinstance(end, str):
            end = datetime.strptime(end, "%H:%M:%S").time()
        duration = (datetime.combine(date.today(), end) - datetime.combine(date.today(), start)).total_seconds() / 3600
        if status == 'Driving':
            daily_totals[day]['totals']['driving'] += duration
        elif status == 'On-Duty':
            daily_totals[day]['totals']['on_duty_not_driving'] += duration
        elif status == 'Off-Duty':
            daily_totals[day]['totals']['off_duty'] += duration
        elif status == 'Sleeper Berth':
            daily_totals[day]['totals']['sleeper'] += duration
        daily_totals[day]['totals']['lines_3_4_total'] = daily_totals[day]['totals']['driving'] + daily_totals[day]['totals']['on_duty_not_driving']
    return daily_totals

def normalize_and_summarize(logs):
    """
    Input: list of log dicts (no 'Total' rows).
    Output: (new_logs_with_totals, hos_compliant, violations)
    - Splits data by date
    - Ensures 00:00–24:00 coverage per day
    - Computes totals (hours) and appends a 'Total' row per day
    - Validates HOS using minute thresholds
    """
    by_day = defaultdict(list)
    for e in logs:
        by_day[e["date"]].append(e)

    out_logs = []
    all_flags = []

    for day in sorted(by_day.keys()):
        day_items = _ensure_full_day(day, by_day[day])

        # minutes accumulation
        mins = dict(off=0, sleeper=0, driving=0, onduty=0)
        for e in day_items:
            m = int(round(_min_between(e["start_time"], e["end_time"])))
            key = STATUS_KEYS.get(e["status"])
            if key: mins[key] += m

        # HOS flags for this day’s shift sequence
        all_flags.extend(_hos_flags(day_items))

        # append normalized entries
        out_logs.extend(day_items)

        # human-readable totals in HOURS
        totals = {
            "off_duty": _min_to_hours(mins["off"]),
            "sleeper": _min_to_hours(mins["sleeper"]),
            "driving": _min_to_hours(mins["driving"]),
            "onduty": _min_to_hours(mins["onduty"]),
            "line34": _min_to_hours(mins["driving"] + mins["onduty"]),
            "sum24": _min_to_hours(sum(mins.values())),
        }
        out_logs.append({
            "date": day, "status": "Total",
            "start_time": None, "end_time": None,
            "remarks": (f"Daily Total - Lines 3+4: {totals['line34']} hrs "
                        f"(Driving: {totals['driving']} hrs, "
                        f"On-Duty Not Driving: {totals['onduty']} hrs), "
                        f"Off-Duty: {totals['off_duty']} hrs, "
                        f"Sleeper Berth: {totals['sleeper']} hrs"),
            "miles": 0
        })

    violations = sorted(set(all_flags))
    return out_logs, (len(violations) == 0), violations

def calculate_route_and_logs(trip):
    # Use stored coordinates
    locations = {
        trip.current_location: trip.current_location_coords,
        trip.pickup_location: trip.pickup_location_coords,
        trip.dropoff_location: trip.dropoff_location_coords,
    }
    
    # Get routes using OSRM
    route_to_pickup = router.get_route(locations[trip.current_location], locations[trip.pickup_location])
    route_to_dropoff = router.get_route(locations[trip.pickup_location], locations[trip.dropoff_location])
    
    if not route_to_pickup or not route_to_dropoff:
        # Fallback to geodesic distance if routing fails
        distance_to_pickup = geodesic(locations[trip.current_location], locations[trip.pickup_location]).miles
        distance_to_dropoff = geodesic(locations[trip.pickup_location], locations[trip.dropoff_location]).miles
        total_distance = distance_to_pickup + distance_to_dropoff
        route_coordinates = [locations[trip.current_location], locations[trip.pickup_location], locations[trip.dropoff_location]]
    else:
        # Use OSRM distances and combine route coordinates
        distance_to_pickup = route_to_pickup["distance"]
        distance_to_dropoff = route_to_dropoff["distance"]
        total_distance = distance_to_pickup + distance_to_dropoff
        
        # Combine coordinates for the full route
        route_coordinates = route_to_pickup["coordinates"]
        # Avoid duplicating the pickup location
        route_coordinates.extend(route_to_dropoff["coordinates"][1:])

    # Enforce 14-hour window: Start after 10 consecutive off-duty hours
    # Assume driver has had 10 hours off-duty before starting
    current_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)  # Start at 6 AM
    window_end = current_time + timedelta(hours=14)  # 14-hour window ends at 8 PM

    driving_hours = 0
    cumulative_driving_hours = 0  # Track cumulative driving for 30-min break
    on_duty_hours = float(trip.current_cycle_hours)
    next_allowed_onduty = current_time  # Earliest time we may be on-duty again

    # Initialize rolling 8-day window with simulated historical on-duty hours
    # Distribute current_cycle_hours across the past 7 days, with some variation
    historical_days = 7
    base_daily_hours = trip.current_cycle_hours / historical_days
    rolling_window = []
    for i in range(historical_days):
        # Add some random variation (±2 hours) but ensure non-negative
        variation = random.uniform(-2, 2)
        daily_hours = max(0, base_daily_hours + variation)
        rolling_window.append(daily_hours)
    # Current day starts at 0
    rolling_window.append(0.0)  # Index 7 is current day

    cycle_hours_8_day = sum(rolling_window)  # Initial rolling total

    logs = []
    daily_totals = {}  # Track daily totals
    total_miles_driven = 0  # Track total miles for fueling

    def add_log_entry(status, duration_minutes, remarks, miles=0, skip_limit_check=False):
        nonlocal current_time, driving_hours, cumulative_driving_hours, on_duty_hours, cycle_hours_8_day, rolling_window, total_miles_driven, window_end

        # Check 11-hour driving limit BEFORE adding driving time (only if not skipping)
        if status == 'Driving' and not skip_limit_check:
            hours_to_add = duration_minutes / 60.0
            if driving_hours + hours_to_add > 11:
                # Can only drive up to 11 hours
                allowed_minutes = int((11 - driving_hours) * 60)
                if allowed_minutes > 0:
                    # Drive what we can (skip limit check to avoid recursion)
                    add_log_entry('Driving', allowed_minutes, remarks, miles * (allowed_minutes / duration_minutes), skip_limit_check=True)
                # Take mandatory 10-hour break and reset driving hours
                add_log_entry('Off-Duty', 600, '10-hour break (11-hour driving limit reached)', 0, skip_limit_check=True)
                # After 10-hour break, reset driving counters
                driving_hours = 0
                cumulative_driving_hours = 0
                window_end = current_time + timedelta(hours=14)
                # Continue with remaining driving time
                remaining_minutes = duration_minutes - allowed_minutes
                if remaining_minutes > 0:
                    # Continue driving with remaining time (will check limit again on next call)
                    add_log_entry('Driving', remaining_minutes, remarks, miles * (remaining_minutes / duration_minutes))
                return

        # Check if adding this entry would exceed 14-hour window
        if status in ['Driving', 'On-Duty'] and current_time + timedelta(minutes=duration_minutes) > window_end:
            remaining = int((window_end - current_time).total_seconds() // 60)

            # 1) Write the clipped SAME-status chunk up to window end
            if remaining > 0:
                start = current_time
                end = window_end
                miles_part = miles * (remaining / max(1, duration_minutes))
                logs.append({
                    'date': start.date(),
                    'status': status,
                    'start_time': start.strftime("%H:%M:%S"),
                    'end_time': end.strftime("%H:%M:%S"),
                    'remarks': f'{remarks} (clipped to end of 14-hour window)',
                    'miles': miles_part
                })

                # ---- UPDATE DAILY TOTALS + 70-hr WINDOW ----
                day = start.date()
                if day not in daily_totals:
                    daily_totals[day] = {'driving': 0, 'on_duty': 0, 'off_duty': 0, 'sleeper_berth': 0, 'miles': 0}

                hrs = remaining / 60.0
                if status == 'Driving':
                    daily_totals[day]['driving'] += hrs
                    daily_totals[day]['on_duty'] += hrs
                    driving_hours += hrs
                    cumulative_driving_hours += hrs
                    rolling_window[-1] += hrs
                    total_miles_driven += miles_part
                elif status == 'On-Duty':
                    daily_totals[day]['on_duty'] += hrs
                    rolling_window[-1] += hrs
                cycle_hours_8_day = sum(rolling_window)
                daily_totals[day]['miles'] += miles_part
                # --------------------------------------------

            # 2) Insert the mandatory 10-hour break
            break_start = window_end
            break_end = window_end + timedelta(minutes=600)
            if break_start.date() == break_end.date():
                logs.append({
                    'date': break_start.date(),
                    'status': 'Off-Duty',
                    'start_time': break_start.strftime("%H:%M:%S"),
                    'end_time': break_end.strftime("%H:%M:%S"),
                    'remarks': '10-hour break',
                    'miles': 0
                })
                # Update daily totals
                day = break_start.date()
                if day not in daily_totals:
                    daily_totals[day] = {'driving': 0, 'on_duty': 0, 'off_duty': 0, 'sleeper_berth': 0, 'miles': 0}
                daily_totals[day]['off_duty'] += 10.0
            else:
                # Split at midnight
                midnight = datetime.combine(break_start.date() + timedelta(days=1), time(0, 0, 0))
                first_duration_hours = (midnight - break_start).total_seconds() / 3600
                second_duration_hours = (break_end - midnight).total_seconds() / 3600
                # First part
                logs.append({
                    'date': break_start.date(),
                    'status': 'Off-Duty',
                    'start_time': break_start.strftime("%H:%M:%S"),
                    'end_time': '23:59:59',
                    'remarks': '10-hour break (continued next day)',
                    'miles': 0
                })
                day1 = break_start.date()
                if day1 not in daily_totals:
                    daily_totals[day1] = {'driving': 0, 'on_duty': 0, 'off_duty': 0, 'sleeper_berth': 0, 'miles': 0}
                daily_totals[day1]['off_duty'] += first_duration_hours
                # Second part
                logs.append({
                    'date': break_end.date(),
                    'status': 'Off-Duty',
                    'start_time': '00:00:00',
                    'end_time': break_end.strftime("%H:%M:%S"),
                    'remarks': '10-hour break (continued from previous day)',
                    'miles': 0
                })
                day2 = break_end.date()
                if day2 not in daily_totals:
                    daily_totals[day2] = {'driving': 0, 'on_duty': 0, 'off_duty': 0, 'sleeper_berth': 0, 'miles': 0}
                daily_totals[day2]['off_duty'] += second_duration_hours

            # 3) Move clocks to break end, reset driving clocks, and refresh window
            current_time = break_end.replace(second=0, microsecond=0)
            next_allowed_onduty = current_time
            window_end = current_time + timedelta(hours=14)
            driving_hours = 0.0
            cumulative_driving_hours = 0.0
            return

        # Handle sleeper berth restart: If 9+ consecutive hours off-duty with berth, reset 11/14-hour clocks
        if status == 'Off-Duty' and trip.use_sleeper_berth and duration_minutes >= 540:  # 9 hours
            berth_minutes = 420  # 7 hours
            remainder_minutes = duration_minutes - berth_minutes
            if remainder_minutes >= 120:  # At least 2 hours remainder
                # Split into 7 hours Sleeper Berth + remainder Off-Duty
                add_log_entry('Sleeper Berth', berth_minutes, f'{remarks} (Sleeper Berth)', 0)
                add_log_entry('Off-Duty', remainder_minutes, f'{remarks} (Off-Duty after Berth)', 0)
                # Reset 11/14-hour clocks
                driving_hours = 0
                cumulative_driving_hours = 0
                return

        start_time = current_time
        end_time = current_time + timedelta(minutes=duration_minutes)

        # Handle multi-day splitting
        if start_time.date() != end_time.date():
            # Split the entry at midnight
            midnight = datetime.combine(start_time.date(), datetime.max.time()).replace(hour=23, minute=59, second=59)
            first_duration = (midnight - start_time).total_seconds() / 60
            second_duration = duration_minutes - first_duration

            # Only add first part if it has meaningful duration (> 1 minute)
            if first_duration > 1:
                # First part of the day
                logs.append({
                    'date': start_time.date(),
                    'status': status,
                    'start_time': start_time.strftime("%H:%M:%S"),
                    'end_time': "23:59:59",
                    'remarks': f'{remarks} (continued next day)',
                    'miles': miles if miles > 0 else 0
                })

                # Update daily totals for first day
                day = start_time.date()
                if day not in daily_totals:
                    daily_totals[day] = {'driving': 0, 'on_duty': 0, 'off_duty': 0, 'sleeper_berth': 0, 'miles': 0}
                if status == 'Driving':
                    daily_totals[day]['driving'] += first_duration / 60
                    daily_totals[day]['on_duty'] += first_duration / 60
                    rolling_window[-1] += first_duration / 60
                    cycle_hours_8_day = sum(rolling_window)
                    total_miles_driven += miles * (first_duration / duration_minutes)
                elif status == 'On-Duty':
                    daily_totals[day]['on_duty'] += first_duration / 60
                    rolling_window[-1] += first_duration / 60
                    cycle_hours_8_day = sum(rolling_window)
                elif status == 'Off-Duty':
                    daily_totals[day]['off_duty'] += first_duration / 60
                elif status == 'Sleeper Berth':
                    daily_totals[day]['sleeper_berth'] += first_duration / 60
                daily_totals[day]['miles'] += miles * (first_duration / duration_minutes)

            # Only add second part if it has meaningful duration (> 1 minute)
            if second_duration > 1:
                # Second part next day
                logs.append({
                    'date': end_time.date(),
                    'status': status,
                    'start_time': "00:00:00",
                    'end_time': end_time.strftime("%H:%M:%S"),
                    'remarks': f'{remarks} (continued from previous day)',
                    'miles': miles if miles > 0 else 0
                })

                # Update daily totals for second day
                day = end_time.date()
                if day not in daily_totals:
                    daily_totals[day] = {'driving': 0, 'on_duty': 0, 'off_duty': 0, 'sleeper_berth': 0, 'miles': 0}
                if status == 'Driving':
                    daily_totals[day]['driving'] += second_duration / 60
                    daily_totals[day]['on_duty'] += second_duration / 60
                    rolling_window.pop(0)
                    rolling_window.append(0.0)
                    rolling_window[-1] += second_duration / 60
                    cycle_hours_8_day = sum(rolling_window)
                    total_miles_driven += miles * (second_duration / duration_minutes)
                elif status == 'On-Duty':
                    daily_totals[day]['on_duty'] += second_duration / 60
                    rolling_window.pop(0)
                    rolling_window.append(0.0)
                    rolling_window[-1] += second_duration / 60
                    cycle_hours_8_day = sum(rolling_window)
                elif status == 'Off-Duty':
                    daily_totals[day]['off_duty'] += second_duration / 60
                elif status == 'Sleeper Berth':
                    daily_totals[day]['sleeper_berth'] += second_duration / 60
                daily_totals[day]['miles'] += miles * (second_duration / duration_minutes)

            current_time = end_time
        else:
            logs.append({
                'date': start_time.date(),
                'status': status,
                'start_time': start_time.strftime("%H:%M:%S"),
                'end_time': end_time.strftime("%H:%M:%S"),
                'remarks': remarks,
                'miles': miles
            })

            # Update daily totals
            day = start_time.date()
            if day not in daily_totals:
                daily_totals[day] = {'driving': 0, 'on_duty': 0, 'off_duty': 0, 'sleeper_berth': 0, 'miles': 0}
            if status == 'Driving':
                daily_totals[day]['driving'] += duration_minutes / 60
                daily_totals[day]['on_duty'] += duration_minutes / 60
                driving_hours += duration_minutes / 60
                cumulative_driving_hours += duration_minutes / 60
                on_duty_hours += duration_minutes / 60
                rolling_window[-1] += duration_minutes / 60
                cycle_hours_8_day = sum(rolling_window)
                total_miles_driven += miles
            elif status == 'On-Duty':
                daily_totals[day]['on_duty'] += duration_minutes / 60
                on_duty_hours += duration_minutes / 60
                rolling_window[-1] += duration_minutes / 60
                cycle_hours_8_day = sum(rolling_window)
            elif status == 'Off-Duty':
                daily_totals[day]['off_duty'] += duration_minutes / 60
            elif status == 'Sleeper Berth':
                daily_totals[day]['sleeper_berth'] += duration_minutes / 60

            daily_totals[day]['miles'] += miles
            current_time = end_time

    # Off-duty from midnight to 6 AM (home terminal time base)
    add_log_entry('Off-Duty', 360, 'Home terminal time base')

    # Pre-trip inspection (30 min, On-Duty)
    add_log_entry('On-Duty', 30, f'{trip.current_location}, Pre-trip and TIV')

    # Drive to pickup (exact time, check for breaks and rolling 70-hour limit)
    drive_minutes_to_pickup = int((distance_to_pickup / 60) * 60)  # Exact minutes at 60 mph
    if drive_minutes_to_pickup > 0:
        # Check for 30-min break after 8 cumulative driving hours
        if cumulative_driving_hours >= 8:
            add_log_entry('Off-Duty', 30, '30-min break after 8 hours driving')
            cumulative_driving_hours = 0
        # Check rolling 70-hour limit before adding driving time
        projected_rolling = cycle_hours_8_day + (drive_minutes_to_pickup / 60)
        if projected_rolling > 70:
            # Force 34-hour restart - this will move current_time forward
            add_log_entry('Off-Duty', 2040, '34-hour restart to reset 70-hour limit', skip_limit_check=True)
            # After the restart, reset the rolling window
            rolling_window = [0.0] * 8
            cycle_hours_8_day = 0
            # Reset driving hours and window
            driving_hours = 0
            cumulative_driving_hours = 0
            window_end = current_time + timedelta(hours=14)
        add_log_entry('Driving', drive_minutes_to_pickup, f'Drive to {trip.pickup_location}', distance_to_pickup)

    # Pickup (1 hour, On-Duty)
    add_log_entry('On-Duty', 60, f'{trip.pickup_location}, Loading')

    # Drive to dropoff (split into reasonable segments, check for breaks, fueling every 1000 miles)
    drive_minutes_to_dropoff = int((distance_to_dropoff / 60) * 60)
    remaining_drive = drive_minutes_to_dropoff
    remaining_miles = distance_to_dropoff
    miles_since_fueling = 0

    while remaining_drive > 0:
        # Drive in segments, but check for 8-hour break, fueling, and rolling 70-hour limit
        chunk_minutes = min(remaining_drive, 60)  # Max 1 hour segments
        chunk_miles = (chunk_minutes / drive_minutes_to_dropoff) * distance_to_dropoff if drive_minutes_to_dropoff > 0 else 0

        # Check for fueling every 1000 miles
        if total_miles_driven + chunk_miles - miles_since_fueling >= 1000:
            add_log_entry('On-Duty', 30, 'Fueling stop')
            miles_since_fueling = total_miles_driven + chunk_miles

        # Check for 30-min break after 8 cumulative driving hours
        if cumulative_driving_hours + (chunk_minutes / 60) >= 8:
            add_log_entry('Off-Duty', 30, '30-min break after 8 hours driving')
            cumulative_driving_hours = 0

        # Check rolling 70-hour limit before adding driving time
        projected_rolling = cycle_hours_8_day + (chunk_minutes / 60)
        if projected_rolling > 70:
            # Force 34-hour restart
            add_log_entry('Off-Duty', 2040, '34-hour restart to reset 70-hour limit', skip_limit_check=True)
            rolling_window = [0.0] * 8
            cycle_hours_8_day = 0
            # Reset driving hours and window
            driving_hours = 0
            cumulative_driving_hours = 0
            window_end = current_time + timedelta(hours=14)

        add_log_entry('Driving', chunk_minutes, f'Drive to {trip.dropoff_location}', chunk_miles)
        remaining_drive -= chunk_minutes
        remaining_miles -= chunk_miles

    # Unload immediately at break end (same morning)
    add_log_entry('On-Duty', 60, f'{trip.dropoff_location}, Unloading')

    # Ensure full day coverage
    by_day = defaultdict(list)
    for log in logs:
        by_day[log['date']].append(log)
    for day in sorted(by_day.keys()):
        by_day[day] = _ensure_full_day(day, by_day[day])
    
    # Merge adjacent Off-Duty/Sleeper Berth entries after ensuring full day
    logs = []
    for day in sorted(by_day.keys()):
        day_logs = by_day[day]
        merged_day_logs = []
        
        for log in day_logs:
            if not merged_day_logs:
                merged_day_logs.append(log)
                continue
            
            last = merged_day_logs[-1]
            # Merge if both are Off-Duty or Sleeper Berth and they're adjacent
            if (log['status'] in ('Off-Duty', 'Sleeper Berth') and 
                last['status'] in ('Off-Duty', 'Sleeper Berth') and
                last['end_time'] == log['start_time']):
                # Extend the last entry
                last['end_time'] = log['end_time']
                # Combine remarks if different
                if log.get('remarks') and log['remarks'] not in last.get('remarks', ''):
                    if last.get('remarks'):
                        last['remarks'] = f"{last['remarks']} / {log['remarks']}"
                    else:
                        last['remarks'] = log['remarks']
            else:
                merged_day_logs.append(log)
        
        logs.extend(merged_day_logs)

    # Generate PDF log
    pdf_buffer = generate_log_pdf(logs, trip)
    pdf_file = ContentFile(pdf_buffer.getvalue(), name=f'log_{trip.id}.pdf')
    pdf_path = default_storage.save(f'logs/{logs[0]["date"]}.pdf', pdf_file)

    # Compute normalized daily totals
    daily_totals = compute_daily_totals(logs)

    # Validate HOS compliance
    hos_compliant = True
    violations = []

    # Check 11-hour driving limit
    max_driving_per_day = max([day_data['totals']['driving'] for day_data in daily_totals.values()] + [0])
    if max_driving_per_day > 11:
        hos_compliant = False
        violations.append("Exceeded 11-hour driving limit")

    # Check 14-hour window (already enforced)
    # Check 70-hour limit
    if cycle_hours_8_day > 70:
        hos_compliant = False
        violations.append("Exceeded 70-hour/8-day limit")

    # Sort logs by date and start_time
    def sort_key(x):
        start_time = x['start_time']
        if isinstance(start_time, str):
            try:
                start_time = datetime.strptime(start_time, "%H:%M:%S").time()
            except ValueError:
                start_time = time(0, 0, 0)
        elif isinstance(start_time, time):
            pass
        else:
            start_time = time(0, 0, 0)
        return (x['date'], start_time)
    logs.sort(key=sort_key)

    # Add totals to logs
    for day, day_data in daily_totals.items():
        totals = day_data['totals']
        logs.append({
            'date': day,
            'status': 'Total',
            'start_time': None,
            'end_time': None,
            'remarks': f'Daily Total - Lines 3+4: {totals["lines_3_4_total"]:.1f} hrs (Driving: {totals["driving"]:.1f} hrs, On-Duty Not Driving: {totals["on_duty_not_driving"]:.1f} hrs), Off-Duty: {totals["off_duty"]:.1f} hrs, Sleeper Berth: {totals["sleeper"]:.1f} hrs, Miles: {0:.1f}',
            'miles': 0
        })

    # Save logs to database
    for log in logs:
        if log['status'] != 'Total':  # Skip total entries
            grid_positions = calculate_grid_positions(log) if log['status'] != 'Total' else None
            LogEntry.objects.create(trip=trip, grid_positions=grid_positions, **{k: v for k, v in log.items() if k != 'miles'})

    # Calculate total duration from logs
    total_duration = 0
    for log in logs:
        if log['status'] != 'Total' and log.get('start_time') and log.get('end_time'):
            start = log['start_time']
            end = log['end_time']
            if isinstance(start, str):
                start = datetime.strptime(start, "%H:%M:%S").time()
            if isinstance(end, str):
                end = datetime.strptime(end, "%H:%M:%S").time()
            duration = (datetime.combine(date.today(), end) - datetime.combine(date.today(), start)).total_seconds() / 3600
            if duration < 0:  # Handle midnight crossing
                duration += 24
            total_duration += duration
    
    return {
        'route': [trip.current_location, trip.pickup_location, trip.dropoff_location],
        'route_coordinates': route_coordinates,
        'logs': logs,
        'total_distance': total_distance,
        'total_duration': round(total_duration, 2),
        'hos_compliant': hos_compliant,
        'violations': violations if not hos_compliant else [],
        'pdf_url': pdf_path,
        'use_sleeper_berth': trip.use_sleeper_berth
    }

def calculate_grid_positions(log_entry):
    # Calculate grid positions for drawing on log sheet
    # Assuming 24-hour grid with 15-min increments
    if isinstance(log_entry['start_time'], str):
        start_time = datetime.strptime(log_entry['start_time'], "%H:%M:%S").time()
    else:
        start_time = log_entry['start_time']
    if isinstance(log_entry['end_time'], str):
        end_time = datetime.strptime(log_entry['end_time'], "%H:%M:%S").time()
    else:
        end_time = log_entry['end_time']

    start_hour = start_time.hour
    start_minute = start_time.minute
    end_hour = end_time.hour
    end_minute = end_time.minute

    # Convert to grid positions (0-95 for 15-min slots)
    start_slot = (start_hour * 4) + (start_minute // 15)
    end_slot = (end_hour * 4) + (end_minute // 15)

    return {'start_slot': start_slot, 'end_slot': end_slot, 'status': log_entry['status']}

def generate_log_pdf(logs, trip):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Group logs by date
    logs_by_date = {}
    daily_totals_by_date = {}
    for log in logs:
        date = log['date']
        if log['status'] == 'Total':
            daily_totals_by_date[date] = log
        else:
            if date not in logs_by_date:
                logs_by_date[date] = []
            logs_by_date[date].append(log)

    # Generate a page for each date
    for date in sorted(logs_by_date.keys()):
        date_logs = logs_by_date[date]
        
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(0.75*inch, height - 0.6*inch, "DRIVER'S DAILY LOG")
        
        # Date
        c.setFont("Helvetica-Bold", 14)
        c.drawString(width - 2.5*inch, height - 0.6*inch, f"Date: {date.strftime('%m/%d/%Y')}")

        # Driver info section
        y_pos = height - 1.2*inch
        c.setFont("Helvetica", 10)
        c.drawString(0.75*inch, y_pos, f"Driver: ________________")
        c.drawString(3*inch, y_pos, f"Truck #: ________________")
        c.drawString(5.5*inch, y_pos, f"Trailer #: ________________")

        # Grid section - move grid right to make room for labels
        grid_top = height - 2*inch
        grid_left = 1.3*inch  # Moved right from 0.75" to 1.3"
        grid_width = width - 2.1*inch  # Adjusted to maintain right margin
        grid_height = 4*inch
        row_height = grid_height / 4

        # Status labels - positioned to the left of grid
        c.setFont("Helvetica-Bold", 9)
        label_x = 0.5*inch
        c.drawString(label_x, grid_top - row_height * 0.5, "1")
        c.drawString(label_x, grid_top - row_height * 1.5, "2")
        c.drawString(label_x, grid_top - row_height * 2.5, "3")
        c.drawString(label_x, grid_top - row_height * 3.5, "4")
        
        c.setFont("Helvetica", 8)
        text_x = 0.65*inch
        c.drawString(text_x, grid_top - row_height * 0.5, "Off Duty")
        c.drawString(text_x, grid_top - row_height * 1.5, "Sleeper Berth")
        c.drawString(text_x, grid_top - row_height * 2.5, "Driving")
        c.drawString(text_x, grid_top - row_height * 3.5, "On Duty")

        # Hour labels
        hour_labels = ["12M", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", 
                      "12N", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12M"]
        per_hour = grid_width / 24
        c.setFont("Helvetica", 7)
        for i, label in enumerate(hour_labels):
            x = grid_left + i * per_hour
            c.drawString(x - 0.05*inch, grid_top + 0.1*inch, label)

        # Draw grid
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(grid_left, grid_top - grid_height, grid_width, grid_height)
        
        # Horizontal lines
        for i in range(1, 4):
            y = grid_top - i * row_height
            c.line(grid_left, y, grid_left + grid_width, y)

        # Vertical hour lines
        c.setLineWidth(0.8)
        for h in range(1, 24):
            x = grid_left + h * per_hour
            c.line(x, grid_top, x, grid_top - grid_height)

        # Quarter hour ticks
        c.setLineWidth(0.3)
        for h in range(24):
            for q in range(1, 4):
                x = grid_left + h * per_hour + q * (per_hour / 4)
                c.line(x, grid_top, x, grid_top - grid_height)

        # Draw log lines on grid
        YROW = {
            'Off-Duty': grid_top - row_height * 0.5,
            'Sleeper Berth': grid_top - row_height * 1.5,
            'Driving': grid_top - row_height * 2.5,
            'On-Duty': grid_top - row_height * 3.5,
        }

        def x_at_hms(hms: str) -> float:
            H, M, S = map(int, hms.split(":"))
            return grid_left + (H + M/60 + S/3600) * per_hour

        c.setStrokeColor(colors.blue)
        c.setLineWidth(3)
        prev = None
        for e in sorted(date_logs, key=lambda x: x['start_time']):
            if e['status'] in YROW:
                y = YROW[e['status']]
                x1 = x_at_hms(e['start_time'])
                x2 = x_at_hms(e['end_time'])
                c.line(x1, y, x2, y)
                
                # Draw vertical connector if status changed
                if prev and prev['status'] in YROW and prev['end_time'] == e['start_time']:
                    prev_y = YROW[prev['status']]
                    c.line(x1, prev_y, x1, y)
                prev = e

        # Total hours boxes (right side)
        total_x = grid_left + grid_width + 0.15*inch
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.setFont("Helvetica-Bold", 8)
        
        # Get daily totals
        totals_entry = daily_totals_by_date.get(date)
        if totals_entry:
            # Parse totals from remarks
            remarks = totals_entry['remarks']
            # Extract hours from remarks string
            import re
            driving_match = re.search(r'Driving: ([\d.]+) hrs', remarks)
            onduty_match = re.search(r'On-Duty Not Driving: ([\d.]+) hrs', remarks)
            offduty_match = re.search(r'Off-Duty: ([\d.]+) hrs', remarks)
            sleeper_match = re.search(r'Sleeper Berth: ([\d.]+) hrs', remarks)
            
            driving_hrs = driving_match.group(1) if driving_match else "0"
            onduty_hrs = onduty_match.group(1) if onduty_match else "0"
            offduty_hrs = offduty_match.group(1) if offduty_match else "0"
            sleeper_hrs = sleeper_match.group(1) if sleeper_match else "0"
        else:
            driving_hrs = onduty_hrs = offduty_hrs = sleeper_hrs = "0"

        # Draw total boxes with values
        for i, hrs in enumerate([offduty_hrs, sleeper_hrs, driving_hrs, onduty_hrs]):
            box_y = grid_top - i * row_height - row_height * 0.5
            c.rect(total_x, box_y - 0.15*inch, 0.6*inch, 0.3*inch)
            c.drawString(total_x + 0.1*inch, box_y - 0.05*inch, str(hrs))

        # Remarks section
        remarks_y = grid_top - grid_height - 0.6*inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0.75*inch, remarks_y, "Remarks:")
        
        c.setLineWidth(0.8)
        c.rect(0.75*inch, remarks_y - 1.8*inch, width - 1.5*inch, 1.7*inch)
        
        c.setFont("Helvetica", 8)
        y_offset = remarks_y - 0.25*inch
        for i, log in enumerate(date_logs[:10]):  # Show up to 10 remarks
            if log.get('remarks'):
                remark_text = f"{log['start_time'][:5]} - {log['end_time'][:5]}: {log['remarks']}"
                if len(remark_text) > 90:
                    remark_text = remark_text[:87] + "..."
                c.drawString(0.85*inch, y_offset - i * 0.15*inch, remark_text)

        # Footer info
        footer_y = remarks_y - 2.2*inch
        c.setFont("Helvetica", 8)
        c.drawString(0.75*inch, footer_y, "Carrier: ________________")
        c.drawString(3.5*inch, footer_y, "Home Terminal: ________________")
        
        c.drawString(0.75*inch, footer_y - 0.2*inch, "Signature: ________________")
        c.drawString(3.5*inch, footer_y - 0.2*inch, "Date: ________________")

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer
