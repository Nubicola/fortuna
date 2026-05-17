"""
Fortuna Conjunction Finder Utility

Calculates the Part of Fortune and checks for conjunctions with major planets 
over a specified time period using the pyswisseph library.

Author: Nubicola Rex
Date: 2026-05-17
License: GPL v3.0
Repository: https://github.com/Nubicola/fortuna
"""

import os
import swisseph as swe
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
import argparse

EPHE_PATH='/path/to/swissepe/ephe'  # Set this to the directory containing Swiss Ephemeris files

house_system = 'W'

def get_longitude(jd, body_id):
    """Calculates the ecliptic longitude of a celestial body."""
    xx, rflags = swe.calc_ut(jd, body_id, swe.FLG_SWIEPH)
    return xx[0] # Return just the longitude float

def get_zodiac_sign(longitude):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]

BODY_MAP = OrderedDict([
    (swe.SUN, "Sun"),
    (swe.MOON, "Moon"),
    (swe.MERCURY, "Mercury"),
    (swe.VENUS, "Venus"),
    (swe.MARS, "Mars"),
    (swe.JUPITER, "Jupiter"),
    (swe.SATURN, "Saturn")
])

def get_planet_positions(julian_day_ut):
    positions_dict = {}

    for body_id, name in BODY_MAP.items():
        xx, rflags = swe.calc_ut(julian_day_ut, body_id, swe.FLG_SWIEPH)
        longitude = xx[0] # Get the longitude float, not the whole tuple
        positions_dict[body_id] = (name, longitude) # Store (name, longitude) tuple

    return positions_dict

def find_house(body_longitude, house_cusps):
    # Determine if the input is 0-indexed (len 12) or 1-indexed (len 13)
    if len(house_cusps) == 13:
        cusp_lons = house_cusps[1:] # Slice off the unused 0-index
    elif len(house_cusps) == 12:
        cusp_lons = house_cusps
    else:
        raise ValueError(f"Expected 12 or 13 cusps, but received {len(house_cusps)}.")
    
    for i in range(12):
        start_lon = cusp_lons[i]
        end_lon = cusp_lons[(i + 1) % 12]
        
        if start_lon < end_lon:
            if start_lon <= body_longitude < end_lon:
                return i + 1
        else:
            if body_longitude >= start_lon or body_longitude < end_lon:
                return i + 1
                
    return None

def is_reasonable(dt: datetime) -> bool:
    hour = dt.hour
    return 6 <= hour <= 23

def print_fortuna_conjunctions(start_date, end_date, lat, lon, only_exact, only_reasonable, print_short, create_ics):
    time_increment = timedelta(minutes=1)
    current_time = start_date
    threshold = 1.0 if only_exact == 'Y' else 6.0
    create_ics = create_ics == 'Y'

    orb_states = {
        body_id: {
            'active': False,
            'start_snapshot': None,
            'last_snapshot': None
        }
        for body_id in BODY_MAP
    }

    def build_output_snapshot(timestamp, sun_longitude, moon_longitude, fortuna_longitude, name, longitude, house):
        return {
            'timestamp': timestamp,
            'sun_longitude': sun_longitude,
            'moon_longitude': moon_longitude,
            'fortuna_longitude': fortuna_longitude,
            'name': name,
            'longitude': longitude,
            'house': house
        }

    def format_output(snapshot, prefix):
        F_deg = snapshot['fortuna_longitude'] % 30
        P_deg = snapshot['longitude'] % 30

        if print_short=='Y':
            output_str = (
                f"Date: {snapshot['timestamp'].strftime('%D %H:%M')}, "
                f"Planet {snapshot['name']} {P_deg:.2f} deg {get_zodiac_sign(snapshot['longitude'])} "
            )
        else:
            output_str = (
                f"Date: {snapshot['timestamp'].strftime('%D %H:%M')}, "
                f"S: {snapshot['sun_longitude']%30:.2f} deg {get_zodiac_sign(snapshot['sun_longitude'])}, "
                f"M: {snapshot['moon_longitude']%30:.2f} deg {get_zodiac_sign(snapshot['moon_longitude'])} "
                f"F: {F_deg:.2f} deg {get_zodiac_sign(snapshot['fortuna_longitude'])} House {snapshot['house']}, "
                f"Planet {snapshot['name']} {P_deg:.2f} deg {get_zodiac_sign(snapshot['longitude'])} "
            )
        return f"[{prefix}] {output_str}"

    def write_ics_file(start_snapshot, last_snapshot):
        start = start_snapshot['timestamp']
        end = last_snapshot['timestamp'] + time_increment
        summary = f"{start_snapshot['name']} conjunct fortuna"
        # Keep DTSTART/DTEND as floating local times (no Z) so imported
        # calendars display the same clock hour as in the .ics file.
        dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        dtstart = start.strftime('%Y%m%dT%H%M%S')
        dtend = end.strftime('%Y%m%dT%H%M%S')
        safe_name = start_snapshot['name'].replace(' ', '_').lower()
        filename = f"{safe_name}_conjunct_fortuna_{start.strftime('%Y%m%dT%H%M')}_{end.strftime('%Y%m%dT%H%M')}.ics"
        path = os.path.join('/tmp', filename)
        suffix = 1
        while os.path.exists(path):
            path = os.path.join('/tmp', f"{safe_name}_conjunct_fortuna_{start.strftime('%Y%m%dT%H%M')}_{end.strftime('%Y%m%dT%H%M')}_{suffix}.ics")
            suffix += 1

        ics_content = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//Fortuna//EN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{safe_name}-{start.strftime('%Y%m%dT%H%M%S')}-{end.strftime('%Y%m%dT%H%M%S')}@fortuna\r\n"
            f"DTSTAMP:{dtstamp}\r\n"
            f"DTSTART:{dtstart}\r\n"
            f"DTEND:{dtend}\r\n"
            f"SUMMARY:{summary}\r\n"
            f"DESCRIPTION:{summary}\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(ics_content)

    def flush_state(body_id):
        state = orb_states[body_id]
        if not state['active']:
            return

        start_snapshot = state['start_snapshot']
        last_snapshot = state['last_snapshot']
        if start_snapshot is None or last_snapshot is None:
            state['active'] = False
            return

        if create_ics:
            write_ics_file(start_snapshot, last_snapshot)
        else:
            if start_snapshot['timestamp'] == last_snapshot['timestamp']:
                print(format_output(start_snapshot, 'First/Last'))
            else:
                print(format_output(start_snapshot, 'First'))
                print(format_output(last_snapshot, 'Last'))

        state['active'] = False
        state['start_snapshot'] = None
        state['last_snapshot'] = None

    while current_time <= end_date:
        if ((only_reasonable == 'Y') and is_reasonable(current_time)) or (only_reasonable != 'Y'):
            year = current_time.year
            month = current_time.month
            day = current_time.day
            hour_float = current_time.hour + (current_time.minute / 60.0) + (current_time.second / 3600.0)
            julian_day_ut = swe.julday(year, month, day, hour_float)

            planet_positions = get_planet_positions(julian_day_ut)

            swe.set_ephe_path(EPHE_PATH)
            cusps_list, ascmc = swe.houses(julian_day_ut, lat, lon, house_system.encode('ascii'))

            sun_longitude = planet_positions[swe.SUN][1]
            moon_longitude = planet_positions[swe.MOON][1]
            ascendant_longitude = ascmc[0]  # Ascendant is at index 0 of the ascmc tuple

            fortuna_longitude = moon_longitude + ascendant_longitude - sun_longitude
            fortuna_longitude = swe.degnorm(fortuna_longitude)

            house = find_house(fortuna_longitude, cusps_list)

            for body_id, (name, longitude) in planet_positions.items():
                orb = abs(fortuna_longitude - longitude)
                if orb > 180:
                    orb = 360 - orb  # Take the shortest angular distance

                in_orb = orb <= threshold and get_zodiac_sign(fortuna_longitude) == get_zodiac_sign(longitude)
                state = orb_states[body_id]

                if in_orb:
                    snapshot = build_output_snapshot(
                        current_time,
                        sun_longitude,
                        moon_longitude,
                        fortuna_longitude,
                        name,
                        longitude,
                        house
                    )
                    if not state['active']:
                        state['active'] = True
                        state['start_snapshot'] = snapshot
                    state['last_snapshot'] = snapshot
                elif state['active']:
                    flush_state(body_id)

        current_time += time_increment

    for body_id in orb_states:
        if orb_states[body_id]['active']:
            flush_state(body_id)

def main():
    parser = argparse.ArgumentParser(description="Calculate Part of Fortune over a duration.")
    # Set path here too for general script access
    swe.set_ephe_path(EPHE_PATH) 

    parser.add_argument('--lat', type=float, default=51.5072, help="Your latitude (North is positive, South is negative). Default: 57.485")
    parser.add_argument('--lon', type=float, default=-0.1276, help="Your longitude (East is positive, West is negative). Default: -3.216")
    parser.add_argument('--start_date', type=str, default=datetime.now().strftime('%Y-%m-%d'), help="Starting date in YYYY-MM-DD format. Default: today's date")
    parser.add_argument('--start_time', type=str, default="00:00", help="Starting time in HH:MM format (UTC). Default: 00:00")
    parser.add_argument('--duration', type=int, default=1, help="Duration of the calculation loop in full days. Default: 1")
    parser.add_argument('--exact', type=str, default="N", help="Y for only exact conjunctions (<1 degree), N for wide orb (<6 degrees). Default: N")
    parser.add_argument('--reasonable', type=str, default="Y", help="Y to restrict to 'reasonable' times only (from 06:00 until 23:59) Default: Y")
    parser.add_argument('--short', type=str, default="N", help="Y to reduce the output strings to short form. Default: N")
    parser.add_argument('--ics', type=str, default="N", help="Y to generate .ics files instead of printing conjunctions. Default: N")

    args = parser.parse_args()

    print("--- Parameters Received ---")
    print(f"Latitude: {args.lat}")
    print(f"Longitude: {args.lon}")
    print(f"Starting Date: {args.start_date}")
    print(f"Starting Time: {args.start_time}")
    print(f"Duration (days): {args.duration}")
    print(f"Only Exact Conjunctions: {args.exact}")
    print(f"Only print reasonable times: {args.reasonable}")
    print(f"Print short form: {args.short}")
    print(f"Generate ICS files: {args.ics}")
    print("---------------------------")

    try:
        start_datetime_str = f"{args.start_date} {args.start_time}"
        start_datetime_obj = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
        end_datetime_obj = start_datetime_obj + timedelta(days=args.duration)
        
        print_fortuna_conjunctions(start_datetime_obj, end_datetime_obj, args.lat, args.lon, args.exact, args.reasonable, args.short, args.ics)
        
    except ValueError as e:
        print(f"Error parsing date/time: {e}. Ensure correct YYYY-MM-DD and HH:MM format.")

if __name__ == "__main__":
    main()
