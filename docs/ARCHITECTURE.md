# Architecture Documentation

## Overview

The repository currently runs on a legacy `src/` implementation while the refactor introduces a service-oriented architecture in `src/investing_workbench/`. The short-term goal is to keep the current product working while moving orchestration, logging, and future domain code into clearer layers.

## Current vs Target

### Current Runtime
- `src/api/`: FastAPI routes and API models
- `src/cli.py`: command-line entry point
- `src/engine.py`: legacy backtest engine
- `src/strategies/`: current strategy implementations

### Target Runtime
- `src/investing_workbench/application/`: use cases and orchestration
- `src/investing_workbench/domain/`: future domain models and services
- `src/investing_workbench/infrastructure/`: logging, persistence, and providers
- `src/investing_workbench/interfaces/`: HTTP and CLI adapters

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   UI Components │  │   State Mgmt    │  │   API Client │ │
│  │                 │  │                 │  │              │ │
│  │ • BacktestForm  │  │ • App Context   │  │ • Axios      │ │
│  │ • ChartsSection │  │ • Response Data │  │ • Error      │ │
│  │ • MetricsCards  │  │ • Loading State │  │   Handling   │ │
│  │ • TradesTable   │  │ • Config Data   │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   API Layer     │  │ Business Logic  │  │  Data Layer  │ │
│  │                 │  │                 │  │              │ │
│  │ • REST Endpts   │  │ • BacktestEng   │  │ • Yahoo      │ │
│  │ • Pydantic Mod  │  │ • Strategies    │  │   Finance    │ │
│  │ • CORS Mdw      │  │ • Metrics Calc  │  │ • Parquet    │ │
│  │ • Error Hdl     │  │ • Results       │  │ • Caching    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Backend Architecture

#### 1.1 API Layer (`src/api/`)

**FastAPI Application (`main.py`)**
```python
app = FastAPI(
    title="Investing Workbench API",
    description="Interactive investment comparison, backtesting, and research API",
    version="1.0.0"
)

# Key endpoints:
@app.get("/configs")                    # List configuration profiles
@app.post("/backtest")                  # Execute backtest
@app.get("/reports/{strategy}/download") # Export functionality
```

**Pydantic Models (`models.py`)**
- **Request Models**: Input validation and serialization
- **Response Models**: Structured API responses
- **Type Safety**: Compile-time type checking
- **Auto-documentation**: OpenAPI/Swagger generation

#### 1.2 Business Logic Layer

**Backtest Engine (`src/engine.py`)**
```python
class BacktestEngine:
    """Core backtesting engine with realistic execution modeling"""

    def __init__(self, initial_cash: float = 30000.0, slippage: float = 0.0005):
        self.initial_cash = initial_cash
        self.slippage = slippage  # Default 0.05% per trade
        self.state = State(cash=initial_cash, max_equity=initial_cash)

    def run(self, data: pd.DataFrame, strategy) -> Dict[str, Any]:
        """Execute backtest with strategy on provided data"""

    def buy(self, timestamp, price, quantity, layer_id) -> bool:
        """Execute buy order with slippage at close price"""

    def sell(self, timestamp, price, quantity, layer_id) -> bool:
        """Execute sell order with slippage at close price"""

    def _apply_slippage(self, price: float, is_buy: bool) -> float:
        """Apply conservative slippage model"""
        return price * (1 + self.slippage) if is_buy else price * (1 - self.slippage)
```

#### Realistic Execution Model

The framework implements a conservative execution model to avoid look-ahead bias and unrealistic backtesting results:

**Signal Detection vs Trade Execution**
```python
# Signal generation uses OHLC extremes for accuracy
def detect_signals(self, bar_data):
    # Buy signals: Detect when low price touches/breaches target
    buy_signal = bar_data['Low'] <= target_buy_price

    # Sell signals: Detect when high price reaches target
    sell_signal = bar_data['High'] >= target_sell_price

    return buy_signal, sell_signal

# Trade execution uses close price with slippage for realism
def execute_trade(self, signal, bar_data):
    if signal == 'BUY':
        execution_price = self._apply_slippage(bar_data['Close'], is_buy=True)
        self.buy(timestamp, execution_price, quantity, layer_id)
    elif signal == 'SELL':
        execution_price = self._apply_slippage(bar_data['Close'], is_buy=False)
        self.sell(timestamp, execution_price, quantity, layer_id)
```

**Key Design Principles**
- **No Perfect Fills**: Eliminates unrealistic perfect-timing assumptions
- **Conservative Slippage**: Default 0.05% per trade (configurable)
- **Signal Accuracy**: Uses high/low prices for precise signal detection
- **Execution Reality**: All trades execute at candle close with spread
- **Look-Ahead Prevention**: Cannot execute trades based on future information

**State Management**
```python
@dataclass
class State:
    """Immutable backtest state"""
    cash: float
    layers: List[Layer] = field(default_factory=list)
    equity_history: List[float] = field(default_factory=list)
    cash_history: List[float] = field(default_factory=list)
    timestamp_history: List[pd.Timestamp] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    max_equity: float = field(default_factory=lambda: 0.0)

@dataclass
class Layer:
    """Open position layer"""
    entry_price: float
    quantity: float
    cost: float
    timestamp: pd.Timestamp
    layer_id: int

@dataclass
class Trade:
    """Trade record"""
    timestamp: pd.Timestamp
    action: str  # BUY or SELL
    price: float
    quantity: float
    cost: float
    pnl: Optional[float] = None
    layer: Optional[int] = None
```

#### 1.3 Strategy Layer (`src/strategies/`)

**Base Strategy Hierarchy**
```python
class Strategy(ABC):
    """Abstract base class for all strategies"""

    @abstractmethod
    def on_bar(self, timestamp, data, engine) -> Optional[str]:
        """Process bar data and return trading signal"""
        pass

class BaseStrategy(Strategy):
    """Base class for traditional trading strategies"""

    def __init__(self, initial_capital: float = 30000.0, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.slippage = slippage  # Configurable execution slippage
        self.cash = initial_capital
        self.position_size = 0.0
        self.trades = []

class MartingaleStrategy(BaseStrategy):
    """Base class for Martingale strategies with realistic execution"""

    def __init__(self, base_bet: float, multiplier: float,
                 drop_step: float, take_profit: float, max_layers: int,
                 slippage: float = 0.0005):
        super().__init__(slippage=slippage)
        self.base_bet = base_bet
        self.multiplier = multiplier
        self.drop_step = drop_step
        self.take_profit = take_profit
        self.max_layers = max_layers
        self.layers: List[Dict] = []

    def _check_layer_trigger(self, data: Dict, layer_id: int) -> bool:
        """Check if Martingale layer should trigger using realistic execution"""
        layer = self.layers[layer_id]
        target_price = layer['entry_price'] * (1 - self.drop_step)

        # Signal detection using low price (realistic touch detection)
        return data['Low'] <= target_price

    def _check_take_profit(self, data: Dict, layer_id: int) -> bool:
        """Check if layer should take profit using realistic execution"""
        layer = self.layers[layer_id]
        target_price = layer['entry_price'] * (1 + self.take_profit)

        # Signal detection using high price (realistic target detection)
        return data['High'] >= target_price
```

**Strategy Pattern Implementation**
- **Strategy Interface**: Common interface for all trading strategies
- **Concrete Implementations**: Specific strategy logic
- **Context Integration**: Engine provides trading context
- **Extensibility**: Easy addition of new strategies

#### 1.4 Data Layer (`src/data.py`)

**Data Management Pipeline**
```python
def get_data(start: str = None, end: str = None,
             force_download: bool = False) -> pd.DataFrame:
    """Download and cache Bitcoin price data"""

    # 1. Check cache validity
    if cache_exists and not force_download:
        cached_data = load_from_cache()
        if date_range_valid(cached_data, start, end):
            return cached_data

    # 2. Download from Yahoo Finance
    try:
        data = yf.download("BTC-BRL", start=start, end=end, progress=False)
    except Exception:
        data = yf.download("BTC-USD", start=start, end=end, progress=False)

    # 3. Save to cache (Parquet format)
    save_to_cache(data)

    return data
```

**Caching Strategy**
- **Format**: Parquet for efficient storage and retrieval
- **Validation**: Date range checking before cache usage
- **Fallback**: BTC-USD if BTC-BRL unavailable
- **Performance**: Eliminates repeated network calls

### 2. Frontend Architecture

#### 2.1 Component Architecture

**Hierarchical Component Structure**
```
App.tsx (Root Component)
├── Header.tsx
├── BacktestForm.tsx
│   ├── ConfigSelector.tsx
│   ├── ParameterOverrides.tsx
│   └── DateRangePicker.tsx
├── MetricsCards.tsx
│   ├── StrategyMetrics.tsx
│   └── ComparisonTable.tsx
├── ChartsSection.tsx
│   ├── EquityChart.tsx
│   ├── DrawdownChart.tsx
│   └── AllocationChart.tsx
└── TradesTable.tsx
```

**State Management Pattern**
```typescript
// App Context for global state
interface AppContextType {
  configs: ConfigInfo[];
  currentRequest: BacktestRequest;
  currentResponse: BacktestResponse | null;
  isLoading: boolean;
  error: string | null;
  setCurrentRequest: (request: BacktestRequest) => void;
  runBacktest: () => Promise<void>;
}

// Local component state
const [activeStrategy, setActiveStrategy] = useState<string | null>(null);
const [chartData, setChartData] = useState<EquityPoint[]>([]);
```

#### 2.2 API Integration

**HTTP Client Abstraction**
```typescript
// lib/api.ts
class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
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
}
```

**Type Safety**
```typescript
// types/api.ts
export interface BacktestRequest {
  config_path?: string;
  strategies?: string[];
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  base_bet?: number;
  multiplier?: number;
  drop_step?: number;
  take_profit?: number;
  max_layers?: number;
  force_download?: boolean;
}

export interface StrategyResult {
  strategy_name: string;
  metrics: StrategyMetrics;
  equity: EquityPoint[];
  trades: Trade[];
}
```

## Data Flow Architecture

### 1. Request Flow

```
User Interface → Form Validation → API Request →
Backtest Engine → Strategy Execution → Result Processing →
Response Formatting → UI Update
```

**Detailed Flow**:
1. **User Input**: Form validation and parameter assembly
2. **API Request**: HTTP POST to `/backtest` endpoint
3. **Request Validation**: Pydantic model validation
4. **Data Loading**: Check cache or download from Yahoo Finance
5. **Strategy Execution**: Iterate through data bars, call strategy.on_bar()
6. **Trade Execution**: Strategy signals engine buy/sell operations
7. **Metrics Calculation**: Performance analysis and statistics
8. **Response Formatting**: JSON serialization with error handling
9. **UI Update**: React state update and component re-render

### 2. Strategy Execution Flow

```
Data Bar Entry → Strategy.on_bar() → Signal Detection →
Conservative Execution → State Update → Trade Recording →
Next Bar → Repeat until End
```

**Realistic Execution Pipeline**:
1. **Signal Detection**: Uses OHLC extremes for accuracy
   - Buy signals: `low_price <= target_price`
   - Sell signals: `high_price >= target_price`
2. **Execution Modeling**: All trades execute at close price with slippage
3. **Conservative Timing**: No perfect fills or instant execution
4. **Spread Modeling**: Bid-ask spread simulation through slippage

**Martingale Strategy Specifics**:
1. **Layer Management**: LIFO (Last In, First Out) stack
2. **Position Sizing**: Geometric progression based on multiplier
3. **Risk Controls**: Maximum layers and position size limits
4. **Exit Logic**: Take-profit targets per layer with realistic execution
5. **Signal Accuracy**: Layer triggers detected when `low <= target`
6. **Execution Reality**: Layer purchases execute at `close * (1 + slippage)`

**Traditional Strategy Examples**:
- **Mean Reversion**: Buy on `low <= lower_band`, sell on `high >= middle_band`
- **Breakout Trading**: Buy on `high > resistance + volume`, execute at close
- **Trend Following**: Signal on MA cross, execute at close with slippage

**Key Benefits of Realistic Execution**:
- **No Look-Ahead Bias**: Cannot trade based on future information
- **Conservative Results**: More achievable real-world performance
- **Slippage Costs**: Accounts for transaction costs and market impact
- **Reality Testing**: Better indicator of actual strategy performance

### 3. State Management Flow

```
Initial State → Trade Execution → State Update →
Equity Calculation → History Recording → Performance Metrics
```

**State Transitions**:
- **BUY**: Decrease cash, increase position, record trade
- **SELL**: Increase cash, decrease position, calculate P&L
- **MARKET UPDATE**: Update equity, record history

## Performance Architecture

### 1. Backend Optimizations

**Data Processing**
```python
# Vectorized operations with pandas/numpy
total_btc = sum(layer.quantity for layer in self.state.layers)
current_equity = self.state.cash + (total_btc * close_price)

# Efficient DataFrame operations
trades_df = pd.DataFrame([vars(trade) for trade in self.state.trades])
equity_df = pd.DataFrame({
    'timestamp': self.state.timestamp_history,
    'equity': self.state.equity_history,
    'cash': self.state.cash_history
})
```

**Memory Management**
- **Immutable State**: Prevents accidental state corruption
- **Data Class Usage**: Memory-efficient data structures
- **Lazy Loading**: Strategies loaded only when needed
- **Garbage Collection**: Proper cleanup of temporary objects

**Caching Strategy**
```python
# Parquet format for efficient storage
data.to_parquet(cache_path, compression='snappy')

# Date range validation
def cache_valid(cached_data: pd.DataFrame, start: str, end: str) -> bool:
    cache_start = cached_data.index[0].strftime('%Y-%m-%d')
    cache_end = cached_data.index[-1].strftime('%Y-%m-%d')
    return start >= cache_start and end <= cache_end
```

### 2. Frontend Optimizations

**React Performance**
```typescript
// Memoization for expensive computations
const processedChartData = useMemo(() => {
  return chartData.map(point => ({
    ...point,
    formattedDate: format(new Date(point.timestamp), 'MMM dd, yyyy'),
    value: parseFloat(point.equity.toFixed(2))
  }));
}, [chartData]);

// Component memoization
const MetricsCards = memo(({ metrics }: { metrics: StrategyMetrics }) => {
  return <div>{/* Heavy rendering logic */}</div>;
});
```

**Chart Performance**
```typescript
// Data sampling for large datasets
const sampleData = (data: EquityPoint[], maxPoints: number = 1000) => {
  if (data.length <= maxPoints) return data;

  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

// Efficient updates with plotly.react
Plotly.react('chart-div', data, layout, { responsive: true });
```

## Security Architecture

### 1. API Security

**Input Validation**
```python
class BacktestRequest(BaseModel):
    """Pydantic model with automatic validation"""
    config_path: Optional[str] = Field(None, regex=r'^configs/[^/]+\.yaml$')
    initial_capital: Optional[float] = Field(None, gt=0, le=1000000)
    strategies: Optional[List[str]] = Field(None, max_items=10)
```

**Error Handling**
```python
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Validation error: {str(exc)}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**CORS Configuration**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Data Security

**Input Sanitization**
- **File Path Validation**: Restrict configuration file paths
- **Date Range Limits**: Prevent excessive data requests
- **Parameter Bounds**: Validate numeric input ranges

**Cache Security**
```python
# Safe cache file handling
def safe_cache_path(symbol: str) -> str:
    """Generate safe cache file path"""
    safe_symbol = re.sub(r'[^a-zA-Z0-9_-]', '', symbol)
    return f"data/{safe_symbol.lower()}.parquet"
```

## Testing Architecture

### 1. Backend Testing

**Test Structure**
```
tests/
├── test_api.py              # API endpoint tests
├── test_engine.py           # Engine functionality tests
├── test_strategies.py       # Strategy logic tests
├── test_metrics.py          # Performance metrics tests
├── test_data.py            # Data handling tests
└── fixtures/              # Test data and fixtures
```

**Testing Patterns**
```python
# Strategy testing
@pytest.fixture
def sample_data():
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    return pd.DataFrame({
        'Open': np.random.uniform(30000, 60000, 100),
        'High': np.random.uniform(30000, 60000, 100),
        'Low': np.random.uniform(30000, 60000, 100),
        'Close': np.random.uniform(30000, 60000, 100),
        'Volume': np.random.uniform(1000, 10000, 100)
    }, index=dates)

# Engine testing
def test_engine_buy_sell_cycle():
    """Test complete buy-sell cycle"""
    engine = BacktestEngine(initial_cash=10000)
    strategy = BuyAndHoldStrategy()

    # Execute trades
    engine.buy(pd.Timestamp('2020-01-01'), 40000, 0.1, 0)
    engine.sell(pd.Timestamp('2020-01-02'), 41000, 0.1, 0)

    # Verify state
    assert engine.state.cash > 10000  # Profit
    assert len(engine.state.trades) == 2
```

### 2. Frontend Testing

**Component Testing**
```typescript
// Form component testing
test('BacktestForm validates input correctly', async () => {
  render(<BacktestForm onSubmit={jest.fn()} />);

  const initialCapitalInput = screen.getByLabelText('Initial Capital');
  await userEvent.type(initialCapitalInput, '-1000');

  const submitButton = screen.getByRole('button', { name: 'Run Backtest' });
  fireEvent.click(submitButton);

  expect(screen.getByText('Initial capital must be positive')).toBeInTheDocument();
});

// API client testing
test('ApiClient handles errors correctly', async () => {
  const mockAxios = axios as jest.Mocked<typeof axios>;
  mockAxios.post.mockRejectedValue(new Error('Network error'));

  const client = new ApiClient('http://localhost:8001');

  await expect(client.runBacktest({})).rejects.toThrow('Network error');
});
```

## Deployment Architecture

### 1. Production Deployment

**Backend Deployment**
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PYTHONPATH=/app
      - DATA_CACHE_DIR=/app/data
    volumes:
      - ./data:/app/data
      - ./reports:/app/reports
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8001
```

**Frontend Deployment**
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2. Scaling Considerations

**Backend Scaling**
- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Database Scaling**: Separate cache storage (Redis) for data
- **Task Queue**: Celery for long-running backtest tasks
- **Monitoring**: Health checks and performance metrics

**Frontend Scaling**
- **CDN Distribution**: Static assets served via CDN
- **Bundle Optimization**: Code splitting and lazy loading
- **Caching**: Browser and CDN caching strategies
- **Performance Monitoring**: Real user monitoring (RUM)

This architecture documentation provides a comprehensive view of the system's design, implementation patterns, and operational considerations. The modular design ensures maintainability, extensibility, and scalability while maintaining high performance and security standards.
