---
name: firepoints-registro
description: Registro compartilhado do FirePoints (Space Apps 2026). Use com "abrir sessão", "checkpoint" ou "fechar sessão" e, sem pedido, sempre que surgir decisão, código, descoberta, bloqueio ou tarefa da dupla.
---

<!-- AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1441_nicholas_skill-registro.md -->
> *Assistant skill (in Portuguese) that keeps the team's shared AI log, written with Claude (Anthropic). See [`docs/AI_USE.md`](../../../docs/AI_USE.md).*

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

Gatilhos: "abrir sessão", "o que a dupla já decidiu?", ou **automaticamente** na primeira mensagem de trabalho sobre o FirePoints. No modo automático, faça a leitura em silêncio e mostre só o que for relevante para o pedido: conflitos, propostas que esperam revisão e pendências da pessoa, em no máximo 4 linhas antes da resposta. Se não houver nada relevante, não mostre nada.

1. Leia primeiro `docs/SINTESE.md`, a visão unificada da dupla, que o GitHub Action regenera a cada push. Se ela não existir ou estiver desatualizada e houver shell, rode `python docs/ai-log/ai_log.py sintese`. Depois leia `docs/decisions.md` e os 3 logs mais recentes de `docs/ai-log/`, se precisar de detalhe.
2. Liste as pendências abertas. Com shell, rode `python docs/ai-log/ai_log.py pendencias <autor>`. Sem shell, procure as linhas `- [ ] @<autor>` nos logs.
3. Responda em no máximo 12 linhas:
   - **Decisões confirmadas** que tocam no assunto de hoje (uma linha cada).
   - **Propostas da outra pessoa** que esperam a sua revisão.
   - **Pendências para você.**
   - **Ideias para combinar:** temas 🔀 ou conflitos ⚠️ da síntese que tocam no assunto de hoje. Se houver, rode o modo 5.
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
   ## Ideias (ainda não decididas)
   - #tema ideia em uma linha
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

## Modo 4: registro automático (durante a conversa, sem pedido)

Fica ativo em toda conversa sobre o FirePoints. A cada resposta, veja se apareceu algo importante para o projeto.

**Conta como importante:**
| Tipo | Exemplos | Vai para |
|---|---|---|
| Decisão técnica | dado/coleção, filtro, parâmetro, fórmula, métrica, biblioteca, arquitetura, estrutura do repo, formato de arquivo | `decisions.md` + log |
| Mudança de decisão | trocar a grade, o período de calibração ou o fuso | `decisions.md` (`substitui #N`) + log |
| Código para o repo | arquivo ou função gerada/alterada que vai ser usada | log (código com IA) + cabeçalho |
| Descoberta sobre os dados | bug, limitação, peculiaridade do FIRMS, resultado de validação | log (decisões ou referências) |
| Bloqueio ou risco ao prazo | API fora, dado faltando, algo que não termina até domingo | log (pendências) |
| Tarefa ou pergunta para a dupla | "ela precisa ver X", divisão de tarefas, responsável | log (pendências `@nome`) |
| Escopo, prazo ou entrega | cortar funcionalidade, mudar o formato da demo | `decisions.md` + log |
| Ideia ainda não decidida | "e se mostrarmos X?", alternativa boa que ficou para depois | log (`## Ideias`, `- #tema ...`) |

**Não conta como importante:** explicações e conceitos, alternativas descartadas, passos intermediários de debug, ajustes cosméticos, conversa fora do projeto.

**Como agir:**
1. **Claro** (a pessoa decidiu ou aceitou de forma explícita, ou o código foi aceito): registre sem perguntar.
2. **Parece importante, mas é incerto** (a sugestão foi sua e a pessoa não confirmou, ou soou como hipótese): ao fim da resposta, pergunte em uma linha: `📌 Registro como decisão: <resumo>? (s/n)`. Se a pessoa não responder, não registre.
3. **Contradiz uma decisão `confirmada`:** avise logo, antes de seguir: `⚠️ Isso muda a decisão #N (<resumo>). Registro como substituição?`
4. **Quando salvar:**
   - Decisões e pendências para a outra pessoa: salve na hora, porque a dupla precisa ver logo. Faça commit e push se tiver acesso.
   - O resto (código, descobertas): acumule e salve em lote junto da próxima decisão, num checkpoint, ou quando juntar 3 itens.
   - Escreva sempre no log desta sessão, criando-o no primeiro registro e atualizando-o depois. Não crie um arquivo por item.
   - Commit do modo automático: `log(<autor>): auto — <resumo curto>`.
5. **Avise em uma linha só**, no fim da resposta: `📌 Registrado: <itens>`. Nunca interrompa a resposta principal para isso.
6. **Sem escrita no repo:** acumule os itens na conversa e mostre `📌 Anotado (N itens pendentes de salvar)`. Entregue o bloco pronto para colar quando chegar a 5 itens, num checkpoint ou ao fechar a sessão.

## Modo 5: juntar ideias da dupla

Gatilhos: "juntar ideias", "o que ela/ele pensou sobre X?", ou automaticamente no "abrir sessão" quando a `SINTESE.md` tiver um tema 🔀 ou um conflito ⚠️ ligado ao assunto de hoje.

1. Leia na `SINTESE.md` as ideias e propostas da outra pessoa sobre o tema. Abra os logs citados se precisar de contexto.
2. Compare com o que a pessoa atual pensa ou pediu e classifique: **complementares** (dá para fazer as duas), **sobrepostas** (mesma ideia com outro nome) ou **conflitantes** (uma exclui a outra).
3. Proponha uma síntese em no máximo 5 linhas: o que fica de cada um, o que se combina e, se houver conflito, o trade-off. Não decida pela pessoa.
4. Se ela aceitar, registre uma decisão `proposta` com o motivo "combina ideias de <A> e <B>" e a pendência `- [ ] @<outra> validar combinação #N`. Nunca descarte uma proposta da outra pessoa: registre a alternativa e deixe a decisão final para as duas.

Temas usados nas ideias: `#dados`, `#filtros`, `#harmonizacao`, `#validacao`, `#app`, `#mapa`, `#docs`, `#demo`, `#infra`. Um tema novo só pode ser criado se nenhum desses servir.

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
- **Nunca editar nem commitar `docs/SINTESE.md`.** Quem gera esse arquivo é o GitHub Action. Localmente, só leia ou gere a síntese na saída do terminal.
- **Não ultrapassar o limite:** no máximo 20 linhas por log e 1–2 linhas de resposta no checkpoint.
- **Modo automático sem ruído:** no máximo uma linha `📌` por resposta, e nenhuma quando não houver nada importante. Mesmo tema não se registra duas vezes: atualize a linha do log.
