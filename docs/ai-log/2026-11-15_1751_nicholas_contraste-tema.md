---
data: 2026-11-15
autor: nicholas
ferramenta: Claude
tema: contraste-tema
---

# Padrões visuais e contraste do tema — 2026-11-15 — nicholas

## Objetivo
Avaliar o que vale aplicar do Brand Guide do Space Apps no app e na demo, e corrigir o que custa pouco no site.

## Decisões
- Cor principal do app (`primaryColor`) de `#d94801` para `#c44100`: botões e links passam de 4,5:1 (antes 4,19:1 no fundo e 4,31:1 sob texto branco; agora 5,0:1 e 5,1:1) *(decisions #29)*

## Código gerado ou alterado com IA
- `.streamlit/config.toml` — `primaryColor` — alterado

## Ideias (ainda não decididas)
- #app manter as paletas de dados (laranja = quanto fogo; RdBu = abaixo/acima do normal, seguras para daltonismo) e as fontes do app; a paleta azul do Brand Guide é da marca, não de dados
- #demo slides: fundo Deep Blue `#07173F` ou Electric Blue `#0042A6` com texto branco, Fira Sans (títulos) + Overpass (corpo), prints do app em cartão branco, Rocket Red só como destaque

## Pendências / perguntas para a dupla
- [ ] @mariaeliza a cor principal do tema mudou (`.streamlit/config.toml`); ao mexer nas cores do app (#28), manter contraste ≥ 4,5:1 em texto e botões

## Referências
- Space Apps Brand Guidelines (25/06/2026): https://www.spaceappschallenge.org/brand/ ; contraste calculado pela fórmula do WCAG 2.x
