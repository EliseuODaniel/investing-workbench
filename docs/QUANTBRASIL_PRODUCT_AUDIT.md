# QuantBrasil Product Audit

Date: 2026-04-24

Source: authenticated structural crawl of <https://quantbrasil.com.br/> using the approved Premium account.

Raw local artifact: `/tmp/quantbrasil_full_scan.json`
Generated local inventories:

- `reports/quantbrasil_audit_20260424/page_inventory.csv`
- `reports/quantbrasil_audit_20260424/api_inventory.csv`
- `reports/quantbrasil_audit_20260424/menu_inventory.csv`
- `reports/quantbrasil_audit_20260424/summary.json`

This document turns the QuantBrasil crawl into a product and implementation reference for Investing Workbench. It is intentionally a functional audit, not a clone of proprietary datasets or long-form copyrighted content. The crawl stored page metadata, headings, table schemas, route inventory, API surface, and short snippets only. No password, cookie, access token, or full table export was stored.

## Crawl Coverage

- Sitemap URLs parsed: 1,009.
- Next.js route patterns discovered from the bundle: 75.
- Initial crawl targets: 1,036.
- Second-pass internal links discovered and visited: 120.
- Total visited routes/pages: 1,156.
- Successful HTML pages: 1,126.
- Generated metadata routes skipped: 7.
- 404 pages observed: 23.
- JavaScript chunks analyzed: 162.
- API endpoints discovered: 80.
- Safe GET endpoints schema-probed: 30.
- Pages with table-like content: 143.

The largest category is asset detail pages: 885 visited entries using the same dashboard template. This is useful as a product pattern and asset-universe signal, but it should not be treated as a dataset to copy.

## Navigation Model

QuantBrasil uses two navigation modes:

- Public/marketing navigation: Ferramentas, Screenings, Factor Investing, QuantBrasil, Planos, Sobre, Buscar, Testar Gratis, Entrar.
- Authenticated app navigation: Feed, Robos, Backtests, Cointegracao, Ferramentas, Buscar, plus a user/account menu.

The authenticated layout keeps research-heavy workflows close to the top nav while educational/legal/support material stays in footer and content sections. This maps well to the current Investing Workbench direction:

- `Investimentos`: investor-facing comparisons, portfolios, factor rankings, asset dashboards.
- `Simular`: backtest simulator, strategy scoring, rankings, alerts.
- `Avancado`: cointegração, custom screeners, support/resistance scanners, robots/labs.

## Product Areas

### Market And Asset Surface

Observed pages:

- `/ativos/`: searchable asset index.
- `/ativos/:ticker/`: asset dashboard template. The sitemap exposed hundreds of B3, US, BDR, index, ETF, future, fund, and crypto symbols.
- `/beta/`: beta, correlation, daily volatility, annualized volatility, last update.
- `/ranking/` variants: B3 and S&P 500 performance rankings over WTD, MTD, YTD, 30d, 90d, 180d, 365d.
- `/drawdown/`: current drawdown, peak, trough, peak date, trough date, current price.
- `/topo-historico/`: all-time high, current price, ATH date, distance from ATH.
- `/ipos/`: IPO date, IPO open price, current price, benchmark-relative return.
- `/bdrs-mais-liquidas/`: BDR return, initial/current price, average volume, benchmark-relative return.
- `/hurst/` and `/hurst/sp500/`: Hurst value, 30-day return, 1-year return, classification.

Replication idea:

- Build a local `MarketExplorer` module that produces repeatable asset cards and ranking tables from local/cacheable providers.
- Keep the first implementation focused on B3 tickers already supported by local data sources.
- Add US, crypto, BDR, and future symbols only after source reliability and cache semantics are explicit.

### Factor Investing

Observed pages:

- `/magic-formula/`: EV/EBIT, ROIC, segment, points.
- `/momentum/`, `/momentum/30d/`, `/momentum/180d/`, plus S&P 500 variants: sector, price, momentum, regression coefficient, R2.
- `/momentum-double/` and `/momentum-double/sp500/`: 1-year return, 90-day momentum, points, sector.
- `/low-risk/` and `/low-risk/sp500/`: dividends, beta, variation, points.
- `/full-factor/`: composite ranking across momentum, low risk, magic formula, points.
- `/ranking-fatorial/`: Premium tool for custom multi-factor ranking with user-defined weights.

Replication idea:

- Make factor rankings a first-class `Investimentos` capability because they fit investor decision support better than pure trading.
- Use transparent scoring explainers, factor weights, benchmark, universe, date range, and data freshness.
- Implement `Ranking Fatorial` as a guided wizard before exposing advanced arbitrary weighting.

### Portfolio And Risk Tools

Observed pages:

- `/retorno-historico/`: portfolio historical return with period, assets, weights, long/short allocation.
- `/beta-da-carteira/`: portfolio beta calculator with long/short portfolio inputs.
- `/value-at-risk/`: portfolio VaR with confidence and horizon framing.
- `/carteiras-quantitativas/`: automatic rebalanced factor portfolios, currently presented as Beta.
- `/portfolios/`: user-defined asset groups for quick reuse across tools.

Replication idea:

- This is the strongest bridge into the existing Investing Workbench `Investimentos` workflow.
- Treat user portfolios as reusable local entities that can feed historical return, beta, VaR, fixed-income comparisons, and future rebalancing studies.
- Add a shared portfolio request/response contract before adding each individual calculator UI.

### Backtests And Strategy Research

Observed pages:

- `/backtests/`: simulator with help text, strategy selection, asset selection, and score explanation.
- `/backtests/score/`: educational explanation of score, EV, drawdown, classification.
- `/backtests/radar/`: authenticated discovery/history/favorites surface.
- `/backtests/ranking/`: public and custom rankings by setup/strategy.
- `/backtests/alertas/`: WhatsApp alert workflow for strategy signals.
- `/estrategias/`: strategy catalog.
- `/estrategias/:slug/`: 44 strategy detail pages.

Strategy catalog observed:

- 123 compra/venda.
- Bandas de Bollinger abertura/reversao compra/venda.
- Breakout compra/venda.
- Canal de Donchian compra/venda.
- Candle Pavio compra/venda.
- Compra/venda por horario.
- Estocastico Lento compra/venda.
- Gap Trap compra/venda.
- HiLo Activator compra/venda.
- IFR and IFR2 compra.
- Inside Bar compra/venda.
- Maximas e minimas compra/venda.
- Preco de fechamento de reversao compra/venda.
- Saudade de casa compra/venda.
- Shark compra/venda.
- Supertrend compra/venda.
- Trap na media compra.
- Trap no candle compra/venda.
- Tres medias compra/venda.
- Turnaround compra.
- Variacao atipica compra/venda.
- Variacao intradiaria compra/venda.

Replication idea:

- Keep the local backtest engine as the source of truth; avoid copying QuantBrasil strategy text or formulas verbatim.
- Add a `StrategyCatalog` layer with stable metadata: name, direction, family, required candles, parameters, supported timeframes, and educational caveats.
- Add score explainers around EV, drawdown, profit factor, hit rate, trade count, and robustness instead of a single opaque score.

### Screenings

Observed landing pages and variants:

- `/ifr2/`: IFR, price, target, upside, moving-average direction.
- `/setup-123/` plus H1, H2, W1.
- `/estocastico-lento/` plus H1, H2, W1.
- `/candle-pavio/` plus W1.
- `/turnaround/`.
- `/trap/` plus H1, H2, W1.
- `/preco-de-fechamento-de-reversao/` plus D1, H1, H2, W1.
- `/bandas-de-bollinger/` plus H1, H2, W1.
- `/inside-bar/` plus H1, H2, W1.
- `/supertrend/` with B3, S&P 500, crypto and D1/H2/W1 variants.
- `/eden-dos-traders/` plus H1, H2, W1.
- `/indicadores/screening/`: authenticated custom technical indicator screening with logical rules.
- `/suportes-e-resistencias/screening/`: authenticated support/resistance proximity scanner.

Replication idea:

- Build a generic screener engine first: universe, timeframe, indicator values, predicates, ranking columns, and explanation metadata.
- Add prebuilt screeners as saved presets, not hard-coded pages.
- Keep beginner UX in `Investimentos` limited to a few didactic rankings; put dense signal tables in `Avancado`.

### Cointegration

Observed pages:

- `/cointegracao/`: pair test with FAQ and guidance.
- `/cointegracao/radar/`: authenticated radar with validity window, asset/sector filters, favorites.
- `/cointegracao/trades/`: authenticated trade tracker.

Observed API families:

- `/api/cointegration/${id}` for result fetch.
- `/api/cointegration/batch` for batch creation/update.
- `/api/cointegration/me` for user batches.
- `/api/cointegration/trade` and `/api/cointegration/trade?status=...` for trade tracking.
- `/api/metrics/cointegration`, sector, ticker, and favorite endpoints.

Replication idea:

- Treat cointegration as an advanced research workflow, not part of default investor onboarding.
- Add pair testing first, then radar/favorites, then trade tracking.
- Store methodology, p-value/z-score interpretation, lookback window, hedge ratio, residual behavior, and trade caveats with each result.

### Robots

Observed pages:

- `/robos/`: live/simulated robot list with aggregate robot-vs-IBOV table.
- `/robos/1/`: robot detail page with backtest link, follow flow, parameters, and card requirement.

Observed API families:

- `/api/automated/robot`.
- `/api/automated/robot/${id}`.
- `/api/automated/robot/${id}/follow`.
- `/api/automated/robot/${id}/returns`.
- `/api/automated/robot/${id}/trades`.

Replication idea:

- This should remain behind `Avancado` until the local engine has stable signal generation and audit logs.
- If implemented, frame robots as simulated research agents, not recommendations.

### Feed, Releases, And Education

Observed pages:

- `/feed/`: authenticated quantitative feed with Brazil/Crypto sections and releases.
- `/releases/` plus release detail pages.
- `/blog/` plus 40 article pages.
- `/youtube/` plus paginated video pages.
- `/code-capital/`.

Replication idea:

- The local app does not need a content CMS now.
- It should borrow the product pattern: every complex tool needs local explainers, FAQ sections, and "how to interpret" panels.
- The current Investing Workbench narrative panels are the right direction; expand them with methodology cards rather than marketing pages.

## API Surface

Endpoint families discovered:

- Activation/onboarding: `/api/activation-checklist`.
- Alerts: `/api/alert/...`.
- Auth/account: `/api/auth/...`.
- Automated robots: `/api/automated/robot...`.
- Backtests: `/api/backtest...`.
- Batch backtests: `/api/batch...`.
- Cointegration: `/api/cointegration...`.
- Public config: `/api/config/public`.
- Contact/feedback: `/api/contact...`.
- Feed: `/api/feed...`.
- Metrics: `/api/metrics/beta`, `/api/metrics/historical_return`, `/api/metrics/var`, `/api/metrics/supply_demand`, `/api/metrics/cointegration`.
- Notifications: `/api/notification...`.
- Payment/subscription: `/api/payment...`.
- Portfolio: `/api/portfolio...`.
- Screens: `/api/screen...`.
- Static BTC vs IBOV: `/api/static/btc_vs_ibov`.

Safe schema probes showed:

- `activation-checklist`: steps, completed count, next step, audience.
- `alert/user`: user alert list.
- `automated/robot`: robot metadata including ticker, timeframe, strategy, parameters, backtest id, status, following flag, recent trade profit list.
- `backtest/expiration`, `batch/expiration`, `cointegration/expiration`: expiration/limit metadata.
- `batch/me`, `cointegration/me`, `portfolio/`, `screen/`: user-owned collection lists.
- `notification/`: notification preference rows.
- `payment/subscription`: subscription status, premium flag, card/trial metadata.

Replication idea:

- Investing Workbench should not copy this API shape directly.
- Use it as a bounded-context map: onboarding, portfolio, metrics, screeners, backtests, cointegration, notifications.
- Keep route handlers thin and put behavior in `src/investing_workbench/application/*` services.

## Implementation Backlog For Investing Workbench

### Phase 1: Investor-First Tables

- Add market list services for ranking, drawdown, ATH distance, beta, and factor ranking.
- Create a reusable table schema: column label, metric key, tooltip, directionality, source freshness, formatting.
- Add didactic explanations for every metric.
- Start with B3 and current local data providers.

### Phase 2: Portfolio Core

- Create local portfolio entities with name, assets, weights, side, benchmark, and notes.
- Reuse portfolios across historical return, beta, VaR, and investment comparison studies.
- Add charts for cumulative return, drawdown, rolling volatility, benchmark-relative return.

### Phase 3: Screener Engine

- Build a generic indicator/predicate engine.
- Implement saved presets for IFR2, Momentum, Low Risk, Hurst, Drawdown, ATH distance, Bollinger, Supertrend.
- Add timeframe support only where the data source and cache are reliable.

### Phase 4: Backtest Research Layer

- Add a strategy catalog around existing backtest capabilities.
- Add score cards, robustness checks, trade count warnings, and explainers.
- Add radar/ranking only after backtest jobs are reproducible and cached.

### Phase 5: Cointegration And Advanced Labs

- Add pair test, sector/universe filtering, result history, and interpretation cards.
- Defer trade tracking until portfolio accounting and audit trails are in place.

### Phase 6: Account-Like Local Workflow

- Add local saved portfolios, saved screens, saved simulations, and notification preferences.
- Keep it local-first; do not add payments/subscriptions.

## Gaps And Risks

- Several sitemap asset URLs returned 404, mostly delisted or stale tickers such as `APER3`, `ATOM3`, `CCRO3`, `CIEL3`, `ELET3`, `ELET6`, `EMBR3`, `JBSS3`, `PETZ3`, and others. The local app should separate active, inactive, delisted, and aliased tickers.
- Some legacy `/app/*` links redirect to login even after the current Premium login path; they appear to be old URL shapes or app aliases.
- The `checkout/sucesso` route returns 404 without a session id, which is expected for a payment-return flow.
- `form_page_count` is inflated by global search, feedback, and repeated layout controls. Treat individual page controls as more meaningful than the raw count.
- Page content often includes educational material and examples. Reimplement concepts and workflows; do not copy article prose.
- Some API endpoints are POST-only calculators. The crawl only schema-probed safe GET endpoints, so calculator payloads still need manual design from our own domain model.

## Recommended Local Architecture

- `application/market_lists`: ranking, drawdown, ATH, beta, Hurst, BDR/IPOs, factor lists.
- `application/portfolios`: saved local portfolios, weights, benchmarks, portfolio analytics.
- `application/screeners`: generic rule engine plus preset screeners.
- `application/backtests`: strategy catalog, scoring, radar/ranking adapters.
- `application/cointegration`: pair tests, radar, result history.
- `infrastructure/data_providers`: B3/yfinance/CVM/fixed-income adapters with explicit cache ownership.
- `interfaces/api`: thin FastAPI endpoints that call application services.
- `frontend`: keep `Investimentos` simple; move screeners, backtest radar, cointegration, robots, and custom factor ranking into advanced areas.

## Most Valuable First Slice

The highest-leverage slice for the current repo is not robots or alerts. It is:

1. A reusable portfolio model.
2. Portfolio historical return, beta, and VaR calculators.
3. A factor/market list table system with transparent metric explanations.
4. A guided ranking/factor wizard for `Investimentos`.

That slice directly strengthens the local investor-facing workflow while laying groundwork for screeners and advanced research later.
