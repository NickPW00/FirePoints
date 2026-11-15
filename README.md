# FirePoints 🔥 — a harmonized burning calendar for Brazil

**NASA Space Apps Challenge 2026 · Challenge: "Harmonization of MODIS and VIIRS Hot Spots"**

FirePoints merges 26 years of satellite fire detections into **one consistent record**, so emergency teams, scientists and land managers can see when and where Brazil burns, compare any month with its history and download the detections behind every number.

- **Live app:** <https://firepoints.streamlit.app>
- **Methodology:** [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) · **Data sources:** [`docs/DATA.md`](docs/DATA.md)

## The problem

NASA's MODIS sensors (Terra and Aqua) have recorded active fires since 2000 but are nearing the end of their missions. VIIRS replaces them with finer pixels (375 m vs 1 km) and detects **about 3.8 times more hotspots** over Brazil. Placed side by side, the two records show a false jump in 2012, so 2000–2011 cannot be compared with recent years.

## What we built

1. **Harmonized series, Nov 2000 – Oct 2026.** VIIRS S-NPP detections where they exist; before February 2012, MODIS counts converted to the VIIRS scale with a factor for each **biome and month**, calibrated on 2012–2019, when both sensors overlap and the MODIS orbits were stable.
2. **Validation.** Leaving each year of 2012–2019 out in turn, the predicted national total differs from the observed VIIRS total by **0.9% on average** (per biome: 1.3% Amazônia to 7.4% Pampa).
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

We used Claude (Anthropic) to help write code and documentation. Every AI-assisted file starts with a header pointing to its log in [`docs/ai-log/`](docs/ai-log/), and every team decision is recorded in [`docs/decisions.md`](docs/decisions.md).

## Acknowledgements

We acknowledge the use of data from NASA's Fire Information for Resource Management System (FIRMS), part of NASA's Earth Science Data and Information System (ESDIS). Biome and state boundaries: IBGE (Instituto Brasileiro de Geografia e Estatística). Basemap: © OpenStreetMap contributors.

Full reference list in APA 7 format: [`docs/METHODOLOGY.md` § 9](docs/METHODOLOGY.md#9-references).
