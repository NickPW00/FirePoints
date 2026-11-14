# Contrato de dados: pipeline → app

Combinado entre a dupla: **mariaeliza cuida do pipeline** (`pipeline/`) e **nicholas cuida do app** (`app/`).
O pipeline entrega tabelas prontas em `data/processed/`; o app **só lê**, sem refazer contas.
Mudança de coluna = avisar a outra pessoa e registrar no `docs/decisions.md`.

## 1. `serie_harmonizada.parquet` — pronto ✅
Uma linha por quadradinho de 0,1° × mês. Usar para o **mapa** e para a **área desenhada pelo usuário** (o app soma os quadradinhos que caem dentro da área).

| Coluna | Tipo | O que é |
|---|---|---|
| `gi`, `gj` | int | índice do quadradinho (lat ÷ 0,1 e lon ÷ 0,1, arredondado para baixo) |
| `lat_centro`, `lon_centro` | float | centro do quadradinho (graus) |
| `bioma` | texto | bioma do IBGE (Amazônia, Cerrado, Mata Atlântica, Caatinga, Pantanal, Pampa) |
| `ano`, `mes` | int | mês no horário de Brasília (#5) |
| `focos` | float | focos na **escala VIIRS** (valor a mostrar) |
| `status` | texto | `observado` (S-NPP, fev/2012+), `estimado` (MODIS × fator, 2003–jan/2012), `parcial` (nov/2000–2002, só Terra até 07/2002) |
| `modis`, `snpp` | int | contagens brutas de cada sensor (para quem quiser comparar) |

Período: nov/2000 a out/2026. Meses sem nenhum foco não aparecem (tratar como 0).

## 2. `calendario.parquet` — em construção ⏳ (`pipeline/04_calendario.py`)
Uma linha por região × ano × mês. Usar para o **calendário** (grade meses × anos).

| Coluna | Tipo | O que é |
|---|---|---|
| `regiao_tipo` | texto | `brasil`, `bioma` ou `estado` (estado depende do contorno de UFs do IBGE) |
| `regiao` | texto | nome da região (ex.: `Brasil`, `Cerrado`, `RJ`) |
| `ano`, `mes` | int | |
| `focos` | float | focos na escala VIIRS |
| `status` | texto | igual à tabela 1 |
| `media_mes` | float | média histórica daquele mês na região (2003–2025) |
| `anomalia_pct` | float | `(focos ÷ media_mes − 1) × 100` |
| `faixa` | int 1–5 | faixa de cor (1 = muito abaixo do normal … 5 = muito acima), para a escala acessível |

## 3. Arquivos de apoio
- `fatores_bioma_mes.csv` — fator S-NPP ÷ MODIS por bioma e mês (calibrado em 2012–2019).
- `validacao_harmonizacao.csv` — erro da validação por bioma (para a metodologia).
- `grade_mensal.parquet` — contagens brutas por sensor, quadradinho e mês (entrada do 03).
