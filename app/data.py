# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1642_nicholas_stack-app.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1800_nicholas_melhorias-app-mapa.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1732_mariaeliza_design-app.md
"""Data access for the FirePoints app.

Reads the pre-processed Parquet files in ``data/processed/`` (built by
``pipeline/``) and answers the app's questions: which grid cells fall inside
an area, the monthly harmonized fire counts for that area, and (when the
point files are available) the individual fire points.

Units: ``focos`` = fire detections in VIIRS S-NPP 375 m equivalents
("VIIRS-equivalent fire counts"), per 0.1° cell and local month
(America/Sao_Paulo).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
SERIES_FILE = PROCESSED / "serie_harmonizada.parquet"
FACTORS_FILE = PROCESSED / "fatores_bioma_mes.csv"
VALIDATION_FILE = PROCESSED / "validacao_harmonizacao.csv"
CELLS_FILE = PROCESSED / "quadradinhos.parquet"  # cell -> biome, state (pipeline/04_calendario.py)
POINTS_DIR = PROCESSED / "focos"  # ano=<year>/focos_<year>_<sensor>.parquet (pipeline/05_exportar_focos.py)

CELL = 0.1
FIRST_MONTH = (2000, 11)  # MODIS Terra starts in Nov/2000
LAST_MONTH = (2026, 10)   # last complete S-NPP month in the series (pipeline/03_harmonizar.py)

STATES_GEOJSON = PROCESSED / "ufs_simplificado.geojson"   # smooth state borders (pipeline/07_divisas.py)
MUNICIPALITIES_DIR = PROCESSED / "municipios"               # <UF>.geojson (pipeline/07_divisas.py)

# IBGE macro-regions (internal key = IBGE name) -> states
REGIONS = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}

# Status labels, as written by pipeline/03_harmonizar.py
STATUS_EN = {"observado": "observed", "estimado": "estimated", "parcial": "partial"}


def month_status(year: int, month: int) -> str | None:
    """Status of a month in the harmonized series (same rules as the pipeline).

    Returns ``None`` for months outside the data range (no data, not zero).
    """
    ym = (year, month)
    if ym < FIRST_MONTH or ym > LAST_MONTH:
        return None
    if ym <= (2002, 12):
        return "partial"     # Terra only until Aqua (Jul/2002)
    if ym <= (2012, 1):
        return "estimated"   # MODIS × k (bioma, month)
    return "observed"        # VIIRS S-NPP


def cell_key(gi, gj):
    """Single integer id for a grid cell (gi, gj are 0.1° row/column indices)."""
    return (np.asarray(gi, dtype=np.int32) + 1000) * 4000 + (np.asarray(gj, dtype=np.int32) + 2000)


def load_series() -> pd.DataFrame:
    """Load the harmonized series with compact dtypes (~70 MB in memory)."""
    cols = ["gi", "gj", "bioma", "ano", "mes", "focos", "status", "modis", "snpp"]
    df = pd.read_parquet(SERIES_FILE, columns=cols)
    df["bioma"] = df["bioma"].astype("category")
    df["status"] = df["status"].map(STATUS_EN).astype("category")
    df["focos"] = df["focos"].astype("float32")
    df["modis"] = df["modis"].astype("int32")
    df["snpp"] = df["snpp"].astype("int32")
    df["key"] = cell_key(df["gi"], df["gj"])
    # MODIS × k for every month (also after 2012), to compare against observed VIIRS
    k = load_factors()
    k.columns = k.columns.astype(int)
    k_long = k.stack().rename("k").astype("float32")
    idx = pd.MultiIndex.from_arrays([df["bioma"].astype(str), df["mes"].astype(int)])
    df["modis_adj"] = (df["modis"] * k_long.reindex(idx).to_numpy()).astype("float32")
    df.attrs["n_cells"] = df["key"].nunique()
    return df


def cells_table(series: pd.DataFrame) -> pd.DataFrame:
    """One row per grid cell: indices, centre coordinates and biome."""
    cells = series[["key", "gi", "gj", "bioma"]].drop_duplicates("key").reset_index(drop=True)
    cells["lat"] = (cells["gi"].astype("float64") * CELL + CELL / 2).round(2)
    cells["lon"] = (cells["gj"].astype("float64") * CELL + CELL / 2).round(2)
    if CELLS_FILE.exists():
        st_ = pd.read_parquet(CELLS_FILE, columns=["gi", "gj", "estado", "estado_nome"])
        st_["key"] = cell_key(st_["gi"], st_["gj"])
        cells = cells.merge(st_[["key", "estado", "estado_nome"]], on="key", how="left")
    return cells


def states_of(area: dict) -> list[str]:
    """States (UF) covered by a "states" or "regions" area; empty list for the other kinds."""
    if area.get("type") == "states":
        return list(area["states"])
    if area.get("type") == "regions":
        return [uf for r in area["regions"] for uf in REGIONS.get(r, [])]
    return []


def select_cells(cells: pd.DataFrame, area: dict) -> np.ndarray:
    """Return the keys of the cells whose centre falls inside ``area``.

    ``area`` is one of:
      {"type": "brazil"}
      {"type": "biomes", "biomes": [...]}
      {"type": "states", "states": ["RJ", ...]}
      {"type": "regions", "regions": ["Sudeste", ...]}   (IBGE macro-regions, see REGIONS)
      {"type": "bbox", "lat_min", "lat_max", "lon_min", "lon_max"}
      {"type": "polygon", "coords": [[lon, lat], ...]}
    """
    kind = area["type"]
    if kind == "brazil":
        mask = np.ones(len(cells), dtype=bool)
    elif kind == "biomes":
        mask = cells["bioma"].isin(area["biomes"]).to_numpy()
    elif kind == "states":
        mask = cells["estado"].isin(area["states"]).to_numpy()
    elif kind == "regions":
        mask = cells["estado"].isin(states_of(area)).to_numpy()
    elif kind == "bbox":
        mask = (
            cells["lat"].between(area["lat_min"], area["lat_max"])
            & cells["lon"].between(area["lon_min"], area["lon_max"])
        ).to_numpy()
    elif kind == "polygon":
        from shapely import Polygon, contains_xy

        poly = Polygon(area["coords"])
        mask = contains_xy(poly, cells["lon"].to_numpy(), cells["lat"].to_numpy())
    else:
        raise ValueError(f"unknown area type: {kind}")
    return cells.loc[mask, "key"].to_numpy()


def filter_series(series: pd.DataFrame, keys: np.ndarray, years: tuple[int, int]) -> pd.DataFrame:
    """Rows of the series inside the selected cells and year range."""
    mask = series["ano"].between(years[0], years[1]).to_numpy()
    if len(keys) < series.attrs.get("n_cells", np.inf):
        mask = mask & series["key"].isin(keys).to_numpy()
    return series[mask]


def monthly_counts(sub: pd.DataFrame, years: tuple[int, int]) -> pd.DataFrame:
    """Monthly VIIRS-equivalent counts for the area, one row per month in ``years``.

    Months with no detection inside the data range are 0; months outside the
    range are NaN ("no data").
    """
    agg = sub.groupby(["ano", "mes"], observed=True).agg(
        fires=("focos", "sum"), modis_raw=("modis", "sum"), modis_adj=("modis_adj", "sum"),
        viirs_raw=("snpp", "sum")
    )
    idx = pd.MultiIndex.from_product(
        [range(years[0], years[1] + 1), range(1, 13)], names=["ano", "mes"]
    )
    out = agg.reindex(idx).reset_index()
    out["status"] = [month_status(a, m) for a, m in zip(out["ano"], out["mes"])]
    has_data = out["status"].notna()
    for c in ["fires", "modis_raw", "modis_adj", "viirs_raw"]:
        out[c] = out[c].where(~has_data | out[c].notna(), 0.0)
    out.loc[~has_data, ["fires", "modis_raw", "modis_adj", "viirs_raw"]] = np.nan
    return out.rename(columns={"ano": "year", "mes": "month"})


BASELINE_YEARS = (2003, 2025)  # complete years, same as calendario.parquet (docs/contrato-dados.md)
ANOMALY_BANDS = [  # ratio to the monthly mean -> band (same thresholds as the pipeline)
    (0.5, 1, "far below"), (0.8, 2, "below"), (1.25, 3, "normal"), (2.0, 4, "above"), (np.inf, 5, "far above"),
]


def add_anomaly(monthly: pd.DataFrame) -> pd.DataFrame:
    """Add the monthly mean (2003–2025), % anomaly and 1–5 band to each month."""
    base = monthly[monthly["year"].between(*BASELINE_YEARS)].groupby("month")["fires"].mean()
    out = monthly.copy()
    out["mean_month"] = out["month"].map(base)
    ratio = out["fires"] / out["mean_month"]
    out["anomaly_pct"] = (ratio - 1) * 100
    band = pd.Series(np.nan, index=out.index)
    for upper, code, _ in reversed(ANOMALY_BANDS):
        band = band.mask(ratio < upper, code)
    # Partial months (Nov/2000–2002, Terra only) are under-counted by construction: comparing them
    # with the 2003–2025 normal would show missing satellite coverage as "fewer fires".
    comparable = out["fires"].notna() & (out["mean_month"] > 0) & (out["status"] != "partial")
    out["anomaly_band"] = band.where(comparable)
    return out


def anomaly(monthly: pd.DataFrame, year: int, month: int) -> dict:
    """One month compared with the mean of the same month in 2003–2025."""
    m = add_anomaly(monthly)
    same = m[(m["month"] == month) & m["fires"].notna()]
    row = same[same["year"] == year]
    base = same[same["year"].between(*BASELINE_YEARS) & (same["year"] != year)]
    value = float(row["fires"].iloc[0]) if len(row) else float("nan")
    band = row["anomaly_band"].iloc[0] if len(row) else np.nan
    return {
        "value": value,
        "mean": float(row["mean_month"].iloc[0]) if len(row) else float("nan"),
        "pct": float(row["anomaly_pct"].iloc[0]) if len(row) else float("nan"),
        "band": None if pd.isna(band) else next(n for _, c, n in ANOMALY_BANDS if c == band),
        "n_years": BASELINE_YEARS[1] - BASELINE_YEARS[0] + 1,
        "rank_below": int((base["fires"] < value).sum()) if np.isfinite(value) else None,
        "n_compared": len(base),
        "status": row["status"].iloc[0] if len(row) else None,
        "history": same[["year", "fires", "status"]],
    }


def season_envelope(monthly: pd.DataFrame) -> pd.DataFrame:
    """Usual range of each calendar month in 2003–2025: 10th percentile, median and 90th percentile."""
    base = monthly[monthly["year"].between(*BASELINE_YEARS) & monthly["fires"].notna()]
    q = base.groupby("month")["fires"].quantile([0.1, 0.5, 0.9]).unstack()
    return q.rename(columns={0.1: "p10", 0.5: "p50", 0.9: "p90"}).reindex(range(1, 13))


def year_summary(monthly: pd.DataFrame, year: int) -> dict | None:
    """One year against the normal, over the months of that year that have data.

    ``monthly`` must come from ``add_anomaly`` on the full record. Returns ``None`` when the
    year has no data.
    """
    m = monthly[(monthly["year"] == year) & monthly["fires"].notna()]
    if m.empty:
        return None
    total, normal = float(m["fires"].sum()), float(m["mean_month"].sum())
    env = season_envelope(monthly)
    fires = m.set_index("month")["fires"]
    return {
        "year": year,
        "first_month": int(m["month"].min()),
        "last_month": int(m["month"].max()),
        "n_months": len(m),
        "total": total,
        "normal": normal,
        "pct": (total / normal - 1) * 100 if normal > 0 else float("nan"),
        "partial": bool((m["status"] == "partial").any()),
        "above_range": int((fires > env["p90"].reindex(fires.index)).sum()),
        "below_range": int((fires < env["p10"].reindex(fires.index)).sum()),
        "peak_month": int(fires.idxmax()),
        "peak_fires": float(fires.max()),
    }


def typical_season(monthly: pd.DataFrame) -> dict | None:
    """Typical fire season of the area: peak month and the 3 consecutive months with most fires."""
    base = monthly[monthly["year"].between(*BASELINE_YEARS)].groupby("month")["fires"].mean()
    base = base.reindex(range(1, 13)).fillna(0.0)
    if base.sum() <= 0:
        return None
    windows = {m: base[[(m - 1 + k) % 12 + 1 for k in range(3)]].sum() for m in range(1, 13)}
    start = max(windows, key=windows.get)
    return {
        "peak_month": int(base.idxmax()),
        "window": [(start - 1 + k) % 12 + 1 for k in range(3)],
        "window_share": float(windows[start] / base.sum() * 100),
    }


def calibration_gap(monthly: pd.DataFrame) -> float:
    """Mean absolute difference (%) between yearly MODIS × k and observed VIIRS in the calibration window (2012–2019)."""
    y = monthly[monthly["year"].between(2012, 2019)].groupby("year")[["modis_adj", "viirs_raw"]].sum()
    y = y[y["viirs_raw"] > 0]
    if y.empty:
        return float("nan")
    return float(((y["modis_adj"] / y["viirs_raw"] - 1).abs() * 100).mean())


def data_months(years: tuple[int, int], month: int | None = None) -> list[tuple[int, int]]:
    """(year, month) pairs of the period that have data (optionally only one calendar month)."""
    months = range(1, 13) if month is None else [month]
    return [(y, m) for y in range(years[0], years[1] + 1) for m in months if month_status(y, m)]


def comparable_years(years: tuple[int, int], month: int | None = None) -> list[int]:
    """Years that can be counted in "% of years with fire".

    For one calendar month: the years that have that month. For "any month": the complete
    years (12 months of data), so that 2000 (Nov–Dec only) and the running year do not
    count as years without fire; if the period has no complete year, the years with any data.
    """
    pairs = data_months(years, month)
    if month is not None:
        return sorted({y for y, _ in pairs})
    n = pd.Series([y for y, _ in pairs]).value_counts() if pairs else pd.Series(dtype=int)
    complete = sorted(n[n == 12].index.tolist())
    return complete or sorted(n.index.tolist())


def fire_frequency(sub: pd.DataFrame, cells: pd.DataFrame, keys: np.ndarray, month: int | None,
                   years: tuple[int, int]) -> pd.DataFrame:
    """Per cell, for ``month`` (or any month) in the period.

    - ``pct_years``: % of the comparable years with at least one fire;
    - ``total_fires``: VIIRS-equivalent fires in the period (in that month, if one is chosen);
    - ``fires_per_year``: ``total_fires`` per year of data (so periods of different length compare);
    - ``peak_month``: calendar month with most fires in the period (NaN where nothing burned).
    """
    s = sub if month is None else sub[sub["mes"] == month]
    s = s[s["focos"] > 0]
    valid = comparable_years(years, month)
    yrs_with_fire = s[s["ano"].isin(valid)].groupby("key")["ano"].nunique()
    total = s.groupby("key")["focos"].sum()
    n_data_years = len(data_months(years, month)) / (12 if month is None else 1)
    by_month = sub[sub["focos"] > 0].groupby(["key", "mes"], observed=True)["focos"].sum().unstack(fill_value=0.0)
    peak = by_month.idxmax(axis=1) if len(by_month) else pd.Series(dtype=float)
    cols = [c for c in ["key", "gi", "gj", "lat", "lon", "bioma", "estado", "estado_nome"] if c in cells]
    out = cells[cells["key"].isin(keys)][cols].copy()
    out["pct_years"] = (out["key"].map(yrs_with_fire).fillna(0) / max(len(valid), 1) * 100).round(1)
    out["total_fires"] = out["key"].map(total).fillna(0).round(1)
    out["fires_per_year"] = (out["total_fires"] / max(n_data_years, 1e-9)).round(2)
    out["peak_month"] = out["key"].map(peak)
    out.attrs["n_years"] = len(valid)
    return out


# ---------------------------------------------------------------------------
# Individual fire points (optional: only if data/processed/focos/ exists)
# ---------------------------------------------------------------------------
def point_files(years: tuple[int, int]) -> list[str]:
    """Point files for the years in the period (docs/contrato-dados.md, section 2c).

    Layout: focos/ano=<year>/focos_<year>_<sensor>.parquet. An identical flat copy
    (focos/focos_<year>_<sensor>.parquet) is used only if the partitioned one is missing,
    so no point is read twice.
    """
    files = []
    for year in range(years[0], years[1] + 1):
        found = sorted((POINTS_DIR / f"ano={year}").glob("focos_*.parquet")) or sorted(
            POINTS_DIR.glob(f"focos_{year}_*.parquet"))
        files += [str(f) for f in found]
    return files


def points_available() -> bool:
    return POINTS_DIR.exists() and any(POINTS_DIR.rglob("focos_*_*.parquet"))


def _points_query(keys: np.ndarray, years: tuple[int, int], select: str, tail: str = "") -> pd.DataFrame:
    import duckdb

    files = point_files(years)
    if not files:
        return pd.DataFrame()
    con = duckdb.connect()
    con.register("sel", pd.DataFrame({"key": keys.astype("int64")}))
    # The point files run a few days past the series (NRT detections of the running month):
    # stop at the last month of the harmonized series, so the CSV matches the calendar.
    last_day = (pd.Timestamp(year=LAST_MONTH[0], month=LAST_MONTH[1], day=1) + pd.offsets.MonthEnd(0)).date()
    # Same cell rule as the pipeline: gi = floor(lat / 0.1), gj = floor(lon / 0.1)
    return con.execute(f"""
        SELECT {select}
        FROM read_parquet(?) p
        JOIN sel ON (CAST(floor(p.latitude / 0.1) AS BIGINT) + 1000) * 4000
                  + (CAST(floor(p.longitude / 0.1) AS BIGINT) + 2000) = sel.key
        WHERE p.data <= ?
        {tail}
    """, [files, last_day]).df()


def count_points(keys: np.ndarray, years: tuple[int, int]) -> int:
    df = _points_query(keys, years, "count(*) AS n")
    return int(df["n"].iloc[0]) if len(df) else 0


def fire_points(keys: np.ndarray, years: tuple[int, int]) -> pd.DataFrame:
    """Individual detections (raw, not harmonized) inside the selected cells and years.

    DuckDB reads only the files of the chosen years and streams the filter,
    instead of loading ~27 million points into memory.
    """
    return _points_query(
        keys, years,
        "p.latitude, p.longitude, p.data AS date_local, p.sensor, p.confianca AS confidence, p.frp AS frp_mw, "
        "p.dia_noite AS day_night, p.bioma AS biome, p.estado AS state",
        "ORDER BY p.data, p.sensor",
    )


def load_factors() -> pd.DataFrame:
    return pd.read_csv(FACTORS_FILE).set_index("bioma")


def load_validation() -> pd.DataFrame:
    return pd.read_csv(VALIDATION_FILE)
