# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_clara_pipeline-focos.md
"""
02_comparar_sensores.py
-----------------------
Primeiro gráfico do projeto: focos por mês no Brasil, MODIS x VIIRS S-NPP.
Mostra o problema que a harmonização resolve: o S-NPP enxerga muito mais focos.

Como rodar (depois do 01_processar_focos.py):
    python 02_comparar_sensores.py

Gera: graficos/modis_vs_snpp.html (abre sozinho no navegador)
Precisa de: pip install -r requirements.txt
"""

import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# Raiz do projeto: a pasta acima de pipeline/ (ou a própria pasta do script, se ele estiver solto)
_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
ARQUIVO_GRADE = PASTA / "data" / "processed" / "grade_mensal.parquet"
PASTA_GRAFICOS = PASTA / "graficos"

ULTIMO_MES_COMPLETO = "2026-10"   # o S-NPP vai só até 02/11/2026

# Cores acessíveis para daltonismo (azul e laranja)
CORES = {"modis": "#0072B2", "snpp": "#E69F00"}
NOMES = {"modis": "MODIS (1 km)", "snpp": "VIIRS S-NPP (375 m)"}


def main():
    grade = pd.read_parquet(ARQUIVO_GRADE)

    # Total de focos por mês e sensor, no Brasil inteiro
    mensal = grade.groupby(["sensor", "ano", "mes"], as_index=False)["n_focos"].sum()
    mensal["mes_ref"] = pd.to_datetime(
        mensal["ano"].astype(str) + "-" + mensal["mes"].astype(str).str.zfill(2) + "-01")
    mensal = mensal[mensal["mes_ref"] <= pd.Timestamp(ULTIMO_MES_COMPLETO + "-01")]

    tabela = mensal.pivot(index="mes_ref", columns="sensor", values="n_focos").sort_index()

    # Período em que os dois funcionam juntos
    juntos = tabela.dropna(subset=[c for c in ["modis", "snpp"] if c in tabela.columns])
    if {"modis", "snpp"} <= set(tabela.columns) and len(juntos):
        razao = (juntos["snpp"].sum() / juntos["modis"].sum())
        print(f"\nPeríodo em comum: {juntos.index.min():%m/%Y} a {juntos.index.max():%m/%Y}")
        print(f"Focos MODIS: {juntos['modis'].sum():,.0f}".replace(",", "."))
        print(f"Focos S-NPP: {juntos['snpp'].sum():,.0f}".replace(",", "."))
        razao_txt = f"{razao:.1f}".replace(".", ",")
        print(f"O S-NPP detecta, em média, {razao_txt}x mais focos que o MODIS.")
        print("Esse número (que muda por mês e por bioma) é o que a harmonização vai corrigir.\n")

    # Gráfico
    fig = go.Figure()
    for sensor in ["modis", "snpp"]:
        if sensor in tabela.columns:
            fig.add_trace(go.Scatter(
                x=tabela.index, y=tabela[sensor], mode="lines",
                name=NOMES[sensor], line=dict(color=CORES[sensor], width=2),
                hovertemplate="%{x|%m/%Y}: %{y:,.0f} focos<extra>" + NOMES[sensor] + "</extra>",
            ))
    fig.update_layout(
        title="Focos de calor por mês no Brasil: MODIS x VIIRS S-NPP",
        xaxis_title="Mês",
        yaxis_title="Número de focos",
        hovermode="x unified",
        template="plotly_white",
        separators=",.",
        legend=dict(orientation="h", y=1.08, x=0),
    )

    PASTA_GRAFICOS.mkdir(exist_ok=True)
    saida = PASTA_GRAFICOS / "modis_vs_snpp.html"
    fig.write_html(saida, include_plotlyjs="cdn")
    print(f"Gráfico salvo em: {saida}")
    webbrowser.open(saida.as_uri())


if __name__ == "__main__":
    main()
