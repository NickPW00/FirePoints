---
data: 2026-11-14
autor: mariaeliza
ferramenta: Claude
tema: creditos-fontes
---

# Créditos e fontes — 2026-11-14 — mariaeliza

## Objetivo
Conferir todos os links usados no projeto e dar crédito às fontes de dados, bibliotecas e frameworks, como pede o guia de submissão.

## Código gerado ou alterado com IA
- `README.md` — "Acknowledgements" virou "Credits": tabela de fontes (NASA FIRMS, IBGE, OpenStreetMap) com origem e DOI, referências dos produtos de fogo, tabela de bibliotecas e hospedagem — alterado
- `docs/DATA.md` — links clicáveis, DOIs do VIIRS S-NPP e do MODIS NRT, seção do basemap OSM — alterado
- `docs/img/space-apps-small-logo-{black,white}.svg` — logo pequeno oficial do Space Apps (só a órbita, sem texto), copiado sem alteração do pacote de logos da página /brand — adicionado
- `README.md` — logo no topo (claro/escuro) e link da página inicial do Space Apps — alterado
- `app/streamlit_app.py` — `space_apps_credit()`: linha "Made for the NASA Space Apps Challenge 2026" com o logo pequeno, no fim da barra lateral — alterado

## Decisões
- Nenhum logo da NASA no projeto; do Space Apps, só o logo pequeno sem texto (todos os outros têm "NASA" escrito) — pedido da mariaeliza

## Pendências / perguntas para a dupla
- [ ] @nicholas revisar o crédito do Space Apps na barra lateral do app (`space_apps_credit()`)
- [ ] @nicholas conferir se a lista de bibliotecas do app no README está completa
- [ ] @mariaeliza abrir firepoints.streamlit.app numa janela anônima para confirmar que é público (o guia exige)

## Referências
- Guia de submissão: listar todos os dados, recursos e ferramentas usados, inclusive código aberto — https://www.spaceappschallenge.org/resources/project-submission-guide/
- Citações sugeridas pelo FIRMS: https://www.earthdata.nasa.gov/data/tools/firms
- Atribuição do OSM: https://www.openstreetmap.org/copyright
