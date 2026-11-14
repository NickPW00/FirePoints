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
- Série harmonizada de 2003 em diante, fator por mês e região (2012–2019); 2003–2011 estimado, 2000–2002 parcial *(decisions #11)*
- Divisão de tarefas e contrato de dados pipeline → app (`docs/contrato-dados.md`) *(decisions #13)*

## Código gerado ou alterado com IA
- `pipeline/01_processar_focos.py` — lê o JSON direto do .zip (ijson), filtros da #4, grade 0,1° e mês em Brasília (#5), saída Parquet em `data/processed/` — gerado
- `pipeline/02_comparar_sensores.py` — gráfico mensal MODIS × S-NPP e razão média no período comum — gerado
- `pipeline/03_harmonizar.py` — fator k por bioma × mês (2012–2019), validação deixando um ano de fora, série harmonizada com status observado/estimado/parcial — gerado
- `pipeline/04_calendario.py` — calendário por Brasil, bioma e estado (IBGE BR_UF_2024): média do mês 2003–2025, anomalia, faixas de cor 1–5 — gerado

## Ideias (ainda não decididas)
- —

## Pendências / perguntas para a dupla
- [x] @mariaeliza rodar 01 e 02 com os dados reais *(feito: 17,9 mi focos S-NPP e 9,5 mi MODIS mantidos)*
- [ ] @nicholas tratar 2000-11 a 2002-06 (só Terra MODIS; Aqua começa em 04/07/2002) na harmonização
- [ ] @nicholas ler `docs/contrato-dados.md` e confirmar a #13 (divisão de tarefas e formato das tabelas do app)
- [ ] @nicholas revisar os scripts em `pipeline/` (também criados `requirements.txt` e `.gitignore` com `data/`)

## Referências
- FIRMS Archive Download: pedidos 848817 (MODIS C6.1) e 848820 (S-NPP), Brasil, JSON; S-NPP disponível só até 02/11/2026; arquivo `archive` do S-NPP tem 7,9 GB descompactado
- Resultado real: razão S-NPP/MODIS = 3,82 em 2012–2019, caindo para 3,4–3,6 em 2023–2025 → reforça calibrar só em 2012–2019 (#6)
- Resultado real: a razão varia por mês, de 2,8 (abril) a 4,1 (outubro) → fator mensal necessário (#6); pico de focos em set/2024 nos dois sensores
- Estudo 2000–2012: fator mensal (2012–2019) validado deixando um ano de fora — erro anual 0,7%, mensal 3% (Brasil); fora da amostra o erro sobe em 2023–2025 (5–11%), mas aí já existe VIIRS → usar o fator só para trás é confiável
- Estudo 2000–2012: o fator varia no espaço (caixas de 1°: 3,0–4,8); fator por região reduz o erro local de 12,6% para 7,7% → usar fator por bioma/região; 2001 só Terra e com poucos focos (135 mil vs ~500 mil em 2003)
- Harmonização rodada com biomas do IBGE (Biomas_250mil): erro anual da validação = Amazônia 1,3%, Cerrado 2,3%, Mata Atlântica 2,1%, Caatinga 3,1%, Pantanal 3,9%, Pampa 7,4%; fator mais baixo no Cerrado na estação chuvosa (mar = 1,27, poucos focos)
- Calendário gerado (Brasil, 6 biomas, 27 UFs; 10.608 linhas). 2026 tem ago–set muito abaixo do normal (−57% e −64%): é real, o S-NPP bate com o esperado pelo MODIS (razão ≈ 1,0), não é falha de dado
