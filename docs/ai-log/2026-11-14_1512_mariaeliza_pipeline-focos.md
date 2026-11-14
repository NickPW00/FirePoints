---
data: 2026-11-14
autor: mariaeliza
ferramenta: Claude
tema: pipeline-focos
---

# Pipeline de focos — 2026-11-14 — mariaeliza

## Objetivo
Baixar MODIS e VIIRS S-NPP do FIRMS (Brasil) e montar o primeiro processamento dos focos.

## Decisões
- Região: Brasil inteiro; no app o usuário escolhe o estado ou desenha a área (RJ como exemplo na demo) — mais focos, estatística mais confiável *(decisions #10)*

## Código gerado ou alterado com IA
- `pipeline/01_processar_focos.py` — lê o JSON direto do .zip (ijson), filtros da #4, grade 0,1° e mês em Brasília (#5), saída Parquet em `data/processed/` — gerado
- `pipeline/02_comparar_sensores.py` — gráfico mensal MODIS × S-NPP e razão média no período comum — gerado

## Ideias (ainda não decididas)
- —

## Pendências / perguntas para a dupla
- [x] @mariaeliza rodar 01 e 02 com os dados reais *(feito 16:1x: 17,9 mi focos S-NPP e 9,5 mi MODIS mantidos)*
- [ ] @nicholas tratar 2000-11 a 2002-06 (só Terra MODIS; Aqua começa em 04/07/2002) na harmonização
- [ ] @nicholas revisar os scripts em `pipeline/` (também criados `requirements.txt` e `.gitignore` com `data/`)

## Referências
- FIRMS Archive Download: pedidos 848817 (MODIS C6.1) e 848820 (S-NPP), Brasil, JSON; S-NPP disponível só até 02/11/2026; arquivo `archive` do S-NPP tem 7,9 GB descompactado
- Resultado real: razão S-NPP/MODIS = 3,82 em 2012–2019, caindo para 3,4–3,6 em 2023–2025 → reforça calibrar só em 2012–2019 (#6)
- Resultado real: a razão varia por mês, de 2,8 (abril) a 4,1 (outubro) → fator mensal necessário (#6); pico de focos em set/2024 nos dois sensores
