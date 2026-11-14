# Síntese da dupla

> Gerado automaticamente a cada push por `.github/workflows/sintese.yml`. **Não edite à mão.**
> Fonte: `docs/decisions.md` + `docs/ai-log/`.

## ✅ Estado atual (confirmado pelos dois)

- —

## ⏳ Esperando revisão da outra pessoa

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

## 💡 Ideias por tema

### #app

- incluir um modelo preditivo de queimadas no calendário, além da calibração MODIS/VIIRS da #6 — *mariaeliza* ([log](ai-log/2026-11-14_1510_clara_revisao-inicial.md))

### #dados

- recortar a análise para o estado do Rio de Janeiro (nenhuma decisão atual limita a região) — *mariaeliza* ([log](ai-log/2026-11-14_1510_clara_revisao-inicial.md))

## ⚠️ Possíveis conflitos ou sobreposições

*Detectados por palavras em comum; confirme com o Claude no "abrir sessão".*

- —

## 📋 Pendências abertas

**@mariaeliza:**

- [ ] @mariaeliza revisar as decisões #3–#6 e marcar como `confirmada` ou propor mudança ([log](ai-log/2026-11-14_1430_nicholas_documentacao.md))
- [ ] @mariaeliza revisar as decisões #3–#6 ([log](ai-log/2026-11-14_1510_clara_revisao-inicial.md))

**@nicholas:**

- [ ] @nicholas definir responsáveis de cada documento do plano ([log](ai-log/2026-11-14_1430_nicholas_documentacao.md))

