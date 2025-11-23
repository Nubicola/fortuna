# fortuna
A part of fortune calculator

This Python utility uses the pyswisseph library to calculate the position of the astrological Part of Fortune and identify conjunctions with major planets (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn) over a specified time period.
It takes command-line arguments for location, start time, and duration, and supports different house systems and orb settings.

While the Part of Fortune is usually calculated for a birth chart, this utility calculates the part of fortunate over a period of time and shows which planets are conjuct the part of fortune. So if you want to know "over the next 3 days, when is Venus conjuct the Part of Fortune?" this utility is for you.

## Prerequisites

Python Installation: Ensure Python 3 is installed on your system (Linux recommended).
Required Libraries: Install the necessary Python packages using pip:

```bash
pip install pyswisseph argparse
```

Swiss Ephemeris Data Files: pyswisseph requires astronomical data files.
Download the core ephemeris files (e.g., seas_18.se1, sepl_18.se1, swedata.txt) from the AstroDienst FTP site.
Place these files in a directory on your system. 
Crucial: Update the EPHE_PATH variable in the Python script if you use a different location:

```python
EPHE_PATH='/path/to/your/ephe/files'
```

## Usage
Run the script from your terminal (Linux environment recommended):
```bash
python3 fortuna.py [options]
```

Command-Line Arguments
The script uses argparse to handle configuration. Run with --help for a summary of options:
```bash
python3 fortuna.py --help
```

| Argument | Type | Default Value | Description |
--- | --- | --- | --- | 
| --lat | float | 51.5072 | Your latitude (North is positive, South is negative). |
| --lon | float | -0.1276 | Your longitude (East is positive, West is negative). |
| --start_date | str | Today's Date | Starting date in YYYY-MM-DD format. |
| --start_time | str | 00:00 | Starting time in HH:MM format (UTC). |
| --duration | int | 1 | Duration of the calculation loop in full days. Due to performance limitations, don't set this to a high number! |
| --exact | str | N | Y for only exact conjunctions (<1 degree), N for wide orb (<6 degrees). |

## Examples
Run with default parameters (1 day duration for current date at London, UK):
```bash
python3 fortuna.py
```

Run for a specific location and date:
```bash
python3 fortuna.py --lat 40.7128 --lon -74.0060 --start_date 2025-11-25 --duration 2
```
Run for exact conjunctions only (narrow orb < 1 degree):
```bash

python3 fortuna.py --lat 51.5 --lon -0.1 --exact Y
```

## Output Format
The utility outputs lines for every minute where a conjunction is found within the specified orb.

```
Date: 11/23/25 14:03, S: Sagittarius, M: Scorpio, F: 15.25 deg Libra, House 5, Planet Jupiter at 15.10 deg Libra
```

The output displays the date/time, Sun/Moon signs, Fortuna position (degree in sign + sign), house number, and the conjuncting planet's position (degree in sign + sign).

## Technical Details
- House System: Currently configured for Whole Sign Houses via the house_system = 'W' variable in the script. This can be changed to 'P' for Placidus, 'K' for Koch, etc., by editing the source file.
- Fortuna Formula: Uses the standard day/night chart formula assumption.
- Orb Logic: Calculates the shortest angular distance between 0-360 degrees.
- There's not a lot of error checking. Don't do anything silly.
- This is not very efficient. The pyswisseph library doesn't support vectors, so the only way to do this is with loops. If you set very high durations, this will take a long time!
