# Developer Guide

## Getting Started as a Developer

This guide provides comprehensive information for developers contributing to Investing Workbench.

## Development Environment Setup

### Prerequisites

- **Python 3.12+** with `uv`
- **Node.js 22.x** with npm
- **Git** for version control
- **IDE** (VS Code recommended with extensions)

### Initial Setup

1. **Clone the Repository**
```bash
git clone <repository-url>
cd investing-workbench
```

2. **Python Environment**
```bash
uv sync --extra dev
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Development Tools Setup**

**Pre-commit Hooks (Optional but Recommended)**
```bash
uv run pre-commit install
```

**VS Code Extensions**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

### Environment Configuration

The backend does not require a committed `.env.example` to run the standard local workflow.

**Frontend Environment (`frontend/.env`)**
```bash
# API configuration
VITE_API_BASE=http://localhost:8001
VITE_API_TIMEOUT=30000
```

## Code Organization

### Backend Structure

```
src/
├── __main__.py                 # `python -m src` entry point
├── api/                        # FastAPI entrypoint and API models
├── cli.py                      # Legacy-compatible CLI surface
├── strategies/                 # Current strategy implementations
└── investing_workbench/         # New application/domain/infrastructure layers
    ├── application/            # Use cases and orchestration
    ├── domain/                 # Domain models and engine logic
    ├── infrastructure/         # Persistence, logging, reporting
    └── interfaces/             # Current API/CLI adapters
```

### Frontend Structure

```
frontend/src/
├── components/                 # Main UI panels and workspaces
├── hooks/                      # Feature-facing React hooks
├── lib/                        # Utilities
├── types/                      # TypeScript definitions
├── App.tsx                     # Main application
├── main.tsx                    # Entry point
└── index.css                   # Global styles
```

## Development Workflow

### 1. Making Changes

**Backend Changes**
```bash
uv run pytest -q
uv run ruff check src/api src/investing_workbench tests
uv run python -m black --check src/api src/investing_workbench tests
uv run mypy src/investing_workbench
```

**Frontend Changes**
```bash
cd frontend

# Lint and tests
npm run lint
npm test -- --run

# Production build performs the TypeScript compile step
npm run build

# Run the full frontend validation sequence
npm run validate
```

The frontend `npm test` script now batches Vitest files sequentially so the canonical command
stays reliable in lower-memory local environments.
The supported runtime is pinned in `frontend/.nvmrc`, `frontend/.node-version`, and the
frontend `package.json` engines field.

**Convenience Make Targets**
```bash
make backend-test
make backend-lint
make backend-format
make backend-type
make frontend-lint
make frontend-test
make frontend-build
```

### Research Workspace Contracts

Recent product work added a shared research-workspace/report contract across backend, CLI, and frontend.

Backend/API:
```bash
GET    /experiments
GET    /experiments/{experiment_type}/{experiment_id}
GET    /research-workspaces
POST   /research-workspaces
GET    /research-workspaces/{workspace_id}
PATCH  /research-workspaces/{workspace_id}
POST   /research-workspaces/import
GET    /research-workspaces/{workspace_id}/report?format=json|markdown|html
```

CLI:
```bash
python -m src system-status --format text
python -m src experiments-list --limit 10
python -m src experiments-show --type run --id <experiment_id>
python -m src experiments-show --type pairs_backtest --id <experiment_id>
python -m src research-workspaces-list --limit 10
python -m src research-workspaces-show --workspace-id <workspace_id>
python -m src research-workspaces-export --workspace-id <workspace_id> --format markdown
```

Frontend:
- `ResearchOverviewPanel` consumes the experiment registry and lineage drilldown.
- `SavedResearchWorkspacesPanel` manages saved workspaces, imports/exports, and metadata edits.
- `Report View` now reads the same server-side workspace report contract used by the API and CLI.

### B3 Pairs Trading Contracts

Recent product work also added a dedicated B3 pairs-trading vertical slice across backend, CLI, and frontend.

Backend/API:
```bash
GET    /pairs/universes
GET    /pairs/ibov-snapshots
GET    /pairs/ibov-snapshots/{as_of_date}
POST   /pairs/ibov-snapshots/backfill
POST   /pairs/universe/resolve
POST   /pairs/screener
POST   /pairs/backtests
POST   /pairs/backtests/jobs
POST   /pairs/backtests/jobs/batch
GET    /pairs/backtests/jobs
GET    /pairs/backtests/jobs/{job_id}
POST   /pairs/backtests/jobs/{job_id}/cancel
POST   /pairs/backtests/jobs/{job_id}/resume
GET    /pairs/backtests/jobs/{job_id}/response
POST   /pairs/backtests/batch
GET    /pairs/backtests
GET    /pairs/backtests/{pairs_backtest_id}
GET    /pairs/backtests/{pairs_backtest_id}/results
```

CLI:
```bash
python -m src pairs-universes --format text
python -m src pairs-ibov-snapshots --format text
python -m src pairs-ibov-snapshot-show --as-of-date 2025-01-20
python -m src pairs-ibov-snapshots-backfill --start-date 2025-01-01 --end-date 2025-12-31
python -m src pairs-universe-resolve --preset ibov_proxy
python -m src pairs-universe-resolve --preset ibov_historical --as-of-date 2025-01-20
python -m src pairs-screen --preset ibov_proxy
python -m src pairs-backtest --preset ibov_proxy --portfolio-construction risk_parity --target-pair-volatility-annual 0.12
python -m src pairs-backtest-batch --preset ibov_proxy
python -m src pairs-backtest-job --preset ibov_proxy
python -m src pairs-backtest-job-batch --preset ibov_proxy
python -m src pairs-backtest-jobs-list --limit 10
python -m src pairs-backtest-jobs-show --job-id <job_id>
python -m src pairs-backtest-jobs-worker --once
python -m src pairs-backtests-list --limit 10
```

Frontend:
- `PairsTradingWorkspace` lives in the `Labs` section and exposes universe diagnostics, screener rankings, persisted history, a local radar of favorite studies, benchmark summaries, and robustness batches.
- The workspace is now decomposed into smaller `frontend/src/components/pairs/*` panels instead of concentrating the whole feature in one large component.
- `usePairsTrading` is the main hook for the feature and keeps the API contract typed through `frontend/src/types/api.ts`.
- The workspace now exposes an explicit `Snapshot Ibov` date field. For `ibov_historical`, leaving it blank uses `start_date` to avoid look-ahead and enriches the preset metadata with the resolved B3 source snapshot.
- The workspace also exposes optional borrow snapshot input plus portfolio construction controls for `risk_parity`, gross/net caps, and sector concentration caps.
- The screener controls now expose stability and robustness thresholds such as `min_level_corr`, `min_stability_score`, `max_structural_break_risk`, and beta bounds, and the UI surfaces `rejected_pairs` with rejection summaries for diagnostics.
- The batch summary now highlights `alpha_decomposition`, benchmark gaps, top/worst pairs, and robustness dispersion instead of only aggregate return cards.
- The controls card also includes a research batch builder that generates sensitivity scenarios across z-score thresholds, z-score windows, pair limits, dynamic beta, frictionless, and no-cointegration-filter variants through the same typed API contract.

Backend notes:
- Official IBOV constituents are imported on demand from B3 BDI PDFs through `B3IbovUniverseHistoryService`.
- Parsed snapshots are cached in `data/index_universes/ibov/<YYYY-MM-DD>.json`.
- Pairs backtests using `ibov_historical` reconstitute the universe across later official B3 review windows when the selected period spans multiple snapshots.
- The API and CLI expose explicit snapshot list/show/backfill tooling so the official cache can be inspected and preloaded before large research runs.
- Borrow overrides can be loaded from a local CSV with `ticker`, `borrow_rate_annual`, `short_eligible`, and `margin_haircut` columns when you need more realistic B3 short assumptions.
- Borrow snapshots passed through `borrow_snapshot_path` are copied into the governed dataset catalog through `DatasetCatalogService.register_pairs_borrow_snapshot`, so they keep provenance history and appear in Dataset Manager views like any other managed dataset.
- Universe diagnostics preserve the original `borrow_snapshot_path` for compatibility and also expose `borrow_snapshot_managed_path` plus `borrow_snapshot_dataset_id` so the governed copy can be audited explicitly.
- `PairsTradingService` now stays focused on orchestration and context building, while `benchmarks.py`, `execution.py`, and `reporting.py` own benchmark preparation, scenario execution, and scenario summaries respectively.
- Async pairs jobs are backed by `PairsBacktestJobService` and reuse the same detached execution-mode flag as core backtests. In detached mode, run `python -m src pairs-backtest-jobs-worker` in a separate process.
- Scenario payloads now surface blocked entries caused by portfolio caps and sector caps, plus portfolio construction metadata in `portfolio_summary`.
- The unified experiment registry now includes persisted pairs artifacts as `experiment_type=pairs_backtest`, so Research Overview and saved workspaces can link them through the same lineage surface used by runs, optimizations, walk-forward, and Monte Carlo workflows.

### 2. Adding New Features

**Feature Development Process**

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Implement Backend Logic**
```python
# Example: New Strategy
# src/strategies/my_strategy.py
from typing import Optional
from .base import MartingaleStrategy
from ..engine import BacktestEngine

class MyCustomStrategy(MartingaleStrategy):
    """Custom strategy implementation"""

    def __init__(self, custom_param: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.custom_param = custom_param
        self.custom_state = {}

    def on_bar(self, timestamp, data, engine) -> Optional[str]:
        """
        Process bar data and generate trading signal

        Args:
            timestamp: Current bar timestamp
            data: Bar data dict with OHLCV
            engine: BacktestEngine instance

        Returns:
            Trading signal: "BUY", "SELL", or None
        """
        # Your strategy logic here
        close_price = float(data['Close'])

        # Example: Simple moving average logic
        if not hasattr(self, 'previous_prices'):
            self.previous_prices = []

        self.previous_prices.append(close_price)
        if len(self.previous_prices) > 20:
            self.previous_prices.pop(0)

        if len(self.previous_prices) >= 10:
            short_ma = sum(self.previous_prices[-10:]) / 10
            long_ma = sum(self.previous_prices) / len(self.previous_prices)

            if short_ma > long_ma and not engine.state.layers:
                return "BUY"

        return None
```

3. **Add Strategy to Configuration**
```yaml
# configs/my_config.yaml
strategies:
  - name: "My Custom Strategy"
    class_path: "strategies.my_strategy.MyCustomStrategy"
    parameters:
      custom_param: 1.5
      base_bet: 500.0
      multiplier: 2.0
      drop_step: 0.10
      take_profit: 0.15
      max_layers: 8
      slippage: 0.0005    # 0.05% execution slippage per trade
```

#### Execution Cost and Liquidity Configuration

**Understanding Execution Realism in Strategy Development**

The framework now models execution with explicit costs and liquidity assumptions in `BacktestCoreEngine`:

- `fee_rate`: percentage fee applied to the executed notional
- `fixed_fee`: fixed cash fee per executed order
- `buy_slippage` and `sell_slippage`: per-side execution adjustments
- `max_volume_participation`: optional cap for how much of each bar volume can be traded
- `allow_partial_fills`: whether the engine can fill only the executable portion of an order
- `min_fill_quantity`: lower bound for a valid partial fill

```python
from src.investing_workbench.domain.backtest import BacktestCoreEngine

engine = BacktestCoreEngine(
    initial_cash=30_000.0,
    fee_rate=0.0003,
    fixed_fee=0.0,
    buy_slippage=0.0005,
    sell_slippage=0.0005,
    max_volume_participation=0.10,
    allow_partial_fills=True,
    min_fill_quantity=0.001,
)
```

**Default Reference Values**:
- **Conservative slippage**: 0.05% (0.0005) per side
- **Tight markets**: 0.01% (0.0001) per side
- **Volatile markets**: 0.1% - 0.5% (0.001 - 0.005) per side
- **Participation cap**: 5% - 15% of bar volume for daily-bar research

**Execution Semantics**:
```python
# BUY orders: execution_price = close_price * (1 + buy_slippage)
# SELL orders: execution_price = close_price * (1 - sell_slippage)
# fees = gross_value * fee_rate + fixed_fee
# if requested quantity exceeds available liquidity:
#   - partial fill when allow_partial_fills is enabled
#   - rejection when allow_partial_fills is disabled
```

Legacy strategy configs that expose a single `slippage` parameter can still map into the older strategy layer, but new engine-facing work should prefer the explicit cost and liquidity controls above.

**Signal Detection vs Execution**:
```python
def on_bar(self, timestamp, data, engine) -> Optional[str]:
    # Signal detection uses OHLC extremes
    buy_signal = data['Low'] <= self.target_buy_price
    sell_signal = data['High'] >= self.target_sell_price

    # Execution occurs at close price with configured costs/liquidity rules
    if buy_signal:
        return "BUY"  # Framework handles execution modeling
    elif sell_signal:
        return "SELL"  # Framework handles execution modeling
    return None
```

**Configuration Examples**:
```yaml
# Tight-market research profile
fee_rate: 0.0001
buy_slippage: 0.0001
sell_slippage: 0.0001
max_volume_participation: 0.15

# Conservative crypto profile
fee_rate: 0.0003
buy_slippage: 0.0005
sell_slippage: 0.0005
max_volume_participation: 0.10

# Lower-liquidity profile
fee_rate: 0.0010
buy_slippage: 0.0020
sell_slippage: 0.0020
max_volume_participation: 0.05
allow_partial_fills: true
```

Every run now records `total_fees_paid`, execution parameters, `execution_log`, `execution_summary`, and `warnings`, which makes it easier to inspect why an order filled, partially filled, or was rejected.

4. **Write Tests**
```python
# tests/test_my_strategy.py
import pytest
import pandas as pd
from src.strategies.my_strategy import MyCustomStrategy
from src.engine import BacktestEngine

@pytest.fixture
def sample_data():
    """Generate sample OHLCV data"""
    dates = pd.date_range('2020-01-01', periods=50, freq='D')
    return pd.DataFrame({
        'Open': [40000 + i * 100 for i in range(50)],
        'High': [40500 + i * 100 for i in range(50)],
        'Low': [39500 + i * 100 for i in range(50)],
        'Close': [40000 + i * 100 for i in range(50)],
        'Volume': [1000] * 50
    }, index=dates)

def test_my_strategy_initialization():
    """Test strategy initialization"""
    strategy = MyCustomStrategy(custom_param=1.5)
    assert strategy.custom_param == 1.5
    assert strategy.base_bet > 0

def test_my_strategy_signals(sample_data):
    """Test signal generation"""
    strategy = MyCustomStrategy(base_bet=500, multiplier=2.0,
                              drop_step=0.1, take_profit=0.15, max_layers=5,
                              slippage=0.0005)  # Test with 0.05% slippage
    engine = BacktestEngine(initial_cash=10000)

    signals = []
    for timestamp, row in sample_data.iterrows():
        signal = strategy.on_bar(timestamp, row, engine)
        if signal:
            signals.append(signal)

    # Verify signals were generated
    assert len(signals) > 0
    assert all(s in ["BUY", "SELL", None] for s in signals)

def test_my_strategy_slippage_handling():
    """Test slippage configuration and execution"""
    # Test default slippage
    strategy_default = MyCustomStrategy()
    assert strategy_default.slippage == 0.0005  # 0.05% default

    # Test custom slippage
    strategy_custom = MyCustomStrategy(slippage=0.001)  # 0.1%
    assert strategy_custom.slippage == 0.001

    # Test execution price calculation
    buy_price = 50000.0
    expected_buy_execution = buy_price * (1 + 0.0005)  # 50025.0
    expected_sell_execution = buy_price * (1 - 0.0005)  # 49975.0

    assert abs(expected_buy_execution - 50025.0) < 0.01
    assert abs(expected_sell_execution - 49975.0) < 0.01
```

5. **Implement Frontend Changes (if needed)**
```typescript
// frontend/src/components/MyFeature.tsx
import React, { useState, useEffect } from 'react';
import { BacktestResponse } from '../types/api';

interface MyFeatureProps {
  data: BacktestResponse;
}

export const MyFeature: React.FC<MyFeatureProps> = ({ data }) => {
  const [processedData, setProcessedData] = useState(null);

  useEffect(() => {
    // Process data when component mounts
    const processed = processDataForDisplay(data);
    setProcessedData(processed);
  }, [data]);

  if (!processedData) {
    return <div>Loading...</div>;
  }

  return (
    <div className="my-feature">
      <h3>My Custom Feature</h3>
      {/* Component JSX */}
    </div>
  );
};

function processDataForDisplay(data: BacktestResponse) {
  // Data processing logic
  return data;
}
```

### 3. Testing Guidelines

**Backend Testing Best Practices**

**Unit Tests**
```python
# Test individual components in isolation
def test_strategy_signal_generation():
    """Test specific strategy logic"""
    strategy = MyCustomStrategy()
    mock_data = {'Close': 40000.0}
    mock_engine = Mock()

    signal = strategy.on_bar(pd.Timestamp.now(), mock_data, mock_engine)
    assert signal in ["BUY", "SELL", None]

# Test with parameterized inputs
@pytest.mark.parametrize("custom_param,expected", [
    (1.0, "conservative"),
    (2.0, "aggressive"),
    (3.0, "very_aggressive"),
])
def test_strategy_behavior(custom_param, expected):
    strategy = MyCustomStrategy(custom_param=custom_param)
    assert strategy.get_behavior_type() == expected
```

**Slippage Testing**
```python
# Test slippage configuration and impact
@pytest.mark.parametrize("slippage,expected_impact", [
    (0.0001, "minimal"),     # 0.01% - tight spread
    (0.0005, "conservative"), # 0.05% - default
    (0.002, "significant"),   # 0.2% - volatile market
])
def test_slippage_impact(slippage, expected_impact):
    """Test slippage impact on execution prices"""
    strategy = MyCustomStrategy(slippage=slippage)
    base_price = 50000.0

    # Test buy execution with slippage
    buy_execution = base_price * (1 + slippage)
    expected_buy_cost = base_price + (base_price * slippage)

    # Test sell execution with slippage
    sell_execution = base_price * (1 - slippage)
    expected_sell_proceeds = base_price - (base_price * slippage)

    assert abs(buy_execution - expected_buy_cost) < 0.01
    assert abs(sell_execution - expected_sell_proceeds) < 0.01

def test_realistic_execution_model():
    """Test realistic execution vs perfect execution"""
    strategy = MyCustomStrategy(slippage=0.0005)
    engine = BacktestEngine(initial_cash=10000)

    # Mock data with signal trigger
    signal_data = {
        'Open': 50000.0, 'High': 51000.0, 'Low': 49000.0,
        'Close': 50500.0, 'Volume': 1000
    }

    # Test that signal detection uses OHLC extremes
    # and execution uses close price with slippage
    buy_signal = signal_data['Low'] <= 49500.0  # Target price
    if buy_signal:
        execution_price = signal_data['Close'] * (1 + strategy.slippage)
        assert execution_price > signal_data['Close']  # Slippage applied
```

**Integration Tests**
```python
def test_complete_backtest_flow():
    """Test entire backtest execution"""
    strategy = MyCustomStrategy(base_bet=500, multiplier=2.0)
    engine = BacktestEngine(initial_cash=10000)

    # Load test data
    data = load_test_data()

    # Run backtest
    results = engine.run(data, strategy)

    # Verify results structure
    assert 'equity' in results
    assert 'trades' in results
    assert 'metrics' in results
    assert len(results['trades']) >= 0
```

**Frontend Testing Best Practices**

**Component Tests**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MyFeature } from './MyFeature';

test('MyFeature renders correctly with data', async () => {
  const mockData = {
    results: {
      'Test Strategy': {
        strategy_name: 'Test Strategy',
        metrics: { total_return: 0.15, cagr: 0.05 },
        equity: [],
        trades: []
      }
    }
  };

  render(<MyFeature data={mockData} />);

  await waitFor(() => {
    expect(screen.getByText('My Custom Feature')).toBeInTheDocument();
    expect(screen.getByText('15.00%')).toBeInTheDocument();
  });
});

test('MyFeature handles loading state', () => {
  render(<MyFeature data={{ results: {} }} />);

  expect(screen.getByText('Loading...')).toBeInTheDocument();
});
```

**API Integration Tests**
```typescript
import { ApiClient } from '../lib/api';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

test('ApiClient handles backtest request', async () => {
  const mockResponse = {
    data: {
      results: { 'Test Strategy': { strategy_name: 'Test Strategy' } }
    }
  };

  mockedAxios.post.mockResolvedValue(mockResponse);

  const client = new ApiClient('http://localhost:8001');
  const result = await client.runBacktest({
    config_path: 'configs/test.yaml'
  });

  expect(result.results['Test Strategy'].strategy_name).toBe('Test Strategy');
  expect(mockedAxios.post).toHaveBeenCalledWith(
    'http://localhost:8001/backtest',
    { config_path: 'configs/test.yaml' }
  );
});
```

## Code Standards

### Python Code Style

**Formatting and Linting**
```bash
uv run python -m black --check src/api src/investing_workbench tests
uv run ruff check src/api src/investing_workbench tests
uv run mypy src/investing_workbench
```

**Naming Conventions**
```python
# Classes: PascalCase
class BacktestEngine:
    pass

# Functions and variables: snake_case
def calculate_metrics(trades_data):
    total_trades = len(trades_data)
    return total_trades

# Constants: UPPER_SNAKE_CASE
DEFAULT_INITIAL_CAPITAL = 30000.0
MAX_LAYERS = 10

# Private methods: prefix with underscore
def _calculate_position_size(self, available_cash):
    return available_cash * 0.95
```

**Documentation Standards**
```python
def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for a series of returns.

    Args:
        returns: List of periodic returns
        risk_free_rate: Annual risk-free rate (default: 2%)

    Returns:
        Sharpe ratio value

    Raises:
        ValueError: If returns list is empty or contains invalid data

    Example:
        >>> calculate_sharpe_ratio([0.05, 0.03, -0.02, 0.07])
        1.234
    """
    if not returns:
        raise ValueError("Returns list cannot be empty")

    excess_returns = [r - risk_free_rate/252 for r in returns]  # Daily adjustment
    return np.mean(excess_returns) / np.std(excess_returns)
```

### TypeScript Code Style

**Configuration Files**
```json
// .eslintrc.json
{
  "extends": [
    "@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn"
  }
}

// prettier.config.js
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2
};
```

**TypeScript Standards**
```typescript
// Interface definitions
interface StrategyMetrics {
  total_return: number;
  cagr: number;
  sharpe_ratio: number;
  max_drawdown: number;
  hit_rate: number;
  profit_factor: number;
  total_trades: number;
}

// Component Props Interface
interface MetricsCardsProps {
  metrics: StrategyMetrics;
  strategyName: string;
  isLoading?: boolean;
  onExport?: () => void;
}

// Component with proper typing
export const MetricsCards: React.FC<MetricsCardsProps> = ({
  metrics,
  strategyName,
  isLoading = false,
  onExport
}) => {
  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className="metrics-cards">
      <h3>{strategyName}</h3>
      {/* Component JSX */}
    </div>
  );
};
```

## Performance Guidelines

### Backend Performance

**Efficient Data Processing**
```python
# Use vectorized operations
def calculate_returns_fast(prices: pd.Series) -> pd.Series:
    """Vectorized return calculation"""
    return prices.pct_change().fillna(0)

# Avoid loops when possible
# BAD: Slow loop-based approach
returns = []
for i in range(1, len(prices)):
    returns.append((prices[i] - prices[i-1]) / prices[i-1])

# GOOD: Vectorized approach
returns = prices.pct_change().fillna(0)
```

**Memory Management**
```python
# Use generators for large datasets
def process_large_dataset(data_path: str):
    """Process large files in chunks"""
    for chunk in pd.read_csv(data_path, chunksize=10000):
        yield process_chunk(chunk)

# Clean up large objects
def cleanup_memory():
    """Explicit memory cleanup"""
    import gc
    gc.collect()
```

### Frontend Performance

**React Optimization**
```typescript
// Use React.memo for expensive components
export const ExpensiveChart = React.memo<ChartProps>(({ data }) => {
  const processedData = useMemo(() => {
    return processDataForChart(data);
  }, [data]);

  return <PlotlyChart data={processedData} />;
});

// Use useCallback for event handlers
const BacktestForm: React.FC = () => {
  const [request, setRequest] = useState<BacktestRequest>({});

  const handleSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    await runBacktest(request);
  }, [request]);

  return <form onSubmit={handleSubmit}>{/* Form JSX */}</form>;
};
```

**Chart Performance**
```typescript
// Sample large datasets for visualization
const sampleChartData = (data: EquityPoint[], maxPoints: number = 1000) => {
  if (data.length <= maxPoints) return data;

  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

// Use efficient Plotly updates
const updateChart = (newData: EquityPoint[]) => {
  const sampledData = sampleChartData(newData);

  Plotly.react('chart-div', {
    x: sampledData.map(d => d.timestamp),
    y: sampledData.map(d => d.equity),
    type: 'scatter'
  }, layout, { responsive: true });
};
```

## Debugging

### Backend Debugging

**Logging Configuration**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use structured logging
def run_backtest(config: AppConfig):
    logger.info(f"Starting backtest with config: {config.config_path}")

    try:
        results = execute_backtest(config)
        logger.info(f"Backtest completed successfully: {len(results)} strategies")
        return results
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}", exc_info=True)
        raise
```

**Debug Mode**
```python
# Debug decorator
def debug_timer(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.2f}s")
        return result
    return wrapper

# Usage
@debug_timer
def run_strategy(data: pd.DataFrame, strategy):
    # Strategy execution logic
    pass
```

### Frontend Debugging

**React DevTools**
```typescript
// Debug component renders
import React from 'react';

export const DebugComponent: React.FC = () => {
  const [renderCount, setRenderCount] = useState(0);

  useEffect(() => {
    setRenderCount(prev => prev + 1);
    console.log(`Component rendered ${renderCount + 1} times`);
  });

  return <div>Render count: {renderCount}</div>;
};
```

**API Debugging**
```typescript
// Add request/response interceptors for debugging
apiClient.interceptors.request.use(request => {
  console.log('API Request:', request);
  return request;
});

apiClient.interceptors.response.use(
  response => {
    console.log('API Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

## Contributing Guidelines

### Pull Request Process

1. **Create Pull Request**
```bash
git checkout -b feature/your-feature
# Make changes
git add .
git commit -m "feat: add new strategy implementation"
git push origin feature/your-feature
# Create PR on GitHub
```

2. **PR Checklist**
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No breaking changes (or clearly documented)

3. **Commit Message Format**
```
type(scope): description

[optional body]

[optional footer]

Types:
feat: new feature
fix: bug fix
docs: documentation
style: formatting
refactor: code refactoring
test: tests
chore: maintenance
```

### Code Review Process

**Review Guidelines**
- Check for code quality and maintainability
- Verify test coverage
- Ensure documentation is updated
- Validate performance implications
- Check security considerations

**Review Checklist**
- [ ] Logic is correct
- [ ] Error handling is appropriate
- [ ] Performance is acceptable
- [ ] Tests are comprehensive
- [ ] Documentation is clear

## Common Issues and Solutions

### Backend Issues

**Import Errors**
```python
# Ensure proper relative imports
from .base import MartingaleStrategy  # Relative import
from ..engine import BacktestEngine   # Parent directory import
```

**Configuration Errors**
```python
# Validate configuration before use
def validate_config(config: dict) -> bool:
    required_keys = ['strategies', 'backtest']
    return all(key in config for key in required_keys)
```

### Frontend Issues

**Type Errors**
```typescript
// Use proper type guards
function isBacktestResponse(obj: any): obj is BacktestResponse {
  return obj &&
         typeof obj === 'object' &&
         'results' in obj &&
         typeof obj.results === 'object';
}

// Use conditional rendering
{isBacktestResponse(data) ? (
  <ResultsDisplay data={data} />
) : (
  <div>No data available</div>
)}
```

**State Management**
```typescript
// Use proper state updates
setRequest(prev => ({ ...prev, newParameter: value }));

// Avoid direct state mutation
// WRONG: request.newParameter = value
// CORRECT: setRequest(prev => ({ ...prev, newParameter: value }))
```

This developer guide provides comprehensive information for contributing to the project. Following these guidelines ensures high-quality code and smooth collaboration among developers.
