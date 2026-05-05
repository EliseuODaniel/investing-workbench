# API Reference

This document provides comprehensive information about the Investing Workbench REST API.

## Base URL

```
Development: http://localhost:8001
Production: https://your-domain.com/api
```

## Authentication

Currently, the API does not require authentication. This may be added in future versions.

## Content-Type

All API requests and responses use JSON format:
```
Content-Type: application/json
```

## Error Handling

The API uses standard HTTP status codes and returns error details in the response body:

```json
{
  "detail": "Error description message"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid input parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

## Endpoints

### 1. List Configurations

Retrieve all available configuration profiles with their associated strategies.

**Endpoint**
```
GET /configs
```

**Response**
```json
[
  {
    "name": "aggressive",
    "path": "configs/aggressive.yaml",
    "display_name": "aggressive",
    "strategies": [
      "Buy & Hold",
      "Aggressive DCA",
      "Breakout Trading",
      "Mean Reversion (Simple MA)",
      "Aggressive Fixed Martingale",
      "Risk-Cap Martingale"
    ]
  },
  {
    "name": "conservative",
    "path": "configs/conservative.yaml",
    "display_name": "conservative",
    "strategies": [
      "Buy & Hold",
      "Conservative DCA",
      "Trend Following (MA Cross)",
      "Mean Reversion (Bollinger Bands)",
      "Conservative Fixed Martingale",
      "ATR-Based Martingale"
    ]
  }
]
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Internal configuration name |
| `path` | string | File path to configuration |
| `display_name` | string | Human-readable name |
| `strategies` | array | List of strategy names in configuration |

**Example Request**
```bash
curl -X GET "http://localhost:8001/configs" \
     -H "Content-Type: application/json"
```

### 1A. Get System Status

**Endpoint**
```
GET /system/status
```

Returns a lightweight operational snapshot for the local platform, including discovered configs,
managed datasets, persisted artifact counts, and any top-level warnings that should be reviewed
before using the workspace.

**Response Highlights**

- `status`: `ok` when the basic local assets exist, `degraded` when core inputs are missing
- `config_count`: number of discovered YAML configs
- `dataset_count`: number of discovered local datasets
- `due_dataset_count`: number of datasets currently due for refresh according to their stored policy
- `artifact_counts`: persisted counts for runs, optimizations, walk-forward jobs, Monte Carlo jobs, saved workspaces, and persisted B3 pairs backtests
- `job_counts`: persisted counts for async backtest jobs grouped by queue/running/completed/failed/cancelled
- `job_runtime`: execution mode plus current worker-pool capacity and active futures for the async backtest executor
- `latest_run_id`: most recent persisted run id discovered through the experiment registry
- `latest_backtest_job_id`: most recent async backtest job id
- `latest_pairs_backtest_id`: most recent persisted B3 pairs backtest id
- `latest_research_workspace_id`: most recent saved research workspace id
- `warnings`: top-level issues such as missing configs, datasets, persisted runs, or failed async jobs

### 1K. B3 Pairs Trading Lab

The platform now exposes a dedicated B3 pairs-trading surface for long-short research driven by
cointegration, liquidity filters, and robustness batches.

**Endpoints**
```
GET  /pairs/universes
GET  /pairs/ibov-snapshots
GET  /pairs/ibov-snapshots/{as_of_date}
POST /pairs/ibov-snapshots/backfill
POST /pairs/universe/resolve
POST /pairs/screener
POST /pairs/backtests
POST /pairs/backtests/jobs
POST /pairs/backtests/jobs/batch
GET  /pairs/backtests/jobs
GET  /pairs/backtests/jobs/{job_id}
POST /pairs/backtests/jobs/{job_id}/cancel
POST /pairs/backtests/jobs/{job_id}/resume
GET  /pairs/backtests/jobs/{job_id}/response
POST /pairs/backtests/batch
GET  /pairs/backtests
GET  /pairs/backtests/{pairs_backtest_id}
GET  /pairs/backtests/{pairs_backtest_id}/results
```

**Highlights**

- `GET /pairs/universes`: returns curated B3 universe presets such as `ibov_proxy` plus the official `ibov_historical` preset backed by B3 BDI snapshots
- `GET /pairs/ibov-snapshots`: lists cached official IBOV snapshots already imported from B3
- `GET /pairs/ibov-snapshots/{as_of_date}`: returns one cached official IBOV snapshot by resolved date, including the parsed constituents
- `POST /pairs/ibov-snapshots/backfill`: imports and caches official IBOV snapshots around the B3 rebalance cadence for a requested date range
- `POST /pairs/universe/resolve`: resolves a preset or custom ticker list and returns coverage, liquidity, short-score, and eligibility diagnostics. The request also accepts `borrow_snapshot_path` for local borrow overrides. When `preset_id=ibov_historical`, the response also includes `resolved_as_of_date` and enriched preset metadata with `source_url`, `validity_label`, and `cache_status`
- `POST /pairs/screener`: ranks candidate pairs by p-value, return/level correlation, beta quality, half-life, a rolling stability score, and structural-break risk diagnostics. The request now also accepts `min_level_corr`, `min_stability_score`, `max_structural_break_risk`, `min_beta_abs`, and `max_beta_abs`, and the response includes `rejected_pairs` plus `rejection_summary` so clients can explain why candidates were filtered out
- `POST /pairs/backtests`: runs and persists one pairs-trading scenario. The request accepts portfolio controls such as `portfolio_construction`, `target_pair_volatility_annual`, `max_gross_exposure_pct`, `max_net_exposure_pct`, `max_sector_pairs`, and `borrow_snapshot_path`. When `preset_id=ibov_historical` and the date range spans later B3 review windows, the run reconstitutes the universe dynamically and persists the executed segment plan. Each scenario result now exposes `alpha_decomposition`, splitting trade PnL, cash carry, frictions, and benchmark gaps
- `POST /pairs/backtests/jobs`: queues the same pairs backtest request for asynchronous execution and returns a `PairsBacktestJobModel` manifest with queue status, progress, worker identity, and persisted event history
- `POST /pairs/backtests/jobs/batch`: queues a multi-scenario pairs batch for asynchronous execution
- `GET /pairs/backtests/jobs/{job_id}/response`: returns the completed persisted `PairsBacktestResults` payload linked to one async job after it reaches `completed`
- `POST /pairs/backtests/batch`: runs and persists a multi-scenario sensitivity batch, including realistic, low-friction, and no-cointegration-filter variants when no custom variants are supplied
- `GET /pairs/backtests`: lists persisted pairs-trading manifests
- `GET /pairs/backtests/{pairs_backtest_id}/results`: returns the full persisted result payload, including universe diagnostics, candidate pairs, benchmark curves, scenarios, and a robustness report

Operational notes:
- Official IBOV snapshots are fetched from B3 BDI PDFs and cached under `data/index_universes/ibov/`
- Curated universe presets now include smaller economic sleeves such as `banks_core`, `oil_gas_core`, `metals_core`, and `consumer_domestic_core` for tighter pair discovery workflows
- Borrow snapshot overrides expect a local CSV with a `ticker` column and optional `borrow_rate_annual`, `short_eligible`, and `margin_haircut` columns
- When `borrow_snapshot_path` is supplied, the file is copied into the managed dataset catalog as `data/pairs_borrow__*.csv`, gains provenance history, and the universe diagnostics keep both the original `borrow_snapshot_path` plus the governed `borrow_snapshot_managed_path` and `borrow_snapshot_dataset_id`
- If the requested `as_of_date` is a weekend or another date without a published BDI PDF, the resolver falls back to the nearest prior date within the built-in lookback window
- Official IBOV backtests can reconstitute the universe across later B3 review dates; the resolved segment plan is returned in `universe.reconstitution_plan`, and persisted manifests expose `reconstitution_segment_count`
- Async pairs jobs reuse the same detached execution mode flag as core backtests: when `BITCOIN_MARTINGALE_BACKTEST_JOB_EXECUTION_MODE=detached`, start `python -m src pairs-backtest-jobs-worker --poll-interval 1.0` to execute the queued jobs outside the API process

### 1L. WEGE3 Regra A Scenario

The API now exposes the dedicated WEGE3 price-grid scenario that is already wired to the
existing backtest engine and available in the frontend Labs area.

**Endpoint**
```
POST /scenarios/wege3-regra-a
```

**Request**
```json
{
  "start_date": "2021-01-01",
  "end_date": null,
  "force_download": false
}
```

**Response Highlights**

- `scenario_id`: always `wege3_regra_a`
- `dataset`: resolved session window, first open, last close, cache path, and Selic path
- `result`: final total, final cash, final position value, final shares, and final return
- `statistics`: counts of buys/sells, average price, realized/unrealized P&L, cash yield, and dividends
- `benchmarks`: benchmark A/B/C totals returned in the same payload
- `audit`: corporate actions summary and data sources
- `trades`: full audit trail of grid executions with `cash_after`, `position_after`, and `reference_after`
- `artifacts`: persisted `summary_output_path` and `trades_output_path`
- `reproduction_command`: exact CLI command used to reproduce the same scenario outside the UI

### 1B. List Local Datasets

### 1B. Investments Catalog

The platform now exposes a didactic B3 investment-comparison flow designed for beginner-friendly
questions such as “what would my money have become if I had used the same aporte plan in each
asset class?”.

**Endpoints**
```
GET  /investments/catalog
POST /investments/compare
POST /investments/product-data/refresh
```

**Highlights**

- `GET /investments/catalog`: returns the curated catalog used by the Investments workspace, grouped by families such as Brazilian stocks, ETFs, FIIs, international exposure via B3, and fixed-income proxies
- `GET /investments/catalog`: also returns beginner-friendly presets like `Primeiros passos`, `Balanceado B3`, `Renda e defensividade`, `Global pela B3`, and `Carteira 40+ (video)`
- `GET /investments/catalog`: includes `investor_easy_parity`, a local comparison with the public Investidor Facil offer, including feature coverage, plan equivalence, remaining gaps, and 15 educational calculators
- `GET /investments/catalog`: guided portfolios expose `components`, `rebalance_frequency`, `implementation_note`, and explanatory `notes` so the UI can show how the allocation was approximated
- `GET /investments/catalog`: includes `market_explorer` facets for category lists, product types, risk, region, and the first ranking backlog inspired by market-list workflows
- `GET /investments/catalog`: includes `product_data_plan` with source registry, local source manifest, catalog enrichment, FII identity map, FII-to-CVM bridge, CVM fund profile summary, initial CVM rankings, ETF/BDR profile and fee ranking, consolidated methodology-readiness ranking, release packages, market-filter backlog, and validation gates for post-roadmap product-data ingestion
- `POST /investments/product-data/refresh`: refreshes one controlled product-data source into `data/product_sources`; operational sources currently include `b3_fii_listed`, `cvm_fund_daily_reports`, and `b3_listed_products`. FIIs attempt the official B3 page, persist a CSV cache, `manifest.json`, and `refresh_history.jsonl`, and fall back to curated seed data when the source shape is not structured. The FII cache schema `b3_fii_listed.v2` also exposes approximate yield, liquidity, income focus, and data-quality fields used by Market Explorer filters and rankings. CVM fund daily reports attempt the official monthly ZIP and normalize quota, PL, subscriptions, redemptions, and holder-count fields before falling back. B3 listed products expose ETF/BDR product type, reference index, admin fee, exposure, and tracking notes through `b3_listed_products.v1`
- `POST /investments/compare`: compares the same initial capital and monthly contribution schedule across the selected assets
- `POST /investments/compare`: returns ranked results, benchmark curves, class summaries, and simple highlights such as how many chosen assets beat SELIC or BOVA11
- `POST /investments/compare`: accepts `decision_profile` so explanations can be ranked by objective, horizon, liquidity need, mark-to-market tolerance, tax view, and income target without changing the historical simulation
- `POST /investments/compare`: returns `methodology_guide`, `product_realism`, `retail_fixed_income_equivalence`, `result_stories`, `market_rankings`, `market_screeners`, `cache_status`, `fixed_income_decision_guide`, `portfolio_objective_summary`, and `portfolio_lifecycle` for didactic interpretation, investable-product caveats, retail fixed-income equivalence, guided result stories, QuantBrasil-inspired rankings/screeners, data-cache observability, and scenario cards
- `POST /investments/market-rankings`: builds a compact market-explorer snapshot from a preset or explicit asset list, returning `market_rankings`, `market_screeners`, `cache_status`, and warnings without the full comparison payload
- `GET /investments/workspaces/portfolios` and `POST /investments/workspaces/portfolios`: list and save reusable custom portfolios for the Investments workspace
- `DELETE /investments/workspaces/portfolios/{portfolio_id}`: removes one saved custom portfolio
- `GET /investments/workspaces/pairs-radar` and `POST /investments/workspaces/pairs-radar`: list and save Pairs radar favorites for reusable cointegration/backtest research
- `DELETE /investments/workspaces/pairs-radar/{pairs_backtest_id}`: removes one saved Pairs radar favorite
- `GET /investments/workspaces/strategy-radar` and `POST /investments/workspaces/strategy-radar`: list, save, and update strategy setup favorites from the `Simular` catalog, including `parameter_values`, `universe`, `timeframe`, and setup notes when available
- `DELETE /investments/workspaces/strategy-radar/{strategy_id}`: removes one saved strategy setup favorite
- `GET /investments/workspaces/strategy-setup-runs` and `POST /investments/workspaces/strategy-setup-runs`: list and persist execution summaries for saved `Simular` setups, including run id or `pairs_backtest_id`, strategy/scenario count, return, drawdown, and route hint
- `GET /investments/workspaces/strategy-setup-scores`: returns the first backend-ranked setup score, using latest persisted run history and the explicit `score = total_return * 100 - abs(max_drawdown) * 50 + min(trade_count, 20) * 0.25 + min(run_count, 5) * 0.5 + data_validity_score` methodology, plus component fields for return, drawdown penalty, execution score, robustness score, data-validity score, route, run id, and Pairs backtest id
- Market assets use adjusted close to approximate total return, while `SELIC_PROXY` compounds by daily SELIC rate as a didactic cash / Tesouro Selic reference

**Example Request**
```json
{
  "asset_ids": ["SELIC_PROXY", "BOVA11", "IVVB11", "HGLG11"],
  "start_date": "2021-01-01",
  "end_date": "2026-04-21",
  "initial_capital": 10000,
  "monthly_contribution": 500,
  "benchmark_ids": ["selic_cash", "bova11"],
  "decision_profile": {
    "objective": "retirement",
    "horizon_years": 12,
    "liquidity_need": "long_term",
    "mark_to_market_tolerance": "medium",
    "tax_view": "net",
    "monthly_income_target": 3000
  },
  "force_download": false
}
```

**Example Response Highlights**

- `results[*]`: invested total, final value, net profit, CAGR, volatility, max drawdown, and availability window for each selected investment
- `benchmarks[*]`: the same summary plus serialized equity curves for comparison references
- `chart`: rendered series metadata plus aligned points for the frontend chart
- `class_summary`: average performance by asset family
- `highlights`: best final value, most defensive asset, and plain-language insights
- `methodology_guide`: evidence types, assumptions, caveats, decision-profile notes, and realism notes
- `product_realism`: explicit coverage of tax, IOF, fees/spreads, liquidity, mark-to-market, income/reinvestment, product investability, and the next methodology gaps
- `retail_fixed_income_equivalence`: first practical CDB versus LCI/LCA/debenture incentivada after-tax equivalence table using IR regressivo, IOF for short redemptions, the profile horizon, and a reference CDI assumption
- `result_stories`: guided readings and first rankings for questions such as who beat SELIC, who fell less, who protected better against inflation, and who led by final value or real return
- `market_rankings`: exportable rankings for period return, real return, drawdown, volatility, momentum, distance from peak, beta to benchmark, and a guided factor score over the selected universe, with methodology notes, benchmark context, source label, and caveats
- `market_screeners`: reusable screener presets for the current universe, including positive real return, low drawdown, low volatility, and income candidates, with rule summaries and matched rows
- `cache_status`: local cache readiness for listed assets, fixed-income indexes, and Tesouro Direto, including cold-start notes, latest file name, approximate cache age, freshness labels, refresh hints, and which groups were used by the current result
- `fixed_income_decision_guide`: profile-scored fixed-income cards when the comparison includes fixed income
- `portfolio_objective_summary`: objective-ranked winners, portfolio rows, and scenario cards for income, retirement, preservation, and accumulation
- `portfolio_lifecycle`: retirement, withdrawal, pre-retirement, accumulation, and portfolio-versus-single-asset scenario cards
- `warnings`: explains excluded assets or incomplete history when the requested window is not fair for all instruments

### 1C. List Local Datasets

**Endpoint**
```
GET /datasets
```

Returns discovered local datasets from the `data/` directory, including parquet caches, benchmark files, and CSV rate files.
Each summary now includes `refresh_due` and `next_refresh_due_at` when a supported dataset has a persisted refresh policy.

### 1D. Inspect Local Dataset

**Endpoint**
```
GET /datasets/{dataset_id}
```

Returns detailed dataset metadata, preview rows, validation warnings, and the dataset fingerprint.
The detail payload also includes validation metrics plus provenance and event history when available.
When supported, provenance also includes the current refresh policy and whether the dataset is due right now.

### 1D. Import Local Dataset

**Endpoint**
```
POST /datasets/import
```

Imports a local CSV or Parquet file into the managed `data/` directory.

### 1E. List Due Dataset Refreshes

**Endpoint**
```
GET /datasets/refresh-due
```

Returns the subset of datasets whose persisted refresh policy is currently due.

### 1F. Execute Due Dataset Refreshes

**Endpoint**
```
POST /datasets/refresh-due
```

Refreshes due datasets in batch. The request body may include an optional `limit`.

### 1G. Persist Dataset Refresh Policy

**Endpoint**
```
POST /datasets/{dataset_id}/refresh-policy
```

Stores the refresh policy used to determine when a dataset becomes due. The request body includes:
- `enabled`
- `interval_days`
- `start_date`
- `end_date` (optional)

### 1H. Refresh Supported Dataset

**Endpoint**
```
POST /datasets/{dataset_id}/refresh
```


Refreshes a supported cached market or benchmark dataset in place. Static imports remain inspectable but may not support refresh.

### 1I. Build Rebalance Plan

**Endpoint**
```
POST /allocations/rebalance-plan
```

Builds a rebalance plan from current cash, holdings, market prices, and target portfolio weights.

**Request Body**

```json
{
  "cash": 2000,
  "holdings": [
    {"asset": "BTC-BRL", "quantity": 0.05},
    {"asset": "ETH-USD", "quantity": 2.0}
  ],
  "prices": {
    "BTC-BRL": 60000,
    "ETH-USD": 2000,
    "SPY": 900
  },
  "targets": [
    {"asset": "BTC-BRL", "target_weight": 0.5},
    {"asset": "ETH-USD", "target_weight": 0.2},
    {"asset": "SPY", "target_weight": 0.1}
  ],
  "weight_tolerance": 0.01,
  "min_trade_notional": 100,
  "reserve_cash": 1000
}
```

**Response Highlights**

- `actions`: per-asset `buy`, `sell`, or `hold` recommendations
- `target_cash`: implied post-rebalance cash based on the target weights
- `projected_cash`: cash expected after applying the executable trades
- `cash_gap_to_target`: difference between projected and ideal cash after thresholds
- `warnings`: allocation or cash-reserve warnings that should be reviewed before execution

### 1J. Persist Allocation Workspaces

**Endpoints**
```
GET /allocations/workspaces
POST /allocations/workspaces
GET /allocations/workspaces/{workspace_id}
PATCH /allocations/workspaces/{workspace_id}
POST /allocations/workspaces/import
DELETE /allocations/workspaces/{workspace_id}
```

Persists a normalized rebalance request together with its computed plan, summary metrics, and optional notes.
The saved payload is designed for reopening the same portfolio draft in the frontend `Alocacao` workspace or exporting/importing it as JSON.

### 2. Run Backtest

Execute backtest with specified parameters and strategies.

### 2.0 Strategy Catalog

**Endpoint**
```
GET /backtests/strategy-catalog
POST /backtests/strategy-setup-plan
```

Returns the first explainable strategy catalog for the `Simular` workspace:

- `strategies`: strategy id, label, family, direction, required inputs, supported timeframe, and risk notes
- `score_dimensions`: EV, drawdown, robustness, and execution-quality dimensions that will feed the score/radar flow
- `radar_plan`: planned local favorites, explainable ranking, and result-validity metadata

`POST /backtests/strategy-setup-plan` accepts one saved strategy radar item and returns a
reviewable execution plan with `route_hint`, `readiness`, a draft `run_request`, assumptions,
warnings, and next actions. It prepares the future run/compare flow without treating the saved
setup as an investment recommendation. In the frontend, plans with `route_hint=/backtest` and
`route_hint=/pairs/backtests` can now be executed directly from the `Simular` setup radar. Pairs
setups still keep the separate handoff into the dedicated lab for deeper inspection. Executed setup runs are persisted through
`/investments/workspaces/strategy-setup-runs` and mirrored in browser storage as a fallback, so the
user can compare recent run ids, Pairs backtest ids, trade counts, and basic metrics. The backend also exposes the first setup score
endpoint from latest setup history using a simple return-minus-drawdown-plus-execution methodology, explicitly as
an interim explanation layer rather than a recommendation. From each persisted setup run, the
frontend can reopen `GET /runs/{run_id}/response` and display a compact per-strategy result summary
inside the setup radar; Pairs executions can likewise reopen `GET /pairs/backtests/{pairs_backtest_id}/results`
for a compact per-scenario result summary. Setups with `route_hint=/pairs/backtests` can be handed off from the
`Simular` radar to the Pairs lab through a browser-persisted draft containing tickers, formation
window, entry/exit z-scores, and stop z-score; the app also switches directly to `Avancado > Pairs
B3` when that handoff is triggered. The frontend can export the executed setup ranking as CSV with
score components, run ids, Pairs backtest ids, route hints, and methodology.

**Endpoint**
```
POST /backtest
```

Runs the backtest synchronously and immediately returns the persisted response payload.

**Request Body**

```json
{
  "config_path": "configs/aggressive.yaml",
  "strategies": ["Risk-Cap Martingale"],
  "start_date": "2020-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 30000,
  "base_bet": 500,
  "multiplier": 2.0,
  "drop_step": 0.10,
  "take_profit": 0.15,
  "max_layers": 10,
  "force_download": false
}
```

**Request Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `config_path` | string | No | null | Path to configuration file |
| `strategies` | array | No | null | Specific strategies to run |
| `start_date` | string | No | null | Start date (YYYY-MM-DD) |
| `end_date` | string | No | null | End date (YYYY-MM-DD) |
| `initial_capital` | number | No | 30000 | Initial capital amount |
| `data_source` | string | No | null | Logical dataset label used in manifests |
| `cache_path` | string | No | null | Local dataset path to use for this run |
| `base_bet` | number | No | null | Base bet amount for Martingale |
| `multiplier` | number | No | null | Position size multiplier |
| `drop_step` | number | No | null | Price drop step percentage |
| `take_profit` | number | No | null | Take profit percentage |
| `max_layers` | integer | No | null | Maximum number of layers |
| `force_download` | boolean | No | false | Force data re-download |
| `fee_rate` | number | No | null | Percentage fee applied per trade |
| `fixed_fee` | number | No | null | Fixed fee applied per order |
| `buy_slippage` | number | No | null | Positive slippage applied to buys |
| `sell_slippage` | number | No | null | Negative slippage applied to sells |
| `max_volume_participation` | number | No | null | Share of bar volume that may be consumed |
| `allow_partial_fills` | boolean | No | null | Allow partial fills under liquidity constraints |
| `min_fill_quantity` | number | No | null | Minimum quantity required for a valid partial fill |

**Response**

```json
{
  "run_info": {
    "run_id": "run_20260323T120000Z_ab12cd34",
    "artifact_dir": "runs/run_20260323T120000Z_ab12cd34",
    "manifest_path": "runs/run_20260323T120000Z_ab12cd34/manifest.json",
    "response_path": "runs/run_20260323T120000Z_ab12cd34/response.json"
  },
  "results": {
    "Risk-Cap Martingale": {
      "strategy_name": "Risk-Cap Martingale",
      "metrics": {
        "total_return": 0.1542,
        "cagr": 0.0523,
        "sharpe_ratio": 0.8234,
        "sortino_ratio": 0.9876,
        "max_drawdown": -0.2341,
        "hit_rate": 0.8543,
        "profit_factor": 2.1456,
        "total_trades": 142,
        "avg_trade_pnl": 156.78,
        "volatility": 0.1256,
        "mar_ratio": 0.2234
      },
      "equity": [
        {
          "timestamp": "2020-01-01T00:00:00",
          "equity": 30000.0,
          "cash": 30000.0
        },
        {
          "timestamp": "2020-01-02T00:00:00",
          "equity": 29850.0,
          "cash": 29400.0
        }
      ],
      "trades": [
        {
          "timestamp": "2020-01-01T00:00:00",
          "action": "BUY",
          "price": 35000.0,
          "quantity": 0.014285714285714286,
          "pnl": null,
          "layer": 0
        },
        {
          "timestamp": "2020-01-15T00:00:00",
          "action": "SELL",
          "price": 40000.0,
          "quantity": 0.014285714285714286,
          "pnl": 71.42857142857143,
          "layer": 0
        }
      ]
    }
  },
  "buy_hold_equity": [
    {
      "timestamp": "2020-01-01T00:00:00",
      "equity": 30000.0,
      "cash": 0.0
    }
  ],
  "data_info": {
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "total_days": 1456,
    "data_source": "BTC-BRL",
    "cache_used": true
  }
}
```

### 2A. Queue Async Backtest Job

**Endpoints**
```
POST /backtest/jobs
GET /backtest/jobs
GET /backtest/jobs/{job_id}
POST /backtest/jobs/{job_id}/cancel
POST /backtest/jobs/{job_id}/resume
GET /backtest/jobs/{job_id}/response
```

Queues the same backtest payload for background execution. The job manifest exposes:

- `status`: `queued`, `running`, `completed`, `failed`, or `cancelled`
- `progress`: current phase, message, percent complete, and optional step counters
- `attempt_count`: incremented each time a cancelled or failed job is resumed
- `worker_id`: last worker identity that claimed the job for execution
- `run_id`: populated when the job completes and its persisted run is available
- `events`: compact execution timeline for operational inspection

Queued or running jobs left behind by a process restart are recovered automatically on startup and
re-queued with an incremented `attempt_count`.

When `BITCOIN_MARTINGALE_BACKTEST_JOB_EXECUTION_MODE=detached`, the API only persists queued jobs.
Run `python -m src backtest-jobs-worker --poll-interval 1.0` in a separate process to execute them.

`GET /backtest/jobs/{job_id}/response` returns the same `BacktestResponse` contract as `POST /backtest`
after the job reaches `completed`.

#### Run Information

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique persisted run identifier |
| `artifact_dir` | string | Directory containing the run artifacts |
| `manifest_path` | string | Path to the persisted `manifest.json` |
| `response_path` | string | Path to the persisted `response.json` |

**Response Fields**

#### Strategy Result

| Field | Type | Description |
|-------|------|-------------|
| `strategy_name` | string | Name of the strategy |
| `metrics` | object | Performance metrics |
| `equity` | array | Equity curve data points |
| `trades` | array | Trade execution records |

#### Performance Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `total_return` | number | Total return as decimal (0.1542 = 15.42%) |
| `cagr` | number | Compound Annual Growth Rate |
| `sharpe_ratio` | number | Risk-adjusted return ratio |
| `sortino_ratio` | number | Downside risk-adjusted return ratio |
| `max_drawdown` | number | Maximum drawdown as negative decimal |
| `hit_rate` | number | Percentage of profitable trades |
| `profit_factor` | number | Total profit / total loss |
| `total_trades` | integer | Number of executed trades |
| `avg_trade_pnl` | number | Average profit/loss per trade |
| `volatility` | number | Annualized volatility |
| `mar_ratio` | number | CAGR / Maximum Drawdown |

#### Equity Point

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp |
| `equity` | number | Total portfolio value |
| `cash` | number | Available cash balance |

#### Trade Record

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp |
| `action` | string | "BUY" or "SELL" |
| `price` | number | Execution price |
| `quantity` | number | BTC quantity |
| `pnl` | number | Profit/loss (null for BUY trades) |
| `layer` | integer | Martingale layer ID (null for non-Martingale) |

#### Data Information

| Field | Type | Description |
|-------|------|-------------|
| `start_date` | string | Data start date |
| `end_date` | string | Data end date |
| `total_days` | integer | Number of price rows used |
| `initial_price` | number | First closing price in the dataset |
| `final_price` | number | Final closing price in the dataset |

### 3. Get Persisted Run Manifest

**Endpoint**
```
GET /runs/{run_id}
```

Returns the persisted `manifest.json` for a previously executed run.

### 4. Get Persisted Run Response

**Endpoint**
```
GET /runs/{run_id}/response
```

Returns the persisted `response.json` payload for a previously executed run.

### 5. Get Persisted Run Config Snapshot

**Endpoint**
```
GET /runs/{run_id}/config
```

Returns the resolved config used during the run, including any request overrides.

### 6. Get Persisted Run Data Profile

**Endpoint**
```
GET /runs/{run_id}/data-profile
```

Returns the dataset profile with columns, row count, timestamps, cache path, and `data_fingerprint`.

### 7. Download Persisted Run HTML Report

**Endpoint**
```
GET /runs/{run_id}/report.html
```

Downloads a persisted HTML report generated from the run manifest, metrics, config snapshot, and data profile.

### 8. List Persisted Runs

**Endpoint**
```
GET /runs
```

Returns persisted manifests ordered from newest to oldest.

**Example Request**
```bash
curl -X POST "http://localhost:8001/backtest" \
     -H "Content-Type: application/json" \
     -d '{
       "config_path": "configs/aggressive.yaml",
       "strategies": ["Risk-Cap Martingale"],
       "initial_capital": 30000
     }'
```

### 9. Export Trades From a Persisted Run

Download trade data for a specific strategy from a persisted run.

**Endpoint**
```
GET /runs/{run_id}/strategies/{strategy_name}/trades.csv
```

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string | Persisted run identifier |
| `strategy_name` | string | URL-encoded strategy name |

**Response**
```
CSV file with trade data
```

**Example Request**
```bash
curl -X GET "http://localhost:8001/runs/run_20260323T120000Z_abcd1234/strategies/Risk-Cap%20Martingale/trades.csv" \
     -o trades.csv
```

### 10. Export Latest Persisted Trades For a Strategy

**Endpoint**
```
GET /reports/{strategy}/download
```

Downloads a CSV for the newest persisted run that contains the requested strategy.

### 11. Preview Optimization Plan

**Endpoint**
```
POST /optimizations/plan
```

Builds a deterministic optimization trial plan without executing runs.

### 12. Execute Optimization Job

**Endpoint**
```
POST /optimizations
```

Executes and persists an optimization job, including ranked trial results and linked run ids.

### 13. List Persisted Optimizations

**Endpoint**
```
GET /optimizations
```

Returns persisted optimization manifests ordered from newest to oldest.

### 14. Get Persisted Optimization Manifest

**Endpoint**
```
GET /optimizations/{optimization_id}
```

Returns summary metadata for a persisted optimization job.

### 15. Get Persisted Optimization Results

**Endpoint**
```
GET /optimizations/{optimization_id}/results
```

Returns ranked trial results, linked persisted run ids, warnings, and objective values.

### 16. Execute Walk-Forward Validation

**Endpoint**
```
POST /walkforward
```

Executes persisted walk-forward validation with rolling train and test windows.

### 17. List Persisted Walk-Forward Validations

**Endpoint**
```
GET /walkforward
```

Returns persisted walk-forward manifests ordered from newest to oldest.

### 18. Get Persisted Walk-Forward Manifest

**Endpoint**
```
GET /walkforward/{walkforward_id}
```

Returns summary metadata and aggregated strategy summaries for a persisted validation.

### 19. Get Persisted Walk-Forward Results

**Endpoint**
```
GET /walkforward/{walkforward_id}/results
```

Returns all window-level train and test metrics for a persisted walk-forward execution.

### 20. Execute Monte Carlo Robustness Analysis

**Endpoint**
```
POST /montecarlo
```

Executes and persists Monte Carlo robustness analysis using either a fresh config-driven run or an existing `run_id`.

### 21. List Persisted Monte Carlo Analyses

**Endpoint**
```
GET /montecarlo
```

Returns persisted Monte Carlo manifests ordered from newest to oldest.

### 22. Get Persisted Monte Carlo Manifest

**Endpoint**
```
GET /montecarlo/{montecarlo_id}
```

Returns summary metadata, linked source run id, and per-strategy robustness summaries.

### 23. Get Persisted Monte Carlo Results

**Endpoint**
```
GET /montecarlo/{montecarlo_id}/results
```

Returns simulation-level robustness results, percentile summaries, and warning flags.

## Data Models

### BacktestRequest

```typescript
interface BacktestRequest {
  config_path?: string;
  strategies?: string[];
  start_date?: string;        // Format: YYYY-MM-DD
  end_date?: string;          // Format: YYYY-MM-DD
  initial_capital?: number;   // Range: 1000 - 1000000
  base_bet?: number;          // Range: 100 - 5000
  multiplier?: number;        // Range: 1.5 - 3.0
  drop_step?: number;         // Range: 0.05 - 0.20 (5% - 20%)
  take_profit?: number;       // Range: 0.10 - 0.30 (10% - 30%)
  max_layers?: number;        // Range: 3 - 20
  data_source?: string;
  cache_path?: string;
  force_download?: boolean;
  apply_cash_yield?: boolean;
  selic_rate_annual?: number;
  use_real_selic?: boolean;
  selic_path?: string;
  selic_fallback_rate?: number;
  fee_rate?: number;                  // Percentage fee per trade
  fixed_fee?: number;                 // Fixed fee per order
  buy_slippage?: number;              // Buy-side slippage
  sell_slippage?: number;             // Sell-side slippage
  max_volume_participation?: number;  // Share of bar volume available to the strategy
  allow_partial_fills?: boolean;
  min_fill_quantity?: number;
  benchmarks?: string[];
  include_selic_benchmark?: boolean;
  include_buy_hold_benchmark?: boolean;
}
```

### BacktestJob

```typescript
interface BacktestJob {
  job_id: string;
  job_type: "backtest";
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  attempt_count: number;
  cancel_requested: boolean;
  request_payload: Record<string, unknown>;
  config_path?: string | null;
  strategy_names: string[];
  progress: {
    phase: string;
    message: string;
    percent: number;
    updated_at: string;
    current_step?: number | null;
    total_steps?: number | null;
  };
  run_id?: string | null;
  result_available: boolean;
  error?: string | null;
  events: Array<{
    timestamp: string;
    level: string;
    phase: string;
    message: string;
    percent?: number | null;
  }>;
}
```

### ConfigInfo

```typescript
interface ConfigInfo {
  name: string;
  path: string;
  display_name: string;
  strategies: string[];
}
```

### StrategyResult

```typescript
interface StrategyResult {
  strategy_name: string;
  metrics: StrategyMetrics;
  equity: EquityPoint[];
  trades: Trade[];
  execution_log: ExecutionEvent[];
  execution_summary: ExecutionSummary;
  warnings: string[];
}
```

### StrategyMetrics

```typescript
interface StrategyMetrics {
  total_return: number;        // Decimal (0.1542 = 15.42%)
  cagr: number;               // Annual growth rate
  sharpe_ratio: number;       // Risk-adjusted return
  sortino_ratio: number;      // Downside risk-adjusted return
  max_drawdown: number;       // Negative decimal (-0.2341 = -23.41%)
  hit_rate: number;           // Percentage (0.8543 = 85.43%)
  profit_factor: number;      // Profit/Loss ratio
  total_trades: number;       // Number of trades
  avg_trade_pnl: number;      // Average P&L per trade
  volatility: number;         // Annualized volatility
  total_interest_earned: number;
  total_fees_paid: number;
  total_dividends_received: number;
  selic_rates_used?: Array<{ period?: string; year?: number; month?: number; rate: number }>;
}
```

### MonteCarloRequest

```typescript
interface MonteCarloRequest {
  config_path?: string;          // Mutually exclusive with run_id
  run_id?: string;               // Mutually exclusive with config_path
  strategies?: string[];
  simulation_count?: number;     // Default: 500
  random_seed?: number;          // Default: 42
  method?: "bootstrap" | "shuffle";
  ruin_threshold_pct?: number;   // Default: 0.30
}
```

### EquityPoint

```typescript
interface EquityPoint {
  timestamp: string;          // ISO 8601 format
  equity: number;             // Portfolio value
  cash: number;               // Available cash
}
```

### Trade

```typescript
interface Trade {
  timestamp: string;          // ISO 8601 format
  action: "BUY" | "SELL";     // Trade action
  price: number;              // Execution price
  quantity: number;           // BTC quantity
  cost?: number;              // Trade cost basis
  pnl?: number;               // Profit/loss (null for BUY)
  layer?: number;             // Martingale layer (null if not applicable)
  requested_quantity?: number;
  fill_ratio?: number;
}
```

### ExecutionEvent

```typescript
interface ExecutionEvent {
  timestamp: string;
  event_type: string;         // fill | partial_fill | buy_rejected | sell_rejected
  side: string;               // buy | sell
  requested_quantity: number;
  filled_quantity: number;
  fill_ratio: number;
  requested_price: number;
  fill_price?: number | null;
  fees: number;
  slippage: number;
  message: string;
}
```

### ExecutionSummary

```typescript
interface ExecutionSummary {
  fill_count: number;
  partial_fill_count: number;
  rejected_buy_count: number;
  rejected_sell_count: number;
  rejected_order_count: number;
  liquidity_constrained: boolean;
  requested_quantity_total: number;
  filled_quantity_total: number;
}
```

## Usage Examples

### JavaScript/TypeScript

```typescript
import axios from 'axios';

class BacktestAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8001') {
    this.baseURL = baseURL;
  }

  async getConfigs(): Promise<ConfigInfo[]> {
    const response = await axios.get(`${this.baseURL}/configs`);
    return response.data;
  }

  async runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
    const response = await axios.post(`${this.baseURL}/backtest`, request);
    return response.data;
  }

  async downloadTrades(strategyName: string): Promise<Blob> {
    const response = await axios.get(
      `${this.baseURL}/reports/${encodeURIComponent(strategyName)}/download`,
      { responseType: 'blob' }
    );
    return response.data;
  }
}

// Usage example
const api = new BacktestAPI();

// Get configurations
const configs = await api.getConfigs();
console.log('Available configs:', configs);

// Run backtest
const request: BacktestRequest = {
  config_path: 'configs/aggressive.yaml',
  strategies: ['Risk-Cap Martingale'],
  initial_capital: 30000,
  start_date: '2020-01-01',
  end_date: '2023-12-31',
  fee_rate: 0.0003,
  buy_slippage: 0.0005,
  sell_slippage: 0.0005,
  max_volume_participation: 0.10,
  allow_partial_fills: true,
};

const results = await api.runBacktest(request);
console.log('Backtest results:', results);

// Download trades
const tradesBlob = await api.downloadTrades('Risk-Cap Martingale');
const url = URL.createObjectURL(tradesBlob);
const a = document.createElement('a');
a.href = url;
a.download = 'trades.csv';
a.click();
```

### Python

```python
import requests
import json

class BacktestAPI:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_configs(self) -> list:
        """Get available configuration profiles"""
        response = self.session.get(f"{self.base_url}/configs")
        response.raise_for_status()
        return response.json()

    def run_backtest(self, request: dict) -> dict:
        """Run backtest with specified parameters"""
        response = self.session.post(
            f"{self.base_url}/backtest",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def download_trades(self, strategy_name: str, filename: str = None) -> str:
        """Download trades for a strategy"""
        if not filename:
            filename = f"{strategy_name}_trades.csv"

        response = self.session.get(
            f"{self.base_url}/reports/{strategy_name}/download"
        )
        response.raise_for_status()

        with open(filename, 'wb') as f:
            f.write(response.content)

        return filename

# Usage example
api = BacktestAPI()

# Get configurations
configs = api.get_configs()
print("Available configs:", configs)

# Run backtest
request = {
    "config_path": "configs/aggressive.yaml",
    "strategies": ["Risk-Cap Martingale"],
    "initial_capital": 30000,
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "fee_rate": 0.0003,
    "buy_slippage": 0.0005,
    "sell_slippage": 0.0005,
    "max_volume_participation": 0.10,
    "allow_partial_fills": True,
}

results = api.run_backtest(request)
print("Backtest completed successfully!")

# Access metrics
strategy_results = results["results"]["Risk-Cap Martingale"]
metrics = strategy_results["metrics"]
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Hit Rate: {metrics['hit_rate']:.2%}")

# Download trades
trades_file = api.download_trades("Risk-Cap Martingale")
print(f"Trades saved to: {trades_file}")
```

### cURL

```bash
# Get configurations
curl -X GET "http://localhost:8001/configs" \
     -H "Content-Type: application/json"

# Run backtest
curl -X POST "http://localhost:8001/backtest" \
     -H "Content-Type: application/json" \
     -d '{
       "config_path": "configs/aggressive.yaml",
       "strategies": ["Risk-Cap Martingale", "Aggressive Fixed Martingale"],
       "initial_capital": 30000,
       "start_date": "2020-01-01",
       "end_date": "2023-12-31"
     }'

# Run backtest with custom parameters
curl -X POST "http://localhost:8001/backtest" \
     -H "Content-Type: application/json" \
     -d '{
       "strategies": ["Fixed Martingale"],
       "initial_capital": 50000,
       "base_bet": 1000,
       "multiplier": 2.5,
       "drop_step": 0.08,
       "take_profit": 0.12,
       "max_layers": 12
     }'
```

## Rate Limiting

Currently, there are no explicit rate limits. However, users should:

- Avoid excessive concurrent requests
- Use reasonable time ranges for backtests
- Consider caching results for repeated requests

## Data Sources

The API automatically handles Bitcoin price data from:

1. **Primary Source**: Yahoo Finance (BTC-BRL)
2. **Fallback Source**: Synthetic BTC-BRL built from Yahoo Finance `BTC-USD` and `USD/BRL`
3. **Cache**: Local Parquet files for performance, including a dedicated synthetic BTC-BRL cache when needed

Data includes daily OHLCV (Open, High, Low, Close, Volume) from 2020-01-01 to present.

## Response Time Estimates

Typical response times based on data range and number of strategies:

| Data Range | Strategies | Estimated Time |
|------------|------------|----------------|
| 1 year     | 1-3       | 2-5 seconds    |
| 3 years    | 1-3       | 5-15 seconds   |
| 5 years    | 1-3       | 10-30 seconds  |
| 5 years    | 4-6       | 20-60 seconds  |

## Error Scenarios

### Common Errors

**Invalid Configuration**
```json
{
  "detail": "Configuration file not found: configs/invalid.yaml"
}
```

**Invalid Date Range**
```json
{
  "detail": "Start date cannot be after end date"
}
```

**Invalid Parameters**
```json
{
  "detail": [
    {
      "loc": ["body", "initial_capital"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**Data Download Error**
```json
{
  "detail": "Failed to download data: Network timeout"
}
```

## SDK Examples

### React Hook

```typescript
import { useState, useEffect } from 'react';

export const useBacktest = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<BacktestResponse | null>(null);

  const runBacktest = async (request: BacktestRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8001/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Backtest failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    results,
    runBacktest,
  };
};

// Usage in component
const BacktestComponent = () => {
  const { loading, error, results, runBacktest } = useBacktest();

  const handleRunBacktest = () => {
    runBacktest({
      config_path: 'configs/aggressive.yaml',
      strategies: ['Risk-Cap Martingale'],
      initial_capital: 30000,
    });
  };

  return (
    <div>
      <button onClick={handleRunBacktest} disabled={loading}>
        {loading ? 'Running...' : 'Run Backtest'}
      </button>

      {error && <div className="error">Error: {error}</div>}

      {results && (
        <div>
          <h3>Results</h3>
          {/* Render results */}
        </div>
      )}
    </div>
  );
};
```

This API reference provides comprehensive information for integrating with Investing Workbench. All examples are production-ready and follow best practices for error handling and type safety.
