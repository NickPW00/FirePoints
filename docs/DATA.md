# Data sources

*AI-assisted: drafted with Claude (Anthropic) and reviewed by the team. The processed files in `data/processed/` are outputs of the AI-assisted pipeline — see [`data/processed/README.md`](../data/processed/README.md) and [`AI_USE.md`](AI_USE.md).*

All inputs are public and free. Raw files are not stored in this repository (the largest are close to 500 MB); the steps below download them again.

## 1. Active fires — NASA FIRMS

| Dataset | Sensor and resolution | Period available | Used in FirePoints |
|---|---|---|---|
| MODIS Collection 6.1 (MCD14ML standard / MCD14DL near-real-time) | Terra and Aqua, 1 km | Terra from 1 Nov 2000; Aqua from 4 Jul 2002 | Nov 2000 – Nov 2026 |
| VIIRS S-NPP 375 m, Collection 2 (standard + near-real-time) | Suomi NPP, 375 m | 20 Jan 2012 – 2 Nov 2026 | whole period |

**How we downloaded them**
1. Create a free NASA **Earthdata Login** account ([urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov)).
2. Open the **FIRMS Archive Download** page ([firms.modaps.eosdis.nasa.gov/download](https://firms.modaps.eosdis.nasa.gov/download/)), sign in with Earthdata and create one request per sensor: area = Brazil, dates = full period, format = JSON (CSV and SHP also work).
3. FIRMS emails a link to a zip (`DL_FIRE_M-C61_<id>.zip` for MODIS, `DL_FIRE_SV-C2_<id>.zip` for S-NPP), kept on its server for 45 days. Each zip has an **archive** file (standard, quality-controlled processing) and an **nrt** file (near-real-time, the most recent ~5 months, provisional).
4. Put the zips anywhere inside the project folder; `pipeline/01_processar_focos.py` reads them without unzipping.

Our requests: 848817 (MODIS) and 848820 (VIIRS S-NPP), made on 14 Nov 2026.

**Fields used:** latitude, longitude, acquisition date and time (UTC), confidence, fire radiative power (FRP), day/night flag and `type` (0 = presumed vegetation fire; 1 = active volcano; 2 = other static land source; 3 = offshore).

**Programmatic alternative:** the FIRMS API (`/api/area/csv/...`) needs a free MAP_KEY requested at [firms.modaps.eosdis.nasa.gov/api/map_key](https://firms.modaps.eosdis.nasa.gov/api/map_key). Never commit a MAP_KEY; use an environment variable or `st.secrets`.

**Citation (APA 7):**

NASA FIRMS. (2026). *MODIS Collection 6.1 hotspot / active fire detections MCD14ML* [Data set]. NASA Fire Information for Resource Management System.\
https://doi.org/10.5067/FIRMS/MODIS/MCD14ML

NASA FIRMS. (2026). *VIIRS (S-NPP) I band 375 m active fire product VNP14IMGT* [Data set]. NASA Fire Information for Resource Management System.\
https://doi.org/10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002

Full reference list: [`METHODOLOGY.md` § 9](METHODOLOGY.md#9-references).

## 2. Boundaries — IBGE

| Dataset | File | Used for |
|---|---|---|
| Biomes of Brazil, 1:250,000 (2019) | `Biomas_250mil.zip` — [geoftp.ibge.gov.br/…/biomas/vetores/](https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/) | biome of each 0.1° cell → harmonization factors |
| States (Unidades da Federação), 2024 territorial mesh | `BR_UF_2024.zip` — [geoftp.ibge.gov.br/…/municipio_2024/Brasil/](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/) | state of each cell → state calendars; smooth state borders on the map (`07_divisas.py`) |
| Municipalities, 2024 territorial mesh | `BR_Municipios_2024.zip` — same folder | municipal borders of the selected area on the map (`07_divisas.py`) |

The zips can stay compressed inside the project folder. IBGE data are public; the source must be cited and changes must be stated: the data keep the IBGE biome names, and the app shows **Amazon** and **Atlantic Forest** in English (Cerrado, Caatinga, Pantanal and Pampa are used as they are in English); borders are simplified for display.

**Citation (APA 7):**

Instituto Brasileiro de Geografia e Estatística. (2019). *Biomas do Brasil 1:250.000* [Data set]. IBGE.\
https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/

Instituto Brasileiro de Geografia e Estatística. (2024). *Malha territorial: Unidades da Federação (BR_UF_2024)* [Data set]. IBGE.\
https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/

## 2b. Basemap — OpenStreetMap

The app's map draws OpenStreetMap standard tiles under the data (loaded live by folium; nothing stored in this repository). © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).

## 3. Outputs in this repository

| File (`data/processed/`) | Produced by | Content |
|---|---|---|
| `grade_mensal.parquet` | 01 | raw detections per 0.1° cell, month and sensor |
| `serie_harmonizada.parquet` | 03 | harmonized detections per cell and month, with status |
| `fatores_bioma_mes.csv` | 03 | VIIRS ÷ MODIS factor per biome and month |
| `validacao_harmonizacao.csv` | 03 | leave-one-year-out error per biome |
| `calendario.parquet` | 04 | burning calendar for Brazil, biomes and states |
| `quadradinhos.parquet` | 04 | biome and state of each cell |
| `ufs_simplificado.geojson` | 07 | 27 state borders, simplified for display (~1 km), with UF, name and IBGE region |
| `municipios/<UF>.geojson` | 07 | municipal borders of each state, simplified for display (~400 m) |
| `focos/ano=<year>/focos_<year>_<sensor>.parquet` | 05 | individual detections for CSV download |

Column definitions: [`contrato-dados.md`](contrato-dados.md) (data contract) and the glossary in [`data/processed/README.md`](../data/processed/README.md).

## 4. Terms of use

NASA Earth science data are not subject to copyright and are freely available. IBGE data are free to use with attribution. OpenStreetMap data are available under the ODbL with attribution. FirePoints outputs inherit these terms.
