# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-14_1512_mariaeliza_pipeline-focos.md
"""
01_processar_focos.py
---------------------
Lê os arquivos .zip baixados do NASA FIRMS (MODIS e VIIRS S-NPP),
direto de dentro do .zip, sem extrair. Os .zip (DL_FIRE_*.zip) podem estar
em qualquer subpasta do projeto. Gera estes arquivos leves:

  data/processed/focos_modis.parquet   -> cada foco (ponto) filtrado
  data/processed/focos_snpp.parquet
  data/processed/grade_mensal.parquet  -> nº de focos por quadradinho x mês x sensor

Parâmetros seguindo as propostas da dupla (docs/decisions.md):
  #3 MODIS C6.1 + VIIRS S-NPP; SP (archive) no histórico, NRT nos meses recentes
  #4 MODIS confidence >= 30; VIIRS confidence n/h; type = 0
  #5 grade de 0,1°; mês no fuso America/Sao_Paulo

Como rodar (no terminal, dentro da pasta space-apps):
    python 01_processar_focos.py

Precisa de: pip install -r requirements.txt
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
# CONFIGURAÇÕES (pode mudar aqui)
# ----------------------------------------------------------------------
# Raiz do projeto: a pasta acima de pipeline/ (ou a própria pasta do script, se ele estiver solto)
_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
PASTA_SAIDA = PASTA / "data" / "processed"


class _Tee:
    """Mostra as mensagens na tela e também salva em log_processamento.txt."""
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

TAMANHO_QUADRADINHO = 0.1    # graus (0,1° ≈ 11 km)  -> decisão #5
FUSO = "America/Sao_Paulo"   # mês contado no horário de Brasília -> decisão #5
CONFIANCA_MIN_MODIS = 30     # MODIS: confiança de 0 a 100; abaixo de 30 = "baixa"
TAMANHO_LOTE = 500_000       # quantos focos processar por vez (memória)

# Como reconhecer o sensor pelo nome do .zip
SENSORES = {
    "SV-C2": "snpp",   # VIIRS Suomi NPP
    "M-C61": "modis",  # MODIS Collection 6.1
}


# ----------------------------------------------------------------------
# LEITURA DO JSON, UM FOCO POR VEZ
# ----------------------------------------------------------------------
def ler_registros(abrir):
    """Lê focos um a um, sem carregar o arquivo inteiro na memória.
    `abrir` é uma função que abre o arquivo do começo (em modo binário).
    Aceita: lista [ {...}, {...} ], um foco por linha, ou um objeto com a lista dentro."""
    with abrir() as f:
        inicio = f.read(65536).lstrip()

    if inicio[:1] == b"[":
        # Formato: lista de focos
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
            # Formato: um foco por linha
            with abrir() as f:
                for linha in f:
                    linha = linha.strip().rstrip(b",")
                    if linha.startswith(b"{"):
                        yield json.loads(linha)
            return

        # Formato: objeto com a lista de focos dentro de algum campo
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

    raise ValueError("Formato de JSON não reconhecido. Mande as primeiras linhas do arquivo para análise.")


# ----------------------------------------------------------------------
# LIMPEZA DE UM LOTE DE FOCOS
# ----------------------------------------------------------------------
def limpar_lote(registros, sensor, origem):
    df = pd.DataFrame.from_records(registros)
    df.columns = [c.lower() for c in df.columns]

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    # Data e hora vêm em UTC; convertemos para o horário de Brasília (decisão #5)
    hora = (df["acq_time"].astype(str).str.zfill(4) if "acq_time" in df.columns
            else pd.Series("0000", index=df.index))
    utc = pd.to_datetime(df["acq_date"].astype(str) + " " + hora, format="%Y-%m-%d %H%M",
                         errors="coerce", utc=True)
    df["data"] = utc.dt.tz_convert(FUSO).dt.tz_localize(None)
    df = df.dropna(subset=["latitude", "longitude", "data"])

    # 1) Só queimada em vegetação (type 0). Tira vulcões (1), fontes fixas
    #    como indústrias e queima de gás (2) e focos no mar (3).
    #    Os arquivos "nrt" não têm essa coluna: nesses, mantém tudo.
    if "type" in df.columns:
        tipo = pd.to_numeric(df["type"], errors="coerce")
        df = df[tipo.isna() | (tipo == 0)]

    # 2) Tira detecções de baixa confiança.
    if sensor == "modis":
        conf = pd.to_numeric(df["confidence"], errors="coerce")
        df = df[conf >= CONFIANCA_MIN_MODIS]
        df["confianca"] = conf[df.index].astype("float32")
    else:
        letra = df["confidence"].astype(str).str.strip().str[0].str.lower()
        df = df[letra.isin(["n", "h"])]          # n = nominal, h = alta
        df["confianca"] = letra[df.index].map({"n": 50.0, "h": 90.0}).astype("float32")

    saida = pd.DataFrame({
        "latitude": df["latitude"].astype("float32"),
        "longitude": df["longitude"].astype("float32"),
        "data": df["data"].dt.date,              # data local (Brasília)
        "confianca": df["confianca"],
        "frp": (pd.to_numeric(df["frp"], errors="coerce") if "frp" in df.columns
                else pd.Series(float("nan"), index=df.index)).astype("float32"),
        "dia_noite": (df["daynight"] if "daynight" in df.columns
                      else pd.Series("", index=df.index)).astype(str),
        "sensor": sensor,
        "origem": origem,                        # archive ou nrt
    })
    # Quadradinho de cada foco (índices inteiros da grade)
    saida["gi"] = (saida["latitude"] // TAMANHO_QUADRADINHO).astype("int16")
    saida["gj"] = (saida["longitude"] // TAMANHO_QUADRADINHO).astype("int16")
    return saida.reset_index(drop=True)


# ----------------------------------------------------------------------
# PROCESSA UM .ZIP INTEIRO
# ----------------------------------------------------------------------
def processar_zip(caminho_zip, sensor):
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    arquivo_saida = PASTA_SAIDA / f"focos_{sensor}.parquet"
    escritor = None
    contagens = []
    total_lido = total_mantido = 0
    ultima_data_archive = None

    with zipfile.ZipFile(caminho_zip) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".json")]
        # "archive" primeiro (histórico revisado), depois "nrt" (meses recentes)
        nomes.sort(key=lambda n: 0 if "archive" in n.lower() else 1)

        for nome in nomes:
            origem = "archive" if "archive" in nome.lower() else "nrt"
            print(f"\n  Lendo {nome} ...")
            t0 = time.time()
            lote = []

            def descarregar(lote):
                nonlocal escritor, total_mantido, ultima_data_archive
                df = limpar_lote(lote, sensor, origem)
                # Evita focos repetidos: do nrt, só entram datas depois do fim do archive
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
                # Contagem por quadradinho x mês
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
                    print(f"    {total_lido:>12,} focos lidos | {total_mantido:>12,} mantidos "
                          f"| {time.time() - t0:,.0f} s".replace(",", "."))
            if lote:
                descarregar(lote)
            print(f"    Fim de {nome}: {time.time() - t0:,.0f} s".replace(",", "."))

    if escritor:
        escritor.close()
    lidos = f"{total_lido:,}".replace(",", ".")
    mantidos = f"{total_mantido:,}".replace(",", ".")
    print(f"\n  {sensor.upper()}: {lidos} lidos, {mantidos} mantidos -> {arquivo_saida.name}")
    if contagens:
        return (pd.concat(contagens)
                  .groupby(["sensor", "ano", "mes", "gi", "gj"], as_index=False)["n_focos"].sum())
    return pd.DataFrame()


# ----------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ----------------------------------------------------------------------
def main():
    print(f"Python {platform.python_version()} | pasta do projeto: {PASTA}")
    # Procura os .zip do FIRMS em qualquer subpasta do projeto
    zips = []
    for raiz, _, arquivos in os.walk(PASTA):
        for nome in arquivos:
            if fnmatch.fnmatch(nome.lower(), "dl_fire_*.zip"):
                zips.append(Path(raiz) / nome)
    zips.sort()
    if not zips:
        print(f"ERRO: nenhum arquivo DL_FIRE_*.zip encontrado dentro de {PASTA}")
        print("Conteúdo da pasta:", os.listdir(PASTA))
        sys.exit(1)
    print("Arquivos encontrados:")
    for z in zips:
        print(f"  {z.relative_to(PASTA)}")

    grades = []
    for caminho in zips:
        sensor = next((s for chave, s in SENSORES.items() if chave in caminho.name), None)
        if sensor is None:
            print(f"Pulando {caminho.name} (não é MODIS nem S-NPP)")
            continue
        print(f"\n=== {caminho.name} -> {sensor.upper()} ===")
        grades.append(processar_zip(caminho, sensor))

    grades = [g for g in grades if len(g)]
    if not grades:
        print("ERRO: nenhum foco foi processado. Mande o arquivo log_processamento.txt para o Claude.")
        sys.exit(1)
    if grades:
        grade = pd.concat(grades, ignore_index=True)
        # Centro de cada quadradinho, para desenhar no mapa
        grade["lat_centro"] = (grade["gi"] + 0.5) * TAMANHO_QUADRADINHO
        grade["lon_centro"] = (grade["gj"] + 0.5) * TAMANHO_QUADRADINHO
        saida = PASTA_SAIDA / "grade_mensal.parquet"
        grade.to_parquet(saida, index=False)
        print(f"\nTabela resumida salva: {saida}  ({len(grade):,} linhas)".replace(",", "."))
        print("\nPronto! Próximo passo: python 02_comparar_sensores.py")


if __name__ == "__main__":
    main()
