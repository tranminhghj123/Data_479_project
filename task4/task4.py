"""NOAA GSOD — Arctic temperature dashboard (Task 4).

Run from repo root:  streamlit run task4/task4.py
"""

from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
TASK2_GLOB = str(REPO_ROOT / "task2_output" / "part-*.csv")
META_PATH = REPO_ROOT / "task4" / "stations_meta.csv"
OUTPUT_DIR = REPO_ROOT / "task4_output"

BG = "#0E1014"        # page
SURF = "#14171D"      # elevated (maps, tables)
INK = "#E8E5DC"       # primary text
MUTED = "#858892"     # secondary text
FAINT = "#4A4E57"     # tertiary / disabled
RULE = "#212530"      # dividers
GRID = "#1C1F27"

COLD = "#7CB0E3"
WARM = "#E58868"
AMBER = "#D5A84A"
BONE = "#B8B2A3"

BAND_COLOR = {
    "Sub-Arctic": AMBER,
    "Arctic": BONE,
    "High Arctic": COLD,
}
BAND_ORDER = ["Sub-Arctic", "Arctic", "High Arctic"]

@st.cache_data
def load_data() -> pd.DataFrame:
    files = sorted(glob.glob(TASK2_GLOB))
    if not files:
        st.error(f"No Task 2 output found at {TASK2_GLOB}")
        st.stop()
    df = pd.concat([pd.read_csv(f, dtype={"STATION": str}) for f in files], ignore_index=True)
    meta = pd.read_csv(META_PATH, dtype={"STATION": str})
    df = df.merge(meta, on="STATION", how="left")
    df["NAME"] = df["NAME"].str.replace(r",\s*NO$|,\s*SV$", "", regex=True).str.title()
    return df


def station_deltas(df: pd.DataFrame) -> pd.DataFrame:
    piv = df.pivot_table(index="STATION", columns="YEAR", values="AVG_TEMP")
    first, last = piv.columns.min(), piv.columns.max()
    out = (
        df.groupby(["STATION", "NAME", "REGION", "LAT", "LON"], as_index=False)["AVG_TEMP"].mean()
        .rename(columns={"AVG_TEMP": "MEAN"})
    )
    out["START"] = out["STATION"].map(piv[first])
    out["END"] = out["STATION"].map(piv[last])
    out["CHANGE"] = out["END"] - out["START"]
    return out.dropna(subset=["START", "END"])

AXIS = dict(
    showgrid=False, zeroline=False, showline=True,
    linecolor=RULE, linewidth=1, ticks="outside",
    tickcolor=RULE, ticklen=4,
    tickfont=dict(size=11, color=MUTED, family="JetBrains Mono, monospace"),
)
BASE = dict(
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(family="Inter, system-ui, sans-serif", size=12, color=INK),
    hoverlabel=dict(bgcolor=SURF, bordercolor=RULE, font_size=12,
                    font_family="Inter, system-ui, sans-serif", font_color=INK),
    margin=dict(l=10, r=10, t=10, b=10),
)


def map_figure(deltas: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scattergeo(
        lon=deltas["LON"], lat=deltas["LAT"], mode="markers",
        marker=dict(
            size=9,
            color=deltas["MEAN"],
            colorscale=[[0, COLD], [0.5, BONE], [1, AMBER]],
            cmin=deltas["MEAN"].min(), cmax=deltas["MEAN"].max(),
            line=dict(color=BG, width=0.6),
            colorbar=dict(
                title=dict(text="°F", side="right",
                           font=dict(size=10, color=MUTED, family="JetBrains Mono, monospace")),
                thickness=8, len=0.6, x=1.0,
                tickfont=dict(size=10, color=MUTED, family="JetBrains Mono, monospace"),
                outlinewidth=0, bgcolor=BG,
            ),
        ),
        customdata=deltas[["NAME", "STATION", "CHANGE"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]}<br>"
            "Mean  %{marker.color:.1f}°F<br>"
            "Δ     %{customdata[2]:+.1f}°F<extra></extra>"
        ),
    ))
    fig.update_geos(
        projection_type="orthographic",
        projection_rotation=dict(lon=15, lat=70),
        center=dict(lon=15, lat=72),
        showcoastlines=True, coastlinecolor="#3A3E48", coastlinewidth=0.6,
        showland=True, landcolor=SURF,
        showocean=True, oceancolor=BG,
        showframe=False, showlakes=False, showcountries=False,
        bgcolor=BG,
        lataxis_range=[58, 84], lonaxis_range=[-15, 40],
    )
    fig.update_layout(height=360, showlegend=False, **BASE)
    return fig


def band_trend_figure(df: pd.DataFrame) -> go.Figure:
    band = df.groupby(["REGION", "YEAR"], as_index=False)["AVG_TEMP"].mean()
    fig = go.Figure()
    for region in BAND_ORDER:
        sub = band[band["REGION"] == region].sort_values("YEAR")
        if sub.empty:
            continue
        color = BAND_COLOR[region]
        fig.add_trace(go.Scatter(
            x=sub["YEAR"], y=sub["AVG_TEMP"],
            mode="lines+markers", name=region,
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color, line=dict(color=BG, width=1.5)),
            hovertemplate=f"<b>{region}</b><br>%{{x}}  %{{y:.1f}}°F<extra></extra>",
        ))
        last = sub.iloc[-1]
        fig.add_annotation(
            x=last["YEAR"], y=last["AVG_TEMP"],
            text=f"  {region}  {last['AVG_TEMP']:.1f}°",
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(size=11, color=color, family="Inter, system-ui, sans-serif"),
        )
    years = sorted(band["YEAR"].unique())
    fig.update_layout(
        height=320, showlegend=False,
        xaxis=dict(**AXIS, tickmode="array", tickvals=years,
                   range=[min(years) - 0.15, max(years) + 0.9]),
        yaxis=dict(**AXIS, title=None, ticksuffix="°"),
        **{k: v for k, v in BASE.items() if k != "margin"},
        margin=dict(l=8, r=10, t=10, b=30),
    )
    return fig


def comparison_figure(df: pd.DataFrame, names: list[str]) -> go.Figure:
    palette = [AMBER, COLD, WARM, BONE, "#9FB89C", "#C496AE", "#E3C27B", "#6E93A8"]
    fig = go.Figure()
    sub = df[df["NAME"].isin(names)].sort_values(["NAME", "YEAR"])
    for i, (name, g) in enumerate(sub.groupby("NAME")):
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=g["YEAR"], y=g["AVG_TEMP"],
            mode="lines+markers", name=name,
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color, line=dict(color=BG, width=1.5)),
            hovertemplate=f"<b>{name}</b><br>%{{x}}  %{{y:.1f}}°F<extra></extra>",
        ))
        last = g.iloc[-1]
        fig.add_annotation(
            x=last["YEAR"], y=last["AVG_TEMP"],
            text=f"  {name}",
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(size=11, color=color, family="Inter, system-ui, sans-serif"),
        )
    years = sorted(df["YEAR"].unique())
    fig.update_layout(
        height=340, showlegend=False,
        xaxis=dict(**AXIS, tickmode="array", tickvals=years,
                   range=[min(years) - 0.15, max(years) + 1.5]),
        yaxis=dict(**AXIS, title=None, ticksuffix="°"),
        **{k: v for k, v in BASE.items() if k != "margin"},
        margin=dict(l=8, r=10, t=10, b=30),
    )
    return fig


def change_ranking_figure(deltas: pd.DataFrame) -> go.Figure:
    d = deltas.sort_values("CHANGE").copy()
    d["COLOR"] = d["CHANGE"].apply(lambda x: WARM if x > 0 else COLD)
    fig = go.Figure(go.Bar(
        x=d["CHANGE"], y=d["NAME"], orientation="h",
        marker=dict(color=d["COLOR"], line=dict(color=BG, width=0)),
        customdata=d[["STATION", "REGION"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>%{customdata[0]} · %{customdata[1]}<br>"
            "Δ 2022→2025  %{x:+.2f}°F<extra></extra>"
        ),
    ))
    fig.add_vline(x=0, line=dict(color=FAINT, width=1))
    fig.update_layout(
        height=max(420, 14 * len(d)),
        xaxis=dict(**AXIS, title=None, ticksuffix="°"),
        yaxis=dict(
            showgrid=False, zeroline=False, showline=False,
            tickfont=dict(size=10, color=INK, family="Inter, system-ui, sans-serif"),
            automargin=True,
        ),
        bargap=0.28,
        **{k: v for k, v in BASE.items() if k != "margin"},
        margin=dict(l=10, r=16, t=10, b=36),
    )
    return fig


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* kill default Streamlit chrome that was blocking the header */
header[data-testid="stHeader"] {{ display: none !important; }}
#MainMenu, footer, [data-testid="stStatusWidget"] {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}

html, body, .stApp, [class*="css"] {{
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  color: {INK};
  background: {BG};
}}
.stApp {{ background: {BG}; }}
.block-container {{
  padding-top: 3.5rem; padding-bottom: 4rem;
  max-width: 1200px;
}}

/* sidebar */
[data-testid="stSidebar"] {{
  background: {BG};
  border-right: 1px solid {RULE};
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 2.5rem; }}
[data-testid="stSidebar"] * {{ color: {INK}; }}
[data-testid="stSidebar"] label {{ color: {MUTED} !important; font-size: 11px !important;
  font-family: 'JetBrains Mono', monospace !important; text-transform: uppercase;
  letter-spacing: 0.1em; font-weight: 500; }}

/* sharp corners on ALL interactive widgets */
[data-baseweb="tag"],
[data-baseweb="select"] > div,
[data-baseweb="select"] input,
[data-baseweb="input"] input,
[data-baseweb="popover"] > div,
button, .stSlider > div, .stSelectbox > div {{
  border-radius: 0 !important;
}}

/* multiselect chips — squared, outlined */
[data-baseweb="tag"] {{
  background: transparent !important;
  border: 1px solid {INK} !important;
  border-radius: 0 !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 0.02em;
  padding: 2px 4px !important;
  margin: 2px 4px 2px 0 !important;
}}
[data-baseweb="tag"] *,
[data-baseweb="tag"] span,
[data-baseweb="tag"] div {{
  color: {INK} !important;
  background: transparent !important;
}}
[data-baseweb="tag"] svg {{ fill: {INK} !important; }}
[data-baseweb="tag"]:hover {{ border-color: {WARM} !important; }}
[data-baseweb="tag"]:hover *,
[data-baseweb="tag"]:hover svg {{ color: {WARM} !important; fill: {WARM} !important; }}

/* select / input borders */
[data-baseweb="select"] > div {{
  background: {BG} !important;
  border: 1px solid {RULE} !important;
  min-height: 38px;
}}
[data-baseweb="select"] > div:hover {{ border-color: {MUTED} !important; }}
[data-baseweb="popover"] [role="listbox"] {{
  background: {SURF} !important; border: 1px solid {RULE};
}}
[data-baseweb="popover"] [role="option"]:hover {{ background: {RULE} !important; }}

/* slider */
.stSlider [role="slider"] {{
  background: {INK} !important;
  border: none !important;
  border-radius: 1px !important;
  height: 14px !important; width: 6px !important;
  box-shadow: none !important;
}}
.stSlider [data-baseweb="slider"] > div > div {{ background: {RULE} !important; }}
.stSlider [data-baseweb="slider"] > div > div > div {{ background: {INK} !important; }}
.stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {{ display: none; }}

/* typography */
h1, h2, h3 {{ font-weight: 500; letter-spacing: -0.015em; color: {INK}; }}
.eyebrow {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
  color: {MUTED}; margin-bottom: 14px;
}}
.hed {{
  font-size: 36px; line-height: 1.08; margin: 0 0 10px 0;
  font-weight: 500; letter-spacing: -0.02em; color: {INK};
  max-width: 24ch;
}}
.dek {{
  font-size: 15px; line-height: 1.55; color: {MUTED};
  margin: 0 0 36px 0; max-width: 64ch;
}}
hr.rule {{ border: 0; border-top: 1px solid {RULE}; margin: 40px 0 28px; }}

/* KPI */
.kpi-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
  color: {MUTED}; margin-bottom: 6px;
}}
.kpi-value {{
  font-size: 30px; font-weight: 500; color: {INK}; line-height: 1;
  font-feature-settings: "tnum";
  letter-spacing: -0.02em;
}}
.kpi-note {{ font-size: 12px; color: {MUTED}; margin-top: 6px; line-height: 1.3; }}

/* section headings */
.sec-h {{ font-size: 17px; font-weight: 500; margin: 0 0 4px 0; color: {INK};
  letter-spacing: -0.01em; }}
.sec-d {{ font-size: 13px; color: {MUTED}; margin: 0 0 14px 0; line-height: 1.5;
  max-width: 70ch; }}

/* dataframe */
[data-testid="stDataFrame"] {{ border: 1px solid {RULE}; background: {SURF}; }}
[data-testid="stDataFrame"] div[role="columnheader"] {{
  background: {SURF} !important; color: {MUTED} !important;
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.08em;
  border-bottom: 1px solid {RULE};
}}
[data-testid="stDataFrame"] div[role="cell"] {{
  background: {BG} !important; color: {INK};
  font-size: 13px; border-bottom: 1px solid {GRID};
}}

/* footer meta chips */
.chip {{
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; letter-spacing: 0.08em;
  padding: 3px 7px; border: 1px solid {RULE};
  color: {MUTED}; margin-right: 6px;
}}
</style>
"""


def kpi(col, label: str, value: str, note: str = "") -> None:
    with col:
        st.markdown(
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-note">{note}</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="Arctic stations · 2022–2025",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    df = load_data()
    years_all = sorted(df["YEAR"].unique())

    with st.sidebar:
        st.markdown('<div class="eyebrow">Filters</div>', unsafe_allow_html=True)
        regions = st.multiselect("Latitude band", BAND_ORDER, default=BAND_ORDER)
        year_range = st.slider(
            "Years",
            min_value=int(min(years_all)), max_value=int(max(years_all)),
            value=(int(min(years_all)), int(max(years_all))),
        )
        st.markdown(f"<hr class='rule' style='margin:24px 0 18px;'/>", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Source</div>', unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:12px; color:{MUTED}; line-height:1.55;'>"
            "NOAA Global Surface Summary of the Day. 50 stations across Norway "
            "and Svalbard, rolled up by Spark into annual means."
            "</div>",
            unsafe_allow_html=True,
        )

    view = df[df["REGION"].isin(regions) & df["YEAR"].between(*year_range)].copy()
    if view.empty:
        st.warning("No stations match the current filters.")
        return

    deltas = station_deltas(view)

    st.markdown(
        '<div class="eyebrow">NOAA GSOD · DATA 479 · 2026</div>'
        '<h1 class="hed">Four winters over the Norwegian Arctic.</h1>'
        '<p class="dek">Fifty weather stations between 60°N and 81°N, '
        'every daily observation from 2022 through 2025, rolled into annual '
        'means on Spark. The view below tracks how each station drifted, '
        'whether latitude explains the drift, and which year-over-year '
        'swings look real.</p>',
        unsafe_allow_html=True,
    )

    mean_all = view["AVG_TEMP"].mean()
    warmest = deltas.loc[deltas["MEAN"].idxmax()]
    coldest = deltas.loc[deltas["MEAN"].idxmin()]
    warming_pct = (deltas["CHANGE"] > 0).mean() * 100
    biggest = deltas.loc[deltas["CHANGE"].abs().idxmax()]

    c1, c2, c3, c4 = st.columns(4, gap="large")
    kpi(c1, "Mean, all stations", f"{mean_all:.1f}°F",
        f"{view['STATION'].nunique()} stations · {year_range[0]}–{year_range[1]}")
    kpi(c2, "Warmest", f"{warmest['MEAN']:.1f}°F", warmest["NAME"])
    kpi(c3, "Coldest", f"{coldest['MEAN']:.1f}°F", coldest["NAME"])
    kpi(c4, "Warmer in 2025 vs 2022", f"{warming_pct:.0f}%",
        f"largest swing {biggest['CHANGE']:+.1f}°F at {biggest['NAME']}")

    st.markdown('<hr class="rule"/>', unsafe_allow_html=True)

    band_means = view.groupby("REGION")["AVG_TEMP"].mean().to_dict()
    spread = max(band_means.values()) - min(band_means.values())
    st.markdown(
        '<div class="sec-h">Mean annual temperature, by latitude band</div>'
        f'<div class="sec-d">{spread:.1f}°F separates the Sub-Arctic and High-Arctic means '
        f'across the four-year window. All three bands moved in lockstep — '
        '2023 reads cool everywhere, 2024 warm — which points at a regional '
        'weather pattern rather than anything station-specific.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(band_trend_figure(view), use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown('<hr class="rule"/>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.4], gap="large")
    with left:
        st.markdown(
            '<div class="sec-h">Geography</div>'
            '<div class="sec-d">Marker color is each station’s four-year mean: '
            'cold blue along Svalbard, amber along the southern coast and '
            'oil platforms.</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(map_figure(deltas), use_container_width=True,
                        config={"displayModeBar": False})
    with right:
        n_warm = int((deltas["CHANGE"] > 0).sum())
        n_cool = int((deltas["CHANGE"] < 0).sum())
        st.markdown(
            '<div class="sec-h">Change per station · 2022 → 2025</div>'
            f'<div class="sec-d">{n_warm} stations end the window warmer, '
            f'{n_cool} colder. The tail at the top is a coverage artifact — '
            'a handful of stations only began reporting consistently in 2023.</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(change_ranking_figure(deltas), use_container_width=True,
                        config={"displayModeBar": False})

    st.markdown('<hr class="rule"/>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-h">Compare stations directly</div>'
        '<div class="sec-d">Pick a handful of stations to overlay their four-year '
        'trajectories. Useful for pairing a coastal oil platform against a Svalbard '
        'ridge — same years, radically different baselines.</div>',
        unsafe_allow_html=True,
    )
    name_options = sorted(view["NAME"].dropna().unique())
    preferred = [n for n in name_options
                 if n.split()[0] in {"Sorstokken", "Karl", "Longyear", "Jan",
                                     "Troll", "Hornsund", "Ny"}]
    defaults = preferred[:4] if preferred else name_options[:4]
    selected = st.multiselect(
        "Stations to overlay",
        name_options,
        default=defaults,
        label_visibility="collapsed",
        placeholder="Select stations…",
    )
    if selected:
        st.plotly_chart(
            comparison_figure(view, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        summary = (
            view[view["NAME"].isin(selected)]
            .groupby("NAME")
            .agg(
                Mean=("AVG_TEMP", "mean"),
                Low=("AVG_TEMP", "min"),
                High=("AVG_TEMP", "max"),
                Spread=("AVG_TEMP", lambda s: s.max() - s.min()),
            )
            .round(2)
            .sort_values("Mean")
            .reset_index()
            .rename(columns={"NAME": "Station"})
        )
        st.dataframe(summary, use_container_width=True, hide_index=True, height=min(44 + 35 * len(summary), 260))
    else:
        st.markdown(
            f"<div style='color:{MUTED}; font-size:13px; padding:12px 0;'>"
            "Pick at least one station above."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="rule"/>', unsafe_allow_html=True)

    swings = view.sort_values(["STATION", "YEAR"]).copy()
    swings["YOY"] = swings.groupby("STATION")["AVG_TEMP"].diff()
    v = swings.dropna(subset=["YOY"])
    mu, sd = v["YOY"].mean(), v["YOY"].std()
    flagged = (
        v[(v["YOY"] - mu).abs() > sd]
        .assign(YOY=lambda x: x["YOY"].round(2), AVG_TEMP=lambda x: x["AVG_TEMP"].round(2))
        .sort_values("YOY")
        [["STATION", "NAME", "REGION", "YEAR", "AVG_TEMP", "YOY"]]
        .rename(columns={
            "STATION": "ID", "NAME": "Station", "REGION": "Band",
            "YEAR": "Year", "AVG_TEMP": "Annual °F", "YOY": "YoY Δ",
        })
    )

    st.markdown(
        '<div class="sec-h">Year-over-year outliers</div>'
        f'<div class="sec-d">Rows where the year-over-year change lands '
        f'more than one standard deviation (σ = {sd:.2f}°F) from the '
        f'dataset-wide mean change of {mu:+.2f}°F. Most are single-year dips '
        'that recover the next season — consistent with sensor gaps rather than a climate signal.</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(flagged, use_container_width=True, hide_index=True, height=340)

    OUTPUT_DIR.mkdir(exist_ok=True)
    flagged.to_csv(OUTPUT_DIR / "extreme_years.csv", index=False)

    st.markdown(
        f"<div style='margin-top:40px; padding-top:20px; border-top:1px solid {RULE};"
        f" font-size:11px; color:{MUTED}; font-family: \"JetBrains Mono\", monospace;'>"
        f"<span class='chip'>{view['STATION'].nunique()} stations</span>"
        f"<span class='chip'>{len(view)} station-years</span>"
        f"<span class='chip'>NOAA GSOD</span>"
        f"<span class='chip'>Spark · Streamlit</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
