import sys
import csv

# Read each CVS line
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    # Parse CSV
    try:
        fields = next(csv.reader([line]))
    except Exception:
        continue  # Skip malformed lines

    # Check all attributes
    if len(fields) < 28:
        continue

    # Parse specified fields
    station = fields[0]
    date = fields[1]
    temp_str = fields[6]

    # Extract year from date

    # Skip invalid dates
    if len(date) < 4:
        continue
    # First four characters in date: YYYY-MM-DD
    year = date[:4]

    # Validate temperature
    try:
        temp = float(temp_str)
    except ValueError:
        continue  # Skip missing or invalid values

    # key = (station, year), value = (temp, 1)
    print(f"{station},{year}\t{temp},1")
