# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
"""
05_exportar_focos.py  (step 5: export the detections)
--------------------
Prepares the individual detections (points) for the app's CSV download.

The files focos_modis.parquet and focos_snpp.parquet are over 100 MB and do not fit
on GitHub. This script splits them by year and sensor, with the biome and state of each detection:

  data/processed/focos/ano=<year>/focos_<year>_<sensor>.parquet   (partitioned by year, as the app expects)

The app reads them with DuckDB: read_parquet('data/processed/focos/ano=*/*.parquet', hive_partitioning=true),
filters the period and the region and builds the CSV.

Input:  data/processed/focos_modis.parquet, focos_snpp.parquet (01) and quadradinhos.parquet (04)
How to run:  python 05_exportar_focos.py
"""

from pathlib import Path

import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PROCESSADOS = PASTA / "data" / "processed"
SAIDA = PROCESSADOS / "focos"
LIMITE_MB = 95   # GitHub rejects files over 100 MB

COLUNAS = ["latitude", "longitude", "data", "sensor", "confianca", "frp", "dia_noite", "gi", "gj"]


def main():
    """Writes one Parquet file per year and sensor and prints the size of each one."""
    SAIDA.mkdir(parents=True, exist_ok=True)
    quad = pd.read_parquet(PROCESSADOS / "quadradinhos.parquet", columns=["gi", "gj", "bioma", "estado"])
    resumo = []

    for sensor in ("modis", "snpp"):
        arq = PROCESSADOS / f"focos_{sensor}.parquet"
        if not arq.exists():
            print(f"Skipping {arq.name} (not found)")
            continue
        print(f"\n=== {arq.name} ===")
        tabela = pq.read_table(arq, columns=COLUNAS)
        anos = pc.year(tabela["data"])
        for ano in sorted(pc.unique(anos).to_pylist()):
            df = tabela.filter(pc.equal(anos, ano)).to_pandas()
            df = df.merge(quad, on=["gi", "gj"], how="left").drop(columns=["gi", "gj"])
            for col in ("sensor", "dia_noite", "bioma", "estado"):
                df[col] = df[col].astype("category")
            df = df.sort_values(["data", "estado"]).reset_index(drop=True)
            pasta_ano = SAIDA / f"ano={ano}"
            pasta_ano.mkdir(exist_ok=True)
            destino = pasta_ano / f"focos_{ano}_{sensor}.parquet"
            df.to_parquet(destino, index=False, compression="zstd")
            mb = destino.stat().st_size / 1e6
            resumo.append((ano, sensor, len(df), mb))
            aviso = "  <-- WARNING: too large for GitHub" if mb > LIMITE_MB else ""
            print(f"  {destino.name}: {len(df):>10,} detections | {mb:6.1f} MB{aviso}")
        del tabela

    total = sum(r[3] for r in resumo)
    maior = max(resumo, key=lambda r: r[3]) if resumo else None
    print(f"\n{len(resumo)} files, {total:.0f} MB in total")
    if maior:
        print(f"Largest file: focos_{maior[0]}_{maior[1]}.parquet ({maior[3]:.1f} MB)")
    print("Done!")


if __name__ == "__main__":
    main()
