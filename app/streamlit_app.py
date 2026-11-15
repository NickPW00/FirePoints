# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1642_nicholas_stack-app.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1815_mariaeliza_mapa-windy.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1800_nicholas_melhorias-app-mapa.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_2331_mariaeliza_creditos-fontes.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1732_mariaeliza_design-app.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1855_mariaeliza_mapa-pixels.md
"""FirePoints — harmonized MODIS + VIIRS fire calendar for Brazil.

Run locally:  streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import importlib

import charts
import data
import i18n
import maps

# Community Cloud can keep the old copy of these modules after a deploy (only this script is
# re-read), so reload any module whose file changed since it was imported.
for _mod in (i18n, data, maps, charts):
    _mtime = Path(_mod.__file__).stat().st_mtime
    if getattr(_mod, "_fp_mtime", None) != _mtime:
        importlib.reload(_mod)
        _mod._fp_mtime = _mtime

from i18n import band_word, biome, month as mname, months, num, region, t

st.set_page_config(page_title=t("page_title"), page_icon="🔥", layout="wide")

STATES_GEOJSON = data.STATES_GEOJSON  # smooth state borders (pipeline/07_divisas.py); optional
# Space Apps small logo (orbit only, no text): official file from spaceappschallenge.org/brand, unaltered
SPACE_APPS_LOGO = Path(__file__).resolve().parent.parent / "docs" / "img" / "space-apps-small-logo-black.svg"
SPACE_APPS_URL = "https://www.spaceappschallenge.org/"


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


def wheel_text() -> dict:
    """Texts of the scroll-zoom button of the map, in the current language."""
    return {"on": t("wheel_on"), "off": t("wheel_off"), "tip": t("wheel_tip")}


@st.cache_resource
def get_municipalities(states: tuple[str, ...]) -> list[dict]:
    """Municipal borders of the selected states (pipeline/07_divisas.py); empty if not available."""
    out = []
    for uf in states:
        f = data.MUNICIPALITIES_DIR / f"{uf}.geojson"
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


@st.cache_resource(show_spinner="Loading the map grid…")
def get_fine() -> dict | None:
    """Fine grid (0.025°) for the map picture; None if the file is not there (the map then shows 0.1° cells)."""
    grid = get_grid()
    return data.load_fine(grid.i0, grid.j0, grid.shape)


@st.cache_resource(show_spinner=False, max_entries=3)
def get_fine_peak(years: tuple[int, int]) -> np.ndarray:
    return data.fine_peak_month(get_fine(), years)


@st.cache_resource
def get_cities() -> list:
    return data.load_cities()


def fine_layer(metric: str, sel_keys, month: int | None, period: tuple[int, int], log: bool) -> dict | None:
    """Map picture with small pixels (None if the fine grid is not available)."""
    fine = get_fine()
    if fine is None:
        return None
    stats = {"factor": data.FINE, "cell": f"{num(data.CELL / data.FINE, 3)}°"}
    if metric == "season":
        stats["peak_month"] = get_fine_peak(period)
    else:
        stats.update(data.fine_frequency(fine, month, period))
    return maps.fine_layer(get_grid(), stats, metric, sel_keys, log=log, month=month)


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
    return mname(first) if first == last else f"{mname(first)}–{mname(last)}"


def vs_normal(pct: float) -> str:
    """'37% above normal' / '12% below normal' / 'on the normal'."""
    if not np.isfinite(pct):
        return t("not_comparable")
    if abs(pct) < 0.5:
        return t("on_normal")
    return t("above_normal" if pct > 0 else "below_normal", pct=num(abs(pct)))


def area_label(area: dict, states: pd.Series) -> str:
    kind = area["type"]
    if kind == "states":
        names = [states.get(uf, uf) for uf in area["states"]]
        return ", ".join(names) if len(names) <= 3 else t("label_n_states", n=len(names))
    if kind == "regions":
        names = [region(r) for r in area["regions"]]
        return ", ".join(names) if len(names) <= 3 else t("label_n_regions", n=len(names))
    if kind == "biomes":
        return (", ".join(biome(b) for b in area["biomes"]) if len(area["biomes"]) <= 3
                else t("label_n_biomes", n=len(area["biomes"])))
    return {"bbox": t("label_box"), "polygon": t("label_drawn")}.get(kind, t("label_brazil"))


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def space_apps_credit() -> None:
    """Small 'made for Space Apps' line with the event's small logo, linked to its home page."""
    text = f'{t("made_for")} <a href="{SPACE_APPS_URL}" target="_blank">NASA Space Apps Challenge 2026</a>'
    if SPACE_APPS_LOGO.exists():
        svg = base64.b64encode(SPACE_APPS_LOGO.read_bytes()).decode("ascii")
        logo = (f'<a href="{SPACE_APPS_URL}" target="_blank"><img src="data:image/svg+xml;base64,{svg}" '
                f'alt="Space Apps logo" width="28" style="vertical-align:middle;margin-right:8px"></a>')
    else:
        logo = ""
    st.markdown(f'<div style="font-size:0.8rem;opacity:0.8">{logo}{text}</div>', unsafe_allow_html=True)


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
    st.radio(t("language"), list(i18n.LANGS), format_func=i18n.LANGS.get, horizontal=True, key="lang")
    st.title("🔥 FirePoints")
    st.caption(t("tagline"))

    modes = ["brazil", "region", "state", "biome", "draw", "box"]
    if states.empty:
        modes = [m for m in modes if m not in ("state", "region")]
    mode = st.radio(t("area"), modes, format_func=lambda m: t(f"mode_{m}"), key="area_mode")
    area = {"type": "brazil"}
    if mode == "region":
        chosen = st.multiselect(t("regions"), list(data.REGIONS), default=["Sudeste"], format_func=region,
                                key="regions_sel")
        if chosen:
            area = {"type": "regions", "regions": chosen}
        else:
            st.caption(t("none_region"))
    elif mode == "state":
        chosen = st.multiselect(t("states"), list(states.index), default=["RJ"] if "RJ" in states.index else None,
                                format_func=lambda uf: f"{uf} – {states[uf]}", key="states_sel")
        if chosen:
            area = {"type": "states", "states": chosen}
        else:
            st.caption(t("none_state"))
    elif mode == "biome":
        chosen = st.multiselect(t("biomes"), biomes, default=["Cerrado"], format_func=biome, key="biomes_sel")
        if chosen:
            area = {"type": "biomes", "biomes": chosen}
        else:
            st.caption(t("none_biome"))
    elif mode == "box":
        c1, c2 = st.columns(2)
        lat_min = c1.number_input(t("lat_min"), -34.0, 6.0, -23.4, 0.1)
        lat_max = c2.number_input(t("lat_max"), -34.0, 6.0, -20.7, 0.1)
        lon_min = c1.number_input(t("lon_min"), -74.0, -28.0, -45.0, 0.1)
        lon_max = c2.number_input(t("lon_max"), -74.0, -28.0, -40.9, 0.1)
        area = {"type": "bbox", "lat_min": min(lat_min, lat_max), "lat_max": max(lat_min, lat_max),
                "lon_min": min(lon_min, lon_max), "lon_max": max(lon_min, lon_max)}
    elif mode == "draw":
        area = st.session_state.get("drawn_area", {"type": "brazil"})

    years = st.slider(t("period"), y_min, y_max, (y_min, y_max))
    log_scale = st.toggle(t("log_scale"), value=True, help=t("log_help"))

    st.divider()
    st.caption(t("data_note"))
    space_apps_credit()

label = area_label(area, states)
st.title(t("title", area=label))
sel_states = data.states_of(area)          # outlined with the smooth IBGE border, with their municipalities

# Drawing tool: the user draws over the fire map itself (the rest of the page follows the shape)
if mode == "draw":
    from streamlit_folium import st_folium

    st.markdown(t("draw_intro"))
    grid = get_grid()
    record = (y_min, y_max)
    all_keys = get_cells()["key"].to_numpy()
    overview = (fine_layer("fires", all_keys, None, record, True)
                or maps.render(grid, get_frequency(record, None), "fires", all_keys, log=True))
    drawn = area if area["type"] == "polygon" else None
    out = st_folium(maps.base_map(grid, draw=True, states_geojson=get_states_geojson(), height=520, wheel=wheel_text(),
                                  cities=get_cities()),
                    key=f"draw_map_{st.session_state.get('draw_gen', 0)}", height=520, use_container_width=True,
                    feature_group_to_add=maps.data_layer(grid, overview, drawn),
                    returned_objects=["last_active_drawing"], pixelated=True)
    drawing = (out or {}).get("last_active_drawing")
    if drawing and drawing.get("geometry", {}).get("type") == "Polygon":
        new_area = {"type": "polygon", "coords": drawing["geometry"]["coordinates"][0]}
        if new_area != st.session_state.get("drawn_area"):
            st.session_state["drawn_area"] = new_area
            st.rerun()
    if drawn is None:
        st.info(t("no_shape"))
    else:
        def _clear_shape():
            st.session_state.pop("drawn_area", None)
            st.session_state["draw_gen"] = st.session_state.get("draw_gen", 0) + 1  # new map, without the old shape

        st.button(t("clear_shape"), on_click=_clear_shape)

area_json = json.dumps(area, sort_keys=True)
keys = get_keys(area_json)
if len(keys) == 0:
    st.warning(t("no_cells"))
    st.stop()

# Always computed on the full record, so the 2003–2025 baseline does not depend on the chosen period
monthly_full = get_monthly(area_json, (y_min, y_max))
monthly = monthly_full[monthly_full["year"].between(*years)].reset_index(drop=True)
valid = monthly.dropna(subset=["fires"])
if valid.empty:
    st.warning(t("no_data_period"))
    st.stop()

st.caption(t("summary", y0=years[0], y1=years[1], fires=num(valid["fires"].sum()), cells=num(len(keys))))

# ---------------------------------------------------------------------------
# Headline numbers: the latest month and year against the normal, then the record and the season
# ---------------------------------------------------------------------------
last = valid.iloc[-1]
last_y, last_m = int(last["year"]), int(last["month"])
peak = valid.loc[valid["fires"].idxmax()]
season = data.typical_season(monthly_full)
year_now = data.year_summary(monthly_full, last_y)
NORMAL_HELP = t("normal_help")

c1, c2, c3, c4 = st.columns(4)
pct_last = float(last["anomaly_pct"]) if last["status"] != "partial" else float("nan")
c1.metric(t("m_latest", m=mname(last_m), y=last_y), t("fires_unit", n=num(last["fires"])),
          delta=t("vs_normal_delta", pct=f"{pct_last:+.0f}") if np.isfinite(pct_last) else None, delta_color="inverse",
          help=NORMAL_HELP)
span = month_span(year_now["first_month"], year_now["last_month"])
pct_year = year_now["pct"] if not year_now["partial"] else float("nan")
c2.metric(f"{last_y} ({span})", t("fires_unit", n=num(year_now["total"])),
          delta=t("vs_normal_delta", pct=f"{pct_year:+.0f}") if np.isfinite(pct_year) else None, delta_color="inverse",
          help=NORMAL_HELP + (t("partial_help") if year_now["partial"] else ""))
c3.metric(t("m_record"), f"{mname(peak['month'])} {int(peak['year'])}",
          help=t("m_record_help", n=num(peak["fires"])))
if season:
    c4.metric(t("m_season"), month_span(season["window"][0], season["window"][-1]),
              help=t("m_season_help", share=num(season["window_share"]), peak=mname(season["peak_month"])))


# ---------------------------------------------------------------------------
# Tabs (only the open tab runs)
# ---------------------------------------------------------------------------
def render_calendar() -> None:
    st.subheader(t("cal_title"))
    view = st.radio(t("colour_by"), ["count", "anomaly"], horizontal=True, key="cal_view",
                    format_func=lambda v: t("view_count" if v == "count" else "view_anomaly"), help=t("view_help"))
    if view == "count":
        text = t("cal_count_text", m=mname(peak["month"]), y=int(peak["year"]), n=num(peak["fires"]))
        if season:
            text = t("cal_season_text", span=month_span(season["window"][0], season["window"][-1]),
                     share=num(season["window_share"])) + text
    else:
        far = monthly[monthly["anomaly_band"] == 5]
        text = t("cal_anom_text")
        if len(far):
            latest = far.iloc[-1]
            text += t("cal_far", n=len(far), m=mname(latest["month"]), y=int(latest["year"]),
                      pct=f"{latest['anomaly_pct']:+.0f}")
        else:
            text += t("cal_far_none")
    st.markdown(text)
    st.plotly_chart(charts.calendar(monthly, log_scale, view), width="stretch", config=charts.PLOT_CONFIG)
    st.caption(t("cal_caption"))


def render_season() -> None:
    st.subheader(t("season_title"))
    options = sorted(valid["year"].unique().tolist(), reverse=True)
    c1, c2 = st.columns(2)
    s_year = c1.selectbox(t("year"), options, key="season_year")
    compare = c2.selectbox(t("compare_with"), ["—"] + [y for y in options if y != s_year], key="season_compare")
    ys = data.year_summary(monthly_full, s_year)
    span = month_span(ys["first_month"], ys["last_month"])
    if ys["partial"]:
        st.markdown(t("season_partial", y=s_year, span=span, n=num(ys["total"])))
    else:
        st.markdown(t("season_text", y=s_year, span=span, n=num(ys["total"]), vs=vs_normal(ys["pct"]),
                      above=ys["above_range"], months=ys["n_months"], below=ys["below_range"],
                      peak=mname(ys["peak_month"]), peak_n=num(ys["peak_fires"])))
    st.plotly_chart(charts.season_tracker(monthly_full, data.season_envelope(monthly_full), s_year,
                                          None if compare == "—" else int(compare)),
                    width="stretch", config=charts.PLOT_CONFIG)
    st.caption(t("season_caption"))

    st.divider()
    st.subheader(t("one_month_title"))
    months_with_data = monthly_full[(monthly_full["year"] == s_year) & monthly_full["fires"].notna()]["month"].tolist()
    a_month = st.selectbox(t("month"), months_with_data, index=months_with_data.index(ys["peak_month"]),
                           format_func=mname, key=f"anomaly_month_{s_year}")
    an = data.anomaly(monthly_full, s_year, a_month)
    name = f"{mname(a_month)} {s_year}"
    c1, c2, c3 = st.columns(3)
    c1.metric(name, t("fires_unit", n=num(an["value"])))
    c2.metric(t("normal_mean"), t("fires_unit", n=num(an["mean"])))
    comparable = an["band"] is not None and np.isfinite(an["pct"])
    c3.metric(t("compared"), f"{an['pct']:+.0f}%" if comparable else "n/a")
    if comparable:
        st.markdown(t("month_text", name=name, vs=vs_normal(an["pct"]), band=band_word(an["band"]),
                      rank=an["rank_below"], n=an["n_compared"]))
    elif an["status"] == "partial":
        st.markdown(t("month_partial", name=name))
    st.plotly_chart(charts.anomaly_bars(an["history"], s_year, an["mean"]), width="stretch", config=charts.PLOT_CONFIG)
    st.caption(t("bars_caption"))


def render_map() -> None:
    grid = get_grid()
    st.subheader(t("map_title"))
    playing = st.session_state.get("play_i")
    if playing is not None:  # month animation: set the month before the widget is drawn
        st.session_state["map_month"] = playing + 1
    c1, c2, c3 = st.columns([4, 2, 3])
    metric = c1.radio(t("show"), list(maps.METRICS), format_func=lambda k: t(maps.METRICS[k]), horizontal=True,
                      key="map_metric")
    m_choice = c2.selectbox(t("month"), list(range(13)), key="map_month", disabled=metric == "season",
                            format_func=lambda m: t("any_month") if m == 0 else mname(m), help=t("month_help"))
    basemap = c3.toggle(t("basemap"), value=True, key="map_basemap", help=t("basemap_help"))
    smooth = c3.toggle(t("smooth"), value=False, key="map_smooth", help=t("smooth_help"), disabled=not basemap)
    month = None if metric == "season" or m_choice == 0 else int(m_choice)

    freq = get_frequency(years, month)
    # Map picture: small pixels from the fine grid when available; otherwise (and offline) the 0.1° cells
    layer = fine_layer(metric, keys, month, years, log_scale) if basemap else None
    fine_px = layer is not None
    if layer is None:
        layer = maps.render(grid, freq, metric, keys, log=log_scale, month=month)
    n_years = len(data.comparable_years(years, month))
    st.markdown(maps.takeaway(freq, keys, metric, month, n_years))
    st.html(maps.legend_html(layer["legend"]))

    fit = None if area["type"] == "brazil" else grid.cell_bounds(keys)
    clicked = None
    if basemap:
        from streamlit_folium import st_folium

        states_geo = get_states_geojson()
        base = maps.base_map(grid, fit=fit, states_geojson=states_geo, height=640, wheel=wheel_text(),
                             municipalities=get_municipalities(tuple(sel_states)), cities=get_cities())
        out = st_folium(base, key="fire_map", height=640, use_container_width=True, pixelated=not smooth,
                        feature_group_to_add=maps.data_layer(grid, layer, area, smooth=smooth,
                                                             states_geojson=states_geo, selected_states=sel_states),
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
            when = t("in_month", m=mname(month)) if month else ""
            peak_m = mname(r["peak_month"]) if np.isfinite(r["peak_month"]) else "—"
            where = "" if np.isin(key, keys) else t("outside_sel")
            st.markdown(t("cell_read", state=r.get("estado_nome", ""), biome=biome(r["bioma"]),
                          lat=f"{r['lat']:.2f}", lon=f"{r['lon']:.2f}", where=where, fpy=num(r["fires_per_year"], 1),
                          when=when, pct=num(r["pct_years"]), peak=peak_m))
        else:
            st.markdown(t("no_fire_cell"))

    if metric != "season":
        st.button(t("play") if playing is None else t("stop"), key="play_button",
                  on_click=lambda: st.session_state.update(play_i=0 if playing is None else None),
                  help=t("play_help"))
    hint = t("hint_click") if basemap else t("hint_hover")
    if not basemap:
        hint += t("hint_grey")
    st.caption(hint + (t("map_caption_fine", cell=num(data.CELL / data.FINE, 3)) if fine_px else t("map_caption")))

    if playing is not None:
        time.sleep(1.2)
        st.session_state["play_i"] = playing + 1 if playing < 11 else None
        st.rerun()


def render_method() -> None:
    st.subheader(t("method_title"))
    st.markdown(t("method_body"))
    gap = data.calibration_gap(monthly_full)
    if np.isfinite(gap):
        st.markdown(t("method_gap", gap=num(gap, 1)))
    st.plotly_chart(charts.harmonization_check(monthly_full), width="stretch", config=charts.PLOT_CONFIG)
    st.caption(t("method_caption"))
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(t("factor_title"))
        st.plotly_chart(charts.factors_heatmap(data.load_factors()), width="stretch", config=charts.PLOT_CONFIG)
    with c2:
        st.markdown(t("validation_title"))
        val = data.load_validation()
        val["bioma"] = val["bioma"].map(biome)
        val = val.rename(columns={"bioma": t("col_biome"), "focos_snpp_ano": t("col_viirs_year"),
                                  "erro_medio_abs_pct": t("col_error")})
        st.dataframe(val, hide_index=True, width="stretch")


def render_download() -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "area"
    stem = f"{slug}_{years[0]}-{years[1]}"
    st.subheader(t("dl_title"))
    smaller = t("dl_smaller")

    st.markdown(t("dl_monthly"))
    out_month = monthly[["year", "month", "fires", "status", "modis_raw", "viirs_raw"]].rename(
        columns={"fires": "fires_viirs_eq"})
    st.download_button(t("dl_monthly_btn", n=num(len(out_month))), csv_bytes(out_month),
                       f"firepoints_monthly_{stem}.csv", "text/csv", on_click="ignore")

    st.markdown(t("dl_cells"))
    sub = data.filter_series(series, keys, years)
    if len(sub) > 1_000_000:
        st.info(t("dl_too_many", n=num(len(sub)), tip=smaller))
    else:
        cells = get_cells()

        def per_cell_csv() -> bytes:  # built only when the button is clicked
            c = cells.set_index("key")
            return csv_bytes(pd.DataFrame({
                "lat": c.loc[sub["key"], "lat"].to_numpy(), "lon": c.loc[sub["key"], "lon"].to_numpy(),
                "biome": sub["bioma"].map(biome).to_numpy(), "year": sub["ano"].to_numpy(), "month": sub["mes"].to_numpy(),
                "fires_viirs_eq": sub["focos"].round(2).to_numpy(), "status": sub["status"].to_numpy(),
            }))

        st.download_button(t("dl_cells_btn", n=num(len(sub))), per_cell_csv,
                           f"firepoints_cells_{stem}.csv", "text/csv", on_click="ignore")

    st.markdown(t("dl_points"))
    if data.points_available():
        n_pts = get_point_count(area_json, years)
        last_data = f"{mname(data.LAST_MONTH[1])} {data.LAST_MONTH[0]}"
        if n_pts > 1_500_000:
            st.info(t("dl_points_too_many", n=num(n_pts), tip=smaller))
        elif n_pts:
            def points_csv() -> bytes:
                pts = data.fire_points(keys, years)
                if "biome" in pts:
                    pts["biome"] = pts["biome"].map(biome)
                return csv_bytes(pts)

            st.download_button(t("dl_points_btn", n=num(n_pts)), points_csv,
                               f"firepoints_detections_raw_{stem}.csv", "text/csv", on_click="ignore")
            st.caption(t("dl_points_until", m=last_data))
        else:
            st.caption(t("dl_points_none"))
    else:
        st.info(t("dl_points_missing"))


def render_about() -> None:
    st.markdown(t("about"))


TABS = {
    "tab_calendar": render_calendar,
    "tab_season": render_season,
    "tab_map": render_map,
    "tab_method": render_method,
    "tab_download": render_download,
    "tab_about": render_about,
}
containers = st.tabs([t(k) for k in TABS], on_change="rerun", key="tab")
for (tab_key, render), container in zip(TABS.items(), containers):
    if container.open is False:  # only the open tab runs (None = no state tracking: run everything)
        if tab_key == "tab_map":
            st.session_state["play_i"] = None  # leaving the map stops the month animation
        continue
    with container:
        render()

st.divider()
st.caption(t("footer"))
