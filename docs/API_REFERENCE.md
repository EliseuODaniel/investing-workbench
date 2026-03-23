# API Reference

This document provides comprehensive information about the Bitcoin Martingale Backtesting Framework REST API.

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

### 2. Run Backtest

Execute backtest with specified parameters and strategies.

**Endpoint**
```
POST /backtest
```

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
| `base_bet` | number | No | null | Base bet amount for Martingale |
| `multiplier` | number | No | null | Position size multiplier |
| `drop_step` | number | No | null | Price drop step percentage |
| `take_profit` | number | No | null | Take profit percentage |
| `max_layers` | integer | No | null | Maximum number of layers |
| `force_download` | boolean | No | false | Force data re-download |

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
| `end_date` | string | Data end date |
| `total_days` | integer | Number of data points |
| `data_source` | string | Data source symbol |
| `cache_used` | boolean | Whether cached data was used |

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

### 3. Export Trades

Download trade data for a specific strategy (placeholder endpoint).

**Endpoint**
```
GET /reports/{strategy}/download
```

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `strategy` | string | URL-encoded strategy name |

**Response**
```
CSV file with trade data
```

**Example Request**
```bash
curl -X GET "http://localhost:8001/reports/Risk-Cap%20Martingale/download" \
     -o trades.csv
```

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
  force_download?: boolean;
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
  mar_ratio: number;          // CAGR / Max Drawdown
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
  pnl?: number;               // Profit/loss (null for BUY)
  layer?: number;             // Martingale layer (null if not applicable)
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
  end_date: '2023-12-31'
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
    "end_date": "2023-12-31"
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
2. **Fallback Source**: Yahoo Finance (BTC-USD)
3. **Cache**: Local Parquet files for performance

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

This API reference provides comprehensive information for integrating with the Bitcoin Martingale Backtesting Framework. All examples are production-ready and follow best practices for error handling and type safety.
