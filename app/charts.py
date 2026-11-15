# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1642_nicholas_stack-app.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1800_nicholas_melhorias-app-mapa.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1732_mariaeliza_design-app.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1815_mariaeliza_mapa-windy.md
"""Plotly figures for the FirePoints app (calendar, season, anomaly, fallback map, method)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from i18n import biome, month, months, num, plotly_separators, status as status_name, t
import maps
from maps import FIRE_RAMP, SEASONS

NO_DATA_GREY = "#d4d3ce"
# One sequential ramp for every "how many fires" encoding (light = few, dark = many); grey = no data
COLORSCALE = [[i / (len(FIRE_RAMP) - 1), c] for i, c in enumerate(FIRE_RAMP)]
K_SCALE = [[0, "#cde2fb"], [0.5, "#5598e7"], [1, "#0d366b"]]          # calibration factor (not a fire count)
STATUS_MARK = {"observed": "", "estimated": " *", "partial": " †"}
# Diverging, colour-blind safe (ColorBrewer RdBu): blue = fewer fires than normal, red = more
BAND_COLORS = ["#2166ac", "#92c5de", "#f7f7f7", "#f4a582", "#b2182b"]
BAND_KEYS = ["c_band1", "c_band2", "c_band3", "c_band4", "c_band5"]   # i18n keys of the 1–5 anomaly bands
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#31333f", "#8a8f98"
PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


def _layout(fig: go.Figure, height: int, **kwargs) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), separators=plotly_separators(),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", **kwargs)
    return fig


def _log_ticks(vmin: float, vmax: float) -> list[int]:
    """1–3–10 ticks inside the data range (at least two, so the scale can be read)."""
    cand = [t for k in range(8) for t in (10 ** k, 3 * 10 ** k)]
    ticks = [t for t in cand if vmin <= t <= vmax]
    return ticks if len(ticks) >= 2 else [t for t in cand if t <= vmax][-3:]


def calendar(monthly: pd.DataFrame, log_scale: bool = True, view: str = "count") -> go.Figure:
    """Fire calendar: years (rows) × months (columns).

    view="count": coloured by fire count; view="anomaly": coloured by the 1–5 band
    of the month compared with its 2003–2025 mean (``data.add_anomaly``). Partial months
    (Terra only) have no band: they stay grey in the anomaly view.
    """
    pivot = monthly.pivot(index="year", columns="month", values="fires").reindex(columns=range(1, 13))
    status = monthly.pivot(index="year", columns="month", values="status").reindex(columns=range(1, 13))
    years = pivot.index.to_list()

    z = pivot.to_numpy(dtype=float)
    zc = np.log10(z + 1) if log_scale else z

    # Year label marks how the year was built (estimated / partial)
    year_status = status.apply(
        lambda r: "partial" if (r == "partial").any() else ("estimated" if (r == "estimated").any() else "observed"),
        axis=1,
    )
    ylabels = [f"{y}{STATUS_MARK[year_status[y]]}" for y in years]

    pct = (monthly.pivot(index="year", columns="month", values="anomaly_pct").reindex(columns=range(1, 13)).to_numpy()
           if "anomaly_pct" in monthly else np.full(z.shape, np.nan))
    hover = np.empty(z.shape, dtype=object)
    MONTHS = months()
    for i, y in enumerate(years):
        for j in range(12):
            v, s = z[i, j], status.iat[i, j]
            if s is None or (isinstance(s, float) and np.isnan(s)):
                hover[i, j] = f"<b>{MONTHS[j]} {y}</b><br>{t('c_no_data')}"
            elif s == "partial":
                hover[i, j] = (f"<b>{MONTHS[j]} {y}</b><br>{t('c_fires_eq', n=num(v))}<br>{t('c_partial_hover')}")
            else:
                extra = f"<br>{t('c_vs_mean', pct=f'{pct[i, j]:+.0f}')}" if np.isfinite(pct[i, j]) else ""
                hover[i, j] = f"<b>{MONTHS[j]} {y}</b><br>{t('c_fires_eq', n=num(v))}{extra}<br>{status_name(s)}"

    if view == "anomaly":
        band = monthly.pivot(index="year", columns="month", values="anomaly_band").reindex(columns=range(1, 13))
        scale = [[k / 5, c] for k, c in enumerate(BAND_COLORS) for k in (k, k + 1)]
        trace = go.Heatmap(
            z=band.to_numpy(dtype=float), x=MONTHS, y=ylabels, text=hover, hoverinfo="text",
            colorscale=scale, zmin=0.5, zmax=5.5, xgap=2, ygap=2,
            colorbar=dict(title=t("c_vs_normal"), tickvals=[1, 2, 3, 4, 5], ticktext=[t(k) for k in BAND_KEYS],
                          len=0.6, thickness=14),
        )
    else:
        finite = z[np.isfinite(z)]
        vmax = float(finite.max()) if len(finite) else 1.0
        vmin = float(finite.min()) if len(finite) else 0.0
        if log_scale:
            ticks = _log_ticks(max(vmin, 1), max(vmax, 1))
            colorbar = dict(title=t("c_fires"), tickvals=np.log10(np.array(ticks) + 1), ticktext=[num(v) for v in ticks])
        else:
            colorbar = dict(title=t("c_fires"))
        colorbar.update(len=0.6, thickness=14)
        trace = go.Heatmap(z=zc, x=MONTHS, y=ylabels, text=hover, hoverinfo="text",
                           colorscale=COLORSCALE, colorbar=colorbar, xgap=2, ygap=2)

    fig = go.Figure(trace)
    _layout(fig, max(320, 22 * len(years) + 90), yaxis=dict(autorange="reversed", type="category"),
            xaxis=dict(side="top"))
    fig.update_layout(plot_bgcolor=NO_DATA_GREY)  # NaN cells (no data / not compared) show the background
    # From Feb/2012 the series is observed VIIRS: mark the change of source between 2011 and 2012
    if 2011 in years and 2012 in years:
        y = years.index(2012) - 0.5
        fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=y, y1=y,
                      line=dict(color=INK, width=1.5, dash="dot"))
    return fig


def season_tracker(monthly: pd.DataFrame, envelope: pd.DataFrame, year: int, compare: int | None = None) -> go.Figure:
    """One year (and optionally another) against the usual range of each month in 2003–2025."""
    fig = go.Figure()
    MONTHS = months()
    fig.add_scatter(x=MONTHS, y=envelope["p90"], mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False)
    fig.add_scatter(x=MONTHS, y=envelope["p10"], mode="lines", line=dict(width=0), fill="tonexty",
                    fillcolor="rgba(82,81,78,0.15)", name=t("c_usual"),
                    hoverinfo="skip")
    fig.add_scatter(x=MONTHS, y=envelope["p50"], mode="lines", line=dict(color=MUTED, width=2, dash="dot"),
                    name=t("c_median"), hovertemplate=t("c_median") + ": %{y:,.0f}<extra></extra>")
    series = [(year, ORANGE)] + ([(compare, BLUE)] if compare and compare != year else [])
    for yr, color in reversed(series):
        d = monthly[(monthly["year"] == yr) & monthly["fires"].notna()]
        if d.empty:
            continue
        fig.add_scatter(x=[month(m) for m in d["month"]], y=d["fires"], mode="lines+markers", name=str(yr),
                        line=dict(color=color, width=2.5), marker=dict(size=8, line=dict(color="white", width=2)),
                        hovertemplate=f"{yr}: %{{y:,.0f}} {t('c_fires_hover')}<extra></extra>")
        fig.add_annotation(x=month(d["month"].iloc[-1]), y=float(d["fires"].iloc[-1]), text=f"<b>{yr}</b>",
                           showarrow=False, xanchor="left", xshift=10, font=dict(color=INK))
    _layout(fig, 400, hovermode="x unified", legend=dict(orientation="h", y=-0.14),
            yaxis=dict(title=t("c_fires_month"), rangemode="tozero", tickformat="~s"),
            xaxis=dict(showgrid=False))
    fig.update_layout(margin=dict(l=10, r=50, t=10, b=10))
    return fig


def anomaly_bars(history: pd.DataFrame, year: int, mean: float) -> go.Figure:
    """Same calendar month across years, highlighting the chosen year, with the 2003–2025 mean."""
    colors = [ORANGE if y == year else ("#b9bec6" if s != "observed" else "#5b7fa8")
              for y, s in zip(history["year"], history["status"])]
    fig = go.Figure(go.Bar(x=history["year"], y=history["fires"], marker_color=colors,
                           hovertemplate="%{x}: %{y:,.0f} " + t("c_fires_hover") + "<extra></extra>"))
    if np.isfinite(mean):
        fig.add_hline(y=mean, line_dash="dash", line_color=INK, line_width=1.5)
        fig.add_annotation(xref="paper", x=1, y=mean, text=t("c_mean_label", n=num(mean)), showarrow=False,
                           xanchor="right", yanchor="bottom", bgcolor="rgba(255,255,255,0.85)", font=dict(color=INK))
    _layout(fig, 320, yaxis=dict(title=t("c_fires_eq_axis"), tickformat="~s"), xaxis=dict(dtick=2), bargap=0.25)
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    return fig


def cell_map(grid, layer: dict, hover: np.ndarray, fit: list[list[float]] | None = None) -> go.Figure:
    """Offline map: the grid as a raster (lat × lon), no basemap or WebGL needed, so it always renders.

    Same reading and colours as the basemap version (``maps.render``, ``maps.THEME``): selected area in
    full colour, the rest of Brazil in grey, state boundaries and labels from the grid. Everything goes in a
    single heatmap (one z array) to keep the page light:
    z = -2 Brazil without fire · [-1, 0) outside the selected area · [0, 1] selected area.
    """
    th = maps.THEME
    value, pos, sel = layer["value"], layer["t"], layer["sel"]   # not "t": that is the i18n function
    shown = np.isfinite(value)
    z = np.full(grid.shape, np.nan, dtype=np.float32)
    z[grid.inside & ~shown] = -2.0
    z[shown & ~sel] = (pos[shown & ~sel] - 1.0) * 0.998 - 0.001
    z[shown & sel] = pos[shown & sel]
    third = 1 / 3
    if layer["legend"]["kind"] == "classes":      # t is 0, 0.5 or 1
        c = [color for _, _, color in SEASONS]
        top = [[2 * third, c[0]], [0.75, c[0]], [0.75, c[1]], [0.9167, c[1]], [0.9167, c[2]], [1, c[2]]]
    else:
        stops = layer["legend"]["stops"]
        top = [[2 * third + i / (len(stops) - 1) * third, color] for i, color in enumerate(stops)]
        top[0][0] = 2 * third + 1e-4
    scale = [[0, th["no_fire"]], [third, th["faded_scale"][0]], [2 * third, th["faded_scale"][1]]] + top
    fig = go.Figure(go.Heatmap(
        z=z, x=grid.lons, y=grid.lats, zmin=-2, zmax=1, colorscale=scale, showscale=False, customdata=hover,
        hovertemplate=t("hover_cell"),
    ))
    if grid.border_lines:
        bx, by = [], []
        for (la0, lo0), (la1, lo1) in grid.border_lines:
            bx += [lo0, lo1, None]
            by += [la0, la1, None]
        fig.add_scatter(x=bx, y=by, mode="lines", line=dict(color=th["line"], width=0.8), opacity=0.6,
                        hoverinfo="skip", showlegend=False)
        fig.add_scatter(x=[lon for _, _, lon in grid.labels], y=[lat for _, lat, _ in grid.labels],
                        text=[uf for uf, _, _ in grid.labels], mode="text", textfont=dict(size=10, color=th["ink"]),
                        hoverinfo="skip", showlegend=False)
    (south, west), (north, east) = fit or grid.bounds
    pad = max(0.3, 0.08 * max(north - south, east - west))
    _layout(fig, 600, dragmode="pan",
            xaxis=dict(visible=False, range=[west - pad, east + pad]),
            yaxis=dict(visible=False, range=[south - pad, north + pad], scaleanchor="x", scaleratio=1))
    if th["plot_bg"]:
        fig.update_layout(plot_bgcolor=th["plot_bg"])
    return fig


def factors_heatmap(factors: pd.DataFrame) -> go.Figure:
    """Calibration factor k (VIIRS / MODIS) per biome and month."""
    fig = go.Figure(go.Heatmap(
        z=factors.to_numpy(), x=months(), y=[biome(b) for b in factors.index], colorscale=K_SCALE,
        text=np.round(factors.to_numpy(), 2), texttemplate="%{text}", colorbar=dict(title="k", thickness=14),
        hovertemplate="%{y}, %{x}: k = %{z:.2f}<extra></extra>", xgap=2, ygap=2,
    ))
    return _layout(fig, 300)


def harmonization_check(monthly: pd.DataFrame) -> go.Figure:
    """Yearly totals: raw MODIS, MODIS × k and observed VIIRS.

    Inside 2012–2019 MODIS × k should track VIIRS (that is the calibration);
    after 2020 the gap shows the Terra/Aqua orbital drift.
    """
    y = monthly.groupby("year", as_index=False)[["fires", "modis_raw", "modis_adj", "viirs_raw"]].sum(min_count=1)
    y.loc[y["year"] < 2012, "viirs_raw"] = np.nan  # S-NPP starts in 2012
    y = y[y["year"] >= 2001]                       # 2000 has only Nov–Dec
    fig = go.Figure()
    fig.add_scatter(x=y["year"], y=y["modis_raw"], name=t("c_modis_raw"), mode="lines+markers", line_color="#9aa5b1",
                    hovertemplate="%{y:,.0f}")
    fig.add_scatter(x=y["year"], y=y["modis_adj"], name=t("c_modis_adj"), mode="lines+markers",
                    line=dict(color=ORANGE, width=3), hovertemplate="%{y:,.0f}")
    fig.add_scatter(x=y["year"], y=y["viirs_raw"], name=t("c_viirs"), mode="lines+markers",
                    line=dict(color=BLUE, width=3, dash="dot"), hovertemplate="%{y:,.0f}")
    fig.add_vrect(x0=2011.5, x1=2019.5, fillcolor="#f2c14e", opacity=0.15, line_width=0,
                  annotation_text=t("c_calibration"), annotation_position="top left")
    _layout(fig, 380, hovermode="x unified", yaxis=dict(title=t("c_fires_year"), tickformat="~s"),
            legend=dict(orientation="h", y=-0.15))
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    return fig
