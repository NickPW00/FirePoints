---
data: 2026-11-15
autor: mariaeliza
ferramenta: Claude
tema: design-app
---

# Plano de design do app — 2026-11-15 — mariaeliza

## Objetivo
Mariaeliza assume o design do app. Revisão do site (desktop e celular) e plano das melhorias de prioridade máxima, **para aprovação do nicholas antes de executar**.

## Decisões
- Plano de design de prioridade máxima (8 itens abaixo), a executar só depois do ok do nicholas *(decisions #28; ok do nicholas na #30)*

## Código gerado ou alterado com IA
- `app/maps.py` — zoom com a rolagem só depois do clique, mapa travado no Brasil (zoom 4–11), zoom suave, nomes (CARTO) por cima das cores, opção de suavizar, divisas IBGE de estados e municípios — alterado
- `app/streamlit_app.py`, `app/charts.py`, `app/data.py` — seletor EN/PT, área por regiões, RJ como padrão, biomas em inglês — alterado
- `app/i18n.py` — textos em inglês e português — gerado
- `pipeline/07_divisas.py` + `data/processed/ufs_simplificado.geojson`, `municipios/<UF>.geojson` — divisas IBGE 2024 simplificadas — gerado

## Ideias (ainda não decididas)
- #app depois: números do topo cortados, faixa de abertura, cores (tirar o azul), contraste das siglas, calendário e celular

## Pendências / perguntas para a dupla
- [ ] @nicholas aprovar (ou ajustar) o plano de design antes de a mariaeliza mexer no `app/` — responder aqui ou confirmar a #28:
  1. Mapa: rolagem dá zoom só depois de clicar no mapa; ao sair dele, a rolagem volta a descer a página; zoom travado no Brasil
  2. Mapa: não perder o zoom ao clicar numa célula
  3. Mapa estilo Windy: zoom em passos menores (suave), nomes de cidades/estados por cima das cores, opção de suavizar os quadradinhos quando afastado
  4. Divisas suaves dos estados (`ufs_simplificado.geojson` gerado no pipeline) e divisas dos municípios só na área selecionada
  5. Estado inicial = RJ (no lugar do TO)
  6. Área por regiões (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)
  7. Biomas em inglês: Amazon e Atlantic Forest; Cerrado, Caatinga, Pantanal e Pampa ficam (IBGE é domínio público com citação da fonte; anotar "nomes traduzidos pela equipe")
  8. Seletor de idioma EN/PT, inglês como padrão
- [x] @mariaeliza executar os 8 itens depois do ok, em pull request *(feito: PR mariaeliza/design-mapa)*
- [ ] @nicholas revisar e fazer o merge do PR de design; depois conferir o mapa no app publicado

## Referências
- Revisão no app publicado (firepoints.streamlit.app), 1440 px e celular; problemas vistos: zoom com a rolagem rouba a página e afasta até o mundo todo; clique recarrega e perde o zoom; divisas em escadinha
- Exemplo de zoom dado pela mariaeliza: Windy.com (nomes por cima, transição suave)
