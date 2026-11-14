# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1642_nicholas_stack-app.md
"""FirePoints — harmonized MODIS + VIIRS fire calendar for Brazil.

Run locally:  streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data

st.set_page_config(page_title="FirePoints – Fire calendar", page_icon="🔥", layout="wide")


# ---------------------------------------------------------------------------
# Cached data
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading harmonized fire series…")
def get_series() -> pd.DataFrame:
    return data.load_series()  # shared read-only (not copied on every rerun)


@st.cache_resource
def get_cells() -> pd.DataFrame:
    return data.cells_table(get_series())


@st.cache_data(show_spinner=False)
def get_keys(area_json: str) -> np.ndarray:
    return data.select_cells(get_cells(), json.loads(area_json))


@st.cache_data(show_spinner="Counting fires…")
def get_monthly(area_json: str, years: tuple[int, int]) -> pd.DataFrame:
    sub = data.filter_series(get_series(), get_keys(area_json), years)
    return data.add_anomaly(data.monthly_counts(sub, years))


@st.cache_data(show_spinner=False)
def get_point_count(area_json: str, years: tuple[int, int]) -> int:
    return data.count_points(get_keys(area_json), years)


@st.cache_data(show_spinner="Building map…")
def get_frequency(area_json: str, years: tuple[int, int], month: int | None) -> pd.DataFrame:
    keys = get_keys(area_json)
    sub = data.filter_series(get_series(), keys, years)
    return data.fire_frequency(sub, get_cells(), keys, month, years)


# ---------------------------------------------------------------------------
# Sidebar: area and period
# ---------------------------------------------------------------------------
series = get_series()
biomes = sorted(series["bioma"].cat.categories)
_cells = get_cells()
states = (_cells.dropna(subset=["estado"]).drop_duplicates("estado").set_index("estado")["estado_nome"].sort_index()
          if "estado" in _cells else pd.Series(dtype=str))
y_min, y_max = data.FIRST_MONTH[0], data.LAST_MONTH[0]

with st.sidebar:
    st.title("🔥 FirePoints")
    st.caption("Harmonized MODIS + VIIRS fire calendar for Brazil, 2000–2026")

    modes = ["Whole Brazil", "State", "Biome", "Draw on map", "Lat/lon box"]
    if states.empty:
        modes.remove("State")
    mode = st.radio("Area", modes)
    if mode == "State":
        chosen = st.multiselect("States", list(states.index), default=["TO"] if "TO" in states.index else None,
                                format_func=lambda uf: f"{uf} – {states[uf]}")
        area = {"type": "states", "states": chosen or list(states.index)}
    elif mode == "Biome":
        chosen = st.multiselect("Biomes", biomes, default=["Cerrado"])
        area = {"type": "biomes", "biomes": chosen or biomes}
    elif mode == "Lat/lon box":
        c1, c2 = st.columns(2)
        lat_min = c1.number_input("Lat min", -34.0, 6.0, -23.4, 0.1)
        lat_max = c2.number_input("Lat max", -34.0, 6.0, -20.7, 0.1)
        lon_min = c1.number_input("Lon min", -74.0, -28.0, -45.0, 0.1)
        lon_max = c2.number_input("Lon max", -74.0, -28.0, -40.9, 0.1)
        area = {"type": "bbox", "lat_min": min(lat_min, lat_max), "lat_max": max(lat_min, lat_max),
                "lon_min": min(lon_min, lon_max), "lon_max": max(lon_min, lon_max)}
    elif mode == "Draw on map":
        area = st.session_state.get("drawn_area", {"type": "brazil"})
    else:
        area = {"type": "brazil"}

    years = st.slider("Period", y_min, y_max, (y_min, y_max))
    log_scale = st.toggle("Log colour scale", value=True,
                          help="Fire counts vary by orders of magnitude between seasons; log keeps both visible.")

    st.divider()
    st.caption(
        "Data: NASA FIRMS — MODIS C6.1 (Terra/Aqua) and VIIRS S-NPP 375 m. "
        "Biomes: IBGE. Counts in **VIIRS-equivalent fires**."
    )

st.title("Fire calendar")

# Drawing tool (only when needed: each map interaction reruns the app)
if mode == "Draw on map":
    import folium
    from folium.plugins import Draw
    from streamlit_folium import st_folium

    st.markdown("Draw a **rectangle** or **polygon** on the map. The last shape drawn is used.")
    fmap = folium.Map(location=[-14, -52], zoom_start=4, tiles="cartodbpositron")
    Draw(export=False, draw_options={"polyline": False, "circle": False, "marker": False,
                                     "circlemarker": False, "polygon": True, "rectangle": True}).add_to(fmap)
    out = st_folium(fmap, height=420, use_container_width=True,  # streamlit-folium API
                     returned_objects=["last_active_drawing"])
    drawing = (out or {}).get("last_active_drawing")
    if drawing and drawing.get("geometry", {}).get("type") == "Polygon":
        new_area = {"type": "polygon", "coords": drawing["geometry"]["coordinates"][0]}
        if new_area != st.session_state.get("drawn_area"):
            st.session_state["drawn_area"] = new_area
            st.rerun()
    if area["type"] == "brazil":
        st.info("No shape drawn yet — showing the whole of Brazil.")

area_json = json.dumps(area, sort_keys=True)
keys = get_keys(area_json)
if len(keys) == 0:
    st.warning("No 0.1° grid cell with fire detections inside this area. Try a larger area.")
    st.stop()

# Always computed on the full record, so the 2003–2025 baseline does not depend on the chosen period
monthly_full = get_monthly(area_json, (y_min, y_max))
monthly = monthly_full[monthly_full["year"].between(*years)].reset_index(drop=True)

# Headline numbers
valid = monthly.dropna(subset=["fires"])
peak = valid.loc[valid["fires"].idxmax()] if len(valid) else None
season = valid.groupby("month")["fires"].median()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Grid cells (0.1°)", f"{len(keys):,}")
c2.metric("Fires in period", f"{valid['fires'].sum():,.0f}")
if peak is not None:
    c3.metric("Peak month", f"{charts.MONTHS[int(peak['month']) - 1]} {int(peak['year'])}",
              help=f"{peak['fires']:,.0f} VIIRS-equivalent fires")
    c4.metric("Typical fire season peak", charts.MONTHS[int(season.idxmax()) - 1])

tab_cal, tab_anom, tab_map, tab_method, tab_dl, tab_about = st.tabs(
    ["📅 Calendar", "📈 Anomaly", "🗺️ Map", "🧪 Method & validation", "⬇️ Download", "ℹ️ How to read"]
)

# ---------------------------------------------------------------------------
with tab_cal:
    view = st.radio("Colour by", ["Fire count", "Compared to normal"], horizontal=True,
                    help="Compared to normal: each month vs the mean of the same month in 2003–2025, in the same area.")
    st.plotly_chart(charts.calendar(monthly, log_scale, "anomaly" if view.startswith("Compared") else "count"),
                    width="stretch")
    st.caption(
        "Each square = one month inside the area, in VIIRS-equivalent fire counts. "
        "**\\*** estimated from MODIS × calibration factor (2003–Jan/2012) · "
        "**†** partial: MODIS Terra only (Nov/2000–2002) · grey = no data."
    )

# ---------------------------------------------------------------------------
with tab_anom:
    c1, c2 = st.columns(2)
    last_y, last_m = data.LAST_MONTH
    a_year = c1.selectbox("Year", list(range(years[1], years[0] - 1, -1)))
    default_m = last_m if a_year == last_y else int(season.idxmax()) if len(season) else 1
    max_m = last_m if a_year == last_y else 12
    a_month = c2.selectbox("Month", list(range(1, max_m + 1)), index=min(default_m, max_m) - 1,
                           format_func=lambda m: charts.MONTHS[m - 1])
    an = data.anomaly(monthly_full, a_year, a_month)
    if np.isnan(an["value"]):
        st.info("No data for this month.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{charts.MONTHS[a_month - 1]} {a_year}", f"{an['value']:,.0f} fires")
        c2.metric("Normal (2003–2025 mean)", f"{an['mean']:,.0f} fires")
        c3.metric("Compared to normal", f"{an['pct']:+.0f}%" if np.isfinite(an["pct"]) else "n/a",
                  help=f"Band: {an['band']}. Higher than {an['rank_below']} of the {an['n_compared']} other years "
                       f"in 2003–2025.")
        if an["band"]:
            label = an["band"] if an["band"] == "normal" else f"{an['band']} normal"
            st.markdown(f"**{charts.MONTHS[a_month - 1]} {a_year} was {label} for this area.**")
        st.plotly_chart(charts.anomaly_bars(an["history"], a_year, an["mean"]), width="stretch")
        st.caption("Normal = mean of the same month in 2003–2025 (complete years). "
                   "Grey bars: estimated/partial years (MODIS-based).")

# ---------------------------------------------------------------------------
with tab_map:
    c1, c2 = st.columns([1, 2])
    metric = c1.radio("Show", ["% of years with fire", "Total fires"])
    m_choice = c2.selectbox("Month", ["Any month"] + charts.MONTHS,
                            help="Fire frequency for a given calendar month, e.g. how often each cell burns in September.")
    month = None if m_choice == "Any month" else charts.MONTHS.index(m_choice) + 1
    freq = get_frequency(area_json, years, month)
    col = "pct_years" if metric.startswith("%") else "total_fires"
    st.plotly_chart(charts.cell_map(freq, col, "% years" if col == "pct_years" else "Fires"),
                    width="stretch")
    st.caption(f"Each pixel is a 0.1° grid cell (≈11 km), WGS84 lat/lon. {len(freq[freq[col] > 0]):,} cells with fire; "
               "white = no detection in the period.")

# ---------------------------------------------------------------------------
with tab_method:
    st.markdown(
        """
**Why harmonize?** MODIS (1 km pixels, since 2000) is being retired; VIIRS (375 m, since 2012) sees
smaller fires and detects **~3–4× more** hot spots. Joining them naively creates a false jump in 2012.

**How.** VIIRS S-NPP is the reference. For each biome and calendar month we compute
k = Σ VIIRS / Σ MODIS over 2012–2019 (before the Terra/Aqua orbital drift) and convert MODIS
2000–2012 into VIIRS-equivalent counts. From Feb/2012 the series is observed VIIRS.
Filters: MODIS confidence ≥ 30, VIIRS confidence nominal/high, vegetation fires only (type 0).
"""
    )
    st.plotly_chart(charts.harmonization_check(monthly), width="stretch")
    st.caption("Selected area. In 2012–2019 MODIS × k should track observed VIIRS (calibration); the growing gap in recent years reflects the Terra/Aqua orbital drift — one reason to use VIIRS as the reference.")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**Calibration factor k by biome and month**")
        st.plotly_chart(charts.factors_heatmap(data.load_factors()), width="stretch")
    with c2:
        st.markdown("**Validation (leave-one-year-out, 2012–2019)**")
        val = data.load_validation().rename(columns={
            "bioma": "Biome", "focos_snpp_ano": "VIIRS fires / year", "erro_medio_abs_pct": "Mean abs. error (%)"})
        st.dataframe(val, hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
with tab_dl:
    st.markdown("**Monthly counts for the selected area**")
    out_month = monthly[["year", "month", "fires", "status", "modis_raw", "viirs_raw"]].rename(
        columns={"fires": "fires_viirs_eq"})
    st.download_button("Download monthly CSV", out_month.to_csv(index=False), "firepoints_monthly.csv", "text/csv")

    st.markdown("**Counts per grid cell and month**")
    sub = data.filter_series(series, keys, years)
    if len(sub) > 1_000_000:
        st.info(f"{len(sub):,} rows — select a smaller area or period to download per-cell data.")
    elif st.button("Prepare per-cell CSV"):
        cells = get_cells().set_index("key")
        out = pd.DataFrame({
            "lat": cells.loc[sub["key"], "lat"].to_numpy(), "lon": cells.loc[sub["key"], "lon"].to_numpy(),
            "biome": sub["bioma"].to_numpy(), "year": sub["ano"].to_numpy(), "month": sub["mes"].to_numpy(),
            "fires_viirs_eq": sub["focos"].round(2).to_numpy(), "status": sub["status"].to_numpy(),
        })
        st.download_button("Download per-cell CSV", out.to_csv(index=False), "firepoints_cells.csv", "text/csv")

    st.markdown("**Individual fire detections** (raw MODIS and VIIRS points, *not* harmonized)")
    if data.points_available():
        n_pts = get_point_count(area_json, years)
        st.caption(f"{n_pts:,} detections in this area and period.")
        if n_pts > 1_500_000:
            st.info("Too many points for one CSV — select a smaller area or a shorter period.")
        elif n_pts and st.button("Prepare fire points CSV"):
            with st.spinner("Reading fire points…"):
                pts = data.fire_points(keys, years)
            st.download_button("Download fire points CSV", pts.to_csv(index=False),
                               f"firepoints_detections_raw_{years[0]}-{years[1]}.csv", "text/csv")
    else:
        st.info("Individual detections are not bundled in this deployment. "
                "They can be downloaded from [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/download/).")

# ---------------------------------------------------------------------------
with tab_about:
    st.markdown(
        """
**Choose an area** in the sidebar: the whole country, one or more states or biomes, a lat/lon box, or a shape drawn on the map.
Cells are included when their centre falls inside the area.

**Reading the calendar.** Rows are years, columns are months. Colour = number of fires (Viridis scale, log by default).
Grey = no data (before Nov/2000 or after the last processed month). Marks next to the year:
\\* estimated from MODIS, † partial (Terra only).

**Unit.** *VIIRS-equivalent fires*: the number of hot spots VIIRS S-NPP would have detected.
Before 2012 this is MODIS × k (see *Method*).

**Compared to normal / anomaly.** Each month vs the mean of the same calendar month in 2003–2025 (complete years),
in the same area. Bands: far below (<0.5×), below (0.5–0.8×), normal (0.8–1.25×), above (1.25–2×), far above (>2×).

**Map.** Each dot is a 0.1° cell (≈11 km). “% of years with fire” = share of years in the period with at least one
detection in that cell (in the chosen month).

**Limitations.** A hot spot is not burned area; clouds hide fires; the factor assumes a stable MODIS/VIIRS relation
per biome and month; the most recent months may still be near-real-time (provisional) data.
"""
    )
