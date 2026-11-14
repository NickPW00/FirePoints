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

## 2. `calendario.parquet` — pronto ✅ (`pipeline/04_calendario.py`)
Uma linha por região × ano × mês, de nov/2000 a out/2026, **com os meses sem foco preenchidos com 0**. Usar para o **calendário** (grade meses × anos).

| Coluna | Tipo | O que é |
|---|---|---|
| `regiao_tipo` | texto | `brasil`, `bioma` ou `estado` |
| `regiao` | texto | `Brasil`, nome do bioma ou sigla da UF (ex.: `RJ`) |
| `regiao_nome` | texto | nome por extenso (ex.: `Rio de Janeiro`) |
| `ano`, `mes` | int | mês no horário de Brasília |
| `focos` | float | focos na escala VIIRS |
| `status` | texto | igual à tabela 1 (`observado`, `estimado`, `parcial`) |
| `media_mes` | float | média histórica daquele mês na região (anos completos 2003–2025) |
| `anomalia_pct` | float | `(focos ÷ media_mes − 1) × 100` |
| `faixa_anomalia` | int 1–5 | cor da comparação com o normal: 1 muito abaixo (<0,5×), 2 abaixo (0,5–0,8×), 3 normal (0,8–1,25×), 4 acima (1,25–2×), 5 muito acima (>2×) |
| `faixa_anomalia_nome` | texto | o mesmo em palavras |
| `faixa_intensidade` | int 0–5 | cor da quantidade de focos: 0 sem focos; 1–5 quintis dos meses com focos daquela região |

Sugestão para o app: duas visões do calendário, **Intensidade** (`faixa_intensidade`) e **Comparado ao normal** (`faixa_anomalia`), com escala acessível para daltonismo.

## 2b. `quadradinhos.parquet` — gerado junto com o calendário
Cada quadradinho (`gi`, `gj`, `lat_centro`, `lon_centro`) com o seu `bioma`, `estado` e `estado_nome`. O app junta com a tabela 1 para filtrar o mapa por estado.
O estado é o do centro do quadradinho; quadradinhos na divisa contam para um só estado.

## 2c. `focos/focos_<ano>_<sensor>.parquet` — para o download em CSV ⏳ (`pipeline/05_exportar_focos.py`)
Cada foco detectado (ponto), dividido por ano e sensor (`modis` ou `snpp`) para caber no GitHub. O app lê só os anos do período escolhido, filtra a região e gera o CSV.

| Coluna | Tipo | O que é |
|---|---|---|
| `latitude`, `longitude` | float | posição do foco |
| `data` | data | dia da detecção no horário de Brasília |
| `sensor` | texto | `modis` ou `snpp` |
| `confianca` | float | MODIS: 30–100; S-NPP: 50 (nominal) ou 90 (alta) |
| `frp` | float | potência radiativa do fogo (MW) |
| `dia_noite` | texto | `D` (dia) ou `N` (noite) |
| `bioma`, `estado` | texto | do quadradinho de 0,1° onde o foco caiu |

Contagens brutas de cada sensor (não harmonizadas). O CSV deve dizer isso no cabeçalho ou no nome do arquivo.

## 3. Arquivos de apoio
- `fatores_bioma_mes.csv` — fator S-NPP ÷ MODIS por bioma e mês (calibrado em 2012–2019).
- `validacao_harmonizacao.csv` — erro da validação por bioma (para a metodologia).
- `grade_mensal.parquet` — contagens brutas por sensor, quadradinho e mês (entrada do 03).
