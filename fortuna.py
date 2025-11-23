"""
Fortuna Conjunction Finder Utility

Calculates the Part of Fortune and checks for conjunctions with major planets 
over a specified time period using the pyswisseph library.

Author: Nubicola Rex
Date: 2025-11-23
License: GPL v3.0
Repository: https://github.com/Nubicola/fortuna
"""

import swisseph as swe
from datetime import datetime, timedelta
from collections import OrderedDict
import argparse

EPHE_PATH='/path/to/swisseph/ephe'

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

def print_fortuna_conjunctions(start_date, end_date, lat, lon, only_exact):
    time_increment = timedelta(minutes=1)
    current_time = start_date

    while current_time <= end_date:
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
        ascendant_longitude = ascmc[0] # Ascendant is at index 0 of the ascmc tuple

        fortuna_longitude = moon_longitude + ascendant_longitude - sun_longitude
        fortuna_longitude = swe.degnorm(fortuna_longitude)

        house = find_house(fortuna_longitude, cusps_list)
        
        for body_id, (name, longitude) in planet_positions.items():
            orb = abs(fortuna_longitude - longitude)
            if orb > 180:
                orb = 360 - orb # Take the shortest angular distance

            if orb <= 6.0 and get_zodiac_sign(fortuna_longitude) == get_zodiac_sign(longitude):
                F_deg = fortuna_longitude % 30
                P_deg = longitude % 30

                output_str = (
                    f"Date: {current_time.strftime('%D %H:%M')}, "
                    f"S: {sun_longitude%30:.2f} deg {get_zodiac_sign(sun_longitude)}, "
                    f"M: {moon_longitude%30:.2f} deg {get_zodiac_sign(moon_longitude)} "
                    f"F: {F_deg:.2f} deg {get_zodiac_sign(fortuna_longitude)} House {house}, "
                    f"Planet {name} {P_deg:.2f} deg {get_zodiac_sign(longitude)} "
                )
                if only_exact == 'N':
                    print(output_str)
                elif only_exact == 'Y' and orb <= 1.0:
                    print(output_str)
        current_time += time_increment

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

    args = parser.parse_args()

    print("--- Parameters Received ---")
    print(f"Latitude: {args.lat}")
    print(f"Longitude: {args.lon}")
    print(f"Starting Date: {args.start_date}")
    print(f"Starting Time: {args.start_time}")
    print(f"Duration (days): {args.duration}")
    print(f"Only Exact Conjunctions: {args.exact}")
    print("---------------------------")

    try:
        start_datetime_str = f"{args.start_date} {args.start_time}"
        start_datetime_obj = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
        end_datetime_obj = start_datetime_obj + timedelta(days=args.duration)
        
        print_fortuna_conjunctions(start_datetime_obj, end_datetime_obj, args.lat, args.lon, args.exact)
        
    except ValueError as e:
        print(f"Error parsing date/time: {e}. Ensure correct YYYY-MM-DD and HH:MM format.")

if __name__ == "__main__":
    swe.set_ephe_path(EPHE_PATH) 
    main()
