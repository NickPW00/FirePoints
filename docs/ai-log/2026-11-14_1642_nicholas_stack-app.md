---
data: 2026-11-14
autor: nicholas
ferramenta: Claude
tema: stack-app
---

# Stack e divisão do app — 2026-11-14 — nicholas

## Objetivo
Definir a stack do projeto e quem fica com o app.

## Decisões
- nicholas fica com o app (`app/`); avisa se mudar *(decisions #12)*

## Código gerado ou alterado com IA
—

## Ideias (ainda não decididas)
- #app stack: Streamlit (front + back num app só), lendo Parquet pré-processado; plotly no calendário; folium + Draw só para escolher a área (células agregadas no mapa, nunca focos brutos)
- #app DuckDB só no CSV dos focos da busca: consulta `focos_*.parquet` (27 mi pontos) por bbox + período sem carregar tudo na memória; calendário/anomalia seguem com pandas sobre `grade_mensal`/`serie_harmonizada`
- #infra `focos_*.parquet` não vai para o GitHub (>100 MB): particionar por ano ou hospedar fora (Release/Hugging Face) para o app em produção

## Pendências / perguntas para a dupla
- [ ] @mariaeliza informar o tamanho de `focos_modis.parquet` e `focos_snpp.parquet` (define onde hospedar os pontos para o CSV da busca)

## Referências
—
