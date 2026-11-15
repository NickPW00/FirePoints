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
- Plano de design de prioridade máxima (8 itens abaixo), a executar só depois do ok do nicholas *(decisions #28)*

## Código gerado ou alterado com IA
- —

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
- [ ] @mariaeliza executar os 8 itens depois do ok, em pull request

## Referências
- Revisão no app publicado (firepoints.streamlit.app), 1440 px e celular; problemas vistos: zoom com a rolagem rouba a página e afasta até o mundo todo; clique recarrega e perde o zoom; divisas em escadinha
- Exemplo de zoom dado pela mariaeliza: Windy.com (nomes por cima, transição suave)
