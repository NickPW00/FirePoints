# Data contract: pipeline → app

*AI-assisted: drafted with Claude (Anthropic) and reviewed by the team. See [`AI_USE.md`](AI_USE.md).*

Agreed by the team: **Maria Eliza owns the pipeline** (`pipeline/`) and **Nicholas owns the app** (`app/`).
The pipeline delivers ready tables in `data/processed/`; the app **only reads them**, without recomputing anything.
A column change = tell the other person and record it in `docs/decisions.md`.

Column names are in Portuguese (the pipeline was written in Portuguese); their meaning is given below and in [`data/processed/README.md`](../data/processed/README.md).

## 1. `serie_harmonizada.parquet` — ready ✅
One row per 0.1° grid cell × month. Used for the **map** and for the **area drawn by the user** (the app sums the cells that fall inside the area).

| Column | Type | Meaning |
|---|---|---|
| `gi`, `gj` | int | grid cell index (lat ÷ 0.1 and lon ÷ 0.1, rounded down) |
| `lat_centro`, `lon_centro` | float | cell center (degrees) |
| `bioma` | text | IBGE biome (Amazônia, Cerrado, Mata Atlântica, Caatinga, Pantanal, Pampa) |
| `ano`, `mes` | int | year and month, in Brasília time (#5) |
| `focos` | float | detections on the **VIIRS scale** (the value to show) |
| `status` | text | `observado` = observed (S-NPP, Feb 2012+), `estimado` = estimated (MODIS × factor, 2003–Jan 2012), `parcial` = partial (Nov 2000–2002, only Terra until Jul 2002) |
| `modis`, `snpp` | int | raw counts of each sensor (for comparison) |

Period: Nov 2000 to Oct 2026. Months without any detection are absent (treat them as 0).

## 2. `calendario.parquet` — ready ✅ (`pipeline/04_calendario.py`)
One row per region × year × month, Nov 2000 to Oct 2026, **with months without detections filled with 0**. Used for the **calendar** (months × years grid).

| Column | Type | Meaning |
|---|---|---|
| `regiao_tipo` | text | region type: `brasil`, `bioma` (biome) or `estado` (state) |
| `regiao` | text | `Brasil`, biome name or state code (e.g. `RJ`) |
| `regiao_nome` | text | full name (e.g. `Rio de Janeiro`) |
| `ano`, `mes` | int | year and month, in Brasília time |
| `focos` | float | detections on the VIIRS scale |
| `status` | text | same as table 1 (`observado`, `estimado`, `parcial`) |
| `media_mes` | float | historical mean of that month in the region (full years 2003–2025) |
| `anomalia_pct` | float | anomaly: `(focos ÷ media_mes − 1) × 100` |
| `faixa_anomalia` | int 1–5 | color class versus normal: 1 far below (<0.5×), 2 below (0.5–0.8×), 3 normal (0.8–1.25×), 4 above (1.25–2×), 5 far above (>2×) |
| `faixa_anomalia_nome` | text | the same in words (in Portuguese: `muito abaixo`, `abaixo`, `normal`, `acima`, `muito acima`) |
| `faixa_intensidade` | int 0–5 | color class of the number of detections: 0 none; 1–5 quintiles of that region's months with detections |

Suggestion for the app: two calendar views, **Intensity** (`faixa_intensidade`) and **Compared with normal** (`faixa_anomalia`), with a colorblind-safe scale.

## 2b. `quadradinhos.parquet` — built together with the calendar
Each grid cell (`gi`, `gj`, `lat_centro`, `lon_centro`) with its `bioma`, `estado` (state code) and `estado_nome` (state name). The app joins it with table 1 to filter the map by state.
The state is the one of the cell center; cells on a border count for one state only.

## 2c. `focos/ano=<year>/focos_<year>_<sensor>.parquet` — for the CSV download ✅ (42 files, 27.4 million detections, 267 MB) (`pipeline/05_exportar_focos.py`)
Every detection (point), split by year and sensor (`modis` or `snpp`) to fit on GitHub, in `ano=YYYY/` folders (Hive partitioning). Read in the app with `read_parquet('data/processed/focos/ano=*/*.parquet', hive_partitioning=true)` — the `ano` column comes from the folder.
An identical copy of the same files also sits loose in `focos/` (Git stores it only once). Different from the columns of step 01: no `gi`, `gj` and `origem`; with `bioma` and `estado`.

| Column | Type | Meaning |
|---|---|---|
| `latitude`, `longitude` | float | detection position |
| `data` | date | detection day, in Brasília time |
| `sensor` | text | `modis` or `snpp` |
| `confianca` | float | confidence. MODIS: 30–100; S-NPP: 50 (nominal) or 90 (high) |
| `frp` | float | fire radiative power (MW) |
| `dia_noite` | text | `D` (day) or `N` (night) |
| `bioma`, `estado` | text | biome and state of the 0.1° cell where the detection fell |

Raw counts of each sensor (not harmonized). The CSV must say so in its header or file name.

## 3. Supporting files
- `fatores_bioma_mes.csv` — S-NPP ÷ MODIS factor per biome and month (calibrated on 2012–2019).
- `validacao_harmonizacao.csv` — validation error per biome (for the methodology).
- `grade_mensal.parquet` — raw counts per sensor, grid cell and month (input of step 03).
