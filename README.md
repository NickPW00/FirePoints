<a href="https://www.spaceappschallenge.org/"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/space-apps-small-logo-white.svg">
  <img src="docs/img/space-apps-small-logo-black.svg" alt="Space Apps logo" width="64" align="right">
</picture></a>

# FirePoints 🔥 — a harmonized burning calendar for Brazil

**[NASA Space Apps Challenge 2026](https://www.spaceappschallenge.org/) · Challenge: "Harmonization of MODIS and VIIRS Hot Spots"**

FirePoints merges 26 years of satellite fire detections into **one consistent record**, so emergency teams, scientists and land managers can see when and where Brazil burns, compare any month with its history and download the detections behind every number.

- **Live app:** <https://firepoints.streamlit.app>
- **Methodology:** [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) · **Data sources:** [`docs/DATA.md`](docs/DATA.md)

## The problem

NASA's MODIS sensors (Terra and Aqua) have recorded active fires since 2000 but are nearing the end of their missions. VIIRS replaces them with finer pixels (375 m vs 1 km) and detects **about 3.8 times more hotspots** over Brazil. Placed side by side, the two records show a false jump in 2012, so 2000–2011 cannot be compared with recent years.

## What we built

1. **Harmonized series, Nov 2000 – Oct 2026.** VIIRS S-NPP detections where they exist; before February 2012, MODIS counts converted to the VIIRS scale with a factor for each **biome and month**, calibrated on 2012–2019, when both sensors overlap and the MODIS orbits were stable.
2. **Validation.** Leaving each year of 2012–2019 out in turn, the predicted national total differs from the observed VIIRS total by **0.9% on average** (per biome: 1.3% Amazon to 7.4% Pampa).
3. **Burning calendar** for Brazil, its 6 biomes and 27 states: detections per month, the month's historical mean, the anomaly (for example "+37% above normal") and accessible color classes for intensity and anomaly.
4. **Web app** (Streamlit): choose a state, a biome or draw an area, pick a period, read the calendar and anomalies on a map, and download the detections as CSV.
5. **Transparency:** every month is labelled *observed*, *estimated* (2003–Jan 2012) or *partial* (Nov 2000–2002, when only Terra flew).

## Repository

| Path | What is there |
|---|---|
| `pipeline/` | Data pipeline, steps 01 → 05 (cleaning, comparison, harmonization, calendar, export) |
| `app/` | Streamlit app (`streamlit_app.py`, `data.py`, `charts.py`) |
| `data/processed/` | Pipeline outputs read by the app: harmonized series, calendar, biome factors, validation, point detections by year |
| `graficos/` | MODIS vs VIIRS comparison chart |
| `docs/` | Methodology, data sources, data contract between pipeline and app, decision log and AI logs |

## Run it

```bash
pip install -r requirements.txt        # pipeline
pip install -r app/requirements.txt    # app
streamlit run app/streamlit_app.py     # opens the app; data/processed/ is already in the repo
```

To rebuild the data from scratch, download the FIRMS and IBGE files listed in [`docs/DATA.md`](docs/DATA.md) into the project folder and run `pipeline/01_processar_focos.py` to `pipeline/05_exportar_focos.py` in order. On Windows, the `rodar*.bat` files do it with a double click.

## Limitations

These are **hotspot detections, not fire events or burned area**. Clouds are not modelled, the Pampa has few detections and the largest error, 2000–2002 is under-counted, and the VIIRS S-NPP record in FIRMS ends on 2 Nov 2026 (extending the series will require calibrating NOAA-20/21). Details in the methodology.

## Team

- **Maria Eliza** ([@Mariaeliza07](https://github.com/Mariaeliza07)) — data pipeline, harmonization and methodology
- **Nicholas** ([@NickPW00](https://github.com/NickPW00)) — web app

## Use of AI

The solution idea is entirely the team's own. We developed it with the help of **Claude (Anthropic)**, a large language model: to work out the technical details of the method with us, write and debug the pipeline and the app, and draft and translate the documentation. Every technical choice was confirmed by both teammates in [`docs/decisions.md`](docs/decisions.md). No images, video or audio were generated with AI.

- **Full declaration, list of AI-assisted files and English summary of our AI sessions:** [`docs/AI_USE.md`](docs/AI_USE.md)
- AI-assisted code files start with a header pointing to their session log in [`docs/ai-log/`](docs/ai-log/) (internal logs, kept in Portuguese).
- The processed data in `data/processed/` are outputs of the AI-assisted pipeline: see [`data/processed/README.md`](data/processed/README.md).
- Variable and column names in `pipeline/` and `data/processed/` are in Portuguese; a glossary is in [`data/processed/README.md`](data/processed/README.md#glossary-of-portuguese-names).

## Credits

### Data sources

| Provider | Data | Where we got it | Citation / terms |
|---|---|---|---|
| **NASA** — FIRMS | MODIS Collection 6.1 active fires, Terra + Aqua, 1 km (standard MCD14ML + near-real-time MCD14DL) | [FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/), area = Brazil, JSON | [doi:10.5067/FIRMS/MODIS/MCD14ML](https://doi.org/10.5067/FIRMS/MODIS/MCD14ML) · NRT: [doi:10.5067/FIRMS/MODIS/MCD14DL.NRT.0061](https://doi.org/10.5067/FIRMS/MODIS/MCD14DL.NRT.0061) |
| **NASA** — FIRMS | VIIRS S-NPP 375 m active fires, Collection 2 (standard VNP14IMGT + near-real-time VNP14IMGTDL_NRT) | [FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/), area = Brazil, JSON | [doi:10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002](https://doi.org/10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002) |
| **IBGE** | Biomes of Brazil, 1:250,000 (2019) — `Biomas_250mil.zip` | [geoftp.ibge.gov.br — biomas/vetores](https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/) | Free use with attribution |
| **IBGE** | State boundaries, 2024 territorial mesh — `BR_UF_2024.zip` | [geoftp.ibge.gov.br — malhas municipais 2024](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/) | Free use with attribution |
| **IBGE** | Municipal boundaries, 2024 territorial mesh — `BR_Municipios_2024.zip` (map borders of the selected area) | [geoftp.ibge.gov.br — malhas municipais 2024](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/) | Free use with attribution |
| **CARTO / OpenStreetMap** | Basemap and place-name tiles of the app map | [carto.com/attributions](https://carto.com/attributions) · [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) | © OpenStreetMap contributors © CARTO |
| **OpenStreetMap** contributors | Basemap of the app's map (loaded live through folium) | OpenStreetMap standard tiles | © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright) |

FIRMS downloads require a free [NASA Earthdata Login](https://urs.earthdata.nasa.gov) account. Full download steps: [`docs/DATA.md`](docs/DATA.md).

**Fire product references**
- Giglio, L., Schroeder, W., & Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire products. *Remote Sensing of Environment*, 178, 31–41. [doi:10.1016/j.rse.2016.02.054](https://doi.org/10.1016/j.rse.2016.02.054)
- Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The New VIIRS 375 m active fire detection data product: algorithm description and initial assessment. *Remote Sensing of Environment*, 143, 85–96. [doi:10.1016/j.rse.2013.12.008](https://doi.org/10.1016/j.rse.2013.12.008)

### Libraries and frameworks

All open source. Versions in [`requirements.txt`](requirements.txt) (pipeline) and [`app/requirements.txt`](app/requirements.txt) (app).

| Library | Used for | Where | Link |
|---|---|---|---|
| pandas | Tables, monthly aggregation | pipeline + app | <https://pandas.pydata.org> |
| NumPy | Numerical arrays | pipeline + app | <https://numpy.org> |
| Apache Arrow (PyArrow) | Reading and writing Parquet files | pipeline + app | <https://arrow.apache.org> |
| ijson | Streaming the large FIRMS JSON files straight from the zip | pipeline | <https://github.com/ICRAR/ijson> |
| tzdata | America/Sao_Paulo time zone for the local month | pipeline | <https://github.com/python/tzdata> |
| GeoPandas | Assigning each 0.1° cell to an IBGE biome and state | pipeline | <https://geopandas.org> |
| pyogrio | Reading the IBGE shapefiles | pipeline | <https://pyogrio.readthedocs.io> |
| Shapely | Geometry operations (area drawn by the user) | pipeline + app | <https://shapely.readthedocs.io> |
| Plotly | Charts (MODIS vs VIIRS, calendar, anomalies) | pipeline + app | <https://plotly.com/python/> |
| Streamlit | Web app framework | app | <https://streamlit.io> |
| folium (Leaflet) | Interactive map with zoom, pan and drawing tool | app | <https://python-visualization.github.io/folium/> · <https://leafletjs.com> |
| streamlit-folium | Embedding the folium map in Streamlit | app | <https://github.com/randyzwitch/streamlit-folium> |
| DuckDB | Fast filtering of the point detections for CSV download | app | <https://duckdb.org> |

**Hosting:** the app runs on [Streamlit Community Cloud](https://streamlit.io/cloud); code and data are on [GitHub](https://github.com/NickPW00/FirePoints).

### Acknowledgements

We acknowledge the use of data and imagery from NASA's Fire Information for Resource Management System ([FIRMS](https://www.earthdata.nasa.gov/data/tools/firms)), part of NASA's Earth Observing System Data and Information System (EOSDIS). Biome and state boundaries: IBGE (Instituto Brasileiro de Geografia e Estatística). Basemap: © OpenStreetMap contributors.

Full reference list in APA 7 format: [`docs/METHODOLOGY.md` § 9](docs/METHODOLOGY.md#9-references).
