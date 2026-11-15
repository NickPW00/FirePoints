# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1800_nicholas_melhorias-app-mapa.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1732_mariaeliza_design-app.md
"""Map layers for the FirePoints app.

The 0.1° grid is drawn as an image (one pixel per cell) so that 60,000 cells stay light:
over a real basemap with pan/zoom (folium / Leaflet, ``base_map`` + ``data_layer``) or,
as an offline fallback, as a Plotly raster (``charts.cell_map``). Both read the same
rasters, built here by ``render``.

State boundaries and labels come from the grid itself (the cell → state table of
``quadradinhos.parquet``), so they match exactly the cells counted for each state.
If ``data/processed/ufs_simplificado.geojson`` exists, the app draws that instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import folium
import numpy as np
import pandas as pd
from branca.element import MacroElement
from folium.plugins import Draw
from folium.raster_layers import ImageOverlay
from jinja2 import Template

from i18n import month as month_name, num
from i18n import t as _t   # "t" is used below for positions on the colour scale

CELL = 0.1

# Sequential ramp for "how much" (one hue, light -> dark; ColorBrewer Oranges, colour-blind safe)
FIRE_RAMP = ["#feedde", "#fdd0a2", "#fdae6b", "#fd8d3c", "#f16913", "#d94801", "#8c2d04"]
# Peak season: three classes, validated for colour-vision deficiencies as a set (all pairs)
SEASONS = [
    ("season_jja", (6, 7, 8), "#2a78d6"),      # i18n keys
    ("season_so", (9, 10), "#eb6834"),
    ("season_nm", (11, 12, 1, 2, 3, 4, 5), "#1baf7a"),
]
NO_FIRE = "#ecebe6"      # inside Brazil, no detection (Plotly fallback)
OUTLINE = "#1f1f1f"
MIN_ZOOM, MAX_ZOOM = 4, 11   # 0.1° cells are ≈11 km: zooming further only shows bigger squares
# The map cannot be dragged or zoomed out beyond Brazil and its neighbours
PAN_LIMITS = dict(min_lat=-40.0, max_lat=10.0, min_lon=-82.0, max_lon=-25.0)
# Basemap without labels under the data; place names on top of the data (as on Windy), both by CARTO from OSM data
TILES_BASE = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
TILES_LABELS = "https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png"
TILES_ATTR = ('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors '
              '&copy; <a href="https://carto.com/attributions">CARTO</a>')

METRICS = {          # metric -> i18n key of its label
    "fires": "metric_fires",
    "pct": "metric_pct",
    "season": "metric_season",
}


# ---------------------------------------------------------------------------
# Grid geometry (computed once)
# ---------------------------------------------------------------------------
@dataclass
class Grid:
    """Raster frame of the 0.1° grid: row 0 is the southernmost row, column 0 the westernmost."""

    i0: int
    j0: int
    shape: tuple[int, int]
    index: pd.Index            # cell key -> position in ``rows`` / ``cols``
    rows: np.ndarray
    cols: np.ndarray
    inside: np.ndarray         # bool: Brazil, including cells that never burned
    present: np.ndarray        # bool: cells of the series (at least one fire in the record)
    state_codes: np.ndarray    # int raster, -1 outside Brazil
    states: list[str]          # code -> UF
    state_names: dict[str, str]
    border_lines: list = field(default_factory=list)   # [[lat, lon], [lat, lon]] segments between states
    labels: list = field(default_factory=list)         # (UF, lat, lon)

    # -- coordinates --------------------------------------------------------
    def lat_edge(self, r):
        return (self.i0 + np.asarray(r)) * CELL

    def lon_edge(self, c):
        return (self.j0 + np.asarray(c)) * CELL

    @property
    def lats(self) -> np.ndarray:  # cell centres
        return (self.lat_edge(np.arange(self.shape[0])) + CELL / 2).round(2)

    @property
    def lons(self) -> np.ndarray:
        return (self.lon_edge(np.arange(self.shape[1])) + CELL / 2).round(2)

    @property
    def bounds(self) -> list[list[float]]:
        """[[south, west], [north, east]] of the whole raster."""
        return [[float(self.lat_edge(0)), float(self.lon_edge(0))],
                [float(self.lat_edge(self.shape[0])), float(self.lon_edge(self.shape[1]))]]

    def raster(self, keys, values, fill=np.nan, dtype=float) -> np.ndarray:
        """Place per-cell ``values`` (aligned with ``keys``) on the raster."""
        out = np.full(self.shape, fill, dtype=dtype)
        pos = self.index.get_indexer(np.asarray(keys))
        ok = pos >= 0
        out[self.rows[pos[ok]], self.cols[pos[ok]]] = np.asarray(values)[ok]
        return out

    def mask(self, keys) -> np.ndarray:
        return self.raster(keys, np.ones(len(keys), dtype=bool), fill=False, dtype=bool)

    def key_at(self, lat: float, lon: float) -> int | None:
        """Key of the grid cell that contains a point (None outside the raster)."""
        r = int(np.floor(lat / CELL + 1e-9)) - self.i0
        c = int(np.floor(lon / CELL + 1e-9)) - self.j0
        if not (0 <= r < self.shape[0] and 0 <= c < self.shape[1]) or not self.present[r, c]:
            return None
        return int((r + self.i0 + 1000) * 4000 + (c + self.j0 + 2000))

    def cell_bounds(self, keys) -> list[list[float]]:
        """[[south, west], [north, east]] of a set of cells."""
        pos = self.index.get_indexer(np.asarray(keys))
        pos = pos[pos >= 0]
        if len(pos) == 0:
            return self.bounds
        r, c = self.rows[pos], self.cols[pos]
        return [[float(self.lat_edge(r.min())), float(self.lon_edge(c.min()))],
                [float(self.lat_edge(r.max() + 1)), float(self.lon_edge(c.max() + 1))]]


def _shift(a: np.ndarray, dr: int, dc: int, fill) -> np.ndarray:
    """``a`` moved by (dr, dc) cells, without wrapping around the edges."""
    out = np.full_like(a, fill)
    src_r = slice(max(-dr, 0), a.shape[0] - max(dr, 0))
    dst_r = slice(max(dr, 0), a.shape[0] - max(-dr, 0))
    src_c = slice(max(-dc, 0), a.shape[1] - max(dc, 0))
    dst_c = slice(max(dc, 0), a.shape[1] - max(-dc, 0))
    out[dst_r, dst_c] = a[src_r, src_c]
    return out


_NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def fill_holes(present: np.ndarray) -> np.ndarray:
    """``present`` plus every empty cell that cannot be reached from the raster edge."""
    outside = np.zeros_like(present)
    outside[0, :] = outside[-1, :] = outside[:, 0] = outside[:, -1] = True
    outside &= ~present
    while True:
        grown = outside.copy()
        for dr, dc in _NEIGHBOURS:
            grown |= _shift(outside, dr, dc, False)
        grown &= ~present
        if grown.sum() == outside.sum():
            return ~outside
        outside = grown


def _spread(codes: np.ndarray, where: np.ndarray) -> np.ndarray:
    """Give the empty cells (-1) inside ``where`` the code of their nearest labelled neighbour."""
    codes = codes.copy()
    while True:
        todo = where & (codes < 0)
        if not todo.any():
            return codes
        new = codes.copy()
        for dr, dc in _NEIGHBOURS:
            nb = _shift(codes, dr, dc, -1)
            take = todo & (new < 0) & (nb >= 0)
            new[take] = nb[take]
        if (new == codes).all():
            return codes
        codes = new


def _runs(idx: np.ndarray):
    """(start, end) of each run of consecutive integers in a sorted array."""
    if len(idx) == 0:
        return
    cut = np.flatnonzero(np.diff(idx) != 1)
    starts = np.r_[idx[0], idx[cut + 1]]
    ends = np.r_[idx[cut], idx[-1]]
    yield from zip(starts.tolist(), ends.tolist())


def edge_lines(grid: Grid, differs_right: np.ndarray, differs_up: np.ndarray) -> list:
    """Cell edges as lat/lon segments, merging collinear neighbours.

    ``differs_right[r, c]``: draw the edge between (r, c) and (r, c + 1);
    ``differs_up[r, c]``: draw the edge between (r, c) and (r + 1, c).
    """
    lines = []
    for c in np.flatnonzero(differs_right.any(axis=0)):
        lon = float(grid.lon_edge(c + 1))
        for a, b in _runs(np.flatnonzero(differs_right[:, c])):
            lines.append([[float(grid.lat_edge(a)), lon], [float(grid.lat_edge(b + 1)), lon]])
    for r in np.flatnonzero(differs_up.any(axis=1)):
        lat = float(grid.lat_edge(r + 1))
        for a, b in _runs(np.flatnonzero(differs_up[r, :])):
            lines.append([[lat, float(grid.lon_edge(a))], [lat, float(grid.lon_edge(b + 1))]])
    return lines


def outline_lines(grid: Grid, sel: np.ndarray) -> list:
    """Outer boundary of a set of cells (holes filled), as lat/lon segments."""
    m = fill_holes(sel)
    right = np.zeros_like(m)
    right[:, :-1] = m[:, :-1] != m[:, 1:]
    up = np.zeros_like(m)
    up[:-1, :] = m[:-1, :] != m[1:, :]
    return edge_lines(grid, right, up)


def build_grid(cells: pd.DataFrame) -> Grid:
    """Raster frame, Brazil mask, state boundaries and state labels from the cell table."""
    gi, gj = cells["gi"].to_numpy(), cells["gj"].to_numpy()
    i0, j0 = int(gi.min()) - 1, int(gj.min()) - 1              # one empty cell of margin
    shape = (int(gi.max()) - i0 + 2, int(gj.max()) - j0 + 2)
    rows, cols = gi - i0, gj - j0
    present = np.zeros(shape, dtype=bool)
    present[rows, cols] = True
    inside = fill_holes(present)

    has_states = "estado" in cells
    uf = pd.Categorical(cells["estado"]) if has_states else pd.Categorical([])
    codes = np.full(shape, -1, dtype=np.int32)
    if has_states:
        codes[rows, cols] = uf.codes
        codes = _spread(codes, inside)                          # cells that never burned inherit a state
    states = list(uf.categories)
    names = (cells.dropna(subset=["estado"]).drop_duplicates("estado").set_index("estado")["estado_nome"].to_dict()
             if has_states else {})

    grid = Grid(i0=i0, j0=j0, shape=shape, index=pd.Index(cells["key"].to_numpy()), rows=rows, cols=cols,
                inside=inside, present=present, state_codes=codes, states=states, state_names=names)

    if has_states:
        right = np.zeros(shape, dtype=bool)
        a, b = codes[:, :-1], codes[:, 1:]
        right[:, :-1] = (a != b) & (a >= 0) & (b >= 0)
        up = np.zeros(shape, dtype=bool)
        a, b = codes[:-1, :], codes[1:, :]
        up[:-1, :] = (a != b) & (a >= 0) & (b >= 0)
        grid.border_lines = edge_lines(grid, right, up)
        for code, name in enumerate(states):
            r, c = np.nonzero(codes == code)
            if len(r) == 0:
                continue
            # label at the cell of the state closest to its centroid (stays inside concave states)
            k = int(np.argmin((r - r.mean()) ** 2 + (c - c.mean()) ** 2))
            grid.labels.append((name, float(grid.lat_edge(r[k]) + CELL / 2), float(grid.lon_edge(c[k]) + CELL / 2)))
    return grid


# ---------------------------------------------------------------------------
# Values -> colours
# ---------------------------------------------------------------------------
def _rgb(hex_color: str) -> list[int]:
    return [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]


def _ramp(t: np.ndarray, stops: list[str]) -> np.ndarray:
    """Colours of ``stops`` interpolated at positions ``t`` in [0, 1] (float RGB, 0–255)."""
    rgb = np.array([_rgb(h) for h in stops], dtype=float)
    x = np.clip(np.nan_to_num(t), 0, 1) * (len(stops) - 1)
    lo = np.clip(np.floor(x).astype(int), 0, len(stops) - 2)
    f = (x - lo)[..., None]
    return rgb[lo] * (1 - f) + rgb[lo + 1] * f


def _nice_ticks(vmax: float, log: bool) -> list[float]:
    if log:
        ticks = [t for t in (1, 3, 10, 30, 100, 300, 1_000, 3_000, 10_000, 30_000, 100_000) if t <= vmax * 1.001]
        return ticks[-6:] or [vmax]
    step = 10 ** np.floor(np.log10(max(vmax, 1e-9)))
    step = step / 2 if vmax / step < 2.5 else step
    return [float(v) for v in np.arange(step, vmax * 1.001, step)][:6]


def _fmt(v: float) -> str:
    return num(v) if v >= 10 or float(v).is_integer() else num(v, 1)


def season_class(peak_month) -> np.ndarray:
    """0, 1, 2 for the classes of ``SEASONS``; NaN where there is no peak month."""
    pm = np.asarray(peak_month, dtype=float)
    out = np.full(pm.shape, np.nan)
    for k, (_, months, _) in enumerate(SEASONS):
        out[np.isin(pm, months)] = k
    return out


def render(grid: Grid, freq: pd.DataFrame, metric: str, sel_keys, log: bool = True, month: int | None = None) -> dict:
    """Rasters and legend for one map.

    ``freq``: ``data.fire_frequency`` for the whole country; ``sel_keys``: cells of the selected
    area (drawn in full colour; the rest of Brazil stays visible but faded).

    Returns ``value`` (NaN = nothing to show), ``t`` (0–1 position on the colour scale),
    ``sel`` (bool), ``rgba`` (uint8, row 0 = south) and ``legend``.
    """
    keys = freq["key"].to_numpy()
    sel = grid.mask(sel_keys)
    when = _t("in_month", m=month_name(month)) if month else ""
    if metric == "season":
        value = grid.raster(keys, season_class(freq["peak_month"]))
        t = value / (len(SEASONS) - 1)
        rgb = np.zeros(grid.shape + (3,))
        for k, (_, _, color) in enumerate(SEASONS):
            rgb[value == k] = _rgb(color)
        legend = {"kind": "classes", "title": _t("leg_season"),
                  "items": [(color, _t(name)) for name, _, color in SEASONS]}
    else:
        col = "fires_per_year" if metric == "fires" else "pct_years"
        value = grid.raster(keys, freq[col].to_numpy(dtype=float))
        value[~(value > 0)] = np.nan
        inside_sel = value[sel & np.isfinite(value)]
        if metric == "pct":
            vmax, t = 100.0, value / 100.0
            ticks = [(v / 100, f"{v}%") for v in (0, 25, 50, 75, 100)]
            title = _t("leg_pct", when=when)
        else:
            # top of the scale = 99th percentile of the selected area (a few extreme cells do not flatten the rest)
            vmax = float(np.percentile(inside_sel, 99)) if len(inside_sel) else 1.0
            vmax = max(vmax, 1e-6)
            if log:
                t = np.log1p(value) / np.log1p(vmax)
                ticks = [(float(np.log1p(v) / np.log1p(vmax)), _fmt(v)) for v in _nice_ticks(vmax, True)]
            else:
                t = value / vmax
                ticks = [(v / vmax, _fmt(v)) for v in _nice_ticks(vmax, False)]
            if ticks:
                ticks[-1] = (ticks[-1][0], ticks[-1][1] + ("+" if ticks[-1][0] > 0.9 else ""))
            title = _t("leg_fires", when=when) + (_t("leg_log") if log else "")
        rgb = _ramp(t, FIRE_RAMP)
        legend = {"kind": "ramp", "title": title, "stops": FIRE_RAMP, "ticks": ticks}

    shown = np.isfinite(value)
    alpha = np.where(shown, 0.92, 0.0)
    # outside the selected area: same pattern in grey, faded (Brazil stays visible for context)
    out_sel = shown & ~sel
    grey = (rgb * [0.299, 0.587, 0.114]).sum(axis=-1, keepdims=True)
    rgb = np.where(out_sel[..., None], 0.45 * grey + 140, rgb)
    alpha = np.where(out_sel, 0.38, alpha)
    rgba = np.dstack([rgb, alpha * 255]).round().clip(0, 255).astype(np.uint8)
    legend["faded"] = bool(out_sel.any())
    return {"value": value, "t": np.clip(np.nan_to_num(t), 0, 1), "sel": sel, "rgba": rgba, "legend": legend}


def hover_data(grid: Grid, freq: pd.DataFrame) -> np.ndarray:
    """Per-cell numbers for tooltips, as a compact (rows, cols, 2) array: fires per year, % of years with fire.

    Cells of Brazil that never burned get 0; cells outside Brazil stay NaN.
    """
    keys = freq["key"].to_numpy()
    out = np.full(grid.shape + (2,), np.nan, dtype=np.float32)
    out[grid.inside] = 0.0
    for k, col in enumerate(("fires_per_year", "pct_years")):
        layer = grid.raster(keys, freq[col].to_numpy(dtype=float))
        out[..., k] = np.where(np.isfinite(layer), layer, out[..., k])
    return out


def takeaway(freq: pd.DataFrame, sel_keys, metric: str, month: int | None = None,
             n_years: int | None = None) -> str:
    """One sentence that reads the map for the selected area."""
    f = freq[freq["key"].isin(sel_keys)]
    when = _t("in_month", m=month_name(month)) if month else ""
    burned = f[f["total_fires"] > 0]
    if burned.empty:
        return _t("tk_none", when=when)
    if metric == "fires":
        v = np.sort(burned["total_fires"].to_numpy())[::-1]
        n_half = int(np.searchsorted(np.cumsum(v), v.sum() / 2) + 1)
        return _t("tk_fires", when=when, pct=num(n_half / len(f) * 100), n=num(n_half), total=num(len(f)))
    if metric == "pct":
        often = (f["pct_years"] >= 50).mean() * 100
        n = n_years if n_years is not None else freq.attrs.get("n_years", 0)
        return _t("tk_pct", pct=num(often), when=when, n=n)
    cls = season_class(burned["peak_month"])
    share = [(np.nanmean(cls == k) * 100, _t(name).split(" (")[0]) for k, (name, _, _) in enumerate(SEASONS)]
    share.sort(reverse=True)
    return _t("tk_season", s1=share[0][1], p1=num(share[0][0]), s2=share[1][1], p2=num(share[1][0]),
             s3=share[2][1], p3=num(share[2][0]))


def legend_html(legend: dict) -> str:
    """Colour legend as a small HTML block (shown above the map)."""
    note = (f'<span class="fp-chip"><i style="background:#b9b9b9"></i>{_t("leg_faded")}</span>'
            if legend.get("faded") else "")
    css = ("<style>.fp-leg{font-size:.82rem;line-height:1.3;color:#31333f;margin:.2rem 0 .5rem}"
           ".fp-leg b{font-weight:600}.fp-bar{position:relative;height:12px;border-radius:3px;max-width:420px;"
           "margin:.35rem 0 1.25rem;border:1px solid rgba(0,0,0,.12)}"
           ".fp-bar span{position:absolute;top:15px;transform:translateX(-50%);font-size:.74rem;color:#52514e;white-space:nowrap}"
           ".fp-bar em{position:absolute;top:-1px;height:13px;border-left:1px solid rgba(0,0,0,.35)}"
           ".fp-chip{display:inline-flex;align-items:center;gap:.35rem;margin-right:1rem;white-space:nowrap}"
           ".fp-chip i{display:inline-block;width:12px;height:12px;border-radius:2px;border:1px solid rgba(0,0,0,.15)}</style>")
    if legend["kind"] == "classes":
        chips = "".join(f'<span class="fp-chip"><i style="background:{c}"></i>{name}</span>' for c, name in legend["items"])
        body = f'<div style="margin-top:.3rem">{chips}{note}</div>'
    else:
        ticks = "".join(f'<em style="left:{p * 100:.1f}%"></em><span style="left:{p * 100:.1f}%">{label}</span>'
                        for p, label in legend["ticks"])
        gradient = ", ".join(legend["stops"])
        body = (f'<div class="fp-bar" style="background:linear-gradient(90deg, {gradient})">{ticks}</div>'
                f'<div><span class="fp-chip"><i style="background:transparent"></i>{_t("leg_nocolour")}</span>{note}</div>')
    return f'{css}<div class="fp-leg"><b>{legend["title"]}</b>{body}</div>'


# ---------------------------------------------------------------------------
# Folium (real basemap, pan and zoom)
# ---------------------------------------------------------------------------
_MAP_CSS = """<style>
.leaflet-tile-pane { filter: grayscale(1) brightness(1.06) contrast(0.92); }   /* quiet basemap: the data carries the colour */
.fp-uf { font: 700 12px/1 system-ui, -apple-system, 'Segoe UI', sans-serif; color: #111; white-space: nowrap;
         letter-spacing: .04em; transform: translate(-50%, -50%); pointer-events: none;
         text-shadow: 0 0 2px #fff, 0 0 3px #fff, 0 0 4px #fff, 0 0 6px #fff; }
.fp-px { image-rendering: pixelated; image-rendering: crisp-edges; }      /* sharp 0.1° cells */
.fp-smooth { image-rendering: auto; }                                    /* smoothed for reading (Windy-like) */
.leaflet-fp-labels-pane { pointer-events: none; }
.fp-hint { background: rgba(255,255,255,.92); padding: 3px 8px; border-radius: 4px; font: 12px system-ui, sans-serif;
           color: #31333f; box-shadow: 0 1px 4px rgba(0,0,0,.2); transition: opacity .3s; }
.leaflet-container { cursor: grab; }
.leaflet-control-scale-line:nth-child(2) { display: none; }                          /* metric scale only */
</style>"""


def mercator_image(rgba: np.ndarray, lat_south: float, lat_north: float, scale: int = 4) -> np.ndarray:
    """Re-sample the rows of a lat/lon raster (row 0 = south) to Web-Mercator, north at the top.

    Leaflet stretches an image linearly in Mercator y; without this step the grid would sit
    up to ~1° (100 km) away from the basemap in the middle of Brazil. Nearest-neighbour, so
    cells keep hard edges.
    """
    def merc(lat):
        return np.arcsinh(np.tan(np.radians(lat)))

    n = rgba.shape[0]
    h = n * scale
    y = merc(lat_north) - (np.arange(h) + 0.5) / h * (merc(lat_north) - merc(lat_south))
    lat = np.degrees(np.arctan(np.sinh(y)))
    src = np.clip(np.floor((lat - lat_south) / CELL).astype(int), 0, n - 1)
    return rgba[src]


def view_for(bounds: list[list[float]], width: int = 760, height: int = 600) -> tuple[list[float], float]:
    """Centre and zoom that show ``bounds`` (plus a margin) in a map of about ``width`` × ``height`` px.

    Computed here instead of Leaflet's ``fitBounds`` because the map is created before its
    frame has its final size. ``width`` is a conservative guess of the page column.
    """
    (south, west), (north, east) = bounds
    pad = max(0.3, 0.04 * max(north - south, east - west))
    south, north, west, east = south - pad, north + pad, west - pad, east + pad

    def merc(lat):
        return np.degrees(np.arcsinh(np.tan(np.radians(lat))))

    zoom = min(np.log2(width * 360 / (256 * (east - west))), np.log2(height * 360 / (256 * (merc(north) - merc(south)))))
    zoom = float(np.clip(np.floor(zoom * 4) / 4, MIN_ZOOM, MAX_ZOOM - 1))
    lat = float(np.degrees(np.arctan(np.sinh(np.radians((merc(north) + merc(south)) / 2)))))
    return [lat, (west + east) / 2], zoom


class ScrollZoomOnClick(MacroElement):
    """Wheel zoom only after the user clicks the map; leaving the map gives the wheel back to the page.

    Avoids the page "scroll trap": scrolling the page over the map does not zoom it by accident.
    A small hint in the corner says how to activate it.
    """

    _template = Template("""
        {% macro script(this, kwargs) %}
        (function () {
            var map = {{ this._parent.get_name() }};
            map.scrollWheelZoom.disable();
            var hint = L.control({position: 'topright'});
            hint.onAdd = function () {
                var d = L.DomUtil.create('div', 'fp-hint');
                d.innerHTML = {{ this.text|tojson }};
                return d;
            };
            hint.addTo(map);
            var box = hint.getContainer();
            map.on('click focus', function () { map.scrollWheelZoom.enable(); box.style.opacity = 0; });
            map.getContainer().addEventListener('mouseleave', function () {
                map.scrollWheelZoom.disable(); box.style.opacity = 1;
            });
        })();
        {% endmacro %}
    """)

    def __init__(self, text: str):
        super().__init__()
        self._name = "ScrollZoomOnClick"
        self.text = text


def base_map(grid: Grid, fit: list[list[float]] | None = None, draw: bool = False,
             states_geojson: dict | None = None, height: int = 600, municipalities: list[dict] | None = None,
             hint: str = "Click the map, then scroll to zoom") -> folium.Map:
    """Basemap with state boundaries and labels. Data goes on top with ``data_layer``.

    Everything here depends only on the area to show, so the map is not rebuilt (and keeps
    the user's zoom) when the metric, the month or the smoothing changes.
    ``municipalities``: GeoJSON of the municipalities of the selected states (thin lines).
    """
    center, zoom = view_for(fit or grid.bounds, height=height)
    m = folium.Map(location=center, zoom_start=zoom, min_zoom=MIN_ZOOM, max_zoom=MAX_ZOOM, tiles=None,
                   control_scale=True, zoom_snap=0.25, zoom_delta=0.5, wheelPxPerZoomLevel=120,
                   minZoom=MIN_ZOOM, maxZoom=MAX_ZOOM,          # Leaflet options (min_zoom alone only limits tiles)
                   max_bounds=True, maxBoundsViscosity=1.0, **PAN_LIMITS)
    folium.TileLayer(TILES_BASE, attr=TILES_ATTR, name="Basemap", max_zoom=MAX_ZOOM, control=False).add_to(m)
    m.get_root().header.add_child(folium.Element(_MAP_CSS))
    folium.map.CustomPane("fp-grid", z_index=350).add_to(m)        # above the tiles, below lines and labels
    folium.map.CustomPane("fp-labels", z_index=450, pointer_events=False).add_to(m)  # place names over the data
    folium.TileLayer(TILES_LABELS, attr=TILES_ATTR, name="Labels", max_zoom=MAX_ZOOM, control=False,
                     pane="fp-labels").add_to(m)
    for fc in municipalities or []:
        folium.GeoJson(fc, interactive=False,
                       style_function=lambda _: {"color": "#5c5b57", "weight": 0.6, "opacity": 0.7,
                                                 "fill": False}).add_to(m)
    if states_geojson:
        folium.GeoJson(states_geojson, interactive=False,
                       style_function=lambda _: {"color": OUTLINE, "weight": 1.2, "opacity": 0.75, "fill": False}).add_to(m)
    elif grid.border_lines:
        folium.PolyLine(grid.border_lines, color=OUTLINE, weight=1, opacity=0.6, interactive=False).add_to(m)
    for uf, lat, lon in grid.labels:
        folium.Marker([lat, lon], interactive=False, keyboard=False,
                      icon=folium.DivIcon(icon_size=(0, 0), icon_anchor=(0, 0), html=f'<div class="fp-uf">{uf}</div>')
                      ).add_to(m)
    if draw:
        Draw(export=False, draw_options={"polyline": False, "circle": False, "marker": False,
                                         "circlemarker": False, "polygon": True, "rectangle": True}).add_to(m)
    ScrollZoomOnClick(hint).add_to(m)
    return m


def data_layer(grid: Grid, rgba: np.ndarray, area: dict | None = None, sel: np.ndarray | None = None,
               smooth: bool = True, states_geojson: dict | None = None,
               selected_states: list[str] | None = None) -> folium.FeatureGroup:
    """Grid image plus the outline of the selected area, as a layer that can be swapped on a live map.

    ``smooth``: let the browser blend neighbouring cells (easier to read, Windy-like) instead of
    sharp 0.1° squares. ``selected_states``: outline these states with the smooth IBGE border.
    """
    fg = folium.FeatureGroup(name="FirePoints")
    (south, west), (north, east) = grid.bounds
    ImageOverlay(mercator_image(rgba, south, north), bounds=grid.bounds, pane="fp-grid", interactive=False,
                 pixelated=not smooth, mercator_project=False, className="fp-smooth" if smooth else "fp-px").add_to(fg)
    kind = (area or {}).get("type", "brazil")
    style = dict(color=OUTLINE, weight=2.5, opacity=0.95, fill=False, interactive=False)
    if kind == "polygon":
        folium.Polygon([[lat, lon] for lon, lat in area["coords"]], **style).add_to(fg)
    elif kind == "bbox":
        folium.Rectangle([[area["lat_min"], area["lon_min"]], [area["lat_max"], area["lon_max"]]], **style).add_to(fg)
    elif selected_states and states_geojson:
        feats = [f for f in states_geojson["features"] if f["properties"].get("uf") in set(selected_states)]
        if feats:
            folium.GeoJson({"type": "FeatureCollection", "features": feats}, interactive=False,
                           style_function=lambda _: {"color": OUTLINE, "weight": 2.8, "opacity": 0.95,
                                                     "fill": False}).add_to(fg)
    elif kind in ("states", "biomes", "regions") and sel is not None and sel.any() and not (sel == grid.present).all():
        folium.PolyLine(outline_lines(grid, sel), **{k: v for k, v in style.items() if k != "fill"}).add_to(fg)
    return fg
