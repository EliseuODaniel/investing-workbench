# Plano Pos-Roadmap: Dados De Produto

Data: 2026-05-04

O roadmap principal de `Investimentos` esta concluido. A proxima frente transforma o catalogo didatico em uma camada de dados de produto com fonte primaria, frescor, cache, caveat e diferenca clara entre indice teorico, proxy e produto investivel.

## Implementado Neste Slice

1. **Fontes externas oficiais**
   - O catalogo agora expoe `product_data_plan.sources` com B3, CVM e Tesouro Transparente.
   - Cada fonte declara cobertura, politica de atualizacao, status de integracao, status do conector, chave de cache, familias de produto e campos esperados.

2. **Integracoes e refresh**
   - O payload diferencia fontes `connected`, `partial` e `planned`.
   - Tesouro Transparente entra como fonte conectada por ja existir trilha real de Tesouro Direto.
   - B3 aparece como parcial, porque parte do catalogo e dos dados publicos ja alimenta produtos listados, mas ainda falta ingestao dedicada por familia.
   - `source_manifest` mostra cache local por fonte, idade, frescor, tamanho, arquivo mais recente e resumo de prontidao.

3. **Catalogo mais amplo com cobertura**
   - `product_data_plan.family_coverage` mostra cobertura por familia do catalogo, quantidade de instrumentos e status externo.
   - Isso prepara a expansao de FIIs, ETFs, BDRs, fundos e Tesouro sem esconder lacunas.

4. **UX de dados**
   - A aba inicial de `Investimentos` agora mostra o painel "Plano pos-roadmap de dados de produto".
   - O usuario ve fontes em uso, proximos pacotes e cobertura por familia antes de comparar.

5. **Hardening**
   - O contrato backend/frontend passou a incluir o plano no catalogo.
   - Testes focados cobrem API, catalogo e renderizacao inicial.
   - `validation_plan` versiona os gates de contrato da fonte, manifesto/cache, caveat metodologico e UI.

6. **Proxima fronteira**
   - Pacotes priorizados: rendimentos/segmentos de FIIs, taxas/tracking de ETFs e BDRs, e fluxo de caixa/liquidez do Tesouro.
   - Antes de virar ranking ou screener, cada pacote precisa passar pelo quality gate: fonte, coleta, refresh, teste e caveat investivel.

## Planejamento 1-9 Agora No Produto

1. **Conector real de FIIs**: B3 FIIs listados esta especificado com campos esperados e pacote `fii_income_data`.
2. **CVM para fundos/FIIs**: Informe Diario de Fundos esta mapeado para `fii_income_data` e `fund_cvm_profile`.
3. **Tesouro Direto mais profundo**: Tesouro Transparente segue como fonte conectada e proximo pacote de cupons/vendas/resgates.
4. **Taxas e tracking de ETFs/BDRs**: B3 produtos listados alimenta o pacote `etf_bdr_fee_tracking`.
5. **Ranking/screener com dados novos**: cada release declara `screeners_enabled` e `ranking_candidates`.
6. **Painel de qualidade dos dados**: a UI mostra manifesto, fontes, cobertura, releases, roadmap e gates.
7. **Persistencia/versionamento dos datasets**: `source_manifest` registra caminho, arquivos, tamanho, data, idade e frescor.
8. **UX de exploracao de mercado**: `market_filter_backlog` lista filtros por renda, liquidez, custo, tributacao e investibilidade.
9. **Validacao metodologica**: `validation_plan` exige fonte, cache, caveat e contrato de UI antes de promover dados.

## Slice Operacional De Refresh

O primeiro refresh controlado foi implementado para `b3_fii_listed`:

- Endpoint: `POST /investments/product-data/refresh`
- Payload: `{"source_id": "b3_fii_listed", "force": true}`
- Saida local: `data/product_sources/b3_fii_listed/fiis_listados.csv`
- Manifesto persistido: `data/product_sources/b3_fii_listed/manifest.json`
- Campos do manifesto: `collected_at`, `row_count`, `schema_version`, `source_url`, `checksum_sha256`, `fields`, `collection_mode`, `fetch_error` e `caveat`.

Nesta etapa, o refresh tenta coletar a pagina oficial da B3 e extrair tickers de FIIs. Quando a pagina nao entrega uma tabela estruturada confiavel, o processo usa fallback curado mantendo o mesmo contrato de CSV + manifesto.

Cada tentativa grava `refresh_history.jsonl`, com status, mensagem, `row_count`, schema, checksum, modo de coleta e erro de fetch quando existir.

O catalogo tambem passou a expor `catalog_enrichment`, ligando linhas em cache aos FIIs ja existentes no catalogo quando os tickers batem. Essa ponte prepara filtros reais por segmento/status e rankings de renda/liquidez.

O Market Explorer passou a expor, quando ha cache de FIIs:

- `product_data_filters`: filtros reais por segmento, status de listagem, liquidez estimada e tipo de renda.
- `product_data_screeners`: screener de FIIs do catalogo com metadados B3 em cache, yield 12m aproximado, liquidez, foco de renda e score de qualidade.
- `product_data_rankings`: rankings iniciais `fii_data_quality` e `fii_income_quality`.

O painel de dados de produto agora permite escolher a fonte no refresh. As quatro fontes do roadmap
1-9 aparecem como conectadas, parciais ou sementes operacionais, e o payload expoe
`roadmap_completion_pct` para evitar que itens ja entregues voltem a aparecer como apenas mapeados.

## Slice De Confiabilidade E UX

Este slice avancou os proximos passos do planejamento:

1. O coletor B3 agora tem parser testavel por texto/fixture e continua tentando a fonte oficial antes do fallback.
2. Foi adicionada fixture HTML/JSON pequena em `tests/fixtures/product_data/b3_fii_listed_sample.html`.
3. `refresh_history.jsonl` agora registra `started_at`, `finished_at`, `duration_ms` e `source_attempted_url`.
4. O painel chama a recarga de catalogo depois de um refresh bem-sucedido, removendo a etapa manual.
5. O Market Explorer expoe filtros de FIIs por segmento/status/liquidez/tipo de renda quando ha cache.
6. O screener de FIIs mostra quantos ativos do catalogo encontraram metadados externos e exibe yield 12m aproximado quando disponivel.
7. `cvm_fund_daily_reports` ganhou o primeiro refresh operacional de contrato com semente local e manifesto.
8. `identity_map` cria a primeira ponte ticker/nome/segmento/status/fonte para FIIs.
9. Os primeiros rankings reais de FIIs classificam ativos por qualidade de dado (`fii_data_quality`) e por renda ponderada por liquidez/qualidade (`fii_income_quality`), ainda com caveat de fallback quando a fonte oficial nao entrega tabela estruturada.

## Slice CVM Oficial

O conector `cvm_fund_daily_reports` agora tenta baixar o ZIP mensal oficial da CVM antes de usar fallback:

- Candidatos: mes corrente e mes anterior em `https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/`.
- Parser: ZIP com CSV separado por `;`, aceitando `CNPJ_FUNDO` e o layout novo `CNPJ_FUNDO_CLASSE`, normalizado para `cnpj_fundo`, `dt_comptc`, `vl_total`, `vl_quota`, `vl_patrim_liq`, `captc_dia`, `resg_dia` e `nr_cotst`.
- Modo de coleta: `official_zip` quando o download e parsing retornam linhas; `curated_seed_fallback` quando o arquivo oficial nao esta disponivel ou falha.
- Teste: parser ZIP/CSV coberto em memoria e refresh de servico coberto por coletor injetado.
- Uso no catalogo: `product_data_plan.cvm_fund_profile` resume linhas em cache, data mais recente, PL agregado, fluxo liquido, cotistas e maiores fundos/classes por PL para orientar futuras telas de fundos e FIIs.
- Rankings iniciais: `product_data_plan.cvm_fund_rankings` expoe maiores fundos/classes por PL, maiores fluxos liquidos e maiores bases de cotistas, ainda sem vinculo CNPJ/ticker.
- Ponte FII/CVM: `product_data_plan.fii_cvm_bridge` cruza um crosswalk inicial de ticker FII para CNPJ CVM com o cache do Informe Diario, mostrando quantos instrumentos do catalogo ja bateram com o cache local.

## Slice ETFs E BDRs

O conector `b3_listed_products` agora tem refresh operacional controlado:

- Saida local: `data/product_sources/b3_listed_products/produtos_listados.csv`.
- Schema: `b3_listed_products.v1`.
- Campos: ticker, nome, tipo de produto, indice de referencia, taxa de administracao, exposicao, nota de tracking e score de qualidade do dado.
- Uso no catalogo: `product_data_plan.etf_bdr_profile` resume quantidade por tipo de produto, taxa media e amostras de menor taxa.
- Ranking inicial: `product_data_plan.etf_bdr_rankings` expoe `b3_lowest_admin_fee`, ainda sem medir tracking error historico, spread ou liquidez.

## Fechamento Metodologico

O plano agora expoe `product_data_plan.methodology_readiness_ranking`:

- Universo inicial: FIIs, ETFs locais, ETFs internacionais via B3, ETFs de renda fixa e BDRs que tenham ticker no catalogo.
- Score FII: qualidade do dado B3, ponte CVM e sinal de renda em cache.
- Score ETF/BDR: qualidade do dado, custo/taxa e contexto de tracking.
- Caveat: cada linha declara por que o ranking ainda nao e recomendacao de compra, destacando dados que faltam como serie mensal oficial de renda, tracking error, spread e liquidez historica.

## Referencias Primarias

- B3 FIIs listados: https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/fundos-de-investimentos/fii/fiis-listados/
- CVM Informe Diario de Fundos: https://dados.cvm.gov.br/dataset/fi-doc-inf_diario
- Tesouro Transparente / Tesouro Direto: https://www.tesourotransparente.gov.br/temas/divida-publica-federal/tesouro-direto
- B3 dados e produtos listados: https://www.b3.com.br/
