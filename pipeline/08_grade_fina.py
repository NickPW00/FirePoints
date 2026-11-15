# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1855_mariaeliza_mapa-pixels.md
"""
08_grade_fina.py  (step 8: fine grid for the app map)
----------------
The same harmonized counts as the 0.1° series, on a 4× finer grid (0.025° ≈ 2.8 km), so that
the app map shows small, sharp pixels instead of 11 km squares. Display only: the calendar,
the statistics and the click on the map keep using the 0.1° grid (decision #5).

Each detection counts as in 03_harmonizar.py:
  until Jan 2012      MODIS detection × k[biome, month]
  from Feb 2012       VIIRS S-NPP detection × 1
so the fine pixels inside a 0.1° cell add up to the cell of the harmonized series
(checked at the end; small differences come from detections exactly on a cell edge).

Fine cell of a detection:  fi = floor(latitude / 0.025),  fj = floor(longitude / 0.025)
(the 0.1° cell is gi = fi // 4, gj = fj // 4).

Input:  data/processed/focos/ano=<year>/focos_<year>_<sensor>.parquet (05),
        fatores_bioma_mes.csv and serie_harmonizada.parquet (03)
Output: data/processed/grade_fina.parquet  (fi, fj, ano, mes, focos), sorted by month
How to run:  python 08_grade_fina.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PROCESSADOS = PASTA / "data" / "processed"
FATOR = 4                      # fine pixels per side of a 0.1° cell
TAMANHO = 0.1 / FATOR          # 0.025°
INICIO_VIIRS = (2012, 2)       # same switch as 03_harmonizar.py (decision #6)


def main():
    k = pd.read_csv(PROCESSADOS / "fatores_bioma_mes.csv").melt(id_vars="bioma", var_name="mes", value_name="k")
    k["mes"] = k["mes"].astype(int)
    serie = pd.read_parquet(PROCESSADOS / "serie_harmonizada.parquet", columns=["gi", "gj", "ano", "mes", "focos"])
    ultimo = max(zip(serie["ano"], serie["mes"]))          # last month of the harmonized series

    partes = []
    for arquivo in sorted((PROCESSADOS / "focos").glob("ano=*/focos_*.parquet")):
        p = pd.read_parquet(arquivo, columns=["latitude", "longitude", "data", "sensor", "bioma"])
        data = pd.to_datetime(p["data"])
        p["ano"], p["mes"] = data.dt.year, data.dt.month
        viirs = (p["ano"] > INICIO_VIIRS[0]) | ((p["ano"] == INICIO_VIIRS[0]) & (p["mes"] >= INICIO_VIIRS[1]))
        depois = (p["ano"] > ultimo[0]) | ((p["ano"] == ultimo[0]) & (p["mes"] > ultimo[1]))
        p = p[((p["sensor"] == "snpp") == viirs) & ~depois]      # the sensor used by the series in each month
        if p.empty:
            continue
        p = p.merge(k, on=["bioma", "mes"], how="left")
        p["peso"] = np.where(p["sensor"] == "snpp", 1.0, p["k"])
        p["fi"] = np.floor(p["latitude"].astype("float64") / TAMANHO).astype("int16")
        p["fj"] = np.floor(p["longitude"].astype("float64") / TAMANHO).astype("int16")
        partes.append(p.groupby(["fi", "fj", "ano", "mes"], as_index=False)["peso"].sum())
        print(f"  {arquivo.name}: {len(p):,} detections")

    fina = pd.concat(partes).groupby(["fi", "fj", "ano", "mes"], as_index=False)["peso"].sum()
    fina = fina.rename(columns={"peso": "focos"}).sort_values(["ano", "mes", "fi", "fj"])
    fina = fina.astype({"ano": "int16", "mes": "int8", "focos": "float32"})
    saida = PROCESSADOS / "grade_fina.parquet"
    fina.to_parquet(saida, index=False, compression="zstd", compression_level=15)
    print(f"\n{saida.name}: {len(fina):,} rows, {saida.stat().st_size / 1e6:.1f} MB")

    # Check against the harmonized series (0.1°)
    pais = fina.assign(gi=fina["fi"] // FATOR, gj=fina["fj"] // FATOR).groupby(["gi", "gj"])["focos"].sum()
    grossa = serie.groupby(["gi", "gj"])["focos"].sum()
    junto = pd.concat([pais.rename("fina"), grossa.rename("serie")], axis=1).fillna(0)
    print(f"Total: fine grid {fina['focos'].sum():,.0f} · harmonized series {serie['focos'].sum():,.0f} "
          f"({(fina['focos'].sum() / serie['focos'].sum() - 1) * 100:+.3f}%)")
    print(f"Largest difference in one 0.1° cell: {(junto['fina'] - junto['serie']).abs().max():.1f} fires")


if __name__ == "__main__":
    main()
