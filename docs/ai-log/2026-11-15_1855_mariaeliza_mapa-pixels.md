---
data: 2026-11-15
autor: mariaeliza
ferramenta: Claude
tema: mapa-pixels
---
# Mapa com pixels pequenos e nomes nítidos — 2026-11-15 — mariaeliza
## Objetivo
Com o mapa do PR #8 no ar, a mariaeliza (design) apontou: letras com baixa qualidade e, ao aproximar, o gradiente "todo junto". Pediu os pixels de antes, só que menores.
## Decisões
- Mapa desenhado numa grade 4× mais fina (0,025° ≈ 2,8 km), só para exibição; calendário, estatísticas e clique seguem na grade de 0,1° (#5/#20 não mudam) *(decisions #36)*
- Pixels nítidos por padrão; "Suavizar cores" vira opção desligada (substitui o campo contínuo da #35) *(decisions #37)*
- Nomes das cidades como texto (GeoNames, CC BY 4.0) em vez de blocos de imagem: nítidos em qualquer zoom *(decisions #38)*
## Código gerado ou alterado com IA
- `pipeline/08_grade_fina.py`, `pipeline/09_cidades.py` — gerados (saídas: `grade_fina.parquet` 13,9 MB, `cidades.json`)
- `app/data.py` — `load_fine()`, `fine_frequency()`, `fine_peak_month()`, `load_cities()` — gerado
- `app/maps.py` — `fine_layer()`, `CityLabels`, `_scale()`, `_png()` — gerado/alterado (removido `smooth_image`)
- `app/streamlit_app.py`, `app/i18n.py` — ligação e textos — alterado
## Ideias (ainda não decididas)
- #mapa tirar bairros (Copacabana, Vidigal) da lista de nomes; #app calendário e mapa com a mesma direção de cor
## Pendências / perguntas para a dupla
- [ ] @nicholas revisar e fazer o merge do PR do mapa com pixels pequenos
## Referências
- Conferência: grade fina soma 36.029.652 focos × 36.028.920 da série (+0,002%); GeoNames (geonames.org)
