---
data: 2026-11-14
autor: nicholas
ferramenta: Claude
tema: documentacao
---

# Plano de documentação e registro compartilhado — 2026-11-14 — nicholas

## Objetivo
Definir quais documentos a equipe precisa entregar no Space Apps e criar um lugar único para as conversas de cada um com sua IA.

## Decisões
- Usar o próprio repo como registro central: `docs/decisions.md` + `docs/ai-log/` — sem montar vault compartilhado, por falta de tempo. *(decisions #1)*
- Documentos dos juízes em EN (README, METHODOLOGY, DATA, guia do app, demo); internos em PT. *(decisions #2)*
- Estrutura do repo: `pipeline/` (download, harmonize, validate), `app/streamlit_app.py`, `data/processed/` em Parquet, `docs/`.
- Parâmetros técnicos registrados para validação da dupla: dados, filtros, grade, calibração. *(decisions #3–#6)*

## Código gerado ou alterado com IA
- `docs/decisions.md`, `docs/ai-log/*`, `CLAUDE.md`, `.gitattributes` — estrutura de registro gerada com Claude.
- `docs/ai-log/ai_log.py` — script gerado com Claude.

## Pendências / perguntas para a dupla
- [ ] @parceira revisar as decisões #3–#6 e marcar como `confirmada` ou propor mudança
- [ ] @parceira criar o primeiro log dela usando o `_template.md`
- [ ] @nicholas definir responsáveis de cada documento do plano

## Referências
- Plano de documentação no Project "Hackathon SpaceApps 2026" (claude.ai)
