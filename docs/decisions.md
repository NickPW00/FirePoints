# Registro de decisões

**Regra:** só acrescentar linhas no fim da tabela; nunca editar nem apagar as antigas. Para mudar uma decisão, adicione uma linha nova com status `substitui #N`.

Status: `proposta` (uma pessoa decidiu, falta a outra ver) · `confirmada` · `substitui #N` · `descartada`

| # | Data | Quem | Decisão | Motivo | Status | Log |
|---|---|---|---|---|---|---|
| 1 | 2026-11-14 | nicholas | Centralizar no próprio repo o que cada um conversa com sua IA (`docs/ai-log/` + este arquivo) | Fica junto do código, funciona com qualquer IA e alimenta a declaração de uso de IA | proposta | [log](ai-log/2026-11-14_1430_nicholas_documentacao.md) |
| 2 | 2026-11-14 | nicholas | Documentos para os juízes em inglês; registros internos em português | Juízes leem em EN; internamente é mais rápido em PT | proposta | [log](ai-log/2026-11-14_1430_nicholas_documentacao.md) |
| 3 | 2026-11-14 | nicholas | Dados: MODIS C6.1 + VIIRS S-NPP 375 m; SP no histórico e NRT nos últimos ~5 meses, marcado como provisório | NRT cobre o período que o SP ainda não tem | proposta | [log](ai-log/2026-11-14_1430_nicholas_documentacao.md) |
| 4 | 2026-11-14 | nicholas | Filtros: MODIS confidence ≥ 30; VIIRS confidence n/h; `type` = 0; só S-NPP | Remove detecções de baixa confiança e fontes industriais/estáticas | proposta | [log](ai-log/2026-11-14_1430_nicholas_documentacao.md) |
| 5 | 2026-11-14 | nicholas | Agregação em grade de 0,1°, mês no fuso America/Sao_Paulo | Resolução compatível com os dois sensores; mês local para o usuário | proposta | [log](ai-log/2026-11-14_1430_nicholas_documentacao.md) |
| 6 | 2026-11-14 | nicholas | Calibração com fator kₘ por mês e bioma, ajustado em 2012–2019; validação leave-one-year-out | Período de sobreposição antes da deriva orbital do Terra/Aqua | proposta | [log](ai-log/2026-11-14_1430_nicholas_documentacao.md) |
| 7 | 2026-11-14 | nicholas | Skill `firepoints-registro` (abrir sessão / checkpoint / fechar sessão) versionada em `.claude/skills/`; cada um instala na própria conta | Padroniza leitura e salvamento do registro nos dois Claudes | proposta | [log](ai-log/2026-11-14_1441_nicholas_skill-registro.md) |
| 8 | 2026-11-14 | nicholas | Skill passa a registrar automaticamente (modo 4) o que for importante e a abrir a sessão sozinha; incerto → pergunta em 1 linha | Não depender de lembrar dos comandos; menos coisa perdida entre os dois Claudes | proposta | [log](ai-log/2026-11-14_1445_nicholas_registro-automatico.md) |
| 9 | 2026-11-14 | nicholas | Merge automático: `docs/SINTESE.md` gerado por GitHub Action a cada push; ideias nos logs com `- #tema`; skill modo 5 "juntar ideias" | Visão central sempre atualizada; a IA de cada um faz a combinação semântica | proposta | [log](ai-log/2026-11-14_1454_nicholas_merge-ideias.md) |
| 10 | 2026-11-14 | mariaeliza | Região: Brasil inteiro; no app o usuário escolhe o estado ou desenha a área (RJ como exemplo na demo) | Mais focos → estatística mais confiável; substitui a ideia de recortar só o RJ | proposta | [log](ai-log/2026-11-14_1512_clara_pipeline-focos.md) |
| 11 | 2026-11-14 | mariaeliza | Série harmonizada a partir de 2003: MODIS × fator por mês e região (calibrado em 2012–2019) até 2011, VIIRS S-NPP real a partir de 2012; 2003–2011 marcado como estimado no app; nov/2000–2002 marcado como parcial (só Terra até 07/2002) | Validação deixando um ano de fora: erro anual 0,7%, mensal 3%; fator por região reduz o erro local de 12,6% para 7,7% | proposta | [log](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md) |
| 12 | 2026-11-14 | nicholas | Divisão de tarefas: nicholas fica responsável pelo app (`app/`) | Pipeline já está com mariaeliza; trabalho em paralelo usando o schema dos Parquet como contrato | proposta | [log](ai-log/2026-11-14_1642_nicholas_stack-app.md) |
