"""Task 4 — Climate Analytics & Interactive Dashboard.

Run: `streamlit run task4/task4.py` from the repo root.
Data source: task2_output/ (PySpark average annual temperature output).
"""

from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
TASK2_GLOB = str(REPO_ROOT / "task2_output" / "part-*.csv")
META_PATH = REPO_ROOT / "task4" / "stations_meta.csv"
OUTPUT_DIR = REPO_ROOT / "task4_output"

REGION_ORDER = ["Sub-Arctic", "Arctic", "High Arctic"]
REGION_COLORS = {
    "Sub-Arctic": "#1f77b4",
    "Arctic": "#2ca02c",
    "High Arctic": "#d62728",
}


@st.cache_data
def load_data() -> pd.DataFrame:
    files = sorted(glob.glob(TASK2_GLOB))
    if not files:
        st.error(f"No Task 2 output found at {TASK2_GLOB}")
        st.stop()
    df = pd.concat(
        [pd.read_csv(f, dtype={"STATION": str}) for f in files],
        ignore_index=True,
    )
    meta = pd.read_csv(META_PATH, dtype={"STATION": str})
    merged = df.merge(meta, on="STATION", how="left")
    merged["LABEL"] = merged["NAME"].fillna(merged["STATION"]) + " (" + merged["STATION"] + ")"
    return merged


def tab_trends(df: pd.DataFrame) -> None:
    st.subheader("Long-term Temperature Trends")
    st.caption(
        "Average annual temperature over 2022–2025, grouped by latitude band. "
        "The top chart shows the region-level mean; the bottom chart shows every station as a faint line."
    )

    region_mean = (
        df.groupby(["REGION", "YEAR"], as_index=False)["AVG_TEMP"]
        .mean()
        .rename(columns={"AVG_TEMP": "MEAN_TEMP"})
    )
    fig_region = px.line(
        region_mean,
        x="YEAR",
        y="MEAN_TEMP",
        color="REGION",
        category_orders={"REGION": REGION_ORDER},
        color_discrete_map=REGION_COLORS,
        markers=True,
        labels={"MEAN_TEMP": "Mean annual temp (°F)", "YEAR": "Year"},
        title="Regional mean annual temperature",
    )
    fig_region.update_layout(height=380, xaxis=dict(tickmode="linear"))
    st.plotly_chart(fig_region, use_container_width=True)

    fig_all = px.line(
        df.sort_values(["STATION", "YEAR"]),
        x="YEAR",
        y="AVG_TEMP",
        color="REGION",
        line_group="STATION",
        category_orders={"REGION": REGION_ORDER},
        color_discrete_map=REGION_COLORS,
        hover_data=["NAME", "STATION", "LAT"],
        labels={"AVG_TEMP": "Annual avg temp (°F)", "YEAR": "Year"},
        title="All stations (each line = one station)",
    )
    fig_all.update_traces(opacity=0.45, line=dict(width=1.2))
    fig_all.update_layout(height=480, xaxis=dict(tickmode="linear"))
    st.plotly_chart(fig_all, use_container_width=True)

    delta = (
        df.groupby("STATION")["AVG_TEMP"]
        .agg(["first", "last"])
        .assign(change=lambda x: x["last"] - x["first"])
    )
    st.markdown(
        f"**Overall change, 2022 → 2025**: mean = {delta['change'].mean():+.2f}°F, "
        f"warming at {(delta['change'] > 0).sum()} of {len(delta)} stations."
    )


def tab_compare(df: pd.DataFrame) -> None:
    st.subheader("Station Comparison")
    st.caption("Pick two or more stations to overlay their annual temperature trends.")

    options = sorted(df["LABEL"].dropna().unique())
    defaults = [
        o for o in options
        if o.startswith(("SORSTOKKEN", "KARL XII OYA", "LONGYEAR", "JAN MAYEN"))
    ][:3]
    selected = st.multiselect("Stations", options, default=defaults or options[:3])

    if not selected:
        st.info("Select at least one station above.")
        return

    subset = df[df["LABEL"].isin(selected)].sort_values(["LABEL", "YEAR"])
    fig = px.line(
        subset,
        x="YEAR",
        y="AVG_TEMP",
        color="LABEL",
        markers=True,
        hover_data=["REGION", "LAT", "LON", "ELEV"],
        labels={"AVG_TEMP": "Annual avg temp (°F)", "YEAR": "Year", "LABEL": "Station"},
    )
    fig.update_layout(height=480, xaxis=dict(tickmode="linear"))
    st.plotly_chart(fig, use_container_width=True)

    summary = (
        subset.groupby("LABEL")
        .agg(mean_temp=("AVG_TEMP", "mean"),
             min_temp=("AVG_TEMP", "min"),
             max_temp=("AVG_TEMP", "max"),
             spread=("AVG_TEMP", lambda s: s.max() - s.min()))
        .round(2)
        .sort_values("mean_temp")
    )
    st.markdown("**Summary across the selected stations**")
    st.dataframe(summary, use_container_width=True)


def tab_extremes(df: pd.DataFrame) -> None:
    st.subheader("Extreme Weather Indicators")
    st.caption(
        "Top/bottom station-years by average temperature, and years with large "
        "year-over-year swings relative to the dataset-wide distribution of swings."
    )

    ordered = df.sort_values("AVG_TEMP")
    cols = ["STATION", "NAME", "REGION", "YEAR", "AVG_TEMP"]
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Top 5 warmest station-years**")
        st.dataframe(ordered.tail(5).iloc[::-1][cols], use_container_width=True, hide_index=True)
    with col_r:
        st.markdown("**Top 5 coldest station-years**")
        st.dataframe(ordered.head(5)[cols], use_container_width=True, hide_index=True)

    swings = df.sort_values(["STATION", "YEAR"]).copy()
    swings["YOY_DELTA"] = swings.groupby("STATION")["AVG_TEMP"].diff()
    valid = swings.dropna(subset=["YOY_DELTA"])
    mu = valid["YOY_DELTA"].mean()
    sigma = valid["YOY_DELTA"].std()
    threshold = max(sigma, 0.1)
    flagged = valid[(valid["YOY_DELTA"] - mu).abs() > threshold].copy()
    flagged["YOY_DELTA"] = flagged["YOY_DELTA"].round(2)

    st.markdown(
        f"**Year-over-year anomalies** — dataset-wide YoY mean = {mu:+.2f}°F, "
        f"stdev = {sigma:.2f}°F. Rows below exceed ±1σ from the mean change."
    )
    st.dataframe(
        flagged.sort_values("YOY_DELTA")[["STATION", "NAME", "REGION", "YEAR", "AVG_TEMP", "YOY_DELTA"]],
        use_container_width=True,
        hide_index=True,
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    flagged.to_csv(OUTPUT_DIR / "extreme_years.csv", index=False)


def main() -> None:
    st.set_page_config(page_title="GSOD Climate Dashboard — Task 4", layout="wide")
    st.title("NOAA GSOD Climate Dashboard")
    st.markdown(
        "DATA 479 · Task 4 · Data source: **Task 2 PySpark output** "
        "(49 Norwegian / Svalbard stations, 2022–2025)."
    )

    df = load_data()

    with st.sidebar:
        st.header("Filters")
        regions = st.multiselect(
            "Regions",
            REGION_ORDER,
            default=REGION_ORDER,
        )
        years = sorted(df["YEAR"].unique())
        year_range = st.slider(
            "Year range",
            min_value=int(min(years)),
            max_value=int(max(years)),
            value=(int(min(years)), int(max(years))),
        )
        st.markdown("---")
        st.markdown(f"**Stations**: {df['STATION'].nunique()}")
        st.markdown(f"**Rows**: {len(df)}")
        st.markdown(f"**Years**: {year_range[0]}–{year_range[1]}")

    filtered = df[
        df["REGION"].isin(regions)
        & df["YEAR"].between(year_range[0], year_range[1])
    ]

    if filtered.empty:
        st.warning("No data for the current filters.")
        return

    t1, t2, t3 = st.tabs(["Long-term Trends", "Station Comparison", "Extreme Weather"])
    with t1:
        tab_trends(filtered)
    with t2:
        tab_compare(filtered)
    with t3:
        tab_extremes(filtered)


if __name__ == "__main__":
    main()
