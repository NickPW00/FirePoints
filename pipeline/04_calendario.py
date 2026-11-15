# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
"""
04_calendario.py  (step 4: burning calendar)
----------------
Builds the burning-calendar tables for the app (data contract in docs/contrato-dados.md):

  calendario.parquet    region × year × month: detections (VIIRS scale), status, historical mean
                        of the month, anomaly (%), anomaly class (1–5) and intensity class (0–5)
  quadradinhos.parquet  each 0.1° grid cell with its biome and state (for map filters)

Regions: Brazil, each biome and each state (IBGE state boundaries, e.g. BR_UF_2024.zip).

Input:  data/processed/serie_harmonizada.parquet (written by 03_harmonizar.py)
How to run:  python 04_calendario.py
"""

import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PROCESSADOS = PASTA / "data" / "processed"

INICIO, FIM = "2000-11", "2026-10"   # months covered by the harmonized series
ANOS_MEDIA = (2003, 2025)            # full years used for the historical mean of each month

# Anomaly classes: detections ÷ mean of the month
LIMITES_ANOMALIA = [0.5, 0.8, 1.25, 2.0]   # <0.5 | 0.5–0.8 | 0.8–1.25 | 1.25–2 | >2
# Class names are stored in Portuguese (data values): far below, below, normal, above, far above
NOMES_ANOMALIA = {1: "muito abaixo", 2: "abaixo", 3: "normal", 4: "acima", 5: "muito acima"}


def achar_ufs():
    """Looks for the IBGE state boundaries (e.g. BR_UF_2024.zip) inside the project."""
    candidatos = []
    for raiz, _, arquivos in os.walk(PASTA):
        for nome in arquivos:
            n = nome.lower()
            if ("_uf_" in n or n.startswith("br_uf")) and n.endswith((".zip", ".shp", ".gpkg", ".geojson", ".json")):
                candidatos.append(Path(raiz) / nome)
    if not candidatos:
        print("ERROR: state boundaries (e.g. BR_UF_2024.zip) not found inside", PASTA)
        sys.exit(1)
    candidatos.sort(key=lambda p: p.suffix.lower() == ".zip")
    arq = candidatos[0]
    print(f"State boundaries: {arq.relative_to(PASTA)}")
    ufs = gpd.read_file(arq)
    sigla = next(c for c in ufs.columns if "sigla" in c.lower())
    nome = next((c for c in ufs.columns if c.lower().startswith("nm_uf")), sigla)
    return ufs[[sigla, nome, "geometry"]].rename(columns={sigla: "estado", nome: "estado_nome"}).to_crs("EPSG:4326")


def estado_por_quadradinho(cel, ufs):
    """Adds the state (estado, estado_nome) of each grid cell, using the cell center."""
    pts = gpd.GeoDataFrame(cel, geometry=gpd.points_from_xy(cel["lon_centro"], cel["lat_centro"]), crs="EPSG:4326")
    dentro = gpd.sjoin(pts, ufs, how="left", predicate="within")
    dentro = dentro[~dentro.index.duplicated()]
    fora = dentro["estado"].isna()
    if fora.any():   # center at sea or exactly on a border: nearest state
        perto = gpd.sjoin_nearest(pts[fora].to_crs("EPSG:5880"), ufs.to_crs("EPSG:5880"), how="left")
        perto = perto[~perto.index.duplicated()]
        dentro.loc[fora, ["estado", "estado_nome"]] = perto[["estado", "estado_nome"]].values
    return pd.DataFrame(dentro.drop(columns=["geometry", "index_right"], errors="ignore"))


def montar(serie, coluna, tipo, nomes=None):
    """Sums detections per region × month and fills months without detections with zero."""
    if coluna is None:
        soma = serie.groupby(["ano", "mes"], as_index=False)["focos"].sum()
        soma["regiao"] = "Brasil"
    else:
        soma = serie.groupby([coluna, "ano", "mes"], as_index=False)["focos"].sum().rename(columns={coluna: "regiao"})
    meses = pd.period_range(INICIO, FIM, freq="M")
    grade = pd.DataFrame([(r, p.year, p.month) for r in sorted(soma["regiao"].unique()) for p in meses],
                         columns=["regiao", "ano", "mes"])
    out = grade.merge(soma, on=["regiao", "ano", "mes"], how="left").fillna({"focos": 0.0})
    out["regiao_tipo"] = tipo
    out["regiao_nome"] = out["regiao"].map(nomes) if nomes is not None else out["regiao"]
    return out


def main():
    serie = pd.read_parquet(PROCESSADOS / "serie_harmonizada.parquet")
    status_mes = serie.groupby(["ano", "mes"])["status"].first()

    # Biome and state of each grid cell
    cel = serie[["gi", "gj", "lat_centro", "lon_centro", "bioma"]].drop_duplicates(["gi", "gj"]).reset_index(drop=True)
    cel = estado_por_quadradinho(cel, achar_ufs())
    cel.to_parquet(PROCESSADOS / "quadradinhos.parquet", index=False)
    serie = serie.merge(cel[["gi", "gj", "estado"]], on=["gi", "gj"], how="left")
    nomes_uf = dict(zip(cel["estado"], cel["estado_nome"]))

    cal = pd.concat([
        montar(serie, None, "brasil"),
        montar(serie, "bioma", "bioma"),
        montar(serie, "estado", "estado", nomes_uf),
    ], ignore_index=True)

    # The month status (observed / estimated / partial) is the same for every region
    cal = cal.merge(status_mes.rename("status").reset_index(), on=["ano", "mes"], how="left")

    # Historical mean of each month, per region (full years 2003–2025)
    base = cal[cal["ano"].between(*ANOS_MEDIA)]
    media = base.groupby(["regiao_tipo", "regiao", "mes"])["focos"].mean().rename("media_mes").reset_index()
    cal = cal.merge(media, on=["regiao_tipo", "regiao", "mes"], how="left")
    razao = cal["focos"] / cal["media_mes"].replace(0, np.nan)
    cal["anomalia_pct"] = ((razao - 1) * 100).round(1)
    cal["faixa_anomalia"] = (np.digitize(razao.fillna(1.0), LIMITES_ANOMALIA) + 1).astype("int8")
    cal["faixa_anomalia_nome"] = cal["faixa_anomalia"].map(NOMES_ANOMALIA)

    # Intensity: 0 = no detections; 1–5 = quintiles of that region's months with detections
    def quintis(g):
        f = g["focos"]
        faixa = pd.Series(0, index=g.index, dtype="int8")
        pos = f > 0
        if pos.sum() >= 5:
            faixa[pos] = pd.qcut(f[pos].rank(method="first"), 5, labels=False).astype("int8") + 1
        else:
            faixa[pos] = 3
        return faixa
    cal["faixa_intensidade"] = cal.groupby(["regiao_tipo", "regiao"], group_keys=False)[["focos"]].apply(quintis)

    cal["focos"] = cal["focos"].round(1)
    cal["media_mes"] = cal["media_mes"].round(1)
    colunas = ["regiao_tipo", "regiao", "regiao_nome", "ano", "mes", "focos", "status", "media_mes",
               "anomalia_pct", "faixa_anomalia", "faixa_anomalia_nome", "faixa_intensidade"]
    cal = cal[colunas].sort_values(["regiao_tipo", "regiao", "ano", "mes"]).reset_index(drop=True)
    cal.to_parquet(PROCESSADOS / "calendario.parquet", index=False)

    # ---------- Summary on screen ----------
    print(f"\nRegions: {cal.groupby('regiao_tipo')['regiao'].nunique().to_dict()}")
    print(f"Rows: {len(cal):,}")
    br = cal[cal["regiao_tipo"] == "brasil"]
    pico = br.loc[br["focos"].idxmax()]
    print(f"Month with the most detections in Brazil: {int(pico['mes']):02d}/{int(pico['ano'])} ({pico['focos']:,.0f} detections)")
    print("Historical mean per month in Brazil (thousand detections):")
    print((br.groupby("mes")["media_mes"].first() / 1000).round(0).to_string())
    print(f"\nSaved to {PROCESSADOS / 'calendario.parquet'}")
    print("Done!")


if __name__ == "__main__":
    main()
