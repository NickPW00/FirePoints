---
data: 2026-11-15
autor: nicholas
ferramenta: Claude
tema: demo-slides
---

# Slides da demo: prints, mapa e PDF — 2026-11-15 — nicholas

## Objetivo
Fechar os 7 slides da demo: nomes e GitHub dos criadores, prints do app, slide do mapa, PDF com link público e declaração de IA.

## Decisões
- Capa dos slides e seção Team do README sem a divisão de responsabilidades: os dois trabalharam no pipeline, no método e no app — pedido do nicholas
- Demo entregue como PDF no repositório (`docs/demo/FirePoints-demo.pdf`), linkado no README; esse é o link público da submissão *(decisions #39)*
- Código sob licença MIT (`LICENSE`); dados e material de terceiros seguem os termos de cada fonte *(decisions #40)*
- README com três prints do app (mapa, calendário, Season vs normal) e aviso de que o app pode estar hibernando

## Código gerado ou alterado com IA
- `LICENSE` — texto padrão MIT — adicionado; `docs/img/app-{map,calendar,season}.png` — prints reais do app — adicionado; `README.md` — prints, seção License, aviso de hibernação — alterado
- `docs/demo/FirePoints-demo.pdf` — 7 slides em EN (texto, layout, gráficos de `data/processed/`, prints do app) — gerado
- `docs/demo/README.md` — origem de cada slide e uso de IA — gerado
- `README.md` (link da demo, uso de IA), `docs/AI_USE.md` (slides declarados) — alterado
- `README.md` — créditos completados: geonamescache, Leaflet.draw, branca, Jinja2, Pillow, ColorBrewer, logo e Brand Guidelines do Space Apps, fontes da demo, GitHub Actions, Python, Claude; Acknowledgements com Esri e GeoNames — alterado

## Ideias (ainda não decididas)
- —

## Pendências / perguntas para a dupla
- [ ] @mariaeliza confirmar a licença MIT (#40): vale para o código dos dois
- [x] @nicholas confirmar o nome da equipe (2XLero) e o nome da Maria Eliza como aparecem no slide 1 *(feito: 2XLero Team; Maria Elizabeth Tavares da Silva Ramos; slides, PDF e README corrigidos)*
- [ ] @mariaeliza conferir o slide 6 (print do mapa de 15/11, leitura "metade dos focos em 14% das células")
- [ ] @nicholas colar o link do PDF no campo "Link to Project Demo" e testar em janela anônima

## Referências
- Prints: calendário e "Season vs normal" do app no commit `0f559ae`; mapa do app publicado (firepoints.streamlit.app), 15/11/2026
- Space Apps Brand Guidelines (25/06/2026); Project Submission Guide (demo ≤ 7 slides, link público)
