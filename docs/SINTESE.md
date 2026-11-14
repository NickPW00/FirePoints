# Síntese da dupla

> Gerado automaticamente a cada push por `.github/workflows/sintese.yml`. **Não edite à mão.**
> Fonte: `docs/decisions.md` + `docs/ai-log/`.

## ✅ Estado atual (confirmado pelos dois)

- —

## ⏳ Esperando revisão da outra pessoa

**Propostas de mariaeliza:**

- **#10** Região: Brasil inteiro; no app o usuário escolhe o estado ou desenha a área (RJ como exemplo na demo) — Mais focos → estatística mais confiável; substitui a ideia de recortar só o RJ
- **#11** Série harmonizada a partir de 2003: MODIS × fator por mês e região (calibrado em 2012–2019) até 2011, VIIRS S-NPP real a partir de 2012; 2003–2011 marcado como estimado no app; nov/2000–2002 marcado como parcial (só Terra até 07/2002) — Validação deixando um ano de fora: erro anual 0,7%, mensal 3%; fator por região reduz o erro local de 12,6% para 7,7%
- **#13** Divisão: mariaeliza no pipeline, nicholas no app. O pipeline entrega tabelas prontas em `data/processed/` (série harmonizada e calendário com média, anomalia e faixa de cor) e o app só lê; área desenhada pelo usuário é somada no app a partir da `serie_harmonizada.parquet`. Colunas em `docs/contrato-dados.md` — Cada um trabalha sem esperar o outro; app leve

**Propostas de nicholas:**

- **#1** Centralizar no próprio repo o que cada um conversa com sua IA (`docs/ai-log/` + este arquivo) — Fica junto do código, funciona com qualquer IA e alimenta a declaração de uso de IA
- **#2** Documentos para os juízes em inglês; registros internos em português — Juízes leem em EN; internamente é mais rápido em PT
- **#3** Dados: MODIS C6.1 + VIIRS S-NPP 375 m; SP no histórico e NRT nos últimos ~5 meses, marcado como provisório — NRT cobre o período que o SP ainda não tem
- **#4** Filtros: MODIS confidence ≥ 30; VIIRS confidence n/h; `type` = 0; só S-NPP — Remove detecções de baixa confiança e fontes industriais/estáticas
- **#5** Agregação em grade de 0,1°, mês no fuso America/Sao_Paulo — Resolução compatível com os dois sensores; mês local para o usuário
- **#6** Calibração com fator kₘ por mês e bioma, ajustado em 2012–2019; validação leave-one-year-out — Período de sobreposição antes da deriva orbital do Terra/Aqua
- **#7** Skill `firepoints-registro` (abrir sessão / checkpoint / fechar sessão) versionada em `.claude/skills/`; cada um instala na própria conta — Padroniza leitura e salvamento do registro nos dois Claudes
- **#8** Skill passa a registrar automaticamente (modo 4) o que for importante e a abrir a sessão sozinha; incerto → pergunta em 1 linha — Não depender de lembrar dos comandos; menos coisa perdida entre os dois Claudes
- **#9** Merge automático: `docs/SINTESE.md` gerado por GitHub Action a cada push; ideias nos logs com `- #tema`; skill modo 5 "juntar ideias" — Visão central sempre atualizada; a IA de cada um faz a combinação semântica
- **#12** Divisão de tarefas: nicholas fica responsável pelo app (`app/`) — Pipeline já está com mariaeliza; trabalho em paralelo usando o schema dos Parquet como contrato

## 💡 Ideias por tema

### #app 🔀 *ideias dos dois — combinar*

- incluir um modelo preditivo de queimadas no calendário, além da calibração MODIS/VIIRS da #6 — *mariaeliza* ([log](ai-log/2026-11-14_1510_mariaeliza_revisao-inicial.md))
- stack: Streamlit (front + back num app só), lendo Parquet pré-processado; plotly no calendário; folium + Draw só para escolher a área (células agregadas no mapa, nunca focos brutos) — *nicholas* ([log](ai-log/2026-11-14_1642_nicholas_stack-app.md))
- DuckDB só no CSV dos focos da busca: consulta `focos_*.parquet` (27 mi pontos) por bbox + período sem carregar tudo na memória; calendário/anomalia seguem com pandas sobre `grade_mensal`/`serie_harmonizada` — *nicholas* ([log](ai-log/2026-11-14_1642_nicholas_stack-app.md))

### #dados

- recortar a análise para o estado do Rio de Janeiro (nenhuma decisão atual limita a região) — *mariaeliza* ([log](ai-log/2026-11-14_1510_mariaeliza_revisao-inicial.md))

### #infra

- `focos_*.parquet` não vai para o GitHub (>100 MB): particionar por ano ou hospedar fora (Release/Hugging Face) para o app em produção — *nicholas* ([log](ai-log/2026-11-14_1642_nicholas_stack-app.md))

## ⚠️ Possíveis conflitos ou sobreposições

*Detectados por palavras em comum; confirme com o Claude no "abrir sessão".*

- —

## 📋 Pendências abertas

**@mariaeliza:**

- [ ] @mariaeliza revisar as decisões #3–#6 e marcar como `confirmada` ou propor mudança ([log](ai-log/2026-11-14_1430_nicholas_documentacao.md))
- [ ] @mariaeliza revisar as decisões #3–#6 ([log](ai-log/2026-11-14_1510_mariaeliza_revisao-inicial.md))
- [ ] @mariaeliza ressincronizar o clone após o force-push: `git fetch origin && git reset --hard origin/main` (salvar antes o que não foi enviado) ([log](ai-log/2026-11-14_1611_nicholas_git-autoria.md))
- [ ] @mariaeliza conferir `git config user.email` — deve ser `217095895+Mariaeliza07@users.noreply.github.com`, senão os commits vão para a conta "clara" ([log](ai-log/2026-11-14_1611_nicholas_git-autoria.md))
- [ ] @mariaeliza informar o tamanho de `focos_modis.parquet` e `focos_snpp.parquet` (define onde hospedar os pontos para o CSV da busca) ([log](ai-log/2026-11-14_1642_nicholas_stack-app.md))

**@nicholas:**

- [ ] @nicholas definir responsáveis de cada documento do plano ([log](ai-log/2026-11-14_1430_nicholas_documentacao.md))
- [ ] @nicholas tratar 2000-11 a 2002-06 (só Terra MODIS; Aqua começa em 04/07/2002) na harmonização ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas ler `docs/contrato-dados.md` e confirmar a #13 (divisão de tarefas e formato das tabelas do app) ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas revisar os scripts em `pipeline/` (também criados `requirements.txt` e `.gitignore` com `data/`) ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))

