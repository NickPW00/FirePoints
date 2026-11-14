---
data: 2026-11-14
autor: nicholas
ferramenta: Claude
tema: revisao-docs
---

# Revisão do que falta na documentação — 2026-11-14 — nicholas

## Objetivo
Comparar o repo com o plano de documentação. Situação: README ~80%, METHODOLOGY ~95%, DATA ~85%, guia (aba "How to read") ok; uso de IA, demo e submissão ainda não começaram.

## Decisões
—
## Código gerado ou alterado com IA
—
## Ideias (ainda não decididas)
- #docs montar a página de submissão a partir do README (resumo) + METHODOLOGY (descrição) + DATA (NASA Data)

## Pendências / perguntas para a dupla
- [ ] @mariaeliza README: trocar "in progress" por https://firepoints.streamlit.app; corrigir @NickPW10 → @NickPW00; faltam screenshot, diagrama do pipeline e licença (não há LICENSE)
- [ ] @mariaeliza METHODOLOGY: falta a seção References e o gráfico previsto × observado da validação (criar `docs/img/`)
- [ ] @mariaeliza DATA.md: dicionário dos Parquet e colunas dos 3 CSVs do app em EN (hoje só no `contrato-dados.md`, em PT)
- [ ] @mariaeliza docstrings no pipeline (só 4 de 19 funções têm) e versões no `requirements.txt`
- [ ] @mariaeliza erro da validação: a #11 diz 0,7% e os docs dizem 0,9% → usar só 0,9% na submissão?
- [ ] @mariaeliza revisar as propostas #1, #2, #7, #8, #9, #12, #14 e #17
- [ ] @nicholas app: marcar meses NRT como provisórios (#3) ou ajustar o texto; docstrings no `streamlit_app.py`; `docs/USER_GUIDE.md` (aba How to read + colunas dos CSVs)
- [ ] @mariaeliza combinar com @nicholas quem faz: AI Use completo no README + texto do "Use of SI", demo (vídeo ≤ 30 s ou ≤ 7 slides) e página de submissão

## Referências
- Plano de documentação e checklist (Project "Hackathon SpaceApps 2026")
