# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1642_nicholas_stack-app.md
"""Plotly figures for the FirePoints app (calendar, anomaly, map, method)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
NO_DATA_GREY = "#d9d9d9"
COLORSCALE = "Viridis"  # perceptually uniform, colour-blind safe, no grey (grey = no data)
STATUS_MARK = {"observed": "", "estimated": " *", "partial": " †"}
# Diverging, colour-blind safe (ColorBrewer RdBu): blue = fewer fires than normal, red = more
BAND_COLORS = ["#2166ac", "#92c5de", "#f7f7f7", "#f4a582", "#b2182b"]
BAND_NAMES = ["far below (<0.5×)", "below (0.5–0.8×)", "normal (0.8–1.25×)", "above (1.25–2×)", "far above (>2×)"]


def calendar(monthly: pd.DataFrame, log_scale: bool = True, view: str = "count") -> go.Figure:
    """Fire calendar: years (rows) × months (columns).

    view="count": coloured by fire count; view="anomaly": coloured by the 1–5 band
    of the month compared with its 2003–2025 mean (``data.add_anomaly``).
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
    for i, y in enumerate(years):
        for j in range(12):
            v, s = z[i, j], status.iat[i, j]
            if s is None or (isinstance(s, float) and np.isnan(s)):
                hover[i, j] = f"{MONTHS[j]} {y}<br>No data"
            else:
                extra = f"<br>{pct[i, j]:+.0f}% vs 2003–2025 mean" if np.isfinite(pct[i, j]) else ""
                hover[i, j] = f"{MONTHS[j]} {y}<br>{v:,.0f} fires (VIIRS-eq.){extra}<br>{s}"

    if view == "anomaly":
        band = monthly.pivot(index="year", columns="month", values="anomaly_band").reindex(columns=range(1, 13))
        scale = [[k / 5, c] for k, c in enumerate(BAND_COLORS) for k in (k, k + 1)]
        fig = go.Figure(go.Heatmap(
            z=band.to_numpy(dtype=float), x=MONTHS, y=ylabels, text=hover, hoverinfo="text",
            colorscale=scale, zmin=0.5, zmax=5.5, xgap=2, ygap=2,
            colorbar=dict(title="vs normal", tickvals=[1, 2, 3, 4, 5], ticktext=BAND_NAMES),
        ))
        fig.update_layout(height=max(320, 22 * len(years) + 90), margin=dict(l=10, r=10, t=10, b=10),
                          plot_bgcolor=NO_DATA_GREY, yaxis=dict(autorange="reversed", type="category"),
                          xaxis=dict(side="top"))
        return fig

    vmax = float(np.nanmax(z)) if np.isfinite(z).any() else 1.0
    if log_scale:
        ticks = [t for t in [0, 1, 10, 100, 1_000, 10_000, 100_000, 1_000_000] if t <= max(vmax, 1) * 1.01]
        colorbar = dict(title="Fires", tickvals=np.log10(np.array(ticks) + 1), ticktext=[f"{t:,}" for t in ticks])
    else:
        colorbar = dict(title="Fires")

    fig = go.Figure(
        go.Heatmap(
            z=zc, x=MONTHS, y=ylabels, text=hover, hoverinfo="text",
            colorscale=COLORSCALE, colorbar=colorbar, xgap=2, ygap=2, zmin=0,
        )
    )
    fig.update_layout(
        height=max(320, 22 * len(years) + 90),
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=NO_DATA_GREY,  # NaN cells (no data) show the background
        yaxis=dict(autorange="reversed", type="category"),
        xaxis=dict(side="top"),
    )
    return fig


def anomaly_bars(history: pd.DataFrame, year: int, mean: float) -> go.Figure:
    """Same calendar month across years, highlighting the chosen year, with the 2003–2025 mean."""
    colors = ["#e4572e" if y == year else ("#9aa5b1" if s != "observed" else "#4c6a92")
              for y, s in zip(history["year"], history["status"])]
    fig = go.Figure(go.Bar(x=history["year"], y=history["fires"], marker_color=colors,
                           hovertemplate="%{x}: %{y:,.0f} fires<extra></extra>"))
    if np.isfinite(mean):
        fig.add_hline(y=mean, line_dash="dash", line_color="#333",
                      annotation_text=f"2003–2025 mean {mean:,.0f}", annotation_position="top left")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10),
                      yaxis_title="Fires (VIIRS-eq.)", xaxis=dict(dtick=2))
    return fig


def cell_map(freq: pd.DataFrame, value: str, title: str) -> go.Figure:
    """Grid cells as a raster (lat × lon heatmap): no basemap or WebGL needed, so it always renders."""
    d = freq[freq[value] > 0]
    if d.empty:
        return go.Figure().update_layout(height=200, annotations=[dict(text="No fires", showarrow=False)])
    gi = np.rint((d["lat"].to_numpy() - 0.05) / 0.1).astype(int)
    gj = np.rint((d["lon"].to_numpy() - 0.05) / 0.1).astype(int)
    i0, j0 = gi.min(), gj.min()
    z = np.full((gi.max() - i0 + 1, gj.max() - j0 + 1), np.nan)
    z[gi - i0, gj - j0] = d[value].to_numpy()
    lats = (np.arange(i0, gi.max() + 1) * 0.1 + 0.05).round(2)
    lons = (np.arange(j0, gj.max() + 1) * 0.1 + 0.05).round(2)
    fig = go.Figure(go.Heatmap(
        z=z, x=lons, y=lats, colorscale=COLORSCALE, colorbar=dict(title=title),
        hovertemplate="lat %{y:.2f}, lon %{x:.2f}<br>" + title + ": %{z:,.1f}<extra></extra>",
    ))
    fig.update_layout(
        height=600, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
        xaxis=dict(title="Longitude", showgrid=False, zeroline=False),
        yaxis=dict(title="Latitude", showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1),
    )
    return fig


def factors_heatmap(factors: pd.DataFrame) -> go.Figure:
    """Calibration factor k (VIIRS / MODIS) per biome and month."""
    fig = go.Figure(go.Heatmap(
        z=factors.to_numpy(), x=MONTHS, y=factors.index.to_list(), colorscale=COLORSCALE,
        text=np.round(factors.to_numpy(), 2), texttemplate="%{text}", colorbar=dict(title="k"),
        hovertemplate="%{y}, %{x}: k = %{z:.2f}<extra></extra>", xgap=2, ygap=2,
    ))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def harmonization_check(monthly: pd.DataFrame) -> go.Figure:
    """Yearly totals: raw MODIS, MODIS × k and observed VIIRS.

    Inside 2012–2019 MODIS × k should track VIIRS (that is the calibration);
    after 2020 the gap shows the Terra/Aqua orbital drift.
    """
    y = monthly.groupby("year", as_index=False)[["fires", "modis_raw", "modis_adj", "viirs_raw"]].sum(min_count=1)
    y.loc[y["year"] < 2012, "viirs_raw"] = np.nan  # S-NPP starts in 2012
    y = y[y["year"] >= 2001]                       # 2000 has only Nov–Dec
    fig = go.Figure()
    fig.add_scatter(x=y["year"], y=y["modis_raw"], name="MODIS (raw)", mode="lines+markers", line_color="#9aa5b1")
    fig.add_scatter(x=y["year"], y=y["modis_adj"], name="MODIS × k (harmonized)", mode="lines+markers",
                    line=dict(color="#e4572e", width=3))
    fig.add_scatter(x=y["year"], y=y["viirs_raw"], name="VIIRS S-NPP (observed)", mode="lines+markers",
                    line=dict(color="#2a6f97", width=3, dash="dot"))
    fig.add_vrect(x0=2011.5, x1=2019.5, fillcolor="#f2c14e", opacity=0.15, line_width=0,
                  annotation_text="calibration 2012–2019", annotation_position="top left")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Fires per year",
                      legend=dict(orientation="h", y=-0.15))
    return fig
