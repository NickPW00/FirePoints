# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
"""
03_harmonizar.py
----------------
Junta MODIS e VIIRS S-NPP numa série única de focos, na escala do VIIRS
(decisões #6 e #11 em docs/decisions.md):

  1. Descobre o bioma de cada quadradinho de 0,1° (contorno de biomas do IBGE).
  2. Calcula o fator k[bioma, mês] = focos S-NPP ÷ focos MODIS em 2012–2019.
  3. Valida deixando um ano de fora (2012–2019) e salva o erro por bioma.
  4. Monta a série harmonizada:
       nov/2000–dez/2002  MODIS × k   -> "parcial"   (só o Terra até 07/2002)
       2003–jan/2012      MODIS × k   -> "estimado"
       fev/2012 em diante VIIRS S-NPP -> "observado" (o S-NPP começa em 20/01/2012)

Entrada:
  data/processed/grade_mensal.parquet        (gerado pelo 01_processar_focos.py)
  contorno de biomas do IBGE em qualquer subpasta do projeto
  (ex.: Biomas_250mil.zip, sem precisar extrair)

Saída (data/processed/):
  serie_harmonizada.parquet   quadradinho × mês: focos na escala VIIRS + status
  fatores_bioma_mes.csv       o fator k de cada bioma e mês
  validacao_harmonizacao.csv  erro da validação por bioma

Como rodar:  python 03_harmonizar.py
"""

import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PROCESSADOS = PASTA / "data" / "processed"

TAMANHO_QUADRADINHO = 0.1
CALIBRACAO = ("2012-02", "2019-12")   # decisão #6 (fev/2012: 1º mês completo do S-NPP)
INICIO_VIIRS = "2012-02"               # a partir daqui a série usa o S-NPP observado
FIM_TERRA_SO = "2002-12"               # até aqui: "parcial" (Aqua só começa em 04/07/2002)
ULTIMO_MES = "2026-10"                 # último mês completo do S-NPP
MIN_FOCOS_MODIS = 300                  # abaixo disso, o fator do bioma no mês usa o fator nacional


def achar_biomas():
    """Procura o contorno de biomas (zip, shp, gpkg ou geojson) dentro do projeto."""
    candidatos = []
    for raiz, _, arquivos in os.walk(PASTA):
        for nome in arquivos:
            n = nome.lower()
            if "bioma" in n and n.endswith((".zip", ".shp", ".gpkg", ".geojson", ".json")):
                candidatos.append(Path(raiz) / nome)
    if not candidatos:
        print("ERRO: não achei o contorno de biomas do IBGE dentro de", PASTA)
        print("Baixe o Biomas_250mil.zip do IBGE e coloque na pasta do projeto.")
        sys.exit(1)
    # Prefere .shp/.gpkg extraídos; senão, lê direto do .zip
    candidatos.sort(key=lambda p: p.suffix.lower() == ".zip")
    arq = candidatos[0]
    print(f"Contorno de biomas: {arq.relative_to(PASTA)}")
    biomas = gpd.read_file(arq)
    texto = [c for c in biomas.columns
             if c != "geometry" and not pd.api.types.is_numeric_dtype(biomas[c])]
    col = next((c for c in texto if "bioma" in c.lower()), None) or texto[0]
    biomas = biomas[[col, "geometry"]].rename(columns={col: "bioma"}).to_crs("EPSG:4326")
    # Deixa só os biomas terrestres (o IBGE inclui o Sistema Costeiro-Marinho em algumas versões)
    biomas = biomas[~biomas["bioma"].str.contains("Costeiro|Marinho", case=False, na=False)]
    print("Biomas:", ", ".join(sorted(biomas["bioma"].unique())))
    return biomas


def bioma_por_quadradinho(grade, biomas):
    cel = grade[["gi", "gj"]].drop_duplicates().copy()
    cel["lat"] = (cel["gi"] + 0.5) * TAMANHO_QUADRADINHO
    cel["lon"] = (cel["gj"] + 0.5) * TAMANHO_QUADRADINHO
    pts = gpd.GeoDataFrame(cel, geometry=gpd.points_from_xy(cel["lon"], cel["lat"]), crs="EPSG:4326")
    dentro = gpd.sjoin(pts, biomas, how="left", predicate="within")
    dentro = dentro[~dentro.index.duplicated()]
    fora = dentro["bioma"].isna()
    if fora.any():
        # Quadradinhos com centro no mar ou na fronteira: usa o bioma mais próximo
        perto = gpd.sjoin_nearest(pts[fora].to_crs("EPSG:5880"), biomas.to_crs("EPSG:5880"), how="left")
        perto = perto[~perto.index.duplicated()]
        dentro.loc[fora, "bioma"] = perto["bioma"]
    return dentro[["gi", "gj", "bioma"]]


def mes_ref(df):
    return pd.PeriodIndex.from_fields(year=df["ano"], month=df["mes"], freq="M")


def main():
    grade = pd.read_parquet(PROCESSADOS / "grade_mensal.parquet")
    biomas = achar_biomas()
    mapa = bioma_por_quadradinho(grade, biomas)
    grade = grade.merge(mapa, on=["gi", "gj"], how="left")
    grade["periodo"] = mes_ref(grade)

    # Tabela larga: uma linha por quadradinho × mês, com MODIS e S-NPP lado a lado
    larga = (grade.pivot_table(index=["gi", "gj", "bioma", "ano", "mes", "periodo"],
                               columns="sensor", values="n_focos", aggfunc="sum", fill_value=0)
                  .reset_index())
    for s in ("modis", "snpp"):
        if s not in larga.columns:
            larga[s] = 0

    ini, fim = pd.Period(CALIBRACAO[0], "M"), pd.Period(CALIBRACAO[1], "M")
    cal = larga[(larga["periodo"] >= ini) & (larga["periodo"] <= fim)]

    # ---------- Fator k[bioma, mês] ----------
    def fatores(dados):
        nac = dados.groupby("mes")[["snpp", "modis"]].sum()
        k_nac = nac["snpp"] / nac["modis"]
        bm = dados.groupby(["bioma", "mes"])[["snpp", "modis"]].sum()
        k = bm["snpp"] / bm["modis"]
        pouco = bm["modis"] < MIN_FOCOS_MODIS
        k[pouco] = k_nac.reindex(bm.index.get_level_values("mes"))[pouco.values].values
        return k.rename("k"), k_nac

    k, k_nac = fatores(cal)

    # ---------- Validação: deixa um ano de fora ----------
    linhas = []
    for ano in range(ini.year, fim.year + 1):
        treino, teste = cal[cal["ano"] != ano], cal[cal["ano"] == ano]
        k_t, _ = fatores(treino)
        t = teste.groupby(["bioma", "mes"])[["snpp", "modis"]].sum().join(k_t)
        t["prev"] = t["modis"] * t["k"]
        por_bioma = t.groupby("bioma")[["snpp", "prev"]].sum()
        por_bioma["ano"] = ano
        linhas.append(por_bioma.reset_index())
    val = pd.concat(linhas)
    val = val[val["snpp"] > 0]
    val["erro_%"] = (val["prev"] / val["snpp"] - 1) * 100
    resumo = (val.groupby("bioma")
                 .agg(focos_snpp_ano=("snpp", "mean"), erro_medio_abs_pct=("erro_%", lambda e: e.abs().mean()))
                 .round(1).sort_values("focos_snpp_ano", ascending=False))
    total = val.groupby("ano")[["snpp", "prev"]].sum()
    erro_br = ((total["prev"] / total["snpp"] - 1).abs().mean() * 100)

    # ---------- Série harmonizada ----------
    larga = larga.merge(k.reset_index(), on=["bioma", "mes"], how="left")
    larga["k"] = larga["k"].fillna(larga["mes"].map(k_nac))
    viirs = larga["periodo"] >= pd.Period(INICIO_VIIRS, "M")
    larga["focos"] = np.where(viirs, larga["snpp"], larga["modis"] * larga["k"]).astype("float32")
    larga["status"] = np.select(
        [viirs, larga["periodo"] <= pd.Period(FIM_TERRA_SO, "M")],
        ["observado", "parcial"], default="estimado")
    larga = larga[larga["periodo"] <= pd.Period(ULTIMO_MES, "M")]
    larga["lat_centro"] = ((larga["gi"] + 0.5) * TAMANHO_QUADRADINHO).round(2)
    larga["lon_centro"] = ((larga["gj"] + 0.5) * TAMANHO_QUADRADINHO).round(2)
    saida = larga[["gi", "gj", "lat_centro", "lon_centro", "bioma", "ano", "mes",
                   "focos", "status", "modis", "snpp"]]
    saida = saida[(saida["focos"] > 0) | (saida["modis"] > 0) | (saida["snpp"] > 0)]

    saida.to_parquet(PROCESSADOS / "serie_harmonizada.parquet", index=False)
    k.reset_index().pivot(index="bioma", columns="mes", values="k").round(3) \
        .to_csv(PROCESSADOS / "fatores_bioma_mes.csv")
    resumo.to_csv(PROCESSADOS / "validacao_harmonizacao.csv")

    # ---------- Resumo na tela ----------
    print("\nFator k (S-NPP ÷ MODIS) por bioma — média dos 12 meses:")
    print(k.groupby("bioma").mean().round(2).sort_values().to_string())
    print(f"\nValidação 2012–2019 (deixando um ano de fora): erro anual médio no Brasil = {erro_br:.1f}%")
    print("Erro anual médio por bioma (%):")
    print(resumo.to_string())
    anual = saida.groupby(["ano"]).agg(focos=("focos", "sum"), status=("status", "last"))
    anual["focos"] = (anual["focos"] / 1000).round(0)
    print("\nSérie harmonizada (mil focos por ano, escala VIIRS):")
    print(anual.to_string())
    print(f"\nSalvo em {PROCESSADOS / 'serie_harmonizada.parquet'}")
    print("Pronto!")


if __name__ == "__main__":
    main()
