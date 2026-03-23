# Bitcoin Martingale Backtesting Framework

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18.2+-61dafb.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2+-blue.svg)](https://typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)

A comprehensive, production-ready Python framework for backtesting Martingale-based trading strategies on Bitcoin (BTC-BRL). This framework provides multiple strategy implementations with realistic execution modeling, detailed performance metrics, interactive web UI, and extensible visualization tools.

## Development Status

- The legacy runtime still lives in `src/`.
- The incremental refactor now starts in `src/bitcoin_martingale/`.
- Repository-level agent guidance lives in `AGENTS.md`.
- Codex workflows, skills, and review conventions live in `docs/codex_workflows.md`, `docs/code_review.md`, and `.agents/skills/`.

## 🌟 Features

### 📊 Multiple Trading Strategies
- **Martingale Variants**: Fixed parameter, volatility-adjusted, trailing take-profit, risk-cap, and DCA hybrid approaches
- **Traditional Strategies**: Buy & Hold, DCA, trend following, mean reversion, and breakout trading
- **Extensible Architecture**: Easy to add custom strategies with clean abstractions

### 🚀 Modern Technology Stack
- **Backend**: Python 3.10+ with FastAPI, pandas, and Plotly
- **Frontend**: React 18 + TypeScript with interactive visualizations
- **Data**: Yahoo Finance integration with intelligent caching (Parquet format)
- **Testing**: Comprehensive test suite with pytest and vitest

### 📈 Advanced Analytics
- **Performance Metrics**: CAGR, Sharpe ratio, maximum drawdown, hit rate, profit factor, and more
- **Interactive Charts**: Equity curves, drawdown analysis, allocation heatmaps, and trade markers
- **Risk Management**: Position sizing, layer management, and portfolio exposure tracking
- **Realistic Execution**: Candle-level backtesting with conservative slippage modeling
- **Cash Yield**: Optional SELIC-based yield on uninvested cash for more realistic returns
- **Export Capabilities**: CSV downloads and HTML reports

### 📊 Market Benchmarks
- **Indices Comparison**: Compare strategies against IBOVESPA (^BVSP), S&P 500 (SPY), and other market indices
- **Multi-Asset Support**: Include Ethereum (ETH-USD), Nasdaq 100 (QQQ), and custom tickers
- **SELIC Benchmark**: Use real SELIC rates as fixed income benchmark
- **Buy & Hold Reference**: Automatic Bitcoin buy-and-hold comparison
- **Performance Metrics**: Calculate CAGR, Sharpe ratio, and drawdown for all benchmarks
- **Visual Comparison**: Side-by-side charts and ranking tables

### 🎯 Production-Ready Features
- **RESTful API**: Full API for integration with external systems
- **Web Interface**: Intuitive React-based UI with dark mode support
- **Configuration-Driven**: YAML-based configuration for flexible parameter testing
- **Data Persistence**: Intelligent caching and data validation

## 🏗️ Architecture Overview

```
bitcoin-martingale/
├── src/                              # Core Python backend
│   ├── api/                          # FastAPI web backend
│   ├── strategies/                   # Trading strategy implementations
│   ├── engine.py                     # Backtesting engine core
│   ├── data.py                       # Data download and caching
│   ├── metrics.py                    # Performance calculations
│   └── cli.py                        # Command-line interface
├── frontend/                         # React web interface
│   ├── components/                   # UI components
│   ├── lib/                         # API client and utilities
│   └── types/                       # TypeScript definitions
├── configs/                          # Strategy configuration files
├── tests/                           # Test suite
├── data/                            # Data cache
└── reports/                         # Generated reports
```

## 🚀 Quick Start

### Option 1: Interactive Web UI (Recommended)

1. **Start Backend API**
```bash
# Clone and setup
git clone <repository-url>
cd bitcoin-martingale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -e .[dev]

# Start FastAPI server
uvicorn src.api.main:app --reload --port 8001
```

2. **Start Frontend**
```bash
# Open new terminal
cd frontend
npm install
npm run dev
```

3. **Access Web Interface**
- Open **http://localhost:5173**
- Select configuration (aggressive, conservative, martingale)
- Adjust parameters and run backtests
- Explore interactive charts and export results

### Option 2: Command Line Interface

```bash
# Run all strategies with default config
python -m src run

# Run specific strategies
python -m src run --config configs/aggressive.yaml --strategies "Risk-Cap Martingale"

# Skip plot generation for faster execution
python -m src run --config configs/martingale.yaml --no-plot --quiet
```

### Development Checks

```bash
make backend-test
make backend-lint
make backend-format
make backend-type
make frontend-lint
make frontend-test
make frontend-build
```

### Persisted Runs

- Every `POST /backtest` call now persists a run manifest and serialized response under `runs/<run_id>/`.
- The API response includes `run_info.run_id`, `artifact_dir`, artifact paths, and a `data_fingerprint`.
- The API exposes `GET /runs`, `GET /runs/{run_id}`, `GET /runs/{run_id}/response`, `GET /runs/{run_id}/config`, `GET /runs/{run_id}/data-profile`, and `GET /runs/{run_id}/report.html`.
- Trades can be exported from a persisted run with `GET /runs/{run_id}/strategies/{strategy_name}/trades.csv`.
- The legacy route `GET /reports/{strategy}/download` now downloads trades for the newest persisted run containing that strategy.
- The frontend can now select up to 3 persisted runs and compare their best-performing strategies side by side.
- Persisted runs can also be shared and reopened directly via `?run=<run_id>` links in the frontend.
- The frontend now exports the current results workspace as PNG and downloads persisted HTML reports directly.
- The frontend now lazy-loads heavy analytics panels and vendor bundles, reducing the initial application payload.
- The CLI now includes `python -m src runs-list`, `python -m src runs-show --run-id <id>`, `python -m src runs-config --run-id <id>`, and `python -m src runs-export-csv --run-id <id> --strategy "<name>"`.

### Option 3: Python API

```python
from src.config import AppConfig
from src.data import get_data
from src.engine import BacktestEngine
from src.strategies.martingale_fixed import MartingaleFixedStrategy

# Load data
data = get_data(start="2020-01-01", end="2023-12-01")

# Setup strategy
strategy = MartingaleFixedStrategy(
    base_bet=500.0,
    multiplier=2.0,
    drop_step=0.10,
    take_profit=0.15,
    max_layers=10
)

# Run backtest (optional: enable cash yield)
engine = BacktestEngine(
    initial_cash=30000.0,
    apply_cash_yield=True,        # Enable SELIC-based cash yield
    selic_rate_annual=0.13,       # 13% annual rate
    yield_frequency="monthly"     # Monthly compounding
)
results = engine.run(data, strategy)
```

## 📋 Available Strategies

### Martingale Strategies

| Strategy | Description | Risk Level | Best For |
|----------|-------------|------------|----------|
| **Fixed Martingale** | Classic Martingale with fixed parameters | High | Volatile markets |
| **Volatility-Adjusted** | Dynamic sizing based on market volatility | Medium-High | Variable volatility |
| **Trailing TP** | Martingale with trailing take-profit stops | Medium | Trending markets |
| **Risk-Cap** | Advanced risk management with position limits | Medium | Risk-averse trading |
| **DCA Hybrid** | Combines DCA with limited Martingale layers | Low-Medium | Long-term accumulation |
| **ATR-Based Martingale** | Volatility sizing using Average True Range | Medium | Adaptive markets |

### Traditional Strategies

| Strategy | Description | Risk Level | Best For |
|----------|-------------|------------|----------|
| **Buy & Hold** | Simple baseline strategy | Low | Market exposure |
| **Monthly/Weekly DCA** | Fixed periodic purchases | Low | Long-term investing |
| **Trend Following** | Moving average crossover signals (Fast/Slow MA Cross) | Medium | Trending markets |
| **Mean Reversion** | Bollinger Bands and Simple MA reversal signals | Medium | Range-bound markets |
| **Breakout Trading** | Breakout from support/resistance levels | High | Momentum trading |

## ⚙️ Configuration

### Strategy Configuration

Configuration files use YAML format for easy editing:

```yaml
# configs/aggressive.yaml
backtest:
  initial_capital: 30000.0
  start_date: "2020-01-01"
  end_date: null  # Use current date
  data_source: "BTC-BRL"
  apply_cash_yield: false     # Optional: Enable SELIC cash yield
  selic_rate_annual: 0.13    # Annual SELIC rate (13%)
  yield_frequency: "monthly"  # Compounding frequency

strategies:
  - name: "Risk-Cap Martingale"
    class_path: "strategies.martingale_risk_cap.MartingaleRiskCapStrategy"
    parameters:
      base_bet: 750.0           # Initial investment
      multiplier: 2.5           # Layer multiplier
      drop_step: 0.08          # 8% drop triggers new layer
      take_profit: 0.12        # 12% take profit per layer
      max_layers: 12           # Maximum concurrent layers
      max_position_pct: 0.85   # Max 85% portfolio exposure
```

### Benchmark Configuration

Add market benchmarks to compare strategy performance:

```yaml
# configs/martingale.yaml
backtest:
  # ... existing configuration ...

  # Market benchmarks
  benchmarks:
    - ticker: "^BVSP"            # Bovespa Index
      name: "IBOVESPA"           # Display name
      enabled: true              # Include in backtest
    - ticker: "SPY"              # S&P 500 ETF
      name: "S&P 500"            # Display name
      enabled: false             # Disabled by default
    - ticker: "ETH-USD"          # Ethereum
      name: "Ethereum"           # Display name
      enabled: false

  # Built-in benchmarks
  include_selic_benchmark: false  # Include SELIC as benchmark
  include_buy_hold_benchmark: true  # Include BTC Buy & Hold
```

#### Supported Benchmark Tickers

| Category | Ticker | Description |
|----------|--------|-------------|
| **Brazilian** | `^BVSP` | Bovespa Index |
| **US Indices** | `SPY` | S&P 500 ETF |
| | `QQQ` | Nasdaq 100 ETF |
| | `VTI` | Total Stock Market ETF |
| **Cryptocurrencies** | `ETH-USD` | Ethereum |
| | `BNB-USD` | Binance Coin |
| **International** | `EWZ` | Brazil ETF (US) |
| | `EFA` | EAFE Index ETF |
| **Commodities** | `GLD` | Gold ETF |
| | `SLV` | Silver ETF |

#### Using Benchmarks

**Via Configuration File:**
```yaml
benchmarks:
  - ticker: "^BVSP"
    name: "IBOVESPA"
    enabled: true
```

**Via Command Line:**
```bash
python -m src run --config configs/martingale.yaml \
  --benchmarks "^BVSP" "SPY" "ETH-USD" \
  --include-selic-benchmark
```

**Via API:**
```json
{
  "benchmarks": ["^BVSP", "SPY"],
  "include_selic_benchmark": true,
  "include_buy_hold_benchmark": true
}
```

**Via Web Interface:**
1. Go to "Benchmarks de Mercado" section
2. Enter tickers (e.g., `^BVSP, SPY, ETH-USD`)
3. Enable SELIC benchmark if desired
4. Run backtest with benchmarks included

### Parameter Guidelines

| Parameter | Range | Typical Values | Effect |
|-----------|-------|----------------|--------|
| **base_bet** | $100-$2000 | $500-$1000 | Initial position size |
| **multiplier** | 1.5-3.0 | 2.0-2.5 | Layer growth rate |
| **drop_step** | 5%-15% | 8%-12% | New layer trigger |
| **take_profit** | 10%-25% | 12%-18% | Exit target |
| **max_layers** | 3-15 | 6-10 | Risk control |

### Available Configurations

- **`configs/aggressive.yaml`**: High-risk, high-reward parameters
- **`configs/conservative.yaml`**: Low-risk, capital preservation focus
- **`configs/martingale.yaml`**: Standard Martingale configurations
- **`configs/classic_strategies.yaml`**: Traditional trading strategies
- **`configs/test.yaml`**: Quick testing configuration

## ⚡ Execution Model

### Realistic Trade Execution

The framework implements a conservative execution model to avoid look-ahead bias and unrealistic backtesting results:

- **Signal Detection**: Strategies use high/low prices to detect trading opportunities (touch levels, breakouts, reversals)
- **Trade Execution**: All trades execute at the candle's close price with default slippage of 0.05% (configurable)
- **Slippage Model**: Conservative bid-ask spread simulation to account for real-world trading costs
- **No Perfect Fills**: Eliminates unrealistic perfect-timing assumptions common in backtesting

### Execution Parameters

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `slippage` | 0.0005 (0.05%) | Price execution adjustment per trade | Reduces unrealistic profits |
| `price_source` | Close price | Execution price for all trades | Conservative fill modeling |
| `signal_source` | High/Low prices | Level detection for triggers | Maintains signal accuracy |

This approach provides more realistic backtesting results while maintaining the simplicity and speed of daily-data backtesting.

## 📊 Performance Metrics

The framework calculates comprehensive performance metrics:

### Return Metrics
- **Total Return**: Overall portfolio return percentage
- **CAGR**: Compound Annual Growth Rate
- **Annualized Return**: Year-over-year performance

### Risk Metrics
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Sortino Ratio**: Downside risk-adjusted returns
- **Volatility**: Annualized standard deviation

### Trading Metrics
- **Hit Rate**: Percentage of profitable trades
- **Profit Factor**: Total profit / total loss
- **Average Trade PnL**: Mean profit/loss per trade
- **Win/Loss Ratio**: Average win / average loss

### Portfolio Metrics
- **Total Trades**: Number of executed trades
- **Open Layers**: Current open positions
- **Portfolio Exposure**: Percentage of capital invested

## 💰 Cash Yield Feature

### Overview

The framework includes an optional cash yield feature that applies SELIC-based interest to uninvested cash, providing more realistic backtesting results by accounting for the time value of money. This is particularly relevant for Brazilian investors where SELIC is the benchmark interest rate.

### How It Works

- **Monthly Compounding**: Interest is calculated and applied monthly based on the available cash balance
- **Two Modes**:
  - **Fixed Rate**: Uses the annual SELIC rate (default: 13%) with monthly compounding
  - **Real SELIC**: Uses actual monthly SELIC rates from Banco Central do Brasil data
- **Cash-Only**: Only applies to uninvested cash (not allocated to open positions)
- **Optional**: Disabled by default to maintain backward compatibility

### Configuration

Add cash yield parameters to your YAML configuration:

```yaml
# configs/martingale.yaml
backtest:
  initial_capital: 30000.0
  start_date: "2020-01-01"
  end_date: null
  apply_cash_yield: true        # Enable cash yield
  selic_rate_annual: 0.13      # 13% annual SELIC rate (fallback)
  yield_frequency: "monthly"    # Monthly compounding
  use_real_selic: false        # Use real monthly SELIC rates
  selic_path: "data/selic.csv" # Path to SELIC data file
  selic_fallback_rate: 0.13    # Annual fallback when real data unavailable

strategies:
  - name: "Fixed Martingale"
    # ... strategy parameters
```

### CLI Usage

Enable cash yield via command line:

```bash
# Enable cash yield with default fixed SELIC rate (13%)
python -m src run --config configs/martingale.yaml --apply-cash-yield

# Custom fixed SELIC rate
python -m src run --config configs/martingale.yaml --apply-cash-yield --selic-rate 0.1275

# Enable real monthly SELIC rates (downloads/creates data/selic.csv)
python -m src run --config configs/martingale.yaml --apply-cash-yield --use-real-selic

# Custom SELIC data file path
python -m src run --config configs/martingale.yaml --apply-cash-yield --use-real-selic --selic-path data/my_selic.csv

# Custom fallback rate when real data unavailable
python -m src run --config configs/martingale.yaml --apply-cash-yield --use-real-selic --selic-fallback-rate 0.11

# Run with quiet output to see interest earned in summary
python -m src run --config configs/martingale.yaml --apply-cash-yield --use-real-selic
```

### API Usage

Include cash yield parameters in API requests:

```json
{
  "config_path": "configs/martingale.yaml",
  "apply_cash_yield": true,
  "selic_rate_annual": 0.13,
  "use_real_selic": true,
  "selic_path": "data/selic.csv",
  "selic_fallback_rate": 0.13,
  "start_date": "2020-01-01",
  "end_date": "2023-12-31"
}
```

### Impact on Results

When enabled, cash yield:
- **Increases Returns**: Adds interest income to total returns
- **Reduces Drawdown**: Cash cushion provides some protection during market downturns
- **Improves Metrics**: Can enhance risk-adjusted metrics like Sharpe ratio
- **Realistic Modeling**: Better represents actual investment returns in Brazil

### Real SELIC Data

The framework supports real monthly SELIC rates from Banco Central do Brasil:

**Automatic Download**:
```bash
# Install required library for downloading real data
pip install bcb

# The framework will automatically attempt to download real SELIC data
# from SGS (Sistema Gerenciador de Séries Temporais) when --use-real-selic is used
```

**Data Format**:
- Expected file: `data/selic.csv`
- Columns: `year`, `month`, `rate` (decimal monthly rate)
- Example row: `2023, 1, 0.0108` (1.08% monthly for January 2023)

**Fallback Behavior**:
- If download fails or file is missing → Generates fake data
- If month/year not found → Uses last available rate
- If no data available → Uses configured annual rate converted to monthly

**Manual SELIC Data**:
You can create your own SELIC file with historical data:
```csv
year,month,rate
2023,1,0.0108
2023,2,0.0108
2023,3,0.0111
# ... more months
```

### Example Results

```
=== Fixed Martingale Performance ===
Total Return: 45.23%
CAGR: 12.84%
Max Drawdown: -18.45%
Sharpe Ratio: 1.23
Total Interest Earned: $2,847.32  # Cash yield contribution
Total Trades: 89
```

## 🔧 Development Guide

### Adding New Strategies

1. **Create Strategy Class**
```python
# src/strategies/my_strategy.py
from .base import MartingaleStrategy

class MyCustomStrategy(MartingaleStrategy):
    def __init__(self, custom_param: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.custom_param = custom_param

    def on_bar(self, timestamp, data, engine) -> Optional[str]:
        """Implement your trading logic here"""
        return "BUY" or "SELL" or None
```

2. **Add to Configuration**
```yaml
strategies:
  - name: "My Custom Strategy"
    class_path: "strategies.my_strategy.MyCustomStrategy"
    parameters:
      custom_param: 1.5
      base_bet: 500.0
```

3. **Write Tests**
```python
# tests/test_my_strategy.py
import pytest
from src.strategies.my_strategy import MyCustomStrategy

def test_my_strategy():
    strategy = MyCustomStrategy(custom_param=1.5)
    # Add test logic here
```

### API Development

Add new endpoints in `src/api/main.py`:

```python
@app.get("/custom-endpoint")
async def custom_endpoint():
    """Custom API endpoint"""
    return {"message": "Custom response"}
```

### Frontend Development

Add new components in `frontend/src/components/`:

```typescript
// components/MyComponent.tsx
import React from 'react';

export const MyComponent: React.FC = () => {
  return <div>My Custom Component</div>;
};
```

## 🧪 Testing

### Running Tests

```bash
# Python backend tests
python -m pytest tests/ -v

# Frontend tests
cd frontend && npm test

# Coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Structure

```
tests/
├── test_api.py              # API endpoint tests
├── test_engine.py           # Backtest engine tests
├── test_strategies.py       # Strategy logic tests
├── test_metrics.py          # Performance metrics tests
└── test_plots.py            # Visualization tests
```

## 📈 API Reference

### REST API Endpoints

#### List Configurations
```http
GET /configs
```
Returns available configuration profiles with strategy lists.

#### Run Backtest
```http
POST /backtest
Content-Type: application/json

{
  "config_path": "configs/aggressive.yaml",
  "strategies": ["Risk-Cap Martingale"],
  "start_date": "2020-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 30000,
  "force_download": false,
  "apply_cash_yield": true,
  "selic_rate_annual": 0.13
}
```

#### Response Format
```json
{
  "results": {
    "Risk-Cap Martingale": {
      "strategy_name": "Risk-Cap Martingale",
      "metrics": {
        "total_return": 0.1542,
        "cagr": 0.0523,
        "sharpe_ratio": 0.8234,
        "max_drawdown": -0.2341,
        "hit_rate": 0.8543,
        "profit_factor": 2.1456,
        "total_trades": 142,
        "total_interest_earned": 1847.32
      },
      "equity": [...],
      "trades": [...]
    }
  },
  "buy_hold_equity": [...],
  "data_info": {
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "total_days": 1456
  }
}
```

## 🎨 Visualizations

### Available Chart Types

1. **Equity Curves**: Portfolio value over time with strategy comparison
2. **Drawdown Charts**: Peak-to-trough decline visualization
3. **Trade Markers**: Buy/sell signals with profit/loss indicators
4. **Allocation Heatmaps**: Asset allocation and exposure tracking
5. **Layer Management**: Martingale layer visualization

### Export Options

- **Interactive HTML**: Fully interactive charts with zoom/pan
- **Static PNG**: High-resolution static images (300 DPI)
- **CSV Data**: Raw trade and equity data for external analysis
- **PDF Reports**: Comprehensive performance summaries

## 📋 Requirements

### System Requirements

- **Python**: 3.10+ (recommended: 3.11+)
- **Node.js**: 16+ (recommended: 18+)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: 1GB+ for data cache and reports
- **OS**: Windows, macOS, Linux

### Dependencies

**Python** (`requirements.txt`):
```
yfinance>=0.2.18        # Yahoo Finance data
pandas>=2.0.0           # Data analysis
numpy>=1.24.0           # Numerical computing
matplotlib>=3.7.0       # Static plotting
plotly>=5.15.0          # Interactive charts
fastapi>=0.104.0        # Web API framework
uvicorn[standard]>=0.24.0 # ASGI server
pydantic>=2.0.0         # Data validation
pyarrow>=12.0.0         # Parquet format
scipy>=1.10.0           # Scientific computing
pyyaml>=6.0             # YAML parsing
```

**Node.js** (`frontend/package.json`):
```
react@^18.2.0           # UI framework
typescript@^5.2.2       # Type safety
vite@^4.5.0             # Build tool
tailwindcss@^3.3.0      # CSS framework
react-plotly.js@^2.6.0  # Charts
axios@^1.6.0            # HTTP client
```

## 🛠️ Installation

### Complete Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd bitcoin-martingale
```

2. **Python Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

3. **Frontend Dependencies**
```bash
cd frontend
npm install
```

4. **Initial Data Cache**
```bash
# Download and cache Bitcoin data
python -m src validate --config configs/martingale.yaml
```

5. **Verification**
```bash
# Test CLI functionality
python -m src validate --config configs/martingale.yaml

# Test backend
python -c "from src.api.main import app; print('✅ Backend ready')"

# Test frontend build
cd frontend && npm run build
```

## 🐛 Troubleshooting

### Common Issues

**Data Download Errors**
```bash
# Force data refresh
python -m src run --config configs/martingale.yaml --force-download
```

**Port Conflicts**
```bash
# Use different ports
uvicorn src.api.main:app --port 8002
cd frontend && npm run dev -- --port 5174
```

**Memory Issues**
```bash
# Reduce date range for testing
python -m src run --start-date 2023-01-01 --end-date 2023-12-31
```

**Frontend Build Errors**
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Known Warnings (Non-Critical)

**pandas SettingWithCopyWarning (CLI Output)**
- **Location**: `src/cli.py:116-119`
- **Cause**: pandas DataFrame slice assignment warnings
- **Impact**: Zero - functional output unaffected
- **Status**: Informational only, functionality works perfectly

**mplfinance Data Volume Warning (Tests/Plots)**
- **Location**: Test output when plotting many data points
- **Cause**: Large dataset visualization warning
- **Impact**: Zero - plots generate successfully
- **Status**: Informational reminder to consider line plots for very large datasets

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**: Fork repository and clone locally
2. **Create Branch**: `git checkout -b feature/your-feature`
3. **Write Tests**: Add comprehensive tests for new functionality
4. **Ensure Coverage**: Maintain 80%+ test coverage
5. **Update Documentation**: Update README and inline docs
6. **Submit PR**: Create pull request with description

### Code Style

- **Python**: Follow PEP 8, use black for formatting
- **TypeScript**: Use ESLint and Prettier configuration
- **Commit Messages**: Use conventional commit format
- **Documentation**: Add docstrings for all public functions

### Project Structure Guidelines

- **Strategies**: Inherit from base classes, implement `on_bar()` method
- **API Endpoints**: Use Pydantic models for request/response validation
- **Components**: Use TypeScript interfaces, add prop documentation
- **Tests**: Use descriptive test names, mock external dependencies

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Yahoo Finance**: For providing comprehensive Bitcoin price data
- **Plotly**: For powerful interactive visualization capabilities
- **FastAPI**: For modern, high-performance API framework
- **React Community**: For excellent UI component ecosystem

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/bitcoin-martingale/issues)
- **Documentation**: [Wiki](https://github.com/your-repo/bitcoin-martingale/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/bitcoin-martingale/discussions)

---

**⚠️ Disclaimer**: This framework is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss. Past performance does not guarantee future results. Always conduct thorough research and consider your risk tolerance before implementing any trading strategy.
