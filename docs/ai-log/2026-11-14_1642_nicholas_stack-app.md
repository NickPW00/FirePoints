---
data: 2026-11-14
autor: nicholas
ferramenta: Claude
tema: stack-app
---

# Stack e 1ª versão do app — 2026-11-14 — nicholas

## Objetivo
Definir a stack e montar a primeira versão do app seguindo `docs/contrato-dados.md`.

## Decisões
- nicholas no app; confirma a divisão e o contrato de dados *(decisions #12, #16)*
- Stack: Streamlit + pandas sobre `serie_harmonizada.parquet`; DuckDB só no CSV de pontos *(decisions #14)*
- CSV de pontos lê `focos/ano=*/` (só anos do período, limite 1,5 mi pontos); plano B da #15 não é mais preciso *(decisions #17)*

## Código gerado ou alterado com IA
- `app/streamlit_app.py`, `app/data.py`, `app/charts.py`, `app/requirements.txt` — gerado (área: Brasil/estado/bioma/desenho/caixa; calendário contagem e "vs normal" com faixas do contrato; anomalia vs média 2003–2025; mapa raster; método/validação; 3 CSVs)

## Ideias (ainda não decididas)
- #validacao gráfico MODIS×k vs VIIRS: razão ≈1,00 em 2012–2019, +5–11% em 2023–2026 (deriva) → usar na demo
- #mapa mapa como imagem lat×lon (sem basemap/WebGL): renderiza sempre na demo

## Pendências / perguntas para a dupla
- [ ] @mariaeliza TO 2001–2004 quase todo "muito abaixo do normal": real (fronteira agrícola) ou fator subestimando os anos iniciais?
- [ ] @nicholas testar "Draw on map" localmente e publicar no Streamlit Cloud (entrypoint `app/streamlit_app.py`)

## Referências
- Conferência: contagens do app = `calendario.parquet` (Brasil, dif. máx. 0,06 foco); pontos RJ 2024 = grade (8.201)
