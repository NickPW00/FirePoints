# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
"""
03_harmonizar.py  (step 3: harmonize)
----------------
Merges MODIS and VIIRS S-NPP into a single detection series, on the VIIRS scale
(decisions #6 and #11 in docs/decisions.md):

  1. Finds the biome of each 0.1° grid cell (IBGE biome boundaries).
  2. Computes the factor k[biome, month] = S-NPP detections ÷ MODIS detections in 2012–2019.
  3. Validates by leaving one year out (2012–2019) and saves the error per biome.
  4. Builds the harmonized series:
       Nov 2000–Dec 2002   MODIS × k   -> "parcial"   (partial: only Terra until Jul 2002)
       2003–Jan 2012       MODIS × k   -> "estimado"  (estimated)
       Feb 2012 onward     VIIRS S-NPP -> "observado" (observed; S-NPP starts on 20 Jan 2012)
     The status values are stored in Portuguese; the app shows them in English.

Input:
  data/processed/grade_mensal.parquet        (written by 01_processar_focos.py)
  IBGE biome boundaries in any subfolder of the project
  (e.g. Biomas_250mil.zip, no need to extract it)

Output (data/processed/):
  serie_harmonizada.parquet   grid cell × month: detections on the VIIRS scale + status
  fatores_bioma_mes.csv       the factor k for each biome and month
  validacao_harmonizacao.csv  validation error per biome

How to run:  python 03_harmonizar.py
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

TAMANHO_QUADRADINHO = 0.1
CALIBRACAO = ("2012-02", "2019-12")   # decision #6 (Feb 2012: first full month of S-NPP)
INICIO_VIIRS = "2012-02"               # from here on the series uses observed S-NPP
FIM_TERRA_SO = "2002-12"               # up to here: "partial" (Aqua only starts on 4 Jul 2002)
ULTIMO_MES = "2026-10"                 # last full month of S-NPP
MIN_FOCOS_MODIS = 300                  # below this, the biome-month factor falls back to the national factor


def achar_biomas():
    """Looks for the biome boundaries (zip, shp, gpkg or geojson) inside the project."""
    candidatos = []
    for raiz, _, arquivos in os.walk(PASTA):
        for nome in arquivos:
            n = nome.lower()
            if "bioma" in n and n.endswith((".zip", ".shp", ".gpkg", ".geojson", ".json")):
                candidatos.append(Path(raiz) / nome)
    if not candidatos:
        print("ERROR: IBGE biome boundaries not found inside", PASTA)
        print("Download Biomas_250mil.zip from IBGE and put it in the project folder.")
        sys.exit(1)
    # Prefers extracted .shp/.gpkg; otherwise reads straight from the .zip
    candidatos.sort(key=lambda p: p.suffix.lower() == ".zip")
    arq = candidatos[0]
    print(f"Biome boundaries: {arq.relative_to(PASTA)}")
    biomas = gpd.read_file(arq)
    texto = [c for c in biomas.columns
             if c != "geometry" and not pd.api.types.is_numeric_dtype(biomas[c])]
    col = next((c for c in texto if "bioma" in c.lower()), None) or texto[0]
    biomas = biomas[[col, "geometry"]].rename(columns={col: "bioma"}).to_crs("EPSG:4326")
    # Keeps only land biomes (some IBGE versions include the Coastal-Marine System)
    biomas = biomas[~biomas["bioma"].str.contains("Costeiro|Marinho", case=False, na=False)]
    print("Biomes:", ", ".join(sorted(biomas["bioma"].unique())))
    return biomas


def bioma_por_quadradinho(grade, biomas):
    """Returns the biome of each grid cell (gi, gj), using the cell center."""
    cel = grade[["gi", "gj"]].drop_duplicates().copy()
    cel["lat"] = (cel["gi"] + 0.5) * TAMANHO_QUADRADINHO
    cel["lon"] = (cel["gj"] + 0.5) * TAMANHO_QUADRADINHO
    pts = gpd.GeoDataFrame(cel, geometry=gpd.points_from_xy(cel["lon"], cel["lat"]), crs="EPSG:4326")
    dentro = gpd.sjoin(pts, biomas, how="left", predicate="within")
    dentro = dentro[~dentro.index.duplicated()]
    fora = dentro["bioma"].isna()
    if fora.any():
        # Cells centered at sea or on a border: use the nearest biome
        perto = gpd.sjoin_nearest(pts[fora].to_crs("EPSG:5880"), biomas.to_crs("EPSG:5880"), how="left")
        perto = perto[~perto.index.duplicated()]
        dentro.loc[fora, "bioma"] = perto["bioma"]
    return dentro[["gi", "gj", "bioma"]]


def mes_ref(df):
    """Monthly period (year-month) built from the ano/mes columns."""
    return pd.PeriodIndex.from_fields(year=df["ano"], month=df["mes"], freq="M")


def main():
    grade = pd.read_parquet(PROCESSADOS / "grade_mensal.parquet")
    biomas = achar_biomas()
    mapa = bioma_por_quadradinho(grade, biomas)
    grade = grade.merge(mapa, on=["gi", "gj"], how="left")
    grade["periodo"] = mes_ref(grade)

    # Wide table: one row per grid cell × month, with MODIS and S-NPP side by side
    larga = (grade.pivot_table(index=["gi", "gj", "bioma", "ano", "mes", "periodo"],
                               columns="sensor", values="n_focos", aggfunc="sum", fill_value=0)
                  .reset_index())
    for s in ("modis", "snpp"):
        if s not in larga.columns:
            larga[s] = 0

    ini, fim = pd.Period(CALIBRACAO[0], "M"), pd.Period(CALIBRACAO[1], "M")
    cal = larga[(larga["periodo"] >= ini) & (larga["periodo"] <= fim)]

    # ---------- Factor k[biome, month] ----------
    def fatores(dados):
        """k per biome and calendar month, plus the national k per month (fallback)."""
        nac = dados.groupby("mes")[["snpp", "modis"]].sum()
        k_nac = nac["snpp"] / nac["modis"]
        bm = dados.groupby(["bioma", "mes"])[["snpp", "modis"]].sum()
        k = bm["snpp"] / bm["modis"]
        pouco = bm["modis"] < MIN_FOCOS_MODIS
        k[pouco] = k_nac.reindex(bm.index.get_level_values("mes"))[pouco.values].values
        return k.rename("k"), k_nac

    k, k_nac = fatores(cal)

    # ---------- Validation: leave one year out ----------
    linhas = []
    for ano in range(ini.year, fim.year + 1):
        treino, teste = cal[cal["ano"] != ano], cal[cal["ano"] == ano]
        k_t, _ = fatores(treino)
        t = teste.groupby(["bioma", "mes"])[["snpp", "modis"]].sum().join(k_t)
        t["prev"] = t["modis"] * t["k"]
        por_bioma = t.groupby("bioma")[["snpp", "prev"]].sum()
        por_bioma["ano"] = ano
        linhas.append(por_bioma.reset_index())
    val = pd.concat(linhas)
    val = val[val["snpp"] > 0]
    val["erro_%"] = (val["prev"] / val["snpp"] - 1) * 100
    resumo = (val.groupby("bioma")
                 .agg(focos_snpp_ano=("snpp", "mean"), erro_medio_abs_pct=("erro_%", lambda e: e.abs().mean()))
                 .round(1).sort_values("focos_snpp_ano", ascending=False))
    total = val.groupby("ano")[["snpp", "prev"]].sum()
    erro_br = ((total["prev"] / total["snpp"] - 1).abs().mean() * 100)

    # ---------- Harmonized series ----------
    larga = larga.merge(k.reset_index(), on=["bioma", "mes"], how="left")
    larga["k"] = larga["k"].fillna(larga["mes"].map(k_nac))
    viirs = larga["periodo"] >= pd.Period(INICIO_VIIRS, "M")
    larga["focos"] = np.where(viirs, larga["snpp"], larga["modis"] * larga["k"]).astype("float32")
    larga["status"] = np.select(
        [viirs, larga["periodo"] <= pd.Period(FIM_TERRA_SO, "M")],
        ["observado", "parcial"], default="estimado")
    larga = larga[larga["periodo"] <= pd.Period(ULTIMO_MES, "M")]
    larga["lat_centro"] = ((larga["gi"] + 0.5) * TAMANHO_QUADRADINHO).round(2)
    larga["lon_centro"] = ((larga["gj"] + 0.5) * TAMANHO_QUADRADINHO).round(2)
    saida = larga[["gi", "gj", "lat_centro", "lon_centro", "bioma", "ano", "mes",
                   "focos", "status", "modis", "snpp"]]
    saida = saida[(saida["focos"] > 0) | (saida["modis"] > 0) | (saida["snpp"] > 0)]

    saida.to_parquet(PROCESSADOS / "serie_harmonizada.parquet", index=False)
    k.reset_index().pivot(index="bioma", columns="mes", values="k").round(3) \
        .to_csv(PROCESSADOS / "fatores_bioma_mes.csv")
    resumo.to_csv(PROCESSADOS / "validacao_harmonizacao.csv")

    # ---------- Summary on screen ----------
    print("\nFactor k (S-NPP ÷ MODIS) per biome — mean of the 12 months:")
    print(k.groupby("bioma").mean().round(2).sort_values().to_string())
    print(f"\nValidation 2012–2019 (leaving one year out): mean annual error for Brazil = {erro_br:.1f}%")
    print("Mean annual error per biome (%):")
    print(resumo.to_string())
    anual = saida.groupby(["ano"]).agg(focos=("focos", "sum"), status=("status", "last"))
    anual["focos"] = (anual["focos"] / 1000).round(0)
    print("\nHarmonized series (thousand detections per year, VIIRS scale):")
    print(anual.to_string())
    print(f"\nSaved to {PROCESSADOS / 'serie_harmonizada.parquet'}")
    print("Done!")


if __name__ == "__main__":
    main()
