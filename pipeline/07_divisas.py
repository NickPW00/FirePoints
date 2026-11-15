# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1732_mariaeliza_design-app.md
"""
07_divisas.py
-------------
Light boundary files for the app map, from the IBGE 2024 territorial mesh:

  data/processed/ufs_simplificado.geojson        27 states (smooth borders), with UF, name and region
  data/processed/municipios/<UF>.geojson         municipalities of each state, drawn only for the selected area

Input (anywhere inside the project folder, no need to unzip):
  BR_UF_2024.zip          https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/
  BR_Municipios_2024.zip  same folder

Source: IBGE (public domain, source must be cited). Geometries are simplified for display.

How to run:  python pipeline/07_divisas.py
"""

import json
import os
import sys
from pathlib import Path

import geopandas as gpd

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parent if _HERE.name == "pipeline" else _HERE
OUT = ROOT / "data" / "processed"

TOL_STATES = 0.01        # degrees (~1 km): smooth at country zoom, light file
TOL_MUNICIPALITIES = 0.004
DIGITS = 4               # coordinate precision in the GeoJSON (~10 m)


def find(prefix: str) -> Path:
    """First file named <prefix>*.zip|.shp|.gpkg inside the project (case-insensitive)."""
    for dirpath, _, files in os.walk(ROOT):
        for name in files:
            low = name.lower()
            if low.startswith(prefix.lower()) and low.endswith((".zip", ".shp", ".gpkg")):
                return Path(dirpath) / name
    sys.exit(f"ERROR: {prefix}*.zip not found inside {ROOT}")


def column(df, *candidates):
    for c in df.columns:
        if c.upper() in candidates:
            return c
    sys.exit(f"ERROR: none of {candidates} in {list(df.columns)}")


def write_geojson(gdf: gpd.GeoDataFrame, path: Path) -> float:
    data = json.loads(gdf.to_json(drop_id=True))

    def rnd(x):
        return [rnd(v) for v in x] if isinstance(x, list) else round(x, DIGITS)

    for f in data["features"]:
        f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path.stat().st_size / 1e6


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # States
    src = find("BR_UF_")
    print(f"States: {src.relative_to(ROOT)}")
    uf = gpd.read_file(src).to_crs("EPSG:4326")
    uf = uf.rename(columns={column(uf, "SIGLA_UF", "SIGLA"): "uf", column(uf, "NM_UF"): "name",
                            column(uf, "NM_REGIAO", "NM_REGIA"): "region"})[["uf", "name", "region", "geometry"]]
    uf["geometry"] = uf.geometry.simplify(TOL_STATES, preserve_topology=True)
    mb = write_geojson(uf, OUT / "ufs_simplificado.geojson")
    print(f"  ufs_simplificado.geojson: {len(uf)} states, {mb:.2f} MB")

    # Municipalities, one file per state
    src = find("BR_Municipios_")
    print(f"Municipalities: {src.relative_to(ROOT)}")
    mun = gpd.read_file(src).to_crs("EPSG:4326")
    mun = mun.rename(columns={column(mun, "NM_MUN"): "name", column(mun, "SIGLA_UF", "SIGLA"): "uf",
                              column(mun, "CD_MUN"): "code"})[["code", "name", "uf", "geometry"]]
    mun = mun[mun["uf"].notna()]
    mun["geometry"] = mun.geometry.simplify(TOL_MUNICIPALITIES, preserve_topology=True)
    folder = OUT / "municipios"
    folder.mkdir(exist_ok=True)
    total = 0.0
    for sigla, part in mun.groupby("uf"):
        total += write_geojson(part.drop(columns="uf"), folder / f"{sigla}.geojson")
    print(f"  municipios/<UF>.geojson: {len(mun):,} municipalities in {mun['uf'].nunique()} files, {total:.1f} MB")
    print("Done!")


if __name__ == "__main__":
    main()
