---
data: 2026-11-15
autor: mariaeliza
ferramenta: Claude
tema: mapa-windy
---
# Mapa estilo Windy e zoom por escolha — 2026-11-15 — mariaeliza
## Objetivo
Com o PR #5 no ar, a mariaeliza (design) pediu: gradiente, divisas e nomes mais bonitos (como o Windy), zoom do mapa e da página só quando ela quiser, e câmera livre.
## Decisões
- Zoom por escolha: botão "Zoom com rolagem" (desligado por padrão) e Ctrl+rolagem/pinça dão zoom no mapa; rolagem simples rola a página — clicar para ativar confundia e fazia a página pular *(decisions #32)*
- Câmera livre: sem trava no Brasil, zoom 3–12 *(decisions #33)*
- Visual: campo contínuo de cor, rampa "inferno" em fundo escuro (mais claro = mais focos), nomes brancos, divisas finas, municípios só de perto *(decisions #34)*
## Código gerado ou alterado com IA
- `app/maps.py` — `THEMES`, `smooth_image()`, `WheelZoom`, `base_map()`, `data_layer()` — gerado/alterado
- `app/charts.py` — `cell_map()` — alterado (cores do tema; corrigido: `t` escondia a tradução e o mapa sem fundo quebrava)
- `app/streamlit_app.py`, `app/i18n.py` — recarga dos módulos após deploy (igual ao PR #7), textos — alterado
## Ideias (ainda não decididas)
- #mapa tema claro (amarelo → vinho, fundo claro) pronto em `maps.THEMES["light"]`: trocar é uma linha
## Pendências / perguntas para a dupla
- [ ] @nicholas revisar e fazer o merge do PR do mapa (inclui a correção do PR #7, que pode ser fechado)
## Referências
- Windy (windy.com) como referência visual; Esri World Dark Gray Canvas (fundo e nomes, sem chave)
