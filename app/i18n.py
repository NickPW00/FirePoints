# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1732_mariaeliza_design-app.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1815_mariaeliza_mapa-windy.md
"""English / Portuguese text for the FirePoints app (English is the default).

``t("key", **values)`` returns the text in the language chosen in the sidebar
(``st.session_state["lang"]``), with ``values`` filled in. Numbers go through ``num``
so that Portuguese uses 1.234,5 and English 1,234.5.

Biome names: Amazon and Atlantic Forest are the usual English names; Cerrado, Caatinga,
Pantanal and Pampa are used as they are in English. Names translated by the team; source: IBGE.
"""

from __future__ import annotations

LANGS = {"en": "English", "pt": "Português"}
DEFAULT = "en"


def lang() -> str:
    try:
        import streamlit as st
        return st.session_state.get("lang", DEFAULT)
    except Exception:  # outside a Streamlit run (tests, scripts)
        return DEFAULT


def t(key: str, **values) -> str:
    entry = TEXT.get(key)
    if entry is None:
        return key
    text = entry.get(lang()) or entry[DEFAULT]
    return text.format(**values) if values else text


def num(x: float, decimals: int = 0) -> str:
    """1,234.5 (English) or 1.234,5 (Portuguese)."""
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".") if lang() == "pt" else s


def plotly_separators() -> str:
    """Plotly ``separators``: decimal mark then thousands mark."""
    return ",." if lang() == "pt" else ".,"


MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "pt": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
}


def months() -> list[str]:
    return MONTHS[lang()]


def month(m: int) -> str:
    return months()[int(m) - 1]


BIOMES = {"Amazônia": "Amazon", "Mata Atlântica": "Atlantic Forest"}   # others are the same in English


def biome(name: str) -> str:
    """Display name of an IBGE biome (data keeps the IBGE name)."""
    return BIOMES.get(name, name) if lang() == "en" else name


REGIONS = {"Norte": "North", "Nordeste": "Northeast", "Centro-Oeste": "Central-West", "Sudeste": "Southeast",
           "Sul": "South"}


def region(name: str) -> str:
    return REGIONS.get(name, name) if lang() == "en" else name


STATUS = {"observed": ("observed", "observado"), "estimated": ("estimated", "estimado"),
          "partial": ("partial", "parcial")}


def status(s: str) -> str:
    pair = STATUS.get(s)
    return s if pair is None else pair[0 if lang() == "en" else 1]


BAND_WORDS = {"far below": "muito abaixo", "below": "abaixo", "normal": "normal", "above": "acima",
              "far above": "muito acima"}


def band_word(name: str) -> str:
    """Anomaly band name (data.ANOMALY_BANDS) in the current language."""
    return BAND_WORDS.get(name, name) if lang() == "pt" else name


def _(en: str, pt: str) -> dict:
    return {"en": en, "pt": pt}


TEXT = {
    # ---------------------------------------------------------------- page and sidebar
    "page_title": _("FirePoints – Fire calendar", "FirePoints – Calendário de queimadas"),
    "tagline": _("Harmonized MODIS + VIIRS fire calendar for Brazil, 2000–2026",
                 "Calendário harmonizado de queimadas MODIS + VIIRS para o Brasil, 2000–2026"),
    "language": _("Language", "Idioma"),
    "area": _("Area", "Área"),
    "mode_brazil": _("Whole Brazil", "Brasil inteiro"),
    "mode_region": _("Region", "Região"),
    "mode_state": _("State", "Estado"),
    "mode_biome": _("Biome", "Bioma"),
    "mode_draw": _("Draw on map", "Desenhar no mapa"),
    "mode_box": _("Lat/lon box", "Caixa lat/lon"),
    "regions": _("Regions", "Regiões"),
    "states": _("States", "Estados"),
    "biomes": _("Biomes", "Biomas"),
    "none_region": _("No region selected: showing the whole of Brazil.",
                     "Nenhuma região escolhida: mostrando o Brasil inteiro."),
    "none_state": _("No state selected: showing the whole of Brazil.",
                    "Nenhum estado escolhido: mostrando o Brasil inteiro."),
    "none_biome": _("No biome selected: showing the whole of Brazil.",
                    "Nenhum bioma escolhido: mostrando o Brasil inteiro."),
    "lat_min": _("Lat min", "Lat mín"), "lat_max": _("Lat max", "Lat máx"),
    "lon_min": _("Lon min", "Lon mín"), "lon_max": _("Lon max", "Lon máx"),
    "period": _("Period", "Período"),
    "log_scale": _("Log colour scale", "Escala de cor logarítmica"),
    "log_help": _("For the calendar and the map. Fire counts vary by orders of magnitude between seasons and places; "
                  "the log scale keeps both ends visible.",
                  "Para o calendário e o mapa. O número de focos varia muito entre estações e lugares; "
                  "a escala logarítmica mantém visíveis os valores pequenos e os grandes."),
    "data_note": _("Data: NASA FIRMS — MODIS C6.1 (Terra/Aqua) and VIIRS S-NPP 375 m. Biomes and states: IBGE "
                   "(biome names translated by the team). Counts in **VIIRS-equivalent fires**.",
                   "Dados: NASA FIRMS — MODIS C6.1 (Terra/Aqua) e VIIRS S-NPP 375 m. Biomas e estados: IBGE. "
                   "Contagens em **focos equivalentes ao VIIRS**."),
    "made_for": _("Made for the", "Feito para o"),
    "label_brazil": _("Brazil", "Brasil"),
    "label_n_states": _("{n} states", "{n} estados"),
    "label_n_biomes": _("{n} biomes", "{n} biomas"),
    "label_n_regions": _("{n} regions", "{n} regiões"),
    "label_box": _("Lat/lon box", "Caixa lat/lon"),
    "label_drawn": _("Drawn area", "Área desenhada"),
    "title": _("Fire calendar — {area}", "Calendário de queimadas — {area}"),
    "draw_intro": _("Draw a **rectangle** or **polygon** over the area you want to analyse (tools on the left of the map). "
                    "Colour shows where fire is detected, so you can aim at the hot spots. The last shape drawn is used.",
                    "Desenhe um **retângulo** ou um **polígono** sobre a área que quer analisar (ferramentas à esquerda do "
                    "mapa). A cor mostra onde há focos, para mirar nos pontos quentes. Vale a última forma desenhada."),
    "no_shape": _("No shape drawn yet — showing the whole of Brazil.",
                  "Nenhuma forma desenhada ainda — mostrando o Brasil inteiro."),
    "clear_shape": _("Clear shape", "Apagar forma"),
    "no_cells": _("No 0.1° grid cell with fire detections inside this area. Try a larger area.",
                  "Nenhuma célula de 0,1° com focos nesta área. Tente uma área maior."),
    "no_data_period": _("No data in this period.", "Sem dados neste período."),
    "summary": _("{y0}–{y1} · {fires} VIIRS-equivalent fires · {cells} grid cells of 0.1° (≈11 km)",
                 "{y0}–{y1} · {fires} focos equivalentes ao VIIRS · {cells} células de 0,1° (≈11 km)"),
    "fires_unit": _("{n} fires", "{n} focos"),
    "vs_normal_delta": _("{pct}% vs normal", "{pct}% vs normal"),
    "normal_help": _("Normal = mean of the same month(s) in 2003–2025, in the same area.",
                     "Normal = média do(s) mesmo(s) mês(es) em 2003–2025, na mesma área."),
    "partial_help": _(" 2000–2002 are under-counted (MODIS Terra only) and are not compared.",
                      " 2000–2002 estão subcontados (só MODIS Terra) e não são comparados."),
    "m_latest": _("Latest month · {m} {y}", "Último mês · {m} {y}"),
    "m_record": _("Record month in the period", "Mês recorde no período"),
    "m_record_help": _("{n} VIIRS-equivalent fires", "{n} focos equivalentes ao VIIRS"),
    "m_season": _("Typical fire season", "Temporada típica de fogo"),
    "m_season_help": _("These three months hold {share}% of the fires of a typical year (2003–2025). Peak month: {peak}.",
                       "Estes três meses concentram {share}% dos focos de um ano típico (2003–2025). Mês de pico: {peak}."),
    "on_normal": _("on the normal", "dentro do normal"),
    "not_comparable": _("not comparable with the normal", "não comparável com o normal"),
    "above_normal": _("{pct}% above normal", "{pct}% acima do normal"),
    "below_normal": _("{pct}% below normal", "{pct}% abaixo do normal"),
    # ---------------------------------------------------------------- tabs
    "tab_calendar": _("📅 Calendar", "📅 Calendário"),
    "tab_season": _("📈 Season vs normal", "📈 Temporada vs normal"),
    "tab_map": _("🗺️ Map", "🗺️ Mapa"),
    "tab_method": _("🧪 Method & validation", "🧪 Método e validação"),
    "tab_download": _("⬇️ Download", "⬇️ Baixar dados"),
    "tab_about": _("ℹ️ How to read", "ℹ️ Como ler"),
    # ---------------------------------------------------------------- calendar
    "cal_title": _("When does it burn, and how much?", "Quando queima, e quanto?"),
    "colour_by": _("Colour by", "Colorir por"),
    "view_count": _("Fire count", "Número de focos"),
    "view_anomaly": _("Compared to normal", "Comparado ao normal"),
    "view_help": _("Compared to normal: each month vs the mean of the same month in 2003–2025, in the same area.",
                   "Comparado ao normal: cada mês contra a média do mesmo mês em 2003–2025, na mesma área."),
    "cal_count_text": _("Each row is a year, each column a month; **darker = more fires**. The record in this period is "
                        "**{m} {y}** ({n} fires).",
                        "Cada linha é um ano e cada coluna um mês; **mais escuro = mais focos**. O recorde no período é "
                        "**{m} {y}** ({n} focos)."),
    "cal_season_text": _("Fire here concentrates in **{span}** ({share}% of a typical year). ",
                         "Aqui o fogo se concentra em **{span}** ({share}% de um ano típico). "),
    "cal_anom_text": _("**Blue = fewer fires than normal for that month, red = more.** ",
                       "**Azul = menos focos que o normal para aquele mês, vermelho = mais.** "),
    "cal_far": _("{n} month(s) in this period had more than twice the normal; the most recent was **{m} {y}** ({pct}%).",
                 "{n} mês(es) neste período tiveram mais que o dobro do normal; o mais recente foi **{m} {y}** ({pct}%)."),
    "cal_far_none": _("No month in this period had more than twice the normal.",
                      "Nenhum mês neste período teve mais que o dobro do normal."),
    "cal_caption": _("Each square = one month inside the area, in VIIRS-equivalent fire counts. Dotted line: from 2012 on "
                     "the series is observed VIIRS. **\\*** estimated from MODIS × calibration factor (2003–Jan/2012) · "
                     "**†** partial: MODIS Terra only (Nov/2000–2002), under-counted and therefore not compared to normal · "
                     "grey = no data or not compared.",
                     "Cada quadrado = um mês dentro da área, em focos equivalentes ao VIIRS. Linha pontilhada: a partir de "
                     "2012 a série é VIIRS observado. **\\*** estimado a partir do MODIS × fator de calibração "
                     "(2003–jan/2012) · **†** parcial: só MODIS Terra (nov/2000–2002), subcontado e por isso não comparado "
                     "ao normal · cinza = sem dados ou não comparado."),
    # ---------------------------------------------------------------- season
    "season_title": _("Is the fire season normal?", "A temporada de fogo está normal?"),
    "year": _("Year", "Ano"),
    "compare_with": _("Compare with", "Comparar com"),
    "season_partial": _("**{y} ({span}): {n} fires.** This year is under-counted (MODIS Terra only until Jul/2002), so it "
                        "is not compared with the normal.",
                        "**{y} ({span}): {n} focos.** Este ano está subcontado (só MODIS Terra até jul/2002), por isso não "
                        "é comparado com o normal."),
    "season_text": _("**{y} ({span}): {n} fires, {vs}.** {above} of {months} months above the usual range and {below} "
                     "below; the strongest month was {peak} ({peak_n} fires).",
                     "**{y} ({span}): {n} focos, {vs}.** {above} de {months} meses acima da faixa usual e {below} abaixo; "
                     "o mês mais forte foi {peak} ({peak_n} focos)."),
    "season_caption": _("Shaded band: where 8 out of 10 years of 2003–2025 fall in each month (10th–90th percentile); "
                        "dotted line: median. A line above the band is an unusually strong month, below it an unusually "
                        "weak one.",
                        "Faixa sombreada: onde caem 8 de cada 10 anos de 2003–2025 em cada mês (percentis 10–90); linha "
                        "pontilhada: mediana. Uma linha acima da faixa é um mês incomumente forte; abaixo, incomumente fraco."),
    "one_month_title": _("One month across the years", "Um mês ao longo dos anos"),
    "month": _("Month", "Mês"),
    "normal_mean": _("Normal (2003–2025 mean)", "Normal (média 2003–2025)"),
    "compared": _("Compared to normal", "Comparado ao normal"),
    "month_text": _("**{name} was {vs}** ({band}): more fires than in {rank} of the {n} other years of 2003–2025 in the "
                    "same month.",
                    "**{name} ficou {vs}** ({band}): mais focos que em {rank} dos outros {n} anos de 2003–2025 no mesmo mês."),
    "month_partial": _("**{name} is under-counted** (MODIS Terra only), so it is not compared with the normal.",
                       "**{name} está subcontado** (só MODIS Terra), por isso não é comparado com o normal."),
    "bars_caption": _("Each bar is the same calendar month in a different year; dashed line = normal (mean of 2003–2025). "
                      "Orange: selected year · grey: estimated or partial years (MODIS-based).",
                      "Cada barra é o mesmo mês em um ano diferente; linha tracejada = normal (média de 2003–2025). "
                      "Laranja: ano escolhido · cinza: anos estimados ou parciais (a partir do MODIS)."),
    # ---------------------------------------------------------------- map
    "map_title": _("Where does it burn?", "Onde queima?"),
    "show": _("Show", "Mostrar"),
    "any_month": _("Any month", "Qualquer mês"),
    "month_help": _("Restrict the map to one calendar month, e.g. where it burns in September.",
                    "Limita o mapa a um mês do ano, por exemplo onde queima em setembro."),
    "basemap": _("Real basemap (needs internet)", "Mapa de fundo real (precisa de internet)"),
    "basemap_help": _("Pan and zoom over a real map with place names. Turn it off for the built-in map, which works offline.",
                      "Arraste e dê zoom sobre um mapa real com nomes de lugares. Desligue para o mapa embutido, que funciona sem internet."),
    "smooth": _("Smooth colours", "Suavizar cores"),
    "smooth_help": _("Draws the 0.1° cells as a continuous colour field, like a weather map (values are lightly blended "
                     "between neighbouring cells). Turn it off to see each cell as a sharp square with its exact colour.",
                     "Desenha as células de 0,1° como um campo contínuo de cor, como um mapa do tempo (os valores são "
                     "levemente misturados entre células vizinhas). Desligue para ver cada célula como um quadrado "
                     "nítido, com a cor exata."),
    "wheel_off": _("Scroll zoom: off", "Zoom com rolagem: desligado"),
    "wheel_on": _("Scroll zoom: on", "Zoom com rolagem: ligado"),
    "wheel_tip": _("Hold Ctrl and scroll to zoom the map, or turn on scroll zoom",
                   "Segure Ctrl e role para dar zoom no mapa, ou ligue o zoom com rolagem"),
    "cell_read": _("📍 **{state}** · {biome} · cell at {lat}, {lon}{where}: **{fpy} fires per year**{when}, fire in "
                   "**{pct}%** of the years, peak month **{peak}**.",
                   "📍 **{state}** · {biome} · célula em {lat}, {lon}{where}: **{fpy} focos por ano**{when}, fogo em "
                   "**{pct}%** dos anos, mês de pico **{peak}**."),
    "outside_sel": _(" · outside the selected area", " · fora da área escolhida"),
    "in_month": _(" in {m}", " em {m}"),
    "no_fire_cell": _("📍 No fire detected in this cell in the whole record.",
                      "📍 Nenhum foco nesta célula em todo o registro."),
    "play": _("▶ Play the 12 months", "▶ Animar os 12 meses"),
    "stop": _("⏹ Stop", "⏹ Parar"),
    "play_help": _("Shows the fire season moving across the country, month by month.",
                   "Mostra a temporada de fogo se movendo pelo país, mês a mês."),
    "hint_click": _("Click the map to read a cell and drag it to move. To zoom, use + and −, hold Ctrl and scroll, or "
                    "turn on **Scroll zoom** on the map. ",
                    "Clique no mapa para ler uma célula e arraste para mover. Para dar zoom, use + e −, segure Ctrl e "
                    "role, ou ligue o **Zoom com rolagem** no mapa. "),
    "hint_hover": _("Hover to read a cell; scroll to zoom, drag to move. ",
                    "Passe o mouse para ler uma célula; role para dar zoom, arraste para mover. "),
    "hint_grey": _("Plain grey = Brazil without fire detections. ", "Cinza liso = Brasil sem focos. "),
    "map_caption": _("The data are 0.1° grid cells (≈11 km); with *Smooth colours* on, the map blends them into a "
                     "continuous field. State and municipality borders: IBGE 2024. The selected area is in colour; "
                     "the rest of Brazil stays visible in grey.",
                     "Os dados são células de 0,1° (≈11 km); com *Suavizar cores* ligado, o mapa as mistura num "
                     "campo contínuo. Divisas de estados e municípios: IBGE 2024. A área escolhida fica colorida; "
                     "o resto do Brasil continua visível em cinza."),
    "metric_fires": _("Fires per year", "Focos por ano"),
    "metric_pct": _("% of years with fire", "% de anos com fogo"),
    "metric_season": _("Peak season", "Estação de pico"),
    "season_jja": _("Jun–Aug (early dry season)", "Jun–Ago (início da seca)"),
    "season_so": _("Sep–Oct (late dry season)", "Set–Out (fim da seca)"),
    "season_nm": _("Nov–May", "Nov–Mai"),
    "leg_season": _("Season with most fires in each cell", "Estação com mais focos em cada célula"),
    "leg_pct": _("% of years with at least one fire{when}", "% de anos com pelo menos um foco{when}"),
    "leg_fires": _("Fires per year{when} in each 0.1° cell", "Focos por ano{when} em cada célula de 0,1°"),
    "leg_log": _(" (log scale)", " (escala log)"),
    "leg_faded": _("faded = outside the selected area", "esmaecido = fora da área escolhida"),
    "leg_nocolour": _("no colour = no fire detected", "sem cor = nenhum foco detectado"),
    "tk_none": _("No fire was detected in this area{when} in the period.",
                 "Nenhum foco foi detectado nesta área{when} no período."),
    "tk_fires": _("Fire is concentrated: **half of the fires{when} come from {pct}% of the cells** ({n} of {total}). ",
                  "O fogo é concentrado: **metade dos focos{when} vem de {pct}% das células** ({n} de {total}). "),
    "more_fires_brighter": _("Brighter = more fires per year.", "Mais claro = mais focos por ano."),
    "more_fires_darker": _("Darker = more fires per year.", "Mais escuro = mais focos por ano."),
    "more_pct_brighter": _("Brighter = fire comes back more often.", "Mais claro = o fogo volta com mais frequência."),
    "more_pct_darker": _("Darker = fire comes back more often.", "Mais escuro = o fogo volta com mais frequência."),
    "tk_pct": _("**{pct}% of the cells burned{when} in at least half of the {n} years** compared. ",
                "**{pct}% das células queimaram{when} em pelo menos metade dos {n} anos** comparados. "),
    "tk_season": _("**{s1} is the peak season in {p1}% of the cells that burned**; {s2} in {p2}% and {s3} in {p3}%. "
                   "The colour shows when each place burns most, not how much.",
                   "**{s1} é a estação de pico em {p1}% das células que queimaram**; {s2} em {p2}% e {s3} em {p3}%. "
                   "A cor mostra quando cada lugar queima mais, não quanto."),
    "hover_cell": _("lat %{y:.2f}, lon %{x:.2f}<br>%{customdata[0]:,.1f} fires per year<br>fire in %{customdata[1]:.0f}% "
                    "of the years<extra></extra>",
                    "lat %{y:.2f}, lon %{x:.2f}<br>%{customdata[0]:,.1f} focos por ano<br>fogo em %{customdata[1]:.0f}% "
                    "dos anos<extra></extra>"),
    # ---------------------------------------------------------------- method
    "method_title": _("Can two satellites be read as one record?", "Dá para ler dois satélites como um só registro?"),
    "method_body": _("""
**Why harmonize?** MODIS (1 km pixels, since 2000) is being retired; VIIRS (375 m, since 2012) sees
smaller fires and detects **~3–4× more** hot spots. Joining them naively creates a false jump in 2012.

**How.** VIIRS S-NPP is the reference. For each biome and calendar month we compute
k = Σ VIIRS / Σ MODIS over 2012–2019 (before the Terra/Aqua orbital drift) and convert MODIS
2000–2012 into VIIRS-equivalent counts. From Feb/2012 the series is observed VIIRS.
Filters: MODIS confidence ≥ 30, VIIRS confidence nominal/high, vegetation fires only (type 0).
""", """
**Por que harmonizar?** O MODIS (pixels de 1 km, desde 2000) está sendo aposentado; o VIIRS (375 m, desde 2012)
enxerga fogos menores e detecta **~3–4× mais** focos. Juntar os dois sem ajuste cria um salto falso em 2012.

**Como.** O VIIRS S-NPP é a referência. Para cada bioma e mês do ano calculamos
k = Σ VIIRS / Σ MODIS em 2012–2019 (antes da deriva orbital do Terra/Aqua) e convertemos o MODIS de
2000–2012 em focos equivalentes ao VIIRS. A partir de fev/2012 a série é VIIRS observado.
Filtros: confiança MODIS ≥ 30, confiança VIIRS nominal/alta, só fogo em vegetação (type 0).
"""),
    "method_gap": _("**In this area, MODIS × k (orange) stays within {gap}% of the observed VIIRS (blue), year by year, "
                    "across the calibration window 2012–2019.** Grey is MODIS before the conversion; the independent check "
                    "(leaving each year out) is in the table below.",
                    "**Nesta área, o MODIS × k (laranja) fica a até {gap}% do VIIRS observado (azul), ano a ano, na janela "
                    "de calibração 2012–2019.** Cinza é o MODIS antes da conversão; o teste independente (deixando cada "
                    "ano de fora) está na tabela abaixo."),
    "method_caption": _("Selected area, whole record. In 2012–2019 MODIS × k should track observed VIIRS (calibration); the "
                        "growing gap in recent years reflects the Terra/Aqua orbital drift — one reason to use VIIRS as the "
                        "reference.",
                        "Área escolhida, registro completo. Em 2012–2019 o MODIS × k deve acompanhar o VIIRS observado "
                        "(calibração); a diferença crescente nos anos recentes reflete a deriva orbital do Terra/Aqua — um "
                        "dos motivos para usar o VIIRS como referência."),
    "factor_title": _("**Calibration factor k by biome and month** (darker = VIIRS sees more fires per MODIS fire)",
                      "**Fator de calibração k por bioma e mês** (mais escuro = o VIIRS vê mais focos por foco do MODIS)"),
    "validation_title": _("**Validation (leave-one-year-out, 2012–2019)**",
                          "**Validação (deixando um ano de fora, 2012–2019)**"),
    "col_biome": _("Biome", "Bioma"),
    "col_viirs_year": _("VIIRS fires / year", "Focos VIIRS / ano"),
    "col_error": _("Mean abs. error (%)", "Erro médio abs. (%)"),
    # ---------------------------------------------------------------- download
    "dl_title": _("Take the data with you", "Leve os dados com você"),
    "dl_smaller": _("Choose a state or a biome, or shorten the period in the sidebar.",
                    "Escolha um estado ou bioma, ou encurte o período na barra lateral."),
    "dl_monthly": _("**Monthly counts for the selected area**", "**Contagens mensais da área escolhida**"),
    "dl_monthly_btn": _("Download monthly CSV ({n} rows)", "Baixar CSV mensal ({n} linhas)"),
    "dl_cells": _("**Counts per grid cell and month**", "**Contagens por célula e mês**"),
    "dl_cells_btn": _("Download per-cell CSV ({n} rows)", "Baixar CSV por célula ({n} linhas)"),
    "dl_too_many": _("{n} rows are too many for one file (limit 1,000,000). {tip}",
                     "{n} linhas são demais para um arquivo (limite 1.000.000). {tip}"),
    "dl_points": _("**Individual fire detections** (raw MODIS and VIIRS points, *not* harmonized)",
                   "**Focos individuais** (pontos brutos do MODIS e do VIIRS, *não* harmonizados)"),
    "dl_points_too_many": _("{n} detections are too many for one file (limit 1,500,000). {tip}",
                            "{n} focos são demais para um arquivo (limite 1.500.000). {tip}"),
    "dl_points_btn": _("Download fire points CSV ({n} detections)", "Baixar CSV de focos ({n} focos)"),
    "dl_points_until": _("Detections up to {m}, the last month of the harmonized series.",
                         "Focos até {m}, o último mês da série harmonizada."),
    "dl_points_none": _("No detection in this area and period.", "Nenhum foco nesta área e período."),
    "dl_points_missing": _("Individual detections are not bundled in this deployment. They can be downloaded from "
                           "[NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/download/).",
                           "Os focos individuais não estão nesta versão. Eles podem ser baixados no "
                           "[NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/download/)."),
    # ---------------------------------------------------------------- footer
    "footer": _("Built by the FirePoints team for the NASA Space Apps Challenge 2026, with AI assistance (Claude, "
                "Anthropic): [how we used AI](https://github.com/NickPW00/FirePoints/blob/main/docs/AI_USE.md). "
                "Basemap © Esri, HERE, Garmin, © OpenStreetMap contributors. Borders: IBGE.",
                "Feito pela equipe FirePoints para o NASA Space Apps Challenge 2026, com ajuda de IA (Claude, "
                "Anthropic): [como usamos IA](https://github.com/NickPW00/FirePoints/blob/main/docs/AI_USE.md). "
                "Mapa de fundo © Esri, HERE, Garmin, © colaboradores do OpenStreetMap. Divisas: IBGE."),
    # ---------------------------------------------------------------- charts
    "c_no_data": _("No data", "Sem dados"),
    "c_fires_eq": _("{n} fires (VIIRS-eq.)", "{n} focos (equiv. VIIRS)"),
    "c_partial_hover": _("partial: MODIS Terra only, under-counted<br>not compared with the normal",
                         "parcial: só MODIS Terra, subcontado<br>não comparado com o normal"),
    "c_vs_mean": _("{pct}% vs 2003–2025 mean", "{pct}% vs média 2003–2025"),
    "c_vs_normal": _("vs normal", "vs normal"),
    "c_fires": _("Fires", "Focos"),
    "c_band1": _("far below (<0.5×)", "muito abaixo (<0,5×)"),
    "c_band2": _("below (0.5–0.8×)", "abaixo (0,5–0,8×)"),
    "c_band3": _("normal (0.8–1.25×)", "normal (0,8–1,25×)"),
    "c_band4": _("above (1.25–2×)", "acima (1,25–2×)"),
    "c_band5": _("far above (>2×)", "muito acima (>2×)"),
    "c_usual": _("usual range (10th–90th percentile, 2003–2025)", "faixa usual (percentis 10–90, 2003–2025)"),
    "c_median": _("median", "mediana"),
    "c_fires_month": _("Fires per month (VIIRS-eq.)", "Focos por mês (equiv. VIIRS)"),
    "c_fires_eq_axis": _("Fires (VIIRS-eq.)", "Focos (equiv. VIIRS)"),
    "c_mean_label": _("2003–2025 mean: {n}", "média 2003–2025: {n}"),
    "c_fires_hover": _("fires", "focos"),
    "c_modis_raw": _("MODIS (raw)", "MODIS (bruto)"),
    "c_modis_adj": _("MODIS × k (harmonized)", "MODIS × k (harmonizado)"),
    "c_viirs": _("VIIRS S-NPP (observed)", "VIIRS S-NPP (observado)"),
    "c_calibration": _("calibration 2012–2019", "calibração 2012–2019"),
    "c_fires_year": _("Fires per year", "Focos por ano"),
    # ---------------------------------------------------------------- how to read
    "about": _("""
**Choose an area** in the sidebar: the whole country, one or more regions, states or biomes, a lat/lon box, or a shape
drawn on the map. Cells are included when their centre falls inside the area.

**Headline numbers.** The latest month and the latest year of the period, each against its *normal*: the mean of the
same month(s) in 2003–2025, in the same area. Red arrow = more fire than normal.

**Calendar.** Rows are years, columns are months. Colour = number of fires (light = few, dark = many; log scale by default).
Grey = no data (before Nov/2000 or after the last processed month). Marks next to the year:
\\* estimated from MODIS, † partial (Terra only). The dotted line marks 2012, when observed VIIRS takes over.

**Season.** One year against the usual range of each month (the band where 8 out of 10 years of 2003–2025 fall).
Below it, one calendar month across all years.

**Unit.** *VIIRS-equivalent fires*: the number of hot spots VIIRS S-NPP would have detected.
Before 2012 this is MODIS × k (see *Method*).

**Compared to normal / anomaly.** Each month vs the mean of the same calendar month in 2003–2025 (complete years),
in the same area. Bands: far below (<0.5×), below (0.5–0.8×), normal (0.8–1.25×), above (1.25–2×), far above (>2×).
Nov/2000–2002 are not compared: only MODIS Terra was flying, so those months are under-counted.

**Map.** Each pixel is a 0.1° cell (≈11 km), over a real map you can pan and zoom (+/−, Ctrl + scroll, or the *Scroll zoom* button).
Place names sit on top of the colours. Three readings: *fires per year* (how much it burns), *% of years with fire*
(how often fire comes back: share of the years with at least one detection in that cell, in the chosen month) and
*peak season* (when it burns most). The selected area is in colour and outlined, with its municipalities; the rest of
Brazil stays visible in grey. Click a cell to read its numbers.

**Limitations.** A hot spot is not burned area; clouds hide fires; the factor assumes a stable MODIS/VIIRS relation
per biome and month; the most recent months may still be near-real-time (provisional) data.
""", """
**Escolha uma área** na barra lateral: o país inteiro, uma ou mais regiões, estados ou biomas, uma caixa lat/lon ou uma
forma desenhada no mapa. Entram as células cujo centro cai dentro da área.

**Números do topo.** O último mês e o último ano do período, cada um comparado com o seu *normal*: a média do(s)
mesmo(s) mês(es) em 2003–2025, na mesma área. Seta vermelha = mais fogo que o normal.

**Calendário.** Linhas são anos e colunas são meses. Cor = número de focos (claro = poucos, escuro = muitos; escala log
por padrão). Cinza = sem dados (antes de nov/2000 ou depois do último mês processado). Marcas ao lado do ano:
\\* estimado a partir do MODIS, † parcial (só Terra). A linha pontilhada marca 2012, quando entra o VIIRS observado.

**Temporada.** Um ano contra a faixa usual de cada mês (onde caem 8 de cada 10 anos de 2003–2025).
Abaixo, um mês do ano ao longo de todos os anos.

**Unidade.** *Focos equivalentes ao VIIRS*: o número de focos que o VIIRS S-NPP teria detectado.
Antes de 2012 é MODIS × k (veja *Método*).

**Comparado ao normal / anomalia.** Cada mês contra a média do mesmo mês em 2003–2025 (anos completos), na mesma área.
Faixas: muito abaixo (<0,5×), abaixo (0,5–0,8×), normal (0,8–1,25×), acima (1,25–2×), muito acima (>2×).
Nov/2000–2002 não são comparados: só o MODIS Terra voava, então esses meses estão subcontados.

**Mapa.** Cada pixel é uma célula de 0,1° (≈11 km), sobre um mapa real que dá para arrastar e dar zoom (+/−, Ctrl + rolagem
ou o botão *Zoom com rolagem*). Os nomes dos lugares ficam por cima das cores. Três leituras: *focos por ano* (quanto queima), *% de anos
com fogo* (com que frequência o fogo volta: fração dos anos com pelo menos um foco naquela célula, no mês escolhido) e
*estação de pico* (quando queima mais). A área escolhida fica colorida e contornada, com seus municípios; o resto do
Brasil continua visível em cinza. Clique numa célula para ler os números dela.

**Limitações.** Foco de calor não é área queimada; nuvens escondem fogos; o fator supõe uma relação MODIS/VIIRS estável
por bioma e mês; os meses mais recentes podem ainda ser dados quase em tempo real (provisórios).
"""),
}
