# Task 4 — Climate Analytics & Interactive Dashboard

Interactive Streamlit dashboard that visualizes the annual temperature averages
produced by the Task 2 PySpark job.

## Data

- **Primary input**: `task2_output/part-*.csv` (49 stations × 2022–2025, ~196 rows).
  Chosen over `task 3 output/` because the MapReduce file has trailing tabs and
  extra whitespace; content is identical.
- **Station metadata**: `task4/stations_meta.csv`, generated once from the raw
  GSOD subset in `shared/` (adds station NAME, LAT, LON, ELEV, REGION).

All 50 stations in the subset are Norwegian / Svalbard; latitude range is
~59.8°N to 80.7°N. Regions are latitude bands:

| Region        | Latitude | Count |
|---------------|----------|-------|
| Sub-Arctic    | <67°N    | 6     |
| Arctic        | 67–75°N  | 33    |
| High Arctic   | ≥75°N    | 11    |

## Analyses implemented

1. **Long-term Temperature Trends** — regional mean + per-station small-multiples.
2. **Station Comparison** — multi-select overlay with a summary table.
3. **Extreme Weather Indicators** — top/bottom 5 station-years and year-over-year
   anomalies (±1σ from the dataset-wide YoY mean).

## Run

```bash
python -m venv .venv
.venv/bin/pip install -r task4/requirements.txt
.venv/bin/python task4/build_metadata.py   # one-shot, writes task4/stations_meta.csv
.venv/bin/streamlit run task4/task4.py
```

## Outputs

- `task4_output/extreme_years.csv` — written by the dashboard when the Extreme
  Weather tab is viewed.
- `task4_output/screenshots/` — dashboard screenshots for the final report.
