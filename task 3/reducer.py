
import sys

# Track (station, year)
current_key = None

# Initialize aggregation totals
temp_sum = 0.0
count = 0

# Header for output
print("Station, Year, Average Temperature")

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    # Mapper emits (station, year)--(temp,1)
    key, value = line.split("\t")
    station_year = key.strip()

    try:
        # Split by comma
        temp_str, one_str = value.split(",")
        temp = float(temp_str)
    except:
        continue

    # When key changes
    if station_year != current_key:
        if current_key is not None:
            station, year = current_key.split(",")

            # Compute average annual temperature
            avg_temp = temp_sum / count
            print(f"{station}, {year}, {avg_temp:.2f}")

        # Reset for next key
        current_key = station_year
        temp_sum = 0.0
        count = 0

    # Iterate temperature and observation
    temp_sum += temp
    count += 1

# Emit final key
if current_key is not None:
    station, year = current_key.split(",")

    avg_temp = temp_sum / count
    print(f"{station}, {year}, {avg_temp:.2f}")


