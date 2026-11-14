# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
"""
05_exportar_focos.py
--------------------
Prepara os focos individuais (pontos) para o download em CSV do app.

Os arquivos focos_modis.parquet e focos_snpp.parquet passam de 100 MB e não cabem
no GitHub. Este script divide por ano e sensor, já com o bioma e o estado de cada foco:

  data/processed/focos/focos_<ano>_<sensor>.parquet

O app lê só os anos do período escolhido, filtra a região e gera o CSV.

Entrada:  data/processed/focos_modis.parquet, focos_snpp.parquet (01) e quadradinhos.parquet (04)
Como rodar:  python 05_exportar_focos.py
"""

from pathlib import Path

import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PROCESSADOS = PASTA / "data" / "processed"
SAIDA = PROCESSADOS / "focos"
LIMITE_MB = 95   # o GitHub recusa arquivos acima de 100 MB

COLUNAS = ["latitude", "longitude", "data", "sensor", "confianca", "frp", "dia_noite", "gi", "gj"]


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    quad = pd.read_parquet(PROCESSADOS / "quadradinhos.parquet", columns=["gi", "gj", "bioma", "estado"])
    resumo = []

    for sensor in ("modis", "snpp"):
        arq = PROCESSADOS / f"focos_{sensor}.parquet"
        if not arq.exists():
            print(f"Pulando {arq.name} (não encontrado)")
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
            destino = SAIDA / f"focos_{ano}_{sensor}.parquet"
            df.to_parquet(destino, index=False, compression="zstd")
            mb = destino.stat().st_size / 1e6
            resumo.append((ano, sensor, len(df), mb))
            aviso = "  <-- ATENÇÃO: grande demais para o GitHub" if mb > LIMITE_MB else ""
            print(f"  {destino.name}: {len(df):>10,} focos | {mb:6.1f} MB{aviso}".replace(",", "."))
        del tabela

    total = sum(r[3] for r in resumo)
    maior = max(resumo, key=lambda r: r[3]) if resumo else None
    print(f"\n{len(resumo)} arquivos, {total:.0f} MB no total")
    if maior:
        print(f"Maior arquivo: focos_{maior[0]}_{maior[1]}.parquet ({maior[3]:.1f} MB)")
    print("Pronto!")


if __name__ == "__main__":
    main()
