# Plano De Evolucao: Investing Workbench Pos-QuantBrasil

Data: 2026-04-28

Estimativa atual de implementacao do roadmap: **100% concluido**.

Foram entregues arquitetura, modularizacao, persistencia, ranking, radar, cache, storytelling, fluxo `Simular`, realismo de renda fixa de varejo, leituras acionaveis de retirada/stress de aposentadoria, Monte Carlo mensal estocastico reproduzivel, catalogo tematico, perfis didaticos de produto e fechamento de qualidade do estudo. O saldo restante agora e evolucao pos-roadmap: dados externos de produto mais profundos, integracoes vivas e catalogo ainda mais amplo com fonte/frescor explicitos.

Base usada:

- Estado atual do repo: `InvestmentsWorkspace.tsx` foi reduzido para 1.122 linhas neste ciclo, e `application/investments/service.py` esta em 2.794 linhas apos as primeiras extracoes.
- Pendencias informadas: modularizacao frontend/backend, realismo metodologico, renda fixa de varejo, wizard, cenarios de carteira, cache, storytelling e catalogo.
- Auditoria autenticada do QuantBrasil: [QUANTBRASIL_PRODUCT_AUDIT.md](QUANTBRASIL_PRODUCT_AUDIT.md).
- Boas praticas de arquitetura: componentizacao React, hooks customizados, routers FastAPI por dominio, query/cache keys explicitas e divisao por bundles quando fizer sentido.
- Referencias primarias consultadas: [React custom hooks](https://react.dev/learn/reusing-logic-with-custom-hooks), [FastAPI bigger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/), [TanStack Query invalidation](https://tanstack.com/query/v5/docs/framework/react/guides/query-invalidation), [Vite code splitting/dynamic import](https://vite.dev/guide/features.html).

## Progresso De Implementacao

- 2026-04-24: iniciado o Slice A com `product_realism` no payload de `/investments/compare`, painel frontend de realismo do produto investivel, primeiro split de `InvestmentReviewStatsPanel` e builder backend dedicado em `application/investments/product_realism.py`.
- 2026-04-24: segunda extracao do Slice A com `InvestmentHighlightsPanel` no frontend e `application/investments/summaries.py` para `class_summary` e `highlights` no backend.
- 2026-04-24: iniciado o Slice B com `retail_fixed_income_equivalence`, reaproveitando IR regressivo/IOF em `application/investments/retail_fixed_income.py` e exibindo uma tabela CDB versus LCI/LCA no resultado.
- 2026-04-24: iniciado o Slice C com o perfil de decisao em formato de wizard de tres etapas, preservando o contrato `decision_profile`.
- 2026-04-24: ampliado o storytelling com `result_stories`, leituras guiadas e rankings iniciais para Selic, inflacao, drawdown, volatilidade, valor final e retorno real.
- 2026-04-24: iniciado o Slice de performance/cache com `cache_status`, tornando visivel a prontidao dos caches de ativos listados, indices de renda fixa e Tesouro Direto.
- 2026-04-24: iniciado o Market Explorer com facetas de catalogo em `market_explorer`: listas por categoria, tipo de produto, risco, regiao e backlog de rankings.
- 2026-04-24: extraido `InvestmentFixedIncomeBacktestPanel`, movendo a secao de estudos de renda fixa, lideres e janelas rolantes para um componente dedicado e tipado.
- 2026-04-24: extraido `InvestmentComparisonSummaryPanel`, isolando tabela final, leituras rapidas, inflacao, resumo por familia e benchmarks.
- 2026-04-24: extraido `InvestmentPortfolioContributionPanel`, isolando a contribuicao por sleeve e por familia nas carteiras.
- 2026-04-24: extraidos `InvestmentResultChartPanel` e `InvestmentResultFootnotesPanel`, separando controles/grafico de resultado e o rodape de avisos/fontes.
- 2026-04-24: extraido `InvestmentResultsPanel`, movendo a composicao da aba de resultados para um componente proprio.
- 2026-04-24: extraido `application/investments/simulation_models.py`, separando o value object interno `SimulationResult` do service principal.
- 2026-04-27: iniciado o Slice D com `market_rankings` no payload de `/investments/compare`, painel exportavel em CSV e score fatorial guiado inspirado nos rankings/listas do QuantBrasil.
- 2026-04-27: avancado de 1 a 5 do roadmap com carteiras customizadas reutilizaveis no frontend, `portfolio_lifecycle`, `market_screeners` e `GET /backtests/strategy-catalog`.
- 2026-04-27: cache de investimentos ganhou idade/frescor/arquivo mais recente/dicas de atualizacao, e Pairs ganhou radar local de backtests favoritos para acompanhar estudos de cointegracao.
- 2026-04-27: `market_rankings` foi ampliado com momentum 6m, distancia do topo e beta contra benchmark calculados sobre curvas time-weighted quando disponiveis.
- 2026-04-27: Node 22.x entrou no roadmap operacional: o repo ja declara `frontend/.nvmrc` e `.node-version`, e falta alinhar o runtime ativo da maquina/CI para rodar install, testes e build com Node 22 antes de voltar a exigir apenas 22 no wrapper.
- 2026-04-27: iniciado o Slice de persistencia de workspaces de investimento com endpoints para carteiras reutilizaveis e radar de Pairs, mantendo `localStorage` como fallback do frontend.
- 2026-04-27: adicionado `POST /investments/market-rankings`, um snapshot compacto para o futuro explorador de mercado baseado em preset/lista explicita, rankings, screeners e observabilidade de cache.
- 2026-04-27: o Market Explorer do frontend passou a chamar esse snapshot sob demanda, exibindo rankings e screeners no fluxo inicial de `Investimentos`.
- 2026-04-27: runtime frontend ativo migrado para Node `22.20.0`; `.nvmrc` e `.node-version` foram alinhados a versao instalada e lint/test/build focados passaram em Node 22.
- 2026-04-27: `Simular` passou a exibir o catalogo de estrategias do backend, com familias, notas de risco, dimensoes de score e plano de radar de setups.
- 2026-04-27: `Simular` ganhou um radar local de setups, permitindo favoritar estrategias do catalogo enquanto a persistencia completa de parametros fica para o proximo slice.
- 2026-04-27: o radar de setups do `Simular` passou a persistir em `/investments/workspaces/strategy-radar`, mantendo `localStorage` como fallback local/offline.
- 2026-04-27: extraido `useSavedStrategyRadar`, deixando a persistencia do radar de setups testavel e reutilizavel fora do componente visual.
- 2026-04-27: catalogo e radar de estrategias passaram a carregar defaults de parametros, universo sugerido, timeframe e notas de execucao, preparando o proximo passo de rodar/comparar setups salvos.
- 2026-04-27: o radar de setups ganhou edicao inline de timeframe, universo, parametros e notas, persistindo o rascunho atualizado para o futuro fluxo de execucao/comparacao.
- 2026-04-27: adicionado `POST /backtests/strategy-setup-plan` e a acao `Preparar execucao`, mostrando rota sugerida, payload preliminar, premissas, avisos e proximos passos antes de rodar um setup salvo.
- 2026-04-27: setups preparados com `route_hint=/backtest` agora podem ser executados diretamente do radar de `Simular`, retornando resumo de conclusao e `run_id` persistido.
- 2026-04-27: o radar de `Simular` passou a manter historico local de execucoes por setup, com contagem, retorno, drawdown, `run_id` e ultimos runs.
- 2026-04-27: o radar de `Simular` ganhou ranking local inicial de setups executados, usando score simples de retorno ajustado por drawdown como ponte para o score backend definitivo.
- 2026-04-27: historico de execucoes de setups passou a persistir em `/investments/workspaces/strategy-setup-runs`, com fallback em `localStorage` para hidratacao do ranking.
- 2026-04-27: score/ranking de setups passou a ter endpoint backend em `/investments/workspaces/strategy-setup-scores`, mantendo o calculo local apenas como fallback.
- 2026-04-28: score/ranking de setups foi enriquecido com `trade_count`, `run_count`, validade de dados e componentes explicitos de retorno, penalidade de drawdown, sinal limitado de execucao e robustez operacional, cobrindo runs comuns e Pairs.
- 2026-04-28: ranking do radar de `Simular` passou a mostrar a decomposicao do score na interface, com contribuicao de retorno, penalidade de drawdown, contribuicao de execucao e formula auditavel por setup.
- 2026-04-28: radar de `Simular` ganhou leituras comparativas rapidas para setups executados: melhor score, maior retorno, menor drawdown e mais evidencia.
- 2026-04-28: ranking de setups executados no `Simular` ganhou exportacao CSV com componentes do score, ids de runs/Pairs, rotas e metodologia.
- 2026-04-28: scoring, leituras rapidas e serializacao CSV dos setups foram extraidos para `frontend/src/lib/strategySetupScoring.ts`, reduzindo responsabilidade do componente visual e adicionando teste unitario focado.
- 2026-04-28: bloco visual de ranking/CSV/insights dos setups foi extraido para `frontend/src/components/strategy/StrategySetupRankingPanel.tsx`, deixando o painel de catalogo mais proximo de orquestracao.
- 2026-04-28: execucao de plano preparado, resumo de resultados carregados, handoff para Pairs e historico visual de setup foram extraidos para `frontend/src/components/strategy/StrategySetupPlanCard.tsx`, reduzindo o painel de catalogo para cerca de 630 linhas.
- 2026-04-28: formulario de edicao de rascunho de setup foi extraido para `frontend/src/components/strategy/StrategySetupEditForm.tsx`, reduzindo o catalogo para menos de 600 linhas.
- 2026-04-28: cartao individual de setup salvo foi extraido para `frontend/src/components/strategy/StrategySetupRadarItemCard.tsx`, deixando o catalogo de estrategias abaixo de 500 linhas.
- 2026-04-28: lista de estrategias e dimensoes de score planejado foram extraidas para `StrategyCatalogList.tsx` e `StrategyScoreDimensionsPanel.tsx`, deixando o painel orquestrador do catalogo em cerca de 416 linhas.
- 2026-04-28: secao completa do radar de setups foi extraida para `StrategySetupRadarSection.tsx`, reduzindo o painel orquestrador do catalogo para cerca de 382 linhas.
- 2026-04-28: serializacao e parsing dos rascunhos editaveis de setup foram extraidos para `frontend/src/lib/strategySetupDrafts.ts`, com teste focado e catalogo de estrategias em cerca de 328 linhas.
- 2026-04-28: estado operacional e acoes de execucao dos setups foram extraidos para `frontend/src/hooks/useStrategySetupExecution.ts`, cobrindo preparacao, execucao, historico, scores remotos, carregamento de resultados e handoff para Pairs; o painel de catalogo ficou em cerca de 199 linhas.
- 2026-04-28: carregamento do catalogo e hidratacao de historico/scores foram extraidos para `frontend/src/hooks/useStrategyCatalogData.ts`, com teste focado de sucesso e erro; o painel de catalogo ficou em cerca de 161 linhas.
- 2026-04-28: estado e acoes de edicao de rascunho foram extraidos para `frontend/src/hooks/useStrategySetupDraftEditor.ts`, com teste focado de inicio, alteracao, salvamento e cancelamento; o painel de catalogo ficou em cerca de 138 linhas.
- 2026-04-28: selecao de scores remotos versus fallback local e leituras comparativas foram extraidas para `frontend/src/hooks/useStrategySetupScores.ts`, com teste focado; o painel de catalogo ficou em cerca de 131 linhas.
- 2026-04-28: historico de execucoes e construcao de handoff para Pairs foram extraidos para `frontend/src/lib/strategySetupHistory.ts`, com testes focados de merge, persistencia local e resumo de resultados.
- 2026-04-28: scoring backend dos setups foi extraido para `application/investment_workspaces/setup_scoring.py`, com teste focado para ranking, componentes, historico valido e validade dos dados.
- 2026-04-28: `product_realism` ganhou exemplos de politica de renda e reinvestimento para acoes/JCP, FIIs, ETFs, Tesouro Direto e carteiras, com renderizacao no painel de realismo metodologico.
- 2026-04-28: equivalencia de renda fixa de varejo ganhou exemplos tributados para CDB liquidez diaria, Tesouro Selic proxy e fundos DI com taxa de administracao, exibindo `% CDI` bruto/liquido estimado, IR/IOF, liquidez e notas de risco.
- 2026-04-28: lifecycle de carteiras ganhou um plano didatico de retirada, ranqueando alternativas por retirada mensal real estimada, gap contra a meta de renda, drawdown historico e CAGR real.
- 2026-04-28: plano de retirada ganhou stress tests de aposentadoria em cenario base, conservador e sequencia adversa, com buffers de drawdown e gap contra a meta mensal.
- 2026-04-28: catalogo ganhou novos FIIs, BDRs, ETF de cripto como comparativo de risco, presets de FIIs/BDRs/escada de risco e listas tematicas no Market Explorer para renda, FIIs, exterior via B3, NTN-B, Tesouro Direto e risco.
- 2026-04-28: plano de retirada ganhou uma previa Monte Carlo deterministica com cenarios P50/P25/P10 aproximados, retorno real, volatilidade anual, anos de cobertura da meta e caveat explicito antes da reamostragem mensal completa.
- 2026-04-28: previa Monte Carlo passou a incluir simulacao mensal de exaustao em 30 anos para sequencia favoravel, base e adversa, com retirada mensal, taxa de sucesso, saldo final e ano de exaustao quando aplicavel.
- 2026-04-28: simulacao mensal ganhou Monte Carlo estocastico reproduzivel com 250 trajetorias, seed estavel por ativo, taxa de sucesso, percentis de saldo final, mediana de exaustao e renderizacao compacta no plano de retirada.
- 2026-04-28: catalogo ganhou `product_profile` por instrumento, explicando investibilidade, liquidez, tributacao, politica de renda, taxas/custos e qualidade dos dados para acoes, FIIs, ETFs/BDRs, Tesouro Direto, indices, proxies e carteiras modelo.
- 2026-04-28: comparacao ganhou `study_quality`, um checklist final de prontidao no payload e na UI, consolidando metodologia, realismo de produto, rankings, renda fixa, cache, aposentadoria/Monte Carlo, avisos e score de conclusao.
- 2026-04-27: historico de setups em `Simular` passou a reabrir respostas persistidas de runs com `GET /runs/{run_id}/response`, exibindo resumo compacto por estrategia no radar.
- 2026-04-27: setups `pairs_cointegration` ganharam handoff persistido para o laboratorio de Pairs, levando tickers, janela de formacao e z-scores para abrir o workspace avancado pre-preenchido.
- 2026-04-27: handoff de Pairs agora tambem navega automaticamente para `Avancado > Pairs B3`, removendo a etapa manual de troca de area.
- 2026-04-28: iniciado o ciclo de performance com lazy loading das secoes primarias (`Investimentos`, `Simular`, `Resultados`, `Avancado`) e das ferramentas avancadas; o chunk principal caiu para cerca de 48 kB e o aviso de chunk grande do Vite deixou de aparecer no build.
- 2026-04-28: setups `pairs_cointegration` preparados no radar de `Simular` passaram a executar diretamente em `/pairs/backtests`, persistindo `pairs_backtest_id`, reabrindo resultados de Pairs e usando metricas do melhor cenario no historico/score junto dos demais setups.
- 2026-05-04: iniciado o pos-roadmap de dados de produto com `product_data_plan` no catalogo, painel na aba inicial de `Investimentos`, fontes oficiais B3/CVM/Tesouro, cobertura por familia, proximos pacotes e quality gate de fonte/frescor/caveat.
- 2026-05-04: `product_data_plan` foi expandido para cobrir os passos 1-9: conectores especificados, manifesto local de cache, campos esperados por fonte, releases de FIIs/CVM/Tesouro/ETFs-BDRs, candidatos de rankings/screeners, backlog de filtros de mercado e gates de validacao.
- 2026-05-04: primeiro refresh controlado de dados de produto implementado em `POST /investments/product-data/refresh` para `b3_fii_listed`, com CSV local, `manifest.json`, checksum, row count, schema version, botao na UI e enriquecimento do catalogo quando ha match por ticker.
- 2026-05-04: refresh de FIIs passou a tentar coleta na pagina oficial B3, registrar historico em `refresh_history.jsonl`, usar fallback curado quando necessario, permitir selecao de fonte no painel e expor filtros/screeners de FIIs no Market Explorer quando ha cache.
- 2026-05-05: adicionados parser/fixture de FIIs B3, historico com duracao e URL tentada, recarga automatica de catalogo depois do refresh, primeiro refresh semente da CVM, `identity_map` de FIIs e ranking `fii_data_quality` com metadados em cache.
- 2026-05-05: cache B3 FII evoluiu para schema `b3_fii_listed.v2`, adicionando yield 12m aproximado, liquidez, foco de renda, score de qualidade, filtros correspondentes no Market Explorer e ranking `fii_income_quality` para triagem didatica de renda.
- 2026-05-05: conector CVM `cvm_fund_daily_reports` passou a tentar ZIP mensal oficial, normalizar CSV de Informe Diario para cota, PL, captacao, resgate e cotistas, com parser testado e fallback explicito.
- 2026-05-05: `product_data_plan` ganhou `cvm_fund_profile`, resumindo cache CVM por linhas, data de competencia, PL agregado, fluxo liquido, cotistas e maiores fundos/classes para alimentar futuros screeners.
- 2026-05-05: `product_data_plan` ganhou `cvm_fund_rankings`, com maiores fundos/classes por PL, maior fluxo liquido e maior base de cotistas, exibidos na UI como rankings iniciais sem vinculo CNPJ/ticker.
- 2026-05-05: `b3_listed_products` passou a ter refresh operacional controlado, cache `b3_listed_products.v1`, `etf_bdr_profile` e ranking `b3_lowest_admin_fee` para ETFs/BDRs com caveat de tracking/spread/liquidez.
- 2026-05-05: adicionada a ponte `fii_cvm_bridge`, ligando tickers FIIs iniciais a CNPJs CVM e indicando match real com o cache local do Informe Diario quando existir.
- 2026-05-05: adicionado `methodology_readiness_ranking`, ranking consolidado de prontidao metodologica por produto, combinando FII/B3, ponte CVM, ETF/BDR, custos, renda/qualidade e caveats explicitos.
- 2026-05-05: analisado o site publico Investidor Facil e adicionada `investor_easy_parity` ao catalogo, com cobertura de carteira, metas, aportes, dashboard, relatorios, alertas, planos e 15 calculadoras educativas.
- 2026-05-05: a paridade Investidor Facil virou experiencia interativa no frontend, com subtabs de resumo, calculadoras, metas persistentes, carteira manual/preco medio, alertas pessoais, dashboard e exportacao HTML de relatorio.

## Norte Do Produto

O produto deve evoluir de comparador funcional para uma bancada didatica de decisoes de investimento:

- `Investimentos`: experiencia guiada, didatica e orientada a decisao para investidor nao tecnico.
- `Simular`: backtests, score, ranking e comparacao de estrategias.
- `Avancado`: screeners, cointegração, robos simulados, laboratorios quantitativos e pesquisa densa.

O melhor aproveitamento do QuantBrasil nao e copiar telas ou dados, mas importar a estrutura de produto:

- Catalogos e rankings claros.
- Ferramentas com FAQ/metodologia junto do resultado.
- Portfolios reutilizaveis entre calculadoras.
- Screeners como presets em cima de um motor generico.
- Backtests com score, radar e ranking.
- Cointegracao e robos como areas avancadas, nao como caminho inicial.

## Principios De Execucao

- Fazer refactors incrementais antes de adicionar muita superficie nova.
- Preservar comportamento atual e contratos de API sempre que possivel.
- Todo dado novo precisa de origem, cache, frescor, caveat e equivalencia investivel.
- Nenhuma tela deve transformar vencedor historico em recomendacao.
- Padrao ouro desejado: dominio e aplicacao tipados no backend; UI composta por componentes pequenos, hooks claros e contratos de API explicitos.
- Atalhos pragmaticos sao aceitaveis se tiverem teste, limite de escopo e caminho de remocao.

## Sequencia Recomendada

### Fase 0: Contratos E Inventario Tecnico

Objetivo: travar o mapa antes de mexer nas paredes.

Entregas:

- Criar um inventario de contratos atuais de `/investments/catalog` e `/investments/compare`.
- Mapear todos os campos usados por `InvestmentsWorkspace.tsx`.
- Criar snapshot de payloads representativos: renda fixa, carteira guiada, carteira customizada, perfil conservador, perfil renda.
- Definir taxonomia local inspirada no QuantBrasil:
  - `market_list`
  - `portfolio_metric`
  - `fixed_income_product`
  - `factor_ranking`
  - `screener_preset`
  - `strategy_catalog`
  - `cointegration_research`

Arquivos provaveis:

- `tests/fixtures/investments/*.json`
- `docs/API_REFERENCE.md`
- `frontend/src/types/api.ts`

Validacao:

- `uv run pytest -q tests/test_investment_compare_service.py tests/test_api_investments.py`
- `cd frontend && npm test -- --run src/hooks/useInvestmentsComparison.test.tsx src/components/InvestmentsWorkspace.test.tsx`

### Fase 1: Modularizar A Tela De Investimentos

Objetivo: reduzir risco de produto antes de ampliar funcionalidade.

Extracoes recomendadas:

- `InvestmentsWorkspace.tsx`
  - manter apenas orquestracao de alto nivel, selecao de abas e composicao.
- `components/investments/setup/`
  - `InvestmentModeSelector`
  - `InvestmentScenarioTab`
  - `InvestmentAssetSelection`
  - `InvestmentContributionControls`
  - `InvestmentDecisionWizardPreview`
- `components/investments/review/`
  - `InvestmentReviewSummary`
  - `InvestmentAssumptionChecklist`
  - `InvestmentSelectedUniversePanel`
- `components/investments/results/`
  - `InvestmentResultTabs`
  - `InvestmentResultTable`
  - `InvestmentLeaderStories`
  - `InvestmentRiskReturnPanel`
  - `InvestmentPortfolioScenarioPanel`
- `components/investments/charts/`
  - `InvestmentEquityChart`
  - `InvestmentDrawdownChart`
  - `InvestmentInflationChart`
  - `InvestmentChartControls`
- `hooks/investments/`
  - `useInvestmentSetupState`
  - `useInvestmentReview`
  - `useInvestmentResultStories`
  - `useInvestmentChartState`
  - `useCustomPortfolioDrafts`

Ordem segura:

1. Extrair componentes puros de review e tabelas sem mudar estado.
2. Extrair chart state e legendas.
3. Extrair setup tabs.
4. Extrair carteira customizada.
5. Transformar `InvestmentsWorkspace.tsx` em casca fina.

Criterios de aceite:

- `InvestmentsWorkspace.tsx` abaixo de 700 linhas.
- Nenhuma regressao visual relevante no fluxo padrao.
- Testes atuais continuam passando.
- Novos hooks com testes quando tiverem logica de decisao.

Validacao:

- `cd frontend && npm test -- --run src/components/InvestmentsWorkspace.test.tsx src/components/investments/InvestmentDecisionPanels.test.tsx src/hooks/useInvestmentsComparison.test.tsx`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

### Fase 2: Dividir O Service Backend Em Servicos De Aplicacao

Objetivo: preparar a base para renda fixa, portfolio e rankings sem transformar `service.py` em gargalo.

Arquitetura alvo:

- `application/investments/service.py`
  - casca orquestradora e compatibilidade do contrato atual.
- `application/investments/data_loading.py`
  - series de ativos, indices, componentes e proxies.
- `application/investments/fixed_income_studies.py`
  - estudos de renda fixa, janelas, lideres, takeaways.
- `application/investments/tesouro_simulation.py`
  - Tesouro Direto rolling, lotes, IR, liquidacao, candidato.
- `application/investments/market_simulation.py`
  - buy-and-hold, aportes, Selic proxy, portfolios modelo.
- `application/investments/portfolio_simulation.py`
  - carteiras customizadas, rebalanceamento, decomposicoes.
- `application/investments/result_payloads.py`
  - chart points, benchmark payload, highlights, summaries.
- `application/investments/cache_status.py`
  - metadados de cache, frescor, origem, mensagens de cold start.

Ordem segura:

1. Extrair funcoes sem mudar assinatura publica.
2. Manter `InvestmentComparisonService.compare` como fachada.
3. Mover testes por comportamento, nao por implementacao interna.
4. So depois separar novos bounded contexts como `market_lists` e `portfolios`.

Criterios de aceite:

- `service.py` abaixo de 900 linhas.
- Cada modulo novo tem responsabilidade clara.
- O contrato de `/investments/compare` permanece compativel.
- Testes existentes continuam verdes.

Validacao:

- `uv run pytest -q tests/test_investment_compare_service.py tests/test_api_investments.py`
- `uv run ruff check src/api src/investing_workbench tests`
- `uv run mypy src/investing_workbench`

### Fase 3: Realismo Metodologico E Renda Fixa De Varejo

Objetivo: transformar resultado historico em comparacao realista de produtos investiveis.

Entregas:

- Modelo de produto com:
  - classe: indice, ETF, fundo, Tesouro, CDB, LCI/LCA, debenture, FII, BDR, proxy.
  - tributacao: isento, regressivo IR, come-cotas se aplicavel, IOF, dividendos/JCP/FIIs.
  - custo: taxa de administracao, spread, taxa B3/Tesouro, corretagem se aplicavel.
  - liquidez: D+0, D+1, vencimento, carencia, mercado secundario, marcação a mercado.
  - equivalencia investivel: indice teorico vs produto real.
- Renda fixa de varejo:
  - CDB `% CDI`.
  - LCI/LCA `% CDI` isentas.
  - Tesouro Selic, Prefixado, IPCA+ com vencimentos.
  - Debenture incentivada como classe com caveat de credito/liquidez.
  - equivalencia liquida CDB vs LCI/LCA vs Tesouro.
- Narrativas:
  - rentabilidade bruta, liquida e real.
  - "indice" versus "produto compravel".
  - impacto de prazo e resgate antecipado.

Criterios de aceite:

- Toda linha de resultado informa tratamento tributario e liquidez.
- Renda fixa mostra retorno liquido e real quando dados permitirem.
- Caveats aparecem no payload e na UI.
- Testes cobrem ao menos CDB tributado, LCI/LCA isenta, Tesouro IPCA+ e Tesouro Selic.

### Fase 4: Wizard De Decisao

Objetivo: evoluir o perfil atual para fluxo guiado.

Fluxo proposto:

1. Objetivo: reserva, renda mensal, aposentadoria, acumulacao, preservacao, estudo livre.
2. Horizonte: curto, medio, longo, data alvo.
3. Liquidez: imediata, D+1, aceita vencimento, aceita baixa liquidez.
4. Risco: volatilidade, drawdown, marcação a mercado, perda nominal.
5. Inflacao: proteger poder de compra, superar CDI, renda nominal, renda real.
6. Tributacao: priorizar liquido, isencao, simplicidade, reinvestimento.
7. Portfolio: ativo unico, carteira guiada, carteira customizada.
8. Revisao: escolhas, premissas, produtos elegiveis, alertas.

Inspiracao QuantBrasil:

- Usar onboarding/activation checklist como padrao de progresso, mas local-first.
- Mostrar "proximo melhor passo" sem parecer recomendacao.
- Salvar cenarios locais para comparar depois.

Criterios de aceite:

- O usuario consegue completar o fluxo sem entender termos tecnicos.
- Cada resposta altera explicitamente universo, metricas ou storytelling.
- Ha modo compacto para usuarios avancados.

### Fase 5: Storytelling Didatico De Resultado

Objetivo: tornar a comparacao interpretavel.

Leituras obrigatorias:

- Quem bateu a Selic.
- Quem caiu menos.
- Quem protegeu melhor contra inflacao.
- Quem gerou mais renda.
- Quem foi mais consistente.
- Quem sofreu mais marcação a mercado.
- Qual escolha fez mais sentido para o perfil.
- Onde o resultado e apenas proxy ou indice teorico.

Componentes:

- `InvestmentLeaderStories`
- `InvestmentProfileFitPanel`
- `InvestmentInflationProtectionPanel`
- `InvestmentIncomeCapacityPanel`
- `InvestmentRiskCaveatsPanel`

Criterios de aceite:

- Cada historia referencia metricas reais do payload.
- Historias mudam conforme perfil e objetivo.
- Linguagem evita "compre/venda" e privilegia "historicamente fez sentido para...".

### Fase 6: Cenarios Completos De Carteira

Objetivo: transformar cards atuais em simuladores de vida financeira.

Cenarios:

- Carteira diversificada vs ativo unico.
- Aposentadoria: acumulo, data alvo, patrimonio alvo.
- Pre-aposentadoria: reduzir volatilidade mantendo retorno real.
- Retirada mensal: taxa segura, risco de exaustao, renda real.
- Renda passiva: dividendos/JCP/FIIs quando dados existirem.
- Preservacao: menor drawdown, maior liquidez, menor perda real.
- Acumulacao: retorno real, contribuicoes, consistencia.

Inspiracao QuantBrasil:

- Reutilizar portfolios como entidades centrais, como `/portfolios/`.
- Usar rankings e fatores como insumos de carteira, nao telas isoladas.
- Manter "como interpretar" junto de cada resultado.

Criterios de aceite:

- Portfolio pode ser reutilizado em retorno historico, beta, VaR e comparacao de investimentos.
- Simulacao mostra curvas, drawdown, renda estimada e risco de liquidez.
- O resultado separa contribuicao, retorno, impostos e custos.

### Fase 7: Market Explorer E Rankings Inspirados No QuantBrasil

Objetivo: trazer as melhores ideias de listas/rankings para `Investimentos` e `Avancado`.

Primeiro lote recomendado:

- Ranking B3 por retorno: WTD, MTD, YTD, 30d, 90d, 180d, 365d.
- Drawdown atual e distancia do topo historico.
- Beta/correlacao/volatilidade.
- Momentum 30/90/180 dias.
- Low Risk simples.
- Ranking fatorial guiado: momentum + low risk + retorno real + drawdown.

Segundo lote:

- Magic Formula se houver fonte fundamentalista confiavel.
- BDRs, ETFs, FIIs, S&P 500 e crypto.
- Hurst e screeners tecnicos.

Arquitetura:

- `application/market_lists/`
- `application/factor_rankings/`
- `frontend/src/components/market/`
- `frontend/src/components/rankings/`

Criterios de aceite:

- Cada ranking declara universo, data de referencia, metodologia e fonte.
- Rankings sao exportaveis em CSV local.
- Rankings nao bloqueiam o carregamento principal de `Investimentos`.

### Fase 8: Screener Engine

Objetivo: nao criar dez telas hard-coded de screening.

Motor generico:

- universo
- timeframe
- indicadores
- operadores
- regras AND/OR
- colunas de ranking
- presets salvos
- explicacao de cada indicador

Presets iniciais:

- IFR2.
- Bollinger.
- Supertrend.
- Momentum.
- Drawdown/ATH.
- Suporte/resistencia simples.
- Hurst.

Inspiracao QuantBrasil:

- `Screening de Indicadores`.
- `Screening de Suportes e Resistencias`.
- Variantes por timeframe.

Criterios de aceite:

- Preset e configuracao customizada usam o mesmo motor.
- Resultados incluem explicacao por regra.
- A UI avancada suporta filtros densos sem poluir `Investimentos`.

### Fase 9: Backtest Catalog, Score E Radar

Objetivo: modernizar `Simular` com catalogo e interpretacao.

Entregas:

- `StrategyCatalog`: familia, direcao, parametros, timeframe, requisitos.
- Score de backtest:
  - EV.
  - drawdown.
  - retorno.
  - fator de lucro.
  - acerto.
  - numero de trades.
  - robustez por janela.
- Radar local:
  - historico de simulacoes.
  - favoritos.
  - ranking por setup.
  - validade/cache do resultado.

Inspiracao QuantBrasil:

- Backtest Score.
- Radar de Backtests.
- Rankings de Backtests.
- Alertas como etapa futura, nao inicial.

Criterios de aceite:

- Score e explicavel e testado.
- Estrategias ficam catalogadas antes de virar telas novas.
- Radar usa resultados reproduziveis e cacheados.

### Fase 10: Cointegracao E Labs Avancados

Objetivo: aproveitar o melhor do QuantBrasil sem deslocar o foco principal.

Entregas:

- Teste de par cointegrado.
- Radar por universo/setor.
- Favoritos locais.
- Interpretacao de p-value, z-score, hedge ratio e janela.
- Trade tracker apenas depois de accounting/auditoria.

Criterios de aceite:

- A ferramenta explica diferenca entre correlacao e cointegração.
- Resultado tem validade temporal.
- Nenhuma saida se apresenta como recomendacao.

### Fase 11: Performance, Cache E Observabilidade

Objetivo: reduzir cold start e tornar dados externos compreensiveis.

Entregas:

- Cache manifest por fonte:
  - fonte
  - intervalo coberto
  - criado em
  - atualizado em
  - expira em
  - status: hit, stale, fetching, failed, synthetic/proxy.
- Mensagens de UI:
  - "preparando dados de renda fixa pela primeira vez"
  - "usando cache de X atualizado em Y"
  - "fonte externa indisponivel; usando ultimo cache valido"
- Jobs preparatorios opcionais:
  - aquecer Selic/IPCA/Tesouro.
  - atualizar catalogo de ativos.
  - validar tickers ativos/inativos.
- Métricas:
  - tempo de carregamento por fonte.
  - taxa de cache hit.
  - tamanho do cache.
  - falhas por provedor.

Criterios de aceite:

- Cold start tem mensagem honesta.
- Cache stale nao parece dado atual.
- Testes cobrem fallback para cache valido e erro de fonte externa.

## Ordem De Implementacao Em Slices

### Slice A: Limpeza Estrutural

1. Extrair componentes de review/resultados.
2. Extrair chart state.
3. Extrair `data_loading.py` e `result_payloads.py`.
4. Manter todos os testes verdes.

Motivo: reduz custo de todas as fases seguintes.

### Slice B: Produto Investivel E Renda Fixa

1. Modelo de produto investivel.
2. CDB/LCI/LCA/debenture/Tesouro equivalencia liquida.
3. Narrativas de imposto, liquidez, prazo e inflacao.
4. Testes backend e painéis frontend.

Motivo: maior valor direto para `Investimentos`.

### Slice C: Wizard E Storytelling

1. Fluxo guiado.
2. Historias de resultado.
3. Cenários completos.
4. Persistencia local simples de cenarios.

Motivo: transforma capacidade tecnica em experiencia didatica.

### Slice D: Rankings E Portfolios

1. Portfolio reutilizavel.
2. Retorno historico, beta, VaR.
3. Rankings B3/fatoriais simples.
4. Export local.

Motivo: importa a melhor estrutura do QuantBrasil para o produto local.

### Slice E: Avancado

1. Screener engine.
2. Backtest catalog/score/radar.
3. Cointegracao.
4. Robos simulados somente se houver auditoria de sinais.

Motivo: poder sem poluir o caminho iniciante.

## Matriz De Priorizacao

| Item | Valor | Risco | Dependencia | Prioridade |
| --- | --- | --- | --- | --- |
| Modularizar frontend | Alto | Baixo | Nenhuma | P0 |
| Dividir service backend | Alto | Medio | Nenhuma | P0 |
| Modelo de produto investivel | Alto | Medio | Backend split | P0 |
| Renda fixa varejo | Alto | Medio | Produto investivel | P1 |
| Wizard decisao | Alto | Medio | Frontend split | P1 |
| Storytelling didatico | Alto | Baixo | Payloads mais ricos | P1 |
| Portfolio reutilizavel | Alto | Medio | Backend split | P1 |
| Ranking/fatores | Medio/alto | Medio | Market data/cache | P2 |
| Screener engine | Medio | Alto | Market data/cache | P2 |
| Backtest radar/score | Medio | Medio | Strategy catalog | P2 |
| Cointegracao | Medio | Alto | Advanced UX/data | P3 |
| Robos | Baixo/medio | Alto | Audit logs/sinais | P4 |

## Testes E Validacao Por Camada

Backend:

- `uv run pytest -q tests/test_investment_compare_service.py tests/test_api_investments.py`
- `uv run pytest -q tests/test_selic.py tests/test_selic_daily.py tests/test_ibov_history.py`
- `uv run ruff check src/api src/investing_workbench tests`
- `uv run mypy src/investing_workbench`

Frontend:

- `cd frontend && npm test -- --run src/components/InvestmentsWorkspace.test.tsx`
- `cd frontend && npm test -- --run src/hooks/useInvestmentsComparison.test.tsx`
- `cd frontend && npm test -- --run src/components/investments/InvestmentDecisionPanels.test.tsx`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

Produto:

- Comparar resultado antes/depois para payloads fixture.
- Validar linguagem didatica: historico, nao recomendacao.
- Validar mobile/desktop para wizard e resultados.
- Validar tempo de cold start e cache hit.

## Definicao De Pronto Do Proximo Ciclo

O proximo ciclo esta pronto quando:

- `InvestmentsWorkspace.tsx` e `service.py` deixarem de ser gargalos.
- O usuario conseguir montar um perfil guiado e entender liquidez, imposto, inflacao e risco.
- Renda fixa de varejo tiver comparacao liquida e explicavel.
- Carteiras forem entidades reutilizaveis.
- Storytelling responder "quem ganhou", "quem protegeu", "quem caiu menos" e "o que fez sentido para meu perfil".
- O app tiver pelo menos um primeiro lote de rankings inspirados no QuantBrasil, com fonte/metodologia/caveat.

## Primeira Sprint Recomendada

1. Criar fixtures de payload atual para investimentos.
2. Extrair `InvestmentReviewSummary`, `InvestmentResultTable` e chart controls.
3. Extrair `data_loading.py` e `result_payloads.py` do backend.
4. Adicionar `ProductRealismMetadata` no contrato backend sem mudar comportamento numerico ainda.
5. Mostrar esse metadata em um painel simples de premissas/caveats.

Essa sprint e pequena o bastante para revisar, mas cria a base para todo o resto.
