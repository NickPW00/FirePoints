<!-- AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1931_nicholas_demo-slides.md -->
# FirePoints demo (7 slides)

**[`FirePoints-demo.pdf`](FirePoints-demo.pdf)** is the project demo for the NASA Space Apps Challenge 2026: seven slides in English.

| Slide | Content | Where it comes from |
|---|---|---|
| 1 | Project, team, creators and challenge | [`README.md`](../../README.md) |
| 2 | The problem; chart of yearly detections, MODIS vs VIIRS S-NPP, 2003–2025 | Yearly sums of `data/processed/serie_harmonizada.parquet` |
| 3 | The method; table of the factor k per biome and month | `data/processed/fatores_bioma_mes.csv`, [`docs/METHODOLOGY.md`](../METHODOLOGY.md) |
| 4 | Validation; observed vs predicted detections per year, 2012–2019 | Leave-one-year-out test of `pipeline/03_harmonizar.py`, recomputed from `serie_harmonizada.parquet` |
| 5 | The app: Calendar and Season vs normal tabs | Screenshots of the app at commit `0f559ae`, whole of Brazil |
| 6 | The app: Map tab | Screenshot of the live app (<https://firepoints.streamlit.app>), 15 Nov 2026 |
| 7 | Who it is for, next step, links, credits | [`README.md`](../../README.md), METHODOLOGY § 8 |

**AI use.** The slides (text, layout and the two charts drawn from our processed data) were made with the help of Claude (Anthropic); every number was checked against the documents above. The app screenshots are real screens, not generated. No image, video or audio model was used, and no NASA branding: the only logo is the official Space Apps small logo, unaltered. Colours and typefaces follow the Space Apps Brand Guidelines. See [`docs/AI_USE.md`](../AI_USE.md).
