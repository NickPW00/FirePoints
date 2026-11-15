# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
"""
02_comparar_sensores.py  (step 2: compare the sensors)
-----------------------
The project's first chart: monthly detections over Brazil, MODIS x VIIRS S-NPP.
It shows the problem that the harmonization solves: S-NPP sees many more hotspots.

How to run (after 01_processar_focos.py):
    python 02_comparar_sensores.py

Writes: graficos/modis_vs_snpp.html (opens in the browser by itself)
Requires: pip install -r requirements.txt
"""

import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# Project root: the folder above pipeline/ (or the script's own folder, if it sits on its own)
_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
ARQUIVO_GRADE = PASTA / "data" / "processed" / "grade_mensal.parquet"
PASTA_GRAFICOS = PASTA / "graficos"

ULTIMO_MES_COMPLETO = "2026-10"   # S-NPP only runs until 2 Nov 2026

# Colorblind-safe colors (blue and orange)
CORES = {"modis": "#0072B2", "snpp": "#E69F00"}
NOMES = {"modis": "MODIS (1 km)", "snpp": "VIIRS S-NPP (375 m)"}

# Marks the chart as AI-assisted (Space Apps rule: SI-generated code and data must be acknowledged)
NOTA_IA = "Chart code written with AI assistance (Claude, Anthropic). Data: NASA FIRMS."


def main():
    """Builds the monthly MODIS x S-NPP chart and prints the mean ratio over the overlap period."""
    grade = pd.read_parquet(ARQUIVO_GRADE)

    # Total detections per month and sensor, all of Brazil
    mensal = grade.groupby(["sensor", "ano", "mes"], as_index=False)["n_focos"].sum()
    mensal["mes_ref"] = pd.to_datetime(
        mensal["ano"].astype(str) + "-" + mensal["mes"].astype(str).str.zfill(2) + "-01")
    mensal = mensal[mensal["mes_ref"] <= pd.Timestamp(ULTIMO_MES_COMPLETO + "-01")]

    tabela = mensal.pivot(index="mes_ref", columns="sensor", values="n_focos").sort_index()

    # Period when both sensors work together
    juntos = tabela.dropna(subset=[c for c in ["modis", "snpp"] if c in tabela.columns])
    if {"modis", "snpp"} <= set(tabela.columns) and len(juntos):
        razao = (juntos["snpp"].sum() / juntos["modis"].sum())
        print(f"\nOverlap period: {juntos.index.min():%m/%Y} to {juntos.index.max():%m/%Y}")
        print(f"MODIS detections: {juntos['modis'].sum():,.0f}")
        print(f"S-NPP detections: {juntos['snpp'].sum():,.0f}")
        print(f"On average, S-NPP detects {razao:.1f}x more hotspots than MODIS.")
        print("This ratio (which changes by month and by biome) is what the harmonization corrects.\n")

    # Chart
    fig = go.Figure()
    for sensor in ["modis", "snpp"]:
        if sensor in tabela.columns:
            fig.add_trace(go.Scatter(
                x=tabela.index, y=tabela[sensor], mode="lines",
                name=NOMES[sensor], line=dict(color=CORES[sensor], width=2),
                hovertemplate="%{x|%m/%Y}: %{y:,.0f} detections<extra>" + NOMES[sensor] + "</extra>",
            ))
    fig.update_layout(
        title="Monthly active-fire detections over Brazil: MODIS x VIIRS S-NPP",
        xaxis_title="Month",
        yaxis_title="Number of detections",
        hovermode="x unified",
        template="plotly_white",
        separators=".,",
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.add_annotation(text=NOTA_IA, xref="paper", yref="paper", x=0, y=-0.18,
                       showarrow=False, font=dict(size=10, color="#666"), xanchor="left")

    PASTA_GRAFICOS.mkdir(exist_ok=True)
    saida = PASTA_GRAFICOS / "modis_vs_snpp.html"
    fig.write_html(saida, include_plotlyjs="cdn")
    print(f"Chart saved to: {saida}")
    webbrowser.open(saida.as_uri())


if __name__ == "__main__":
    main()
