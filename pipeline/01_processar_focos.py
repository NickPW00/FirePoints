# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1515_nicholas_ingles-e-ia.md
"""
01_processar_focos.py  (step 1: process the fire detections)
---------------------
Reads the .zip files downloaded from NASA FIRMS (MODIS and VIIRS S-NPP)
straight from inside the .zip, without extracting them. The .zip files
(DL_FIRE_*.zip) can be in any subfolder of the project. Writes these light files:

  data/processed/focos_modis.parquet   -> every filtered detection (point)
  data/processed/focos_snpp.parquet
  data/processed/grade_mensal.parquet  -> number of detections per grid cell x month x sensor

Parameters follow the team's decisions (docs/decisions.md):
  #3 MODIS C6.1 + VIIRS S-NPP; SP (archive) for the history, NRT for the recent months
  #4 MODIS confidence >= 30; VIIRS confidence n/h; type = 0
  #5 0.1° grid; month in the America/Sao_Paulo time zone

How to run (in a terminal, from the project folder):
    python 01_processar_focos.py

Requires: pip install -r requirements.txt

Note: variable and column names are in Portuguese (focos = detections, quadradinho = grid cell,
ano/mes = year/month, confianca = confidence). See data/processed/README.md for a glossary.
"""

import fnmatch
import json
import os
import platform
import sys
import time
import zipfile
from pathlib import Path

import ijson
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ----------------------------------------------------------------------
# SETTINGS (can be changed here)
# ----------------------------------------------------------------------
# Project root: the folder above pipeline/ (or the script's own folder, if it sits on its own)
_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PASTA_SAIDA = PASTA / "data" / "processed"


class _Tee:
    """Shows messages on screen and also saves them to log_processamento.txt."""
    def __init__(self, *saidas):
        self.saidas = saidas
    def write(self, texto):
        for s in self.saidas:
            s.write(texto)
            s.flush()
    def flush(self):
        for s in self.saidas:
            s.flush()


_ARQ_LOG = open(PASTA / "log_processamento.txt", "w", encoding="utf-8")
sys.stdout = _Tee(sys.__stdout__, _ARQ_LOG)
sys.stderr = _Tee(sys.__stderr__, _ARQ_LOG)

TAMANHO_QUADRADINHO = 0.1    # degrees (0.1° ≈ 11 km)  -> decision #5
FUSO = "America/Sao_Paulo"   # month counted in Brasília time -> decision #5
CONFIANCA_MIN_MODIS = 30     # MODIS: confidence from 0 to 100; below 30 = "low"
TAMANHO_LOTE = 500_000       # how many detections to process at a time (memory)

# How to recognize the sensor from the .zip name
SENSORES = {
    "SV-C2": "snpp",   # VIIRS Suomi NPP
    "M-C61": "modis",  # MODIS Collection 6.1
}


# ----------------------------------------------------------------------
# READING THE JSON, ONE DETECTION AT A TIME
# ----------------------------------------------------------------------
def ler_registros(abrir):
    """Reads detections one by one, without loading the whole file into memory.
    `abrir` is a function that opens the file from the start (in binary mode).
    Accepts: a list [ {...}, {...} ], one detection per line, or an object with the list inside."""
    with abrir() as f:
        inicio = f.read(65536).lstrip()

    if inicio[:1] == b"[":
        # Format: list of detections
        with abrir() as f:
            yield from ijson.items(f, "item", use_float=True)
        return

    if inicio[:1] == b"{":
        primeira_linha = inicio.split(b"\n", 1)[0].strip().rstrip(b",")
        try:
            json.loads(primeira_linha)
            por_linha = True
        except ValueError:
            por_linha = False

        if por_linha:
            # Format: one detection per line
            with abrir() as f:
                for linha in f:
                    linha = linha.strip().rstrip(b",")
                    if linha.startswith(b"{"):
                        yield json.loads(linha)
            return

        # Format: object with the list of detections inside some field
        with abrir() as f:
            prefixo_lista = None
            for prefixo, evento, _ in ijson.parse(f):
                if evento == "start_array":
                    prefixo_lista = prefixo
                    break
        if prefixo_lista is not None:
            with abrir() as f:
                caminho = f"{prefixo_lista}.item" if prefixo_lista else "item"
                yield from ijson.items(f, caminho, use_float=True)
            return

    raise ValueError("Unrecognized JSON format. Send the first lines of the file for analysis.")


# ----------------------------------------------------------------------
# CLEANING ONE BATCH OF DETECTIONS
# ----------------------------------------------------------------------
def limpar_lote(registros, sensor, origem):
    """Cleans one batch of raw FIRMS records and returns one row per kept detection.

    Input: list of FIRMS records (dicts), sensor ("modis" or "snpp"), origin ("archive" or "nrt").
    Output: DataFrame with latitude, longitude, local date, confidence, FRP (MW),
    day/night flag, sensor, origin and the grid cell indices gi, gj.
    """
    df = pd.DataFrame.from_records(registros)
    df.columns = [c.lower() for c in df.columns]

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    # Date and time come in UTC; we convert them to Brasília time (decision #5)
    hora = (df["acq_time"].astype(str).str.zfill(4) if "acq_time" in df.columns
            else pd.Series("0000", index=df.index))
    utc = pd.to_datetime(df["acq_date"].astype(str) + " " + hora, format="%Y-%m-%d %H%M",
                         errors="coerce", utc=True)
    df["data"] = utc.dt.tz_convert(FUSO).dt.tz_localize(None)
    df = df.dropna(subset=["latitude", "longitude", "data"])

    # 1) Vegetation fires only (type 0). Removes volcanoes (1), static land sources
    #    such as industry and gas flaring (2) and offshore detections (3).
    #    The "nrt" files do not have this column: in those, everything is kept.
    if "type" in df.columns:
        tipo = pd.to_numeric(df["type"], errors="coerce")
        df = df[tipo.isna() | (tipo == 0)]

    # 2) Removes low-confidence detections.
    if sensor == "modis":
        conf = pd.to_numeric(df["confidence"], errors="coerce")
        df = df[conf >= CONFIANCA_MIN_MODIS]
        df["confianca"] = conf[df.index].astype("float32")
    else:
        letra = df["confidence"].astype(str).str.strip().str[0].str.lower()
        df = df[letra.isin(["n", "h"])]          # n = nominal, h = high
        df["confianca"] = letra[df.index].map({"n": 50.0, "h": 90.0}).astype("float32")

    saida = pd.DataFrame({
        "latitude": df["latitude"].astype("float32"),
        "longitude": df["longitude"].astype("float32"),
        "data": df["data"].dt.date,              # local date (Brasília)
        "confianca": df["confianca"],
        "frp": (pd.to_numeric(df["frp"], errors="coerce") if "frp" in df.columns
                else pd.Series(float("nan"), index=df.index)).astype("float32"),
        "dia_noite": (df["daynight"] if "daynight" in df.columns
                      else pd.Series("", index=df.index)).astype(str),
        "sensor": sensor,
        "origem": origem,                        # archive or nrt
    })
    # Grid cell of each detection (integer grid indices)
    saida["gi"] = (saida["latitude"] // TAMANHO_QUADRADINHO).astype("int16")
    saida["gj"] = (saida["longitude"] // TAMANHO_QUADRADINHO).astype("int16")
    return saida.reset_index(drop=True)


# ----------------------------------------------------------------------
# PROCESSES ONE WHOLE .ZIP
# ----------------------------------------------------------------------
def processar_zip(caminho_zip, sensor):
    """Processes one FIRMS .zip: writes focos_<sensor>.parquet and returns the counts
    per sensor x year x month x grid cell (column n_focos)."""
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    arquivo_saida = PASTA_SAIDA / f"focos_{sensor}.parquet"
    escritor = None
    contagens = []
    total_lido = total_mantido = 0
    ultima_data_archive = None

    with zipfile.ZipFile(caminho_zip) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".json")]
        # "archive" first (reviewed history), then "nrt" (recent months)
        nomes.sort(key=lambda n: 0 if "archive" in n.lower() else 1)

        for nome in nomes:
            origem = "archive" if "archive" in nome.lower() else "nrt"
            print(f"\n  Reading {nome} ...")
            t0 = time.time()
            lote = []

            def descarregar(lote):
                nonlocal escritor, total_mantido, ultima_data_archive
                df = limpar_lote(lote, sensor, origem)
                # Avoids duplicate detections: from nrt, only dates after the end of the archive
                if origem == "nrt" and ultima_data_archive is not None:
                    df = df[df["data"] > ultima_data_archive]
                if origem == "archive" and len(df):
                    maior = max(df["data"])
                    if ultima_data_archive is None or maior > ultima_data_archive:
                        ultima_data_archive = maior
                if len(df) == 0:
                    return
                tabela = pa.Table.from_pandas(df, preserve_index=False)
                if escritor is None:
                    escritor = pq.ParquetWriter(arquivo_saida, tabela.schema)
                escritor.write_table(tabela)
                total_mantido += len(df)
                # Count per grid cell x month
                df = df.assign(ano=pd.to_datetime(df["data"]).dt.year.astype("int16"),
                               mes=pd.to_datetime(df["data"]).dt.month.astype("int8"))
                contagens.append(df.groupby(["sensor", "ano", "mes", "gi", "gj"])
                                   .size().rename("n_focos").reset_index())

            for reg in ler_registros(lambda: z.open(nome)):
                lote.append(reg)
                total_lido += 1
                if len(lote) >= TAMANHO_LOTE:
                    descarregar(lote)
                    lote = []
                    print(f"    {total_lido:>12,} detections read | {total_mantido:>12,} kept "
                          f"| {time.time() - t0:,.0f} s".replace(",", "."))
            if lote:
                descarregar(lote)
            print(f"    Done with {nome}: {time.time() - t0:,.0f} s".replace(",", "."))

    if escritor:
        escritor.close()
    lidos = f"{total_lido:,}".replace(",", ".")
    mantidos = f"{total_mantido:,}".replace(",", ".")
    print(f"\n  {sensor.upper()}: {lidos} read, {mantidos} kept -> {arquivo_saida.name}")
    if contagens:
        return (pd.concat(contagens)
                  .groupby(["sensor", "ano", "mes", "gi", "gj"], as_index=False)["n_focos"].sum())
    return pd.DataFrame()


# ----------------------------------------------------------------------
# MAIN PROGRAM
# ----------------------------------------------------------------------
def main():
    print(f"Python {platform.python_version()} | project folder: {PASTA}")
    # Looks for the FIRMS .zip files in any subfolder of the project
    zips = []
    for raiz, _, arquivos in os.walk(PASTA):
        for nome in arquivos:
            if fnmatch.fnmatch(nome.lower(), "dl_fire_*.zip"):
                zips.append(Path(raiz) / nome)
    zips.sort()
    if not zips:
        print(f"ERROR: no DL_FIRE_*.zip file found inside {PASTA}")
        print("Folder contents:", os.listdir(PASTA))
        sys.exit(1)
    print("Files found:")
    for z in zips:
        print(f"  {z.relative_to(PASTA)}")

    grades = []
    for caminho in zips:
        sensor = next((s for chave, s in SENSORES.items() if chave in caminho.name), None)
        if sensor is None:
            print(f"Skipping {caminho.name} (neither MODIS nor S-NPP)")
            continue
        print(f"\n=== {caminho.name} -> {sensor.upper()} ===")
        grades.append(processar_zip(caminho, sensor))

    grades = [g for g in grades if len(g)]
    if not grades:
        print("ERROR: no detection was processed. Check the file log_processamento.txt.")
        sys.exit(1)
    if grades:
        grade = pd.concat(grades, ignore_index=True)
        # Center of each grid cell, to draw on the map
        grade["lat_centro"] = (grade["gi"] + 0.5) * TAMANHO_QUADRADINHO
        grade["lon_centro"] = (grade["gj"] + 0.5) * TAMANHO_QUADRADINHO
        saida = PASTA_SAIDA / "grade_mensal.parquet"
        grade.to_parquet(saida, index=False)
        print(f"\nSummary table saved: {saida}  ({len(grade):,} rows)".replace(",", "."))
        print("\nDone! Next step: python 02_comparar_sensores.py")


if __name__ == "__main__":
    main()
