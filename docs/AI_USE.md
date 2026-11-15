# Use of Super Intelligence (SI / AI) in FirePoints

*This page is the team's SI declaration for the NASA Space Apps Challenge 2026. It summarizes, in English, our internal AI logs ([`docs/ai-log/`](ai-log/)) and decision log ([`docs/decisions.md`](decisions.md)), which we kept in Portuguese while working.*

## In short

- **The idea is ours.** The solution idea — merge MODIS and VIIRS into one comparable fire record for Brazil and turn it into a burning calendar that anyone can query for their own area — is entirely the team's own.
- **We developed it with AI.** From that idea, we used **Claude (Anthropic)**, a large language model, as an assistant to develop the solution: to work out the technical details of the method with us (filters, grid, calibration period, validation design), to write and debug the Python pipeline and the Streamlit app, and to draft and translate the documentation.
- **The team decided.** Every technical choice was recorded in `docs/decisions.md` as a proposal and only became final after both teammates confirmed it (for example, decisions #3–#6 on data, filters, grid and calibration were confirmed in #18–#21). We ran the pipeline, checked the numbers and tested the app ourselves.
- **Nothing else was generated.** No images, video or audio were generated with AI. No NASA branding was used or modified.

## How AI-assisted content is marked

| What | How it is marked |
|---|---|
| Code (`app/`, `pipeline/`, `docs/ai-log/ai_log.py`, `.github/`, config files, `.bat` scripts) | A header comment at the top of each file: `AI-assisted: Claude (Anthropic). See docs/ai-log/<session log>.md` |
| Documentation (README, METHODOLOGY, DATA, data contract, this page) | A visible note at the top or bottom of the page |
| Data (`data/processed/`) | [`data/processed/README.md`](../data/processed/README.md): all files there are outputs of the AI-assisted pipeline run on NASA FIRMS and IBGE data |
| Chart (`graficos/modis_vs_snpp.html`) | A visible note under the chart and an HTML comment |
| App | A line in the app footer |
| Team tooling (`CLAUDE.md`, `.claude/skills/`) | Instructions for the AI assistant itself, written with it; marked at the top |

## AI-assisted files

| File(s) | What the AI did | Who worked on it | Session log |
|---|---|---|---|
| `docs/decisions.md`, `docs/ai-log/*`, `CLAUDE.md`, `.gitattributes` | Created the structure of the team's shared log | Nicholas | [1430](ai-log/2026-11-14_1430_nicholas_documentacao.md) |
| `docs/ai-log/ai_log.py` | Wrote the log utility (open tasks, team synthesis, AI-use table) | Nicholas | [1430](ai-log/2026-11-14_1430_nicholas_documentacao.md), [1454](ai-log/2026-11-14_1454_nicholas_merge-ideias.md) |
| `.claude/skills/firepoints-registro/SKILL.md` | Wrote the assistant skill that keeps the shared log | Nicholas | [1441](ai-log/2026-11-14_1441_nicholas_skill-registro.md), [1445](ai-log/2026-11-14_1445_nicholas_registro-automatico.md), [1454](ai-log/2026-11-14_1454_nicholas_merge-ideias.md) |
| `.github/workflows/sintese.yml` | Wrote the GitHub Action that regenerates `docs/SINTESE.md` | Nicholas | [1454](ai-log/2026-11-14_1454_nicholas_merge-ideias.md) |
| `pipeline/01_processar_focos.py` | Wrote the reader of the FIRMS .zip files, the filters (#4), the 0.1° grid and local month (#5) | Maria Eliza | [1512](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md) |
| `pipeline/02_comparar_sensores.py` | Wrote the monthly MODIS × S-NPP chart and the overlap ratio | Maria Eliza | [1512](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md) |
| `pipeline/03_harmonizar.py` | Wrote the factor k per biome × month (2012–2019), the leave-one-year-out validation and the harmonized series | Maria Eliza | [1512](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md) |
| `pipeline/04_calendario.py` | Wrote the calendar for Brazil, biomes and states: monthly mean 2003–2025, anomaly, color classes | Maria Eliza | [1512](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md) |
| `pipeline/05_exportar_focos.py` | Wrote the export of individual detections by year and sensor | Maria Eliza | [1512](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md) |
| `requirements.txt`, `.gitignore`, `rodar*.bat` | Wrote the pipeline dependencies, ignore rules and Windows run scripts | Maria Eliza | [1512](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md) |
| `docs/METHODOLOGY.md`, `README.md`, `docs/DATA.md` | Drafted the methodology, home page and data sources; later added APA 7 references | Maria Eliza, Nicholas | [1512](ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md), [2303](ai-log/2026-11-14_2303_nicholas_submissao-ideias-app.md) |
| `app/streamlit_app.py`, `app/data.py`, `app/charts.py`, `app/requirements.txt` | Wrote the first app (area selection, calendar, anomaly, map, method tab, 3 CSV downloads), then improved it | Nicholas | [1642](ai-log/2026-11-14_1642_nicholas_stack-app.md), [1800](ai-log/2026-11-14_1800_nicholas_melhorias-app-mapa.md) |
| `app/maps.py`, `.streamlit/config.toml` | Wrote the map with basemap and the app theme | Nicholas | [1800](ai-log/2026-11-14_1800_nicholas_melhorias-app-mapa.md) |
| `pipeline/*.py`, `rodar*.bat`, `docs/contrato-dados.md`, `graficos/modis_vs_snpp.html`, `data/processed/README.md`, this page | Translated comments, messages and docs into English; added the AI marks | Nicholas | [1515](ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md) |
| `README.md` (Credits), `docs/DATA.md`, `app/streamlit_app.py` (Space Apps credit in the sidebar) | Checked every link in the repository; organized credits for data sources, libraries and frameworks; added the Space Apps small logo (official file, unaltered) | Maria Eliza | [2331](ai-log/2026-11-14_2331_mariaeliza_creditos-fontes.md) |

| `pipeline/06_teste_previsao.py`, `data/processed/teste_previsao.csv`, METHODOLOGY § 8 | Wrote the outlook test (rolling-origin forecasts, climatology vs recent anomaly) and the Future work section | Nicholas | [1733](ai-log/2026-11-15_1733_nicholas_previsao-futuro.md) |

Not AI-assisted: `.devcontainer/devcontainer.json` (GitHub Codespaces template for Streamlit).

## AI sessions (summary of `docs/ai-log/`)

| Session | Person | Goal |
|---|---|---|
| 14 Nov, 14:30 | Nicholas | Plan the documents to deliver and create one shared place for each teammate's AI sessions |
| 14 Nov, 14:41 | Nicholas | Create an assistant skill that reads and saves the shared log at the start, middle and end of each session |
| 14 Nov, 14:45 | Nicholas | Make that skill record important items automatically |
| 14 Nov, 14:54 | Nicholas | Merge both teammates' decisions and ideas into one generated summary |
| 14 Nov, 15:10 | Maria Eliza | Connect to the repository and start reviewing decisions #3–#6 |
| 14 Nov, 15:12 | Maria Eliza | Download MODIS and VIIRS S-NPP from FIRMS for Brazil and build the pipeline, harmonization and calendar |
| 14 Nov, 16:11 | Nicholas | Fix the commit author e-mail so commits show under the right GitHub account |
| 14 Nov, 16:42 | Nicholas | Choose the app stack and build the first version against the data contract |
| 14 Nov, 17:39 | Nicholas | Review the repository against the documentation plan |
| 14 Nov, 18:00 | Nicholas | Review the app (code, numbers, UX) and fix the issues found |
| 14 Nov, 23:03 | Nicholas | Read the submission rules and draft the project page; note new app ideas |
| 14 Nov, 23:31 | Maria Eliza | Check every link used, credit data sources, libraries and frameworks, and add the Space Apps logo (no NASA logos) |
| 15 Nov, 15:15 | Nicholas | Check the project against the Space Apps rules, add the AI marks and translate the remaining Portuguese |
| 15 Nov, 17:33 | Nicholas | Evaluate a fire outlook model; keep it as future work, backed by a first forecast test |
| 15 Nov, 17:32 | Maria Eliza | Review the app design (desktop and mobile) and plan the top-priority improvements, to be approved by Nicholas first |

## Team decisions (summary of `docs/decisions.md`)

| # | Decision | Status |
|---|---|---|
| 1 | Keep each teammate's AI sessions and the decision log inside the repository | proposed |
| 2 | Judge-facing documents in English; internal logs in Portuguese | proposed |
| 3 | Data: MODIS C6.1 + VIIRS S-NPP 375 m; standard archive for the history, near-real-time only after it | confirmed (#18) |
| 4 | Filters: MODIS confidence ≥ 30; VIIRS nominal/high; type = 0 (vegetation); S-NPP only | confirmed (#19) |
| 5 | 0.1° grid; month in America/Sao_Paulo time | confirmed (#20) |
| 6 | Factor k per biome and month, calibrated on 2012–2019; leave-one-year-out validation | confirmed (#21) |
| 7–9 | Team tooling: shared-log skill, automatic recording, generated team summary | proposed |
| 10 | Region: all of Brazil; users pick a state, a biome or draw an area | proposed |
| 11 | Harmonized series: MODIS × k before Feb 2012, observed VIIRS after; 2003–Jan 2012 flagged estimated, Nov 2000–2002 partial | proposed |
| 12, 13, 16 | Split of work: Maria Eliza on the pipeline, Nicholas on the app; data contract in `docs/contrato-dados.md` | confirmed (#16) |
| 14 | App stack: Streamlit + pandas; DuckDB only for the detections CSV | proposed |
| 15, 17 | Detections CSV reads the yearly files with DuckDB, up to 1.5 million points | #17 replaces #15 |
| 22 | Map with OpenStreetMap basemap and the grid as an image; offline fallback | proposed |
| 23 | Reading rules: partial months not compared with normal; same totals in map, calendar and CSV | proposed |
| 24 | References in APA 7 | proposed |
| 27 | No NASA logos; only the Space Apps small logo (no text) in the README and the app | proposed |

"Proposed" means one teammate recorded it and the other had not yet marked it as reviewed in the log; all of them are implemented in the delivered project.
