<!-- AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1430_nicholas_documentacao.md -->
# FirePoints — instruções para o Claude

> *Instructions for the team's AI assistant (Claude), in Portuguese, written with its help. See [`docs/AI_USE.md`](docs/AI_USE.md).*

Projeto do NASA Space Apps 2026 (desafio "Harmonization of MODIS and VIIRS Hot Spots"), feito em dupla. Cada integrante usa o próprio Claude; o registro compartilhado fica em `docs/`.

## Antes de começar
- Leia `docs/SINTESE.md`, a visão unificada da dupla que é gerada sozinha (não edite esse arquivo), e o `docs/decisions.md` para saber o que já foi decidido. Não contradiga uma decisão `confirmada` sem apontar isso explicitamente.
- Veja as pendências abertas: `python docs/ai-log/ai_log.py pendencias`.

## Durante o trabalho
- Use a skill `firepoints-registro` (modo 4): registre automaticamente as decisões, o código, as descobertas, os bloqueios e as tarefas da dupla assim que surgirem. Pergunte antes quando houver dúvida, e avise em uma linha `📌` no fim da resposta.

## Ao terminar uma tarefa
1. Crie `docs/ai-log/AAAA-MM-DD_HHMM_<autor>_<tema>.md` no formato de `docs/ai-log/_template.md` (português, ≤ 20 linhas). Pergunte o nome do autor se não souber.
2. Acrescente as decisões no **fim** da tabela de `docs/decisions.md`, com status `proposta`. Nunca edite nem apague linhas existentes.
3. Todo arquivo de código que você gerou ou alterou leva no topo:
   `# AI-assisted: Claude (Anthropic). See docs/ai-log/<arquivo-do-log>.md`

## Convenções
- Documentos para os juízes (README, docs/METHODOLOGY.md, docs/DATA.md, docs/AI_USE.md, guia do app) e código (comentários, docstrings, mensagens) em inglês; registros internos (`decisions.md`, `ai-log/`) em português (#25). Ao criar um log novo, acrescente a sessão e os arquivos em `docs/AI_USE.md`.
- Nunca commitar a MAP_KEY do FIRMS: usar variável de ambiente ou `st.secrets`.
