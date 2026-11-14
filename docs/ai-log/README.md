# ai-log — o que cada um conversou com sua IA

Um lugar só para as conversas da dupla com Claude (ou outra IA). Ninguém lê a conversa inteira: cada sessão vira um **resumo curto** aqui.

## Fluxo (2 minutos por sessão)

1. Terminou uma conversa útil com a IA? Cole nela o **prompt de fechamento** abaixo.
2. Salve a resposta como `docs/ai-log/AAAA-MM-DD_HHMM_autor_tema.md`
   (ex.: `2026-11-14_1600_nicholas_harmonizacao.md`).
3. Copie as decisões para o fim da tabela em `docs/decisions.md` com status `proposta`.
4. `git pull` → `git add docs/` → `git commit -m "log: tema"` → `git push`.
5. Quando a outra pessoa concordar com uma decisão sua, ela adiciona a confirmação (ver regras em `decisions.md`).

## Regras

- **Um arquivo por sessão e por pessoa** → os dois nunca editam o mesmo log, sem conflito no Git.
- **`decisions.md` só cresce.** O `.gitattributes` usa `merge=union`, então se os dois acrescentarem linhas ao mesmo tempo o Git junta as duas sozinho no `git pull`. Depois confira se os números `#` não repetiram.
- **Perguntas para a dupla** vão em `Pendências` como `- [ ] @nome ...`. Para ver as suas: `python docs/ai-log/ai_log.py pendencias nome`.
- **Arquivos de código feitos com IA** levam no topo:
  `# AI-assisted: Claude (Anthropic). See docs/ai-log/<arquivo-do-log>.md`

## Síntese da dupla: `docs/SINTESE.md`

A cada push, um GitHub Action junta os registros dos dois num arquivo só:
- **estado atual:** as decisões confirmadas;
- **propostas de cada um** que esperam a revisão do outro;
- **ideias por tema**, com 🔀 quando os dois tiveram ideias no mesmo tema;
- **possíveis conflitos** ⚠️;
- **pendências** de cada pessoa.

Não edite esse arquivo. Para juntar as ideias, diga ao seu Claude **"juntar ideias"**. Ele compara o que você pensou com o que a outra pessoa pensou e propõe uma combinação.

## Skill `firepoints-registro` (recomendado)

Com a skill, basta dizer **"abrir sessão"**, **"checkpoint"** ou **"fechar sessão"**. O Claude lê as decisões e pendências, analisa a conversa e salva o log (ou entrega o texto pronto para colar, se não puder fazer push).

- **Claude Code:** já vem no repo, em `.claude/skills/firepoints-registro/`. Não precisa instalar.
- **claude.ai:** compacte a pasta `.claude/skills/firepoints-registro/` em `.zip` e envie em Configurações → Skills (cada pessoa na própria conta).

Sem a skill, use o prompt abaixo.

## Prompt de fechamento (colar no fim da conversa)

```
Resuma esta conversa para o registro da equipe, em português, em no máximo 20 linhas,
EXATAMENTE neste formato Markdown (sem texto antes ou depois):

---
data: AAAA-MM-DD
autor: <meu nome>
ferramenta: Claude
tema: <tema-curto-sem-espacos>
---

# <Tema> — <data> — <autor>

## Objetivo
## Decisões
- decisão — motivo
## Código gerado ou alterado com IA
- `arquivo` — `função` — gerado | alterado | revisado
## Ideias (ainda não decididas)
- #tema ideia em uma linha
## Pendências / perguntas para a dupla
- [ ] @nome ...
## Referências

Regras: só decisões que eu aceitei (não as sugestões que descartei); ideias que surgiram e
ainda não foram decididas vão em "Ideias" com um tema (#dados, #filtros, #harmonizacao,
#validacao, #app, #mapa, #docs, #demo, #infra); liste todo arquivo de código que você gerou
ou alterou; se não houver nada numa seção, escreva "—".
```

## Para quem usa Projects no claude.ai

Cole nas **instruções do Project** de cada um:

> Estou no NASA Space Apps 2026 em dupla (repo NickPW00/FirePoints, desafio "Harmonization of MODIS and VIIRS Hot Spots"). Quando eu disser **"fechar sessão"**, gere o resumo no formato de `docs/ai-log/_template.md` (o mesmo do prompt de fechamento do README do ai-log). Ao sugerir código, lembre de incluir no topo o comentário `# AI-assisted: Claude (Anthropic)`.

Vale também subir `docs/decisions.md` como arquivo do Project de vez em quando, para o seu Claude saber o que a dupla já decidiu.

## Para quem usa Claude Code

O `CLAUDE.md` na raiz já instrui o Claude Code a escrever o log e as decisões ao fim de cada tarefa.

## Gerar a declaração de uso de IA (domingo 15h)

```
python docs/ai-log/ai_log.py ai-use > docs/AI_USE.md
```

Junta, de todos os logs, as ferramentas usadas e os arquivos gerados/alterados com IA. Traduza as descrições para EN e cole na seção "AI Use" do README e no campo "Use of SI" da submissão.
