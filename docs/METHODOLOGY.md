# Methodology — Harmonizing MODIS and VIIRS active-fire hotspots over Brazil

**FirePoints · NASA Space Apps Challenge 2026 · "Harmonization of MODIS and VIIRS Hot Spots"**

We build one consistent monthly record of active-fire detections for Brazil from November 2000 to October 2026, expressed on the VIIRS S-NPP scale. VIIRS observations are used wherever they exist (February 2012 onward); earlier months are MODIS counts converted with biome- and month-specific factors calibrated on the years when both sensors operated. In a leave-one-year-out test, the harmonized annual total for Brazil differs from the observed VIIRS total by **0.9% on average**.

---

## 1. Data

| Source | Product | Coverage used | Access |
|---|---|---|---|
| NASA FIRMS | MODIS Collection 6.1 active fire (Terra + Aqua, 1 km) | Nov 2000 – Nov 2026 | FIRMS Archive Download, area = Brazil, JSON |
| NASA FIRMS | VIIRS S-NPP 375 m active fire (Collection 2) | 20 Jan 2012 – 2 Nov 2026 | FIRMS Archive Download, area = Brazil, JSON |
| IBGE | Biomes of Brazil 1:250,000 (`Biomas_250mil`, 2019) | — | geoftp.ibge.gov.br |
| IBGE | State boundaries (`BR_UF_2024`) | — | geoftp.ibge.gov.br |

Each FIRMS download contains a standard-processing **archive** file and a **near-real-time (NRT)** file. Archive data are used for the whole history; NRT data only for the dates after the last archive date, so no detection is counted twice. NRT months (roughly the last five) are provisional.

## 2. Cleaning (`pipeline/01_processar_focos.py`)

1. **Vegetation fires only:** detections with `type ≠ 0` (volcanoes, static industrial sources such as gas flares, offshore) are removed. NRT files carry no `type` field, so this filter applies to the archive only.
2. **Confidence:** MODIS `confidence ≥ 30`; VIIRS `confidence ∈ {nominal, high}`.
3. **Local time:** acquisition date and time (UTC) are converted to America/Sao_Paulo before assigning the month.
4. **Grid:** each detection is assigned to a 0.1° × 0.1° cell (≈ 11 km).

Result: **9,484,826 MODIS** and **17,909,522 VIIRS S-NPP** detections kept (93% and 90% of the raw records).

## 3. Why harmonization is needed

Over the overlap years the two sensors see the same fire seasons, but VIIRS detects **3.8 times more hotspots** than MODIS (2012–2019), because of its finer resolution (375 m vs 1 km) and higher sensitivity to small fires. The ratio is not constant:

- **By season:** nationally it ranges from about 2.8 (April) to 4.2 (October).
- **By biome:** the 12-month average goes from 3.0 (Cerrado) to 4.5 (Caatinga).
- **Over time:** it is stable from 2012 to 2019 (3.76–3.91 per year) and then falls to 3.4–3.6 in 2023–2025, consistent with the orbital drift of Terra and Aqua.

A single global factor would therefore bias both seasonality and regional totals.

## 4. Harmonization (`pipeline/03_harmonizar.py`)

Each 0.1° cell is assigned to the IBGE biome that contains its centre (coastal cells: nearest biome). For every biome *b* and calendar month *m*:

```math
k_{b,m} = \frac{\sum \text{VIIRS}_{b,m}}{\sum \text{MODIS}_{b,m}} \quad \text{over Feb 2012 – Dec 2019}
```

- **Calibration window 2012–2019:** both sensors are fully operational and the MODIS orbits had not yet drifted. February 2012 is the first full month of S-NPP.
- **Fallback:** if a biome-month has fewer than 300 MODIS detections in the window, the national factor for that month is used.
- **Harmonized value** of a cell-month = observed VIIRS from Feb 2012 onward; `MODIS × k(b,m)` before that.

| Biome | Mean k | Range over 12 months |
|---|---|---|
| Cerrado | 3.02 | 1.27 – 4.21 |
| Pantanal | 3.37 | 2.87 – 3.72 |
| Amazônia | 3.66 | 2.49 – 4.39 |
| Pampa | 4.07 | 3.36 – 6.18 |
| Mata Atlântica | 4.14 | 3.46 – 4.88 |
| Caatinga | 4.53 | 3.65 – 6.52 |

Full table: `data/processed/fatores_bioma_mes.csv`.

Every month carries a **status** flag shown in the app:

| Status | Period | Meaning |
|---|---|---|
| `observed` (`observado`) | Feb 2012 – Oct 2026 | VIIRS S-NPP detections |
| `estimated` (`estimado`) | Jan 2003 – Jan 2012 | MODIS (Terra + Aqua) × k |
| `partial` (`parcial`) | Nov 2000 – Dec 2002 | MODIS × k, but only Terra flew until Aqua started on 4 Jul 2002, so counts are underestimated |

## 5. Validation

**Leave-one-year-out (2012–2019).** For each year, the factors are recomputed without that year and used to predict its VIIRS counts from MODIS.

| Biome | Mean VIIRS detections per year | Mean absolute annual error |
|---|---|---|
| Amazônia | 546,401 | 1.3% |
| Cerrado | 439,983 | 2.3% |
| Mata Atlântica | 93,711 | 2.1% |
| Caatinga | 79,528 | 3.1% |
| Pantanal | 31,905 | 3.9% |
| Pampa | 5,169 | 7.4% |
| **Brazil** | — | **0.9%** (per year: −1.4% to +1.8%) |

**Spatial detail.** At 1° cells (held-out year 2019), a regional factor cuts the median annual error from 12.6% (one national factor) to 7.7%. This is why factors are computed per biome.

**Applying the factor forward fails, applying it backward is safe.** Used on 2020–2025, the 2012–2019 factors miss by −4% to +11%, growing after 2022 as the MODIS orbits drift. The factors are only ever applied to 2000–2012, when the MODIS instruments and orbits match the calibration period.

## 6. Burning calendar (`pipeline/04_calendario.py`)

For Brazil, each of the 6 biomes and each of the 27 states (cell centre → state), and every month from Nov 2000 to Oct 2026:

- **Detections** on the VIIRS scale and the month's status.
- **Historical mean** of that calendar month over the complete years 2003–2025.
- **Anomaly** = detections ÷ historical mean − 1.
- **Anomaly class** 1–5: much below (< 0.5×), below (0.5–0.8×), normal (0.8–1.25×), above (1.25–2×), much above (> 2×).
- **Intensity class** 0–5: 0 = no detections; 1–5 = quintiles of that region's months with detections.

Point-level detections for CSV download are split by year and sensor in `data/processed/focos/` (`pipeline/05_exportar_focos.py`). They are raw detections, not harmonized.

## 7. Limitations

- **Detections are not fires.** One fire can produce many pixels, and VIIRS resolves fires MODIS cannot. The harmonized series is "how many hotspots VIIRS would have reported", not a count of fire events or burned area.
- **Clouds and overpass times** are not modelled; the factors absorb their average effect for each biome and month.
- **Small samples:** the Pampa (≈ 5,000 VIIRS detections per year) has the largest error (7.4%); Cerrado factors in the wet season rest on few detections (March k = 1.27).
- **Borders:** a 0.1° cell belongs to a single state and biome (the one at its centre).
- **End of S-NPP:** the S-NPP record in FIRMS ends on 2 Nov 2026. Extending the series will require calibrating NOAA-20 or NOAA-21 against S-NPP in the same way.
- **2000–2002** remains underestimated (Terra only) and is flagged as partial instead of corrected.

## 8. Reproducing the results

Requirements: Python 3.11+ and `pip install -r requirements.txt`.

1. Download the FIRMS archives (MODIS C6.1 and VIIRS S-NPP, area Brazil) and the two IBGE files listed above into the project folder. The zips do not need to be extracted.
2. Run the scripts in order:
   ```
   python pipeline/01_processar_focos.py    # clean, local month, 0.1° grid
   python pipeline/02_comparar_sensores.py  # MODIS vs VIIRS chart
   python pipeline/03_harmonizar.py         # biome x month factors, validation, harmonized series
   python pipeline/04_calendario.py         # burning calendar for Brazil, biomes, states
   python pipeline/05_exportar_focos.py     # point files for the CSV download
   ```
The outputs and their columns are described in `docs/contrato-dados.md`.

## 9. References

References follow APA 7th edition.

**NASA data**

NASA FIRMS. (2026). *MODIS Collection 6.1 hotspot / active fire detections MCD14ML* [Data set]. NASA Fire Information for Resource Management System.\
https://doi.org/10.5067/FIRMS/MODIS/MCD14ML

NASA FIRMS. (2026). *VIIRS (S-NPP) I band 375 m active fire product VNP14IMGT* [Data set]. NASA Fire Information for Resource Management System.\
https://doi.org/10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002

NASA FIRMS. (2026). *FIRMS archive download* [Data portal]. Retrieved November 14, 2026.\
https://firms.modaps.eosdis.nasa.gov/download/

Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The new VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. *Remote Sensing of Environment, 143*, 85–96.\
https://doi.org/10.1016/j.rse.2013.12.008

**Other data**

Instituto Brasileiro de Geografia e Estatística. (2019). *Biomas do Brasil 1:250.000* [Data set]. IBGE.\
https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/

Instituto Brasileiro de Geografia e Estatística. (2024). *Malha territorial: Unidades da Federação (BR_UF_2024)* [Data set]. IBGE.\
https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/

OpenStreetMap contributors. (2026). *OpenStreetMap* [Map tiles].\
https://www.openstreetmap.org/copyright

**This project**

FirePoints Team. (2026). *FirePoints: Harmonized MODIS and VIIRS fire calendar for Brazil* [Source code and documentation]. GitHub.\
https://github.com/NickPW00/FirePoints

## Use of AI

The solution idea is the team's own. We developed it with the help of Claude (Anthropic): the pipeline code and this document were written with its assistance, and every technical choice was confirmed by both teammates in `docs/decisions.md`. Every AI-assisted file has a header pointing to its log in `docs/ai-log/`. Full declaration: [`AI_USE.md`](AI_USE.md).
