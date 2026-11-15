---
data: 2026-11-15
autor: nicholas
ferramenta: Claude
tema: previsao-futuro
---

# Previsão de queimadas como próximo passo — 2026-11-15 — nicholas

## Objetivo
Avaliar um modelo preditivo (próximos 12 meses, com GFWED) antes de construir e decidir se entra no app hoje.

## Decisões
- Previsão não entra no app nesta entrega: fica como "Future work" no METHODOLOGY e na descrição da submissão, com um teste reproduzível *(decisions #29)*
## Código gerado ou alterado com IA
- `pipeline/06_teste_previsao.py` — `previsoes`, `erro`, `main` — gerado
- `docs/METHODOLOGY.md` (§ 8 Future work; § 9 e § 10 renumeradas), `README.md`, `docs/DATA.md` (links § 10), `data/processed/README.md`, `docs/AI_USE.md` — alterado
## Ideias (ainda não decididas)
- #app modelo por quantis (mediana + faixa de 80%) com FWI/Drought Code defasados do GFWED e ENSO; aba "Outlook" só se ganhar da climatologia no mesmo teste
## Pendências / perguntas para a dupla
- [ ] @mariaeliza onde estão os arquivos do GFWED e até que mês vão? (não estão no repo)
## Referências
- Teste 2016–2025, Brasil, erro 1–3 meses: climatologia 34,2% → com anomalia recente 29,1%; sem ganho de 4 a 12 meses
