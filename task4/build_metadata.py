"""Build stations_meta.csv from the raw GSOD subset in shared/.

Run once: `python task4/build_metadata.py` (from repo root).
"""

from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_GLOB = str(REPO_ROOT / "shared" / "part-*.csv")
OUT_PATH = REPO_ROOT / "task4" / "stations_meta.csv"


def region_for(lat: float) -> str:
    """All stations are Norwegian/Svalbard (~60–81°N); bucket by latitude band."""
    if lat >= 75:
        return "High Arctic"
    if lat >= 67:
        return "Arctic"
    return "Sub-Arctic"


def main() -> None:
    files = sorted(glob.glob(SHARED_GLOB))
    if not files:
        raise SystemExit(f"No files matched {SHARED_GLOB}")

    cols = ["STATION", "NAME", "LATITUDE", "LONGITUDE", "ELEVATION"]
    frames = [pd.read_csv(f, usecols=cols, dtype={"STATION": str}) for f in files]
    raw = pd.concat(frames, ignore_index=True)

    meta = (
        raw.dropna(subset=["LATITUDE", "LONGITUDE"])
        .groupby("STATION", as_index=False)
        .first()
    )
    meta["REGION"] = meta["LATITUDE"].map(region_for)
    meta = meta.rename(columns={"LATITUDE": "LAT", "LONGITUDE": "LON", "ELEVATION": "ELEV"})
    meta = meta[["STATION", "NAME", "LAT", "LON", "ELEV", "REGION"]]

    meta.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(meta)} stations to {OUT_PATH}")
    print(meta["REGION"].value_counts().to_string())


if __name__ == "__main__":
    main()
