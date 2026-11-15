---
data: 2026-11-15
autor: nicholas
ferramenta: Claude
tema: ingles-e-ia
---

# Regulamento, marcação de IA e inglês — 2026-11-15 — nicholas

## Objetivo
Conferir o projeto contra os regulamentos do Space Apps (submissão, julgamento, FAQ, Connect, equipes, Brand Guide), marcar tudo o que foi feito com IA e passar para o inglês o que os juízes veem.

## Decisões
- Código (comentários, docstrings, mensagens), `.bat`, gráfico e contrato de dados em inglês; logs internos seguem em PT, com resumo em EN em `docs/AI_USE.md` *(decisions #25)*
- Texto oficial do uso de IA: a ideia da solução é da equipe; o desenvolvimento a partir dela foi feito com o Claude; toda escolha técnica confirmada pelos dois *(decisions #26)*
## Código gerado ou alterado com IA
- `pipeline/01`–`05` — comentários, docstrings e mensagens em EN (lógica igual, conferida por AST); `02`: rótulos do gráfico em EN + nota de IA — alterado
- `graficos/modis_vs_snpp.html` — regerado em EN — alterado
- `app/streamlit_app.py` — rodapé com link para o uso de IA — alterado
- `docs/ai-log/ai_log.py` — `sintese()`: linha em EN no cabeçalho — alterado
- `docs/AI_USE.md`, `data/processed/README.md` — gerado; `docs/contrato-dados.md` — traduzido; `README.md`, `docs/METHODOLOGY.md`, `docs/DATA.md` — alterado
- Cabeçalhos de IA em `rodar*.bat`, `requirements.txt`, `app/requirements.txt`, `.gitignore`, `.gitattributes`, `CLAUDE.md`, `SKILL.md`, `decisions.md`, `ai-log/README.md` — alterado
## Ideias (ainda não decididas)
- #demo aplicar o Brand Guide na demo: logo do Space Apps sem alterar, paleta azul + Rocket Red, Fira Sans/Overpass, contraste ≥ 4,5:1
## Pendências / perguntas para a dupla
- [ ] @mariaeliza revisar a tradução do `pipeline/` e do `contrato-dados.md` no PR (só texto mudou)
## Referências
- Project Submission Guide e Judging & Awards Guide (13/11/2026); Space Apps Brand Guidelines (25/06/2026)
