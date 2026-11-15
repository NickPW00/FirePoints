# AI-assisted: Claude (Anthropic). See docs/ai-log/2026-11-15_1855_mariaeliza_mapa-pixels.md
"""
09_cidades.py  (step 9: city names for the app map)
-------------
List of cities for the name labels of the app map (drawn as text, sharp at any zoom):

  data/processed/cidades.json   [[name, latitude, longitude, population in thousands, capital], ...]

Brazil: every place of the GeoNames "cities15000" list (population above 15,000);
other South American countries: cities above 500,000, for context around the border.
capital: 2 = Brasília, 1 = state capital, 0 = other. Sorted by importance (capitals, then population).

Source: GeoNames (https://www.geonames.org), CC BY 4.0, through the Python package
geonamescache (https://pypi.org/project/geonamescache/). Nothing was changed besides the selection
and the rounding of coordinates (3 decimals) and population (thousands).

How to run:  pip install geonamescache  &&  python 09_cidades.py
"""

import json
from pathlib import Path

import geonamescache

_AQUI = Path(__file__).resolve().parent
PASTA = _AQUI.parent if _AQUI.name == "pipeline" else _AQUI
SAIDA = PASTA / "data" / "processed" / "cidades.json"
VIZINHOS = {"AR", "BO", "CL", "CO", "EC", "GF", "GY", "PY", "PE", "SR", "UY", "VE"}
CAPITAIS = ["Rio Branco", "Maceió", "Macapá", "Manaus", "Salvador", "Fortaleza", "Brasília", "Vitória", "Goiânia",
            "São Luís", "Cuiabá", "Campo Grande", "Belo Horizonte", "Belém", "João Pessoa", "Curitiba", "Recife",
            "Teresina", "Rio de Janeiro", "Natal", "Porto Alegre", "Porto Velho", "Boa Vista", "Florianópolis",
            "São Paulo", "Aracaju", "Palmas"]


def main():
    cidades = list(geonamescache.GeonamesCache().get_cities().values())
    brasil = [c for c in cidades if c["countrycode"] == "BR"]
    # a capital is the most populous place with that name
    capital = {}
    for nome in CAPITAIS:
        iguais = [c for c in brasil if c["name"] == nome]
        if iguais:
            capital[max(iguais, key=lambda c: c["population"])["geonameid"]] = 2 if nome == "Brasília" else 1
    fora = [c for c in cidades if c["countrycode"] in VIZINHOS and c["population"] >= 500_000]
    linhas = [[c["name"], round(c["latitude"], 3), round(c["longitude"], 3), round(c["population"] / 1000),
               capital.get(c["geonameid"], 0)] for c in brasil + fora]
    linhas.sort(key=lambda r: (-r[4], -r[3]))
    SAIDA.write_text(json.dumps(linhas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{SAIDA.name}: {len(linhas):,} cities ({len(brasil):,} in Brazil, {len(capital)} capitals), "
          f"{SAIDA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
