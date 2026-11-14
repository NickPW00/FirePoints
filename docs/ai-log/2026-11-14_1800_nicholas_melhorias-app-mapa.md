---
data: 2026-11-14
autor: nicholas
ferramenta: Claude
tema: melhorias-app-mapa
---

# Revisão de UX e mapa novo do app — 2026-11-14 — nicholas

## Objetivo
Revisar o app (código, leitura dos dados, UX/UI), atender os pedidos de melhoria da mariaeliza e corrigir os erros achados.

## Decisões
- Mapa em folium: basemap OSM em cinza + grade como imagem reprojetada para Mercator, divisas/siglas, região destacada sem cortar o Brasil; raster Plotly como reserva offline *(decisions #22)*
- Leitura dos números: meses parciais sem faixa no "vs normal"; "% de anos" divide pelos anos com dado; total do mapa respeita o mês; CSV de pontos até out/2026 *(decisions #23)*

## Código gerado ou alterado com IA
- `app/maps.py` — `build_grid()`, `render()`, `base_map()`, `data_layer()`, `mercator_image()` — gerado
- `app/data.py` — `fire_frequency()`, `add_anomaly()`, `_points_query()` — alterado; `season_envelope()`, `year_summary()`, `typical_season()` — gerado
- `app/charts.py` — `calendar()`, `cell_map()` — alterado (paleta única); `season_tracker()` — gerado
- `app/streamlit_app.py` — título e KPIs vs normal, abas preguiçosas, frase de leitura + legenda por gráfico, aba "Season vs normal", mapa "quando queima", animação dos 12 meses, download em um clique — alterado
- `.streamlit/config.toml` (tema) — gerado; `README.md` (link do app, conta NickPW00) — alterado

## Ideias (ainda não decididas)
- #mapa mapa de anomalia do mês (cada célula contra a própria média)

## Pendências / perguntas para a dupla
- [ ] @mariaeliza validar #22 e #23 (mapa novo e correções de leitura)
- [ ] @mariaeliza (opcional) exportar `data/processed/ufs_simplificado.geojson` (UFs do IBGE simplificadas): o app usa no lugar das divisas tiradas da grade
- [ ] @mariaeliza a cópia solta `focos/focos_*.parquet` dobra o checkout (559 MB) e o app só lê `focos/ano=*/`: pode remover?
- [ ] @nicholas testar o mapa com internet real (tiles OSM; só foi testado com tiles simulados) antes do merge e do deploy

## Referências
- Testes: 11 combinações de área/período sem exceção em todas as abas; downloads TO 2024–2026 (322.886 pontos); página do mapa 0,26 MB (figura antiga: 1,9 MB)
