# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1733_nicholas_previsao-futuro.md
"""
06_teste_previsao.py  (step 6, optional: first outlook test — future work)
--------------------
Asks a simple question: how much of the next 1–12 months can be predicted from the
harmonized record alone? It does NOT feed the app; it only backs the "Future work"
section of docs/METHODOLOGY.md.

Two baselines, issued at the end of every month from Jan 2016 to Oct 2025
(rolling origin: each forecast only uses data up to its issue month):

  climatology   mean of the same calendar month, 2003 up to the issue month
  + anomaly     climatology x (last 3 months observed / their climatology) ^ exp(-h/3),
                i.e. the recent anomaly fades back to normal as the horizon h grows

Error: weighted absolute percentage error = sum(|forecast - observed|) / sum(observed),
per horizon band (1–3, 4–6, 7–12 months ahead), for Brazil and for the 6 biomes.

Input:  data/processed/calendario.parquet (written by 04_calendario.py)
Output: data/processed/teste_previsao.csv
How to run:  python pipeline/06_teste_previsao.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PROCESSADOS = PASTA / "data" / "processed"

INICIO_CLIMA = 2003              # first full year with Terra + Aqua
ORIGENS = ("2016-01", "2025-10")  # issue months tested
MESES_ANOMALIA = 3               # recent window used for the anomaly
DECAIMENTO = 3.0                 # months for the anomaly to fade by a factor e
FAIXAS = {"1–3": (1, 3), "4–6": (4, 6), "7–12": (7, 12)}


def previsoes(serie):
    """Rolling-origin forecasts for one region. `serie` is indexed by monthly Period."""
    linhas = []
    for origem in pd.period_range(*ORIGENS, freq="M"):
        hist = serie[(serie.index <= origem) & (serie.index.year >= INICIO_CLIMA)]
        clima = hist.groupby(hist.index.month).mean()
        recentes = hist.iloc[-MESES_ANOMALIA:]
        anomalia = recentes.sum() / clima.loc[recentes.index.month].sum()
        for h in range(1, 13):
            alvo = origem + h
            if alvo not in serie.index:
                continue
            normal = clima.loc[alvo.month]
            linhas.append({"origem": str(origem), "h": h, "observado": serie[alvo],
                           "climatologia": normal,
                           "anomalia": normal * anomalia ** np.exp(-h / DECAIMENTO)})
    return pd.DataFrame(linhas)


def erro(df, coluna):
    """Weighted absolute percentage error (%)."""
    return abs(df[coluna] - df["observado"]).sum() / df["observado"].sum() * 100


def main():
    cal = pd.read_parquet(PROCESSADOS / "calendario.parquet")
    cal = cal[cal["regiao_tipo"].isin(["brasil", "bioma"])]
    resultados = []
    for (tipo, regiao), g in cal.groupby(["regiao_tipo", "regiao"]):
        serie = g.set_index(pd.PeriodIndex.from_fields(year=g["ano"], month=g["mes"], freq="M"))["focos"].sort_index()
        p = previsoes(serie)
        for faixa, (h0, h1) in FAIXAS.items():
            d = p[p["h"].between(h0, h1)]
            resultados.append({"regiao": regiao, "horizonte_meses": faixa, "n_previsoes": len(d),
                               "erro_climatologia_pct": round(float(erro(d, "climatologia")), 1),
                               "erro_com_anomalia_pct": round(float(erro(d, "anomalia")), 1)})
    res = pd.DataFrame(resultados)
    res.to_csv(PROCESSADOS / "teste_previsao.csv", index=False)

    print("Outlook test, forecasts issued monthly Jan 2016 – Oct 2025")
    print("Weighted absolute % error (lower is better):\n")
    print(res.to_string(index=False))
    print(f"\nSaved to {PROCESSADOS / 'teste_previsao.csv'}")


if __name__ == "__main__":
    main()
