---
data: 2026-11-14
autor: nicholas
ferramenta: Claude
tema: stack-app
---

# Stack e 1ª versão do app — 2026-11-14 — nicholas

## Objetivo
Definir a stack e montar a primeira versão do app sobre os dados já no repo.

## Decisões
- nicholas fica com o app (`app/`) *(decisions #12)*
- Stack: Streamlit + pandas sobre `serie_harmonizada.parquet`; DuckDB só no CSV de pontos *(decisions #14)*
- CSV de pontos por último; sem os pontos até dom. de manhã → só a região da demo *(decisions #15)*

## Código gerado ou alterado com IA
- `app/streamlit_app.py` (UI: área, período, abas), `app/data.py` (área, contagens, anomalia, pontos via DuckDB), `app/charts.py` (calendário, anomalia, mapa, método), `app/requirements.txt` — gerado

## Ideias (ainda não decididas)
- #mapa mapa como raster lat×lon (sem basemap/WebGL): sempre renderiza na demo
- #validacao gráfico MODIS×k vs VIIRS 2012–2026: razão ≈1,00 em 2012–2019 e +5–11% em 2023–2026 (deriva orbital) → bom argumento na demo

## Pendências / perguntas para a dupla
- [ ] @mariaeliza subir os pontos particionados por ano em `data/processed/focos/ano=AAAA/` (colunas do 01; o app lê sozinho)
- [ ] @nicholas testar o "Draw on map" localmente (não deu para testar sem internet)

## Referências
—
