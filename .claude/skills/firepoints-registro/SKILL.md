---
name: firepoints-registro
description: Lê, analisa e salva o registro compartilhado do FirePoints (Space Apps 2026). Use com "abrir sessão", "checkpoint" ou "fechar sessão", ou ao falar de decisões e logs da dupla.
---

# Registro compartilhado do FirePoints

Repo: `NickPW00/FirePoints`. Dupla do NASA Space Apps 2026, desafio "Harmonization of MODIS and VIIRS Hot Spots". Cada integrante usa o próprio Claude, e o que importa de cada conversa vai para:

- `docs/decisions.md`: tabela onde só se acrescentam linhas (`# | Data | Quem | Decisão | Motivo | Status | Log`). Os status possíveis são `proposta`, `confirmada`, `substitui #N` e `descartada`.
- `docs/ai-log/AAAA-MM-DD_HHMM_<autor>_<tema>.md`: um resumo por sessão e por pessoa, no formato de `docs/ai-log/_template.md`.

Registros internos ficam em português. Documentos para os juízes ficam em inglês.

## Antes de tudo: quem é o autor e se há acesso ao repo

1. **Autor:** use o nome já dito na conversa (ou na memória). Se não souber, pergunte uma vez. O nome entra em minúsculas e sem acento (ex.: `nicholas`).
2. **Acesso ao repo**, em ordem de preferência:
   - **Git disponível** (Claude Code ou workspace com shell): use um clone existente ou rode `git clone https://github.com/NickPW00/FirePoints`. Faça sempre `git pull` antes de ler ou escrever.
   - **Só leitura** (conector do GitHub, arquivo anexado ou arquivo do Project): leia por ali e, na hora de salvar, siga o modo "sem escrita".
   - **Nenhum acesso:** peça para a pessoa colar o `docs/decisions.md` atual ou anexar o arquivo. Se ela não puder, siga só com o que está na conversa e avise isso em uma linha.

## Modo 1: abrir sessão (início da conversa)

Gatilhos: "abrir sessão", "o que a dupla já decidiu?", ou o início de uma conversa de trabalho no projeto.

1. Leia `docs/decisions.md` e os 3 logs mais recentes de `docs/ai-log/`.
2. Liste as pendências abertas. Com shell, rode `python docs/ai-log/ai_log.py pendencias <autor>`. Sem shell, procure as linhas `- [ ] @<autor>` nos logs.
3. Responda em no máximo 12 linhas:
   - **Decisões confirmadas** que tocam no assunto de hoje (uma linha cada).
   - **Propostas da outra pessoa** que esperam a sua revisão.
   - **Pendências para você.**
   - **Possíveis conflitos:** se o que a pessoa pediu hoje contradiz uma decisão `confirmada`, diga isso antes de seguir.
4. Continue a tarefa. Daqui em diante, trate as decisões `confirmada` como premissas.

## Modo 2: checkpoint (meio da conversa)

Gatilhos: "checkpoint", "salva o que temos até aqui", ou antes de uma mudança grande de assunto.

1. Rascunhe o log da sessão até aqui, no formato do template (ver modo 3).
2. Se o log desta sessão já existe, atualize esse mesmo arquivo em vez de criar outro.
3. Acrescente ao `decisions.md` só as decisões que a pessoa **já aceitou**. Sugestões em aberto não entram.
4. Salve conforme "Como salvar". Responda em 1–2 linhas o que foi salvo e siga a conversa.

## Modo 3: fechar sessão (fim da conversa)

Gatilhos: "fechar sessão", "registra essa conversa", "terminei por hoje".

1. **Analise a conversa inteira** e separe:
   - **Decisões:** só o que a pessoa aceitou. Suas sugestões que ela não confirmou ficam de fora.
   - **Código gerado ou alterado com IA:** arquivo e função, marcados como gerado, alterado ou revisado.
   - **Pendências:** tarefas ou perguntas para a dupla, no formato `- [ ] @nome ...`.
   - **Referências:** links e documentos da NASA/FIRMS usados.
2. Escreva `docs/ai-log/AAAA-MM-DD_HHMM_<autor>_<tema>.md`, com data e hora no fuso America/Sao_Paulo e no máximo 20 linhas:

   ```markdown
   ---
   data: AAAA-MM-DD
   autor: <autor>
   ferramenta: Claude
   tema: <tema-curto>
   ---

   # <Tema> — <data> — <autor>

   ## Objetivo
   ## Decisões
   - decisão — motivo *(decisions #N)*
   ## Código gerado ou alterado com IA
   - `arquivo` — `função` — gerado | alterado | revisado
   ## Pendências / perguntas para a dupla
   - [ ] @nome ...
   ## Referências
   ```
   Se uma seção ficar vazia, escreva "—".
3. **`decisions.md`:** acrescente as linhas no **fim** da tabela. O `#` continua a numeração da última linha, `Quem` é o autor, o status é `proposta` e a coluna `Log` aponta para o arquivo do log. Nunca edite nem apague linhas antigas.
   - Se a pessoa concordou com uma proposta da outra, acrescente uma linha `Confirma #N` com status `confirmada`.
   - Se mudou uma decisão, acrescente a nova com status `substitui #N`.
4. **Cabeçalho de IA:** todo arquivo de código gerado ou alterado deve ter no topo `# AI-assisted: Claude (Anthropic). See docs/ai-log/<arquivo-do-log>.md`. Com acesso de escrita, adicione o cabeçalho onde faltar. Sem acesso, avise quais arquivos precisam dele.
5. Salve conforme "Como salvar".

## Como salvar

**Com git e permissão de push:**
```
git pull
git add docs/ <arquivos com cabeçalho novo>
git commit -m "log(<autor>): <tema>"
git push
```
Se o push falhar por conflito, rode `git pull` e repita (o `decisions.md` usa `merge=union`). Depois confira se nenhum `#` ficou repetido e, se ficou, renumere só as linhas que você acabou de adicionar. Se o push for recusado por falta de permissão, use o modo sem escrita.

**Sem escrita:** entregue para a pessoa, prontos para colar:
1. O nome do arquivo de log e o conteúdo completo dele.
2. As linhas novas do `decisions.md`, só as linhas, já numeradas.
3. Uma linha com o comando: `git pull && git add docs/ && git commit -m "log: <tema>" && git push`.
Se houver como criar um arquivo para download, entregue o log como arquivo `.md`.

## Regras

- **Resumo, nunca a transcrição.** Sem cumprimentos nem tentativas descartadas.
- **Só registrar o que a pessoa disse ou aceitou.** Na dúvida, pergunte em uma linha ("Registro X como decisão?").
- **Nunca registrar** a MAP_KEY do FIRMS, senhas ou tokens.
- **Não ultrapassar o limite:** no máximo 20 linhas por log e 1–2 linhas de resposta no checkpoint.
