# Síntese da dupla

> Gerado automaticamente a cada push por `.github/workflows/sintese.yml`. **Não edite à mão.**
> Fonte: `docs/decisions.md` + `docs/ai-log/`.

## ✅ Estado atual (confirmado pelos dois)

- **#3** Dados: MODIS C6.1 + VIIRS S-NPP 375 m; SP no histórico e NRT nos últimos ~5 meses, marcado como provisório — *nicholas*
- **#4** Filtros: MODIS confidence ≥ 30; VIIRS confidence n/h; `type` = 0; só S-NPP — *nicholas*
- **#5** Agregação em grade de 0,1°, mês no fuso America/Sao_Paulo — *nicholas*
- **#6** Calibração com fator kₘ por mês e bioma, ajustado em 2012–2019; validação leave-one-year-out — *nicholas*
- **#13** Divisão: mariaeliza no pipeline, nicholas no app. O pipeline entrega tabelas prontas em `data/processed/` (série harmonizada e calendário com média, anomalia e faixa de cor) e o app só lê; área desenhada pelo usuário é somada no app a partir da `serie_harmonizada.parquet`. Colunas em `docs/contrato-dados.md` — *mariaeliza*

## ⏳ Esperando revisão da outra pessoa

**Propostas de mariaeliza:**

- **#10** Região: Brasil inteiro; no app o usuário escolhe o estado ou desenha a área (RJ como exemplo na demo) — Mais focos → estatística mais confiável; substitui a ideia de recortar só o RJ
- **#11** Série harmonizada a partir de 2003: MODIS × fator por mês e região (calibrado em 2012–2019) até 2011, VIIRS S-NPP real a partir de 2012; 2003–2011 marcado como estimado no app; nov/2000–2002 marcado como parcial (só Terra até 07/2002) — Validação deixando um ano de fora: erro anual 0,7%, mensal 3%; fator por região reduz o erro local de 12,6% para 7,7%

**Propostas de nicholas:**

- **#1** Centralizar no próprio repo o que cada um conversa com sua IA (`docs/ai-log/` + este arquivo) — Fica junto do código, funciona com qualquer IA e alimenta a declaração de uso de IA
- **#2** Documentos para os juízes em inglês; registros internos em português — Juízes leem em EN; internamente é mais rápido em PT
- **#7** Skill `firepoints-registro` (abrir sessão / checkpoint / fechar sessão) versionada em `.claude/skills/`; cada um instala na própria conta — Padroniza leitura e salvamento do registro nos dois Claudes
- **#8** Skill passa a registrar automaticamente (modo 4) o que for importante e a abrir a sessão sozinha; incerto → pergunta em 1 linha — Não depender de lembrar dos comandos; menos coisa perdida entre os dois Claudes
- **#9** Merge automático: `docs/SINTESE.md` gerado por GitHub Action a cada push; ideias nos logs com `- #tema`; skill modo 5 "juntar ideias" — Visão central sempre atualizada; a IA de cada um faz a combinação semântica
- **#12** Divisão de tarefas: nicholas fica responsável pelo app (`app/`) — Pipeline já está com mariaeliza; trabalho em paralelo usando o schema dos Parquet como contrato
- **#14** Stack do app: Streamlit (front + back) + pandas sobre `serie_harmonizada.parquet`; DuckDB só para o CSV dos focos individuais — Prazo curto, um deploy só (Streamlit Cloud); DuckDB evita carregar 27 mi pontos na memória
- **#15** CSV dos focos individuais fica por último; se os pontos não estiverem no repo até domingo de manhã, oferecer só os pontos da região da demo — Todo o resto do app depende só da série harmonizada, que já está no repo *(substituição proposta em #17)*
- **#17** CSV dos focos lê `focos/ano=*/` via DuckDB, só os anos do período, até 1,5 mi pontos por download — Pontos já estão no repo; plano B da #15 não é mais necessário

## 💡 Ideias por tema

### #app

- incluir um modelo preditivo de queimadas no calendário, além da calibração MODIS/VIIRS da #6 — *mariaeliza* ([log](ai-log/2026-11-14_1510_mariaeliza_revisao-inicial.md))

### #dados

- recortar a análise para o estado do Rio de Janeiro (nenhuma decisão atual limita a região) — *mariaeliza* ([log](ai-log/2026-11-14_1510_mariaeliza_revisao-inicial.md))

### #docs

- montar a página de submissão a partir do README (resumo) + METHODOLOGY (descrição) + DATA (NASA Data) — *nicholas* ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))

### #mapa

- mapa como imagem lat×lon (sem basemap/WebGL): renderiza sempre na demo — *nicholas* ([log](ai-log/2026-11-14_1642_nicholas_stack-app.md))

### #validacao

- gráfico MODIS×k vs VIIRS: razão ≈1,00 em 2012–2019, +5–11% em 2023–2026 (deriva) → usar na demo — *nicholas* ([log](ai-log/2026-11-14_1642_nicholas_stack-app.md))

## ⚠️ Possíveis conflitos ou sobreposições

*Detectados por palavras em comum; confirme com o Claude no "abrir sessão".*

- —

## 📋 Pendências abertas

**@mariaeliza:**

- [ ] @mariaeliza README: trocar "in progress" por https://firepoints.streamlit.app; corrigir @NickPW10 → @NickPW00; faltam screenshot, diagrama do pipeline e licença (não há LICENSE) ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))
- [ ] @mariaeliza METHODOLOGY: falta a seção References e o gráfico previsto × observado da validação (criar `docs/img/`) ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))
- [ ] @mariaeliza DATA.md: dicionário dos Parquet e colunas dos 3 CSVs do app em EN (hoje só no `contrato-dados.md`, em PT) ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))
- [ ] @mariaeliza docstrings no pipeline (só 4 de 19 funções têm) e versões no `requirements.txt` ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))
- [ ] @mariaeliza erro da validação: a #11 diz 0,7% e os docs dizem 0,9% → usar só 0,9% na submissão? ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))
- [ ] @mariaeliza revisar as propostas #1, #2, #7, #8, #9, #12, #14 e #17 ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))
- [ ] @mariaeliza combinar com @nicholas quem faz: AI Use completo no README + texto do "Use of SI", demo (vídeo ≤ 30 s ou ≤ 7 slides) e página de submissão ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))

**@nicholas:**

- [ ] @nicholas definir responsáveis de cada documento do plano ([log](ai-log/2026-11-14_1430_nicholas_documentacao.md))
- [ ] @nicholas tratar 2000-11 a 2002-06 (só Terra MODIS; Aqua começa em 04/07/2002) na harmonização ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas ler `docs/contrato-dados.md` e confirmar a #13 (divisão de tarefas e formato das tabelas do app) ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas revisar os scripts em `pipeline/` (também criados `requirements.txt` e `.gitignore` com `data/`) ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas os pontos estão em `data/processed/focos/ano=AAAA/` (como pedido); colunas: lat, lon, data, sensor, confianca, frp, dia_noite, bioma, estado — sem gi/gj/origem (ver contrato 2c) ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas (pedidos de melhoria do app, da mariaeliza) mapa com as divisas dos estados e a sigla de cada um ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas explicar melhor o que cada gráfico mostra, principalmente o mapa do Brasil (título claro + uma frase de leitura + legenda das cores) ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas ao selecionar uma região, destacá-la sem cortar o mapa: o Brasil inteiro continua visível e a região fica em evidência (referência: mapa da Globo https://share.google/FZ8TOfijHjce0dI4b) ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas zoom e arraste no mapa como no Google Maps, para ver a localidade de perto ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas melhorar o design; se ajudar, animações para a experiência do usuário ([log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md))
- [ ] @nicholas app: marcar meses NRT como provisórios (#3) ou ajustar o texto; docstrings no `streamlit_app.py`; `docs/USER_GUIDE.md` (aba How to read + colunas dos CSVs) ([log](ai-log/2026-11-14_1739_nicholas_revisao-docs.md))

