# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1642_nicholas_stack-app.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1800_nicholas_melhorias-app-mapa.md
"""FirePoints — harmonized MODIS + VIIRS fire calendar for Brazil.

Run locally:  streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import json
import re
import time

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import maps

st.set_page_config(page_title="FirePoints – Fire calendar", page_icon="🔥", layout="wide")

MONTHS = charts.MONTHS
STATES_GEOJSON = data.PROCESSED / "ufs_simplificado.geojson"  # optional: smooth state boundaries (pipeline)


# ---------------------------------------------------------------------------
# Cached data
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading harmonized fire series…")
def get_series() -> pd.DataFrame:
    return data.load_series()  # shared read-only (not copied on every rerun)


@st.cache_resource
def get_cells() -> pd.DataFrame:
    return data.cells_table(get_series())


@st.cache_resource
def get_grid() -> maps.Grid:
    return maps.build_grid(get_cells())


@st.cache_resource
def get_states_geojson() -> dict | None:
    return json.loads(STATES_GEOJSON.read_text(encoding="utf-8")) if STATES_GEOJSON.exists() else None


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


@st.cache_data(show_spinner="Building map…", max_entries=24)
def get_frequency(years: tuple[int, int], month: int | None) -> pd.DataFrame:
    """Per-cell statistics for the whole country (the map keeps Brazil visible around the selected area)."""
    cells = get_cells()
    all_keys = cells["key"].to_numpy()
    sub = data.filter_series(get_series(), all_keys, years)
    return data.fire_frequency(sub, cells, all_keys, month, years)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def month_span(first: int, last: int) -> str:
    return MONTHS[first - 1] if first == last else f"{MONTHS[first - 1]}–{MONTHS[last - 1]}"


def vs_normal(pct: float) -> str:
    """'37% above normal' / '12% below normal' / 'on the normal'."""
    if not np.isfinite(pct):
        return "not comparable with the normal"
    if abs(pct) < 0.5:
        return "on the normal"
    return f"{abs(pct):.0f}% {'above' if pct > 0 else 'below'} normal"


def area_label(area: dict, states: pd.Series) -> str:
    kind = area["type"]
    if kind == "states":
        names = [states.get(uf, uf) for uf in area["states"]]
        return ", ".join(names) if len(names) <= 3 else f"{len(names)} states"
    if kind == "biomes":
        return ", ".join(area["biomes"]) if len(area["biomes"]) <= 3 else f"{len(area['biomes'])} biomes"
    return {"bbox": "Lat/lon box", "polygon": "Drawn area"}.get(kind, "Brazil")


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


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
    area = {"type": "brazil"}
    if mode == "State":
        chosen = st.multiselect("States", list(states.index), default=["TO"] if "TO" in states.index else None,
                                format_func=lambda uf: f"{uf} – {states[uf]}")
        if chosen:
            area = {"type": "states", "states": chosen}
        else:
            st.caption("No state selected: showing the whole of Brazil.")
    elif mode == "Biome":
        chosen = st.multiselect("Biomes", biomes, default=["Cerrado"])
        if chosen:
            area = {"type": "biomes", "biomes": chosen}
        else:
            st.caption("No biome selected: showing the whole of Brazil.")
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

    years = st.slider("Period", y_min, y_max, (y_min, y_max))
    log_scale = st.toggle("Log colour scale", value=True,
                          help="For the calendar and the map. Fire counts vary by orders of magnitude between "
                               "seasons and places; the log scale keeps both ends visible.")

    st.divider()
    st.caption(
        "Data: NASA FIRMS — MODIS C6.1 (Terra/Aqua) and VIIRS S-NPP 375 m. "
        "Biomes and states: IBGE. Counts in **VIIRS-equivalent fires**."
    )

label = area_label(area, states)
st.title(f"Fire calendar — {label}")

# Drawing tool: the user draws over the fire map itself (the rest of the page follows the shape)
if mode == "Draw on map":
    from streamlit_folium import st_folium

    st.markdown("Draw a **rectangle** or **polygon** over the area you want to analyse (tools on the left of the map). "
                "Colour shows where fire is detected, so you can aim at the hot spots. The last shape drawn is used.")
    grid = get_grid()
    record = (y_min, y_max)
    overview = maps.render(grid, get_frequency(record, None), "fires", get_cells()["key"].to_numpy(), log=True)
    drawn = area if area["type"] == "polygon" else None
    out = st_folium(maps.base_map(grid, draw=True, states_geojson=get_states_geojson(), height=520),
                    key=f"draw_map_{st.session_state.get('draw_gen', 0)}", height=520, use_container_width=True,
                    feature_group_to_add=maps.data_layer(grid, overview["rgba"], drawn),
                    returned_objects=["last_active_drawing"], pixelated=True)
    drawing = (out or {}).get("last_active_drawing")
    if drawing and drawing.get("geometry", {}).get("type") == "Polygon":
        new_area = {"type": "polygon", "coords": drawing["geometry"]["coordinates"][0]}
        if new_area != st.session_state.get("drawn_area"):
            st.session_state["drawn_area"] = new_area
            st.rerun()
    if drawn is None:
        st.info("No shape drawn yet — showing the whole of Brazil.")
    else:
        def _clear_shape():
            st.session_state.pop("drawn_area", None)
            st.session_state["draw_gen"] = st.session_state.get("draw_gen", 0) + 1  # new map, without the old shape

        st.button("Clear shape", on_click=_clear_shape)

area_json = json.dumps(area, sort_keys=True)
keys = get_keys(area_json)
if len(keys) == 0:
    st.warning("No 0.1° grid cell with fire detections inside this area. Try a larger area.")
    st.stop()

# Always computed on the full record, so the 2003–2025 baseline does not depend on the chosen period
monthly_full = get_monthly(area_json, (y_min, y_max))
monthly = monthly_full[monthly_full["year"].between(*years)].reset_index(drop=True)
valid = monthly.dropna(subset=["fires"])
if valid.empty:
    st.warning("No data in this period.")
    st.stop()

st.caption(f"{years[0]}–{years[1]} · {valid['fires'].sum():,.0f} VIIRS-equivalent fires · "
           f"{len(keys):,} grid cells of 0.1° (≈11 km)")

# ---------------------------------------------------------------------------
# Headline numbers: the latest month and year against the normal, then the record and the season
# ---------------------------------------------------------------------------
last = valid.iloc[-1]
last_y, last_m = int(last["year"]), int(last["month"])
peak = valid.loc[valid["fires"].idxmax()]
season = data.typical_season(monthly_full)
year_now = data.year_summary(monthly_full, last_y)
NORMAL_HELP = "Normal = mean of the same month(s) in 2003–2025, in the same area."

c1, c2, c3, c4 = st.columns(4)
pct_last = float(last["anomaly_pct"]) if last["status"] != "partial" else float("nan")
c1.metric(f"Latest month · {MONTHS[last_m - 1]} {last_y}", f"{last['fires']:,.0f} fires",
          delta=f"{pct_last:+.0f}% vs normal" if np.isfinite(pct_last) else None, delta_color="inverse",
          help=NORMAL_HELP)
span = month_span(year_now["first_month"], year_now["last_month"])
pct_year = year_now["pct"] if not year_now["partial"] else float("nan")
c2.metric(f"{last_y} ({span})", f"{year_now['total']:,.0f} fires",
          delta=f"{pct_year:+.0f}% vs normal" if np.isfinite(pct_year) else None, delta_color="inverse",
          help=NORMAL_HELP + (" 2000–2002 are under-counted (MODIS Terra only) and are not compared."
                              if year_now["partial"] else ""))
c3.metric("Record month in the period", f"{MONTHS[int(peak['month']) - 1]} {int(peak['year'])}",
          help=f"{peak['fires']:,.0f} VIIRS-equivalent fires")
if season:
    c4.metric("Typical fire season", month_span(season["window"][0], season["window"][-1]),
              help=f"These three months hold {season['window_share']:.0f}% of the fires of a typical year "
                   f"(2003–2025). Peak month: {MONTHS[season['peak_month'] - 1]}.")


# ---------------------------------------------------------------------------
# Tabs (only the open tab runs)
# ---------------------------------------------------------------------------
def render_calendar() -> None:
    st.subheader("When does it burn, and how much?")
    view = st.radio("Colour by", ["Fire count", "Compared to normal"], horizontal=True,
                    help="Compared to normal: each month vs the mean of the same month in 2003–2025, in the same area.")
    if view == "Fire count":
        text = (f"Each row is a year, each column a month; **darker = more fires**. "
                f"The record in this period is **{MONTHS[int(peak['month']) - 1]} {int(peak['year'])}** "
                f"({peak['fires']:,.0f} fires).")
        if season:
            text = (f"Fire here concentrates in **{month_span(season['window'][0], season['window'][-1])}** "
                    f"({season['window_share']:.0f}% of a typical year). " + text)
    else:
        far = monthly[monthly["anomaly_band"] == 5]
        text = "**Blue = fewer fires than normal for that month, red = more.** "
        if len(far):
            latest = far.iloc[-1]
            text += (f"{len(far)} month{'s' if len(far) > 1 else ''} in this period had more than twice the normal; "
                     f"the most recent was **{MONTHS[int(latest['month']) - 1]} {int(latest['year'])}** "
                     f"({latest['anomaly_pct']:+.0f}%).")
        else:
            text += "No month in this period had more than twice the normal."
    st.markdown(text)
    st.plotly_chart(charts.calendar(monthly, log_scale, "anomaly" if view.startswith("Compared") else "count"),
                    width="stretch", config=charts.PLOT_CONFIG)
    st.caption(
        "Each square = one month inside the area, in VIIRS-equivalent fire counts. Dotted line: from 2012 on the "
        "series is observed VIIRS. **\\*** estimated from MODIS × calibration factor (2003–Jan/2012) · "
        "**†** partial: MODIS Terra only (Nov/2000–2002), under-counted and therefore not compared to normal · "
        "grey = no data or not compared."
    )


def render_season() -> None:
    st.subheader("Is the fire season normal?")
    options = sorted(valid["year"].unique().tolist(), reverse=True)
    c1, c2 = st.columns(2)
    s_year = c1.selectbox("Year", options, key="season_year")
    compare = c2.selectbox("Compare with", ["—"] + [y for y in options if y != s_year], key="season_compare")
    ys = data.year_summary(monthly_full, s_year)
    span = month_span(ys["first_month"], ys["last_month"])
    if ys["partial"]:
        st.markdown(f"**{s_year} ({span}): {ys['total']:,.0f} fires.** This year is under-counted (MODIS Terra "
                    "only until Jul/2002), so it is not compared with the normal.")
    else:
        st.markdown(
            f"**{s_year} ({span}): {ys['total']:,.0f} fires, {vs_normal(ys['pct'])}.** "
            f"{ys['above_range']} of {ys['n_months']} months above the usual range and {ys['below_range']} below; "
            f"the strongest month was {MONTHS[ys['peak_month'] - 1]} ({ys['peak_fires']:,.0f} fires).")
    st.plotly_chart(charts.season_tracker(monthly_full, data.season_envelope(monthly_full), s_year,
                                          None if compare == "—" else int(compare)),
                    width="stretch", config=charts.PLOT_CONFIG)
    st.caption("Shaded band: where 8 out of 10 years of 2003–2025 fall in each month (10th–90th percentile); "
               "dotted line: median. A line above the band is an unusually strong month, below it an unusually weak one.")

    st.divider()
    st.subheader("One month across the years")
    months_with_data = monthly_full[(monthly_full["year"] == s_year) & monthly_full["fires"].notna()]["month"].tolist()
    a_month = st.selectbox("Month", months_with_data, index=months_with_data.index(ys["peak_month"]),
                           format_func=lambda m: MONTHS[m - 1], key=f"anomaly_month_{s_year}")
    an = data.anomaly(monthly_full, s_year, a_month)
    name = f"{MONTHS[a_month - 1]} {s_year}"
    c1, c2, c3 = st.columns(3)
    c1.metric(name, f"{an['value']:,.0f} fires")
    c2.metric("Normal (2003–2025 mean)", f"{an['mean']:,.0f} fires")
    comparable = an["band"] is not None and np.isfinite(an["pct"])
    c3.metric("Compared to normal", f"{an['pct']:+.0f}%" if comparable else "n/a")
    if comparable:
        st.markdown(f"**{name} was {vs_normal(an['pct'])}** ({an['band']}): more fires than in {an['rank_below']} "
                    f"of the {an['n_compared']} other years of 2003–2025 in the same month.")
    elif an["status"] == "partial":
        st.markdown(f"**{name} is under-counted** (MODIS Terra only), so it is not compared with the normal.")
    st.plotly_chart(charts.anomaly_bars(an["history"], s_year, an["mean"]), width="stretch", config=charts.PLOT_CONFIG)
    st.caption("Each bar is the same calendar month in a different year; dashed line = normal (mean of 2003–2025). "
               "Orange: selected year · grey: estimated or partial years (MODIS-based).")


def render_map() -> None:
    grid = get_grid()
    st.subheader("Where does it burn?")
    playing = st.session_state.get("play_i")
    if playing is not None:  # month animation: set the month before the widget is drawn
        st.session_state["map_month"] = MONTHS[playing]
    c1, c2, c3 = st.columns([4, 2, 3])
    metric = c1.radio("Show", list(maps.METRICS), format_func=maps.METRICS.get, horizontal=True, key="map_metric")
    m_choice = c2.selectbox("Month", ["Any month"] + MONTHS, key="map_month", disabled=metric == "season",
                            help="Restrict the map to one calendar month, e.g. where it burns in September.")
    basemap = c3.toggle("Real basemap (needs internet)", value=True, key="map_basemap",
                        help="Pan and zoom over a street map. Turn it off for the built-in map, which works offline.")
    month = None if metric == "season" or m_choice == "Any month" else MONTHS.index(m_choice) + 1

    freq = get_frequency(years, month)
    layer = maps.render(grid, freq, metric, keys, log=log_scale, month=month)
    n_years = len(data.comparable_years(years, month))
    st.markdown(maps.takeaway(freq, keys, metric, month, n_years))
    st.html(maps.legend_html(layer["legend"]))

    fit = None if area["type"] == "brazil" else grid.cell_bounds(keys)
    clicked = None
    if basemap:
        from streamlit_folium import st_folium

        out = st_folium(maps.base_map(grid, fit=fit, states_geojson=get_states_geojson(), height=640), key="fire_map",
                        height=640, use_container_width=True, pixelated=True,
                        feature_group_to_add=maps.data_layer(grid, layer["rgba"], area, layer["sel"]),
                        returned_objects=["last_clicked"])
        clicked = (out or {}).get("last_clicked")
    else:
        st.plotly_chart(charts.cell_map(grid, layer, maps.hover_data(grid, freq), fit), width="stretch",
                        config={**charts.PLOT_CONFIG, "scrollZoom": True})

    if clicked:
        key = grid.key_at(clicked["lat"], clicked["lng"])
        row = freq[freq["key"] == key]
        if len(row):
            r = row.iloc[0]
            when = f" in {MONTHS[month - 1]}" if month else ""
            peak_m = MONTHS[int(r["peak_month"]) - 1] if np.isfinite(r["peak_month"]) else "—"
            where = "" if np.isin(key, keys) else " · outside the selected area"
            st.markdown(f"📍 **{r.get('estado_nome', '')}** · {r['bioma']} · cell at {r['lat']:.2f}, {r['lon']:.2f}{where}: "
                        f"**{r['fires_per_year']:,.1f} fires per year**{when}, fire in **{r['pct_years']:.0f}%** of the "
                        f"years, peak month **{peak_m}**.")
        else:
            st.markdown("📍 No fire detected in this cell in the whole record.")

    if metric != "season":
        st.button("▶ Play the 12 months" if playing is None else "⏹ Stop", key="play_button",
                  on_click=lambda: st.session_state.update(play_i=0 if playing is None else None),
                  help="Shows the fire season moving across the country, month by month.")
    hint = "Click the map to read a cell. " if basemap else "Hover to read a cell; scroll to zoom, drag to move. "
    if not basemap:
        hint += "Light grey = Brazil without fire detections. "
    st.caption(f"{hint}Each pixel is a 0.1° grid cell (≈11 km). State boundaries follow the grid cells counted "
               "for each state. The selected area is in colour; the rest of Brazil stays visible in grey.")

    if playing is not None:
        time.sleep(1.2)
        st.session_state["play_i"] = playing + 1 if playing < 11 else None
        st.rerun()


def render_method() -> None:
    st.subheader("Can two satellites be read as one record?")
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
    gap = data.calibration_gap(monthly_full)
    if np.isfinite(gap):
        st.markdown(f"**In this area, MODIS × k (orange) stays within {gap:.1f}% of the observed VIIRS (blue), "
                    "year by year, across the calibration window 2012–2019.** Grey is MODIS before the conversion; "
                    "the independent check (leaving each year out) is in the table below.")
    st.plotly_chart(charts.harmonization_check(monthly_full), width="stretch", config=charts.PLOT_CONFIG)
    st.caption("Selected area, whole record. In 2012–2019 MODIS × k should track observed VIIRS (calibration); the "
               "growing gap in recent years reflects the Terra/Aqua orbital drift — one reason to use VIIRS as "
               "the reference.")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**Calibration factor k by biome and month** (darker = VIIRS sees more fires per MODIS fire)")
        st.plotly_chart(charts.factors_heatmap(data.load_factors()), width="stretch", config=charts.PLOT_CONFIG)
    with c2:
        st.markdown("**Validation (leave-one-year-out, 2012–2019)**")
        val = data.load_validation().rename(columns={
            "bioma": "Biome", "focos_snpp_ano": "VIIRS fires / year", "erro_medio_abs_pct": "Mean abs. error (%)"})
        st.dataframe(val, hide_index=True, width="stretch")


def render_download() -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "area"
    stem = f"{slug}_{years[0]}-{years[1]}"
    st.subheader("Take the data with you")
    smaller = "Choose a state or a biome, or shorten the period in the sidebar."

    st.markdown("**Monthly counts for the selected area**")
    out_month = monthly[["year", "month", "fires", "status", "modis_raw", "viirs_raw"]].rename(
        columns={"fires": "fires_viirs_eq"})
    st.download_button(f"Download monthly CSV ({len(out_month):,} rows)", csv_bytes(out_month),
                       f"firepoints_monthly_{stem}.csv", "text/csv", on_click="ignore")

    st.markdown("**Counts per grid cell and month**")
    sub = data.filter_series(series, keys, years)
    if len(sub) > 1_000_000:
        st.info(f"{len(sub):,} rows are too many for one file (limit 1,000,000). {smaller}")
    else:
        cells = get_cells()

        def per_cell_csv() -> bytes:  # built only when the button is clicked
            c = cells.set_index("key")
            return csv_bytes(pd.DataFrame({
                "lat": c.loc[sub["key"], "lat"].to_numpy(), "lon": c.loc[sub["key"], "lon"].to_numpy(),
                "biome": sub["bioma"].to_numpy(), "year": sub["ano"].to_numpy(), "month": sub["mes"].to_numpy(),
                "fires_viirs_eq": sub["focos"].round(2).to_numpy(), "status": sub["status"].to_numpy(),
            }))

        st.download_button(f"Download per-cell CSV ({len(sub):,} rows)", per_cell_csv,
                           f"firepoints_cells_{stem}.csv", "text/csv", on_click="ignore")

    st.markdown("**Individual fire detections** (raw MODIS and VIIRS points, *not* harmonized)")
    if data.points_available():
        n_pts = get_point_count(area_json, years)
        last_data = f"{MONTHS[data.LAST_MONTH[1] - 1]} {data.LAST_MONTH[0]}"
        if n_pts > 1_500_000:
            st.info(f"{n_pts:,} detections are too many for one file (limit 1,500,000). {smaller}")
        elif n_pts:
            st.download_button(f"Download fire points CSV ({n_pts:,} detections)",
                               lambda: csv_bytes(data.fire_points(keys, years)),
                               f"firepoints_detections_raw_{stem}.csv", "text/csv", on_click="ignore")
            st.caption(f"Detections up to {last_data}, the last month of the harmonized series.")
        else:
            st.caption("No detection in this area and period.")
    else:
        st.info("Individual detections are not bundled in this deployment. "
                "They can be downloaded from [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/download/).")


def render_about() -> None:
    st.markdown(
        """
**Choose an area** in the sidebar: the whole country, one or more states or biomes, a lat/lon box, or a shape drawn on the map.
Cells are included when their centre falls inside the area.

**Headline numbers.** The latest month and the latest year of the period, each against its *normal*: the mean of the
same month(s) in 2003–2025, in the same area. Red arrow = more fire than normal.

**Calendar.** Rows are years, columns are months. Colour = number of fires (light = few, dark = many; log scale by default).
Grey = no data (before Nov/2000 or after the last processed month). Marks next to the year:
\\* estimated from MODIS, † partial (Terra only). The dotted line marks 2012, when observed VIIRS takes over.

**Season.** One year against the usual range of each month (the band where 8 out of 10 years of 2003–2025 fall).
Below it, one calendar month across all years.

**Unit.** *VIIRS-equivalent fires*: the number of hot spots VIIRS S-NPP would have detected.
Before 2012 this is MODIS × k (see *Method*).

**Compared to normal / anomaly.** Each month vs the mean of the same calendar month in 2003–2025 (complete years),
in the same area. Bands: far below (<0.5×), below (0.5–0.8×), normal (0.8–1.25×), above (1.25–2×), far above (>2×).
Nov/2000–2002 are not compared: only MODIS Terra was flying, so those months are under-counted.

**Map.** Each pixel is a 0.1° cell (≈11 km), over a real map you can pan and zoom. Three readings:
*fires per year* (how much it burns), *% of years with fire* (how often fire comes back: share of the years with at
least one detection in that cell, in the chosen month) and *peak season* (when it burns most). The selected area is
in colour and outlined; the rest of Brazil stays visible in grey. Click a cell to read its numbers.

**Limitations.** A hot spot is not burned area; clouds hide fires; the factor assumes a stable MODIS/VIIRS relation
per biome and month; the most recent months may still be near-real-time (provisional) data.
"""
    )


TABS = {
    "📅 Calendar": render_calendar,
    "📈 Season vs normal": render_season,
    "🗺️ Map": render_map,
    "🧪 Method & validation": render_method,
    "⬇️ Download": render_download,
    "ℹ️ How to read": render_about,
}
tab_map_label = "🗺️ Map"
containers = st.tabs(list(TABS), on_change="rerun", key="tab")
for (tab_label, render), container in zip(TABS.items(), containers):
    if container.open is False:  # only the open tab runs (None = no state tracking: run everything)
        if tab_label == tab_map_label:
            st.session_state["play_i"] = None  # leaving the map stops the month animation
        continue
    with container:
        render()
