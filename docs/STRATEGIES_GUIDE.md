# Trading Strategies Guide

This guide provides comprehensive documentation of the available trading strategies inside Investing Workbench, including their theoretical foundations, parameters, and optimal use cases.

## Overview

The framework includes two main categories of strategies:

1. **Martingale Strategies**: Position sizing strategies that increase exposure after losses
2. **Traditional Strategies**: Standard trading approaches without Martingale mechanics

## Martingale Strategies

### Core Concepts

**Martingale trading** involves increasing position sizes after losing trades to recover previous losses and achieve profit. The key principles are:

- **Progressive Position Sizing**: Each layer is larger than the previous
- **Mean Reversion Assumption**: Expectation that prices will return to average
- **Risk Management**: Maximum layers and position limits control exposure
- **LIFO Exit**: Last-In, First-Out layer management

### Risk Considerations

⚠️ **Warning**: Martingale strategies carry high risk:
- Require substantial capital reserves
- Can lead to rapid capital depletion
- Perform poorly in trending markets
- May hit maximum layer limits

### 1. Fixed Martingale

**Class Name**: `MartingaleFixedStrategy`

**Description**: Classic Martingale implementation with fixed parameters throughout the backtest period.

#### Algorithm

```
1. Initial buy at base_bet amount
2. If price drops by drop_step% (low <= target), buy next layer
3. Layer size = base_bet * (multiplier ^ layer_number)
4. When any layer hits take_profit target (high >= target), sell that layer
5. All trades execute at close price with 0.05% slippage
6. Repeat until max_layers or end of data
```

#### Signal & Execution Model

**Signal Detection**:
- **Buy Signals**: `low_price <= target_buy_price` (layer triggers)
- **Sell Signals**: `high_price >= target_sell_price` (take-profit triggers)

**Trade Execution**:
- **Price**: `close_price` of the candle
- **Slippage**: Default 0.05% (configurable via strategy kwargs)
- **Fill Guarantee**: All detected signals execute (no missed fills)
- **Conservative Model**: Avoids unrealistic perfect-timing assumptions

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `base_bet` | $100-$2000 | $500 | Initial investment amount |
| `multiplier` | 1.5-3.0 | 2.0 | Position size growth factor |
| `drop_step` | 5%-15% | 10% | Price drop for new layer |
| `take_profit` | 10%-25% | 15% | Profit target per layer |
| `max_layers` | 3-15 | 10 | Maximum concurrent layers |

#### Risk Level: High

**Best For**: Volatile, range-bound markets with frequent reversions

**Example Configuration**
```yaml
- name: "Fixed Martingale"
  class_path: "strategies.martingale_fixed.MartingaleFixedStrategy"
  parameters:
    base_bet: 750.0
    multiplier: 2.0
    drop_step: 0.08      # 8% drop triggers new layer
    take_profit: 0.18    # 18% take profit
    max_layers: 8
```

#### Performance Characteristics

- **Capital Efficiency**: Moderate (requires 30-50% of capital for full layer stack)
- **Win Rate**: High (80-95% typical)
- **Risk**: High (potential for complete capital loss)
- **Market Conditions**: Best in choppy/sideways markets

#### Mathematical Analysis

**Total Capital Required**:
```
Total = base_bet * (1 + multiplier + multiplier^2 + ... + multiplier^(max_layers-1))
```

**Break-even Requirements**:
```
Win Rate > 1 / (1 + take_profit * (1 / drop_step))
```

### 2. Volatility-Adjusted Martingale

**Class Name**: `MartingaleVolatilityStrategy`

**Description**: Dynamic Martingale that adjusts parameters based on market volatility using ATR and standard deviation.

#### Algorithm

```
1. Calculate market volatility (ATR and standard deviation)
2. Adjust position sizing inversely to volatility
3. Modify take-profit targets based on volatility
4. Execute volatility-adjusted Martingale with conservative execution:
   - Buy triggers: low_price <= volatility_adjusted_target
   - Position size: adjusted_base_bet * (multiplier ^ layer_number)
5. High volatility = smaller positions, wider targets
6. Low volatility = larger positions, tighter targets
7. All trades execute at close price with default 0.05% slippage
```

#### Signal & Execution Model

**Buy Signals**:
```python
# Volatility-adjusted layer trigger
base_target = entry_price * (1 - drop_step)
volatility_factor = 1 / (1 + vol_multiplier * volatility_ratio)
adjusted_target = base_target * volatility_factor
signal = low_price <= adjusted_target
```

**Sell Signals**:
```python
# Standard take-profit with volatility consideration
base_target = entry_price * (1 + take_profit)
volatility_adjusted_tp = base_target * (1 + volatility_factor * 0.1)  # Slight adjustment
signal = high_price >= volatility_adjusted_tp
```

**Trade Execution**: All trades execute at `close_price` with configurable slippage:
```python
execution_price = close_price * (1 - slippage)  # BUY
execution_price = close_price * (1 + slippage)  # SELL
```

#### Volatility Calculations

**Average True Range (ATR)**:
```
ATR = 14-period average of True Range
True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
```

**Position Size Adjustment**:
```
adjusted_base_bet = base_bet / (1 + vol_multiplier * volatility_ratio)
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `base_bet` | $100-$2000 | $500 | Base investment amount |
| `multiplier` | 1.5-3.0 | 2.0 | Position size multiplier |
| `drop_step` | 5%-15% | 8% | Base drop step (adjusted by volatility) |
| `take_profit` | 10%-25% | 18% | Base take profit (adjusted by volatility) |
| `max_layers` | 3-12 | 8 | Maximum concurrent layers |
| `volatility_period` | 10-50 | 20 | Period for volatility calculation |
| `vol_multiplier` | 0.5-2.0 | 1.0 | Volatility adjustment factor |
| `atr_period` | 10-30 | 14 | ATR calculation period |
| `slippage` | 0.01%-0.5% | 0.05% | Trade execution slippage |

#### Risk Level: Medium-High

**Best For**: Markets with variable volatility; adaptive risk management

**Example Configuration**
```yaml
- name: "Volatility-Adjusted Martingale"
  class_path: "strategies.martingale_vol_adj.MartingaleVolatilityStrategy"
  parameters:
    base_bet: 600.0
    multiplier: 2.2
    drop_step: 0.07
    take_profit: 0.20
    max_layers: 10
    volatility_period: 25
    vol_multiplier: 1.5
    atr_period: 14
```

#### Performance Characteristics

- **Adaptability**: High (adjusts to market conditions)
- **Capital Efficiency**: Better than fixed in high volatility periods
- **Win Rate**: Variable (70-90% typical)
- **Market Conditions**: Excellent in volatile, changing markets

### 3. Trailing Take-Profit Martingale

**Class Name**: `MartingaleTrailingTPStrategy`

**Description**: Martingale strategy with trailing stop-loss to lock in profits while allowing upside potential.

#### Algorithm

```
1. Execute standard Martingale buy signals (low <= target)
2. Set trailing stop when position becomes profitable
3. Trail stop by trailing_percent from peak price
4. Sell when price hits trailing stop or take-profit target (high >= target)
5. All trailing stop sells execute at close price with slippage
6. Continue layer management as standard Martingale
```

#### Trailing Stop Logic

```
# Peak tracking and trailing stop calculation
if current_price > entry_price * (1 + take_profit):
    peak_price = max(peak_price, current_price)
    trailing_stop = peak_price * (1 - trailing_percent)

# Trailing stop execution at close with slippage
elif current_price <= trailing_stop:
    execute_sell(price=current_price * (1 + slippage))
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `base_bet` | $100-$2000 | $500 | Base investment amount |
| `multiplier` | 1.5-3.0 | 2.0 | Position size multiplier |
| `drop_step` | 5%-15% | 10% | Price drop for new layer |
| `take_profit` | 10%-25% | 20% | Initial take profit target |
| `max_layers` | 3-12 | 8 | Maximum concurrent layers |
| `trailing_percent` | 3%-15% | 5% | Trailing stop percentage |

#### Risk Level: Medium

**Best For**: Trending markets with momentum; wants to capture upside

**Example Configuration**
```yaml
- name: "Trailing TP Martingale"
  class_path: "strategies.martingale_trailing_tp.MartingaleTrailingTPStrategy"
  parameters:
    base_bet: 500.0
    multiplier: 2.0
    drop_step: 0.10
    take_profit: 0.25    # 25% initial target
    max_layers: 8
    trailing_percent: 0.07  # 7% trailing stop
```

#### Performance Characteristics

- **Profit Potential**: Higher than fixed Martingale in trends
- **Risk Management**: Better than fixed (profit protection)
- **Complexity**: Medium (requires tracking peaks and stops)
- **Market Conditions**: Excellent in strong trending markets

### 4. Risk-Cap Martingale

**Class Name**: `MartingaleRiskCapStrategy`

**Description**: Advanced Martingale with comprehensive risk management including position limits, drawdown controls, and emergency stops.

#### Risk Management Features

1. **Maximum Position Size**: Limits total portfolio exposure
2. **Drawdown-Based Sizing**: Reduces position size after significant drawdowns
3. **Emergency Stop**: Complete position closure on severe losses
4. **Layer Limits**: Dynamic maximum layer adjustment based on portfolio health

#### Algorithm

```
1. Calculate current portfolio metrics and risk limits
2. Apply position size limits (max_position_pct of portfolio)
3. Check drawdown and adjust sizing if necessary
4. Execute risk-constrained Martingale with conservative execution:
   - Buy triggers: low_price <= target AND within risk limits
   - Position size: min(base_bet * (multiplier ^ layer_number), risk_limit)
   - All trades execute at close price with default 0.05% slippage
5. Trigger emergency stop if losses exceed stop_loss_pct
6. Reset risk metrics on profitable periods
```

#### Signal & Execution Model

**Buy Signals (Risk-Constrained)**:
```python
# Check layer trigger with risk constraints
target_price = entry_price * (1 - drop_step)
layer_size = base_bet * (multiplier ^ layer_number)
risk_ok = (current_exposure + layer_size) <= max_total_exposure
signal = low_price <= target_price and risk_ok and not emergency_stopped
```

**Sell Signals**:
```python
# Standard take-profit or emergency stop
take_profit_signal = high_price >= (entry_price * (1 + take_profit))
emergency_signal = current_drawdown >= stop_loss_pct
signal = take_profit_signal or emergency_signal
```

**Trade Execution**: All trades execute at `close_price` with configurable slippage:
```python
execution_price = close_price * (1 - slippage)  # BUY
execution_price = close_price * (1 + slippage)  # SELL

# Emergency stops execute immediately at market (close price)
if emergency_stop:
    execute_all_positions_at_market()
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `base_bet` | $100-$2000 | $500 | Base investment amount |
| `multiplier` | 1.5-3.0 | 2.0 | Position size multiplier |
| `drop_step` | 5%-15% | 10% | Price drop for new layer |
| `take_profit` | 10%-25% | 15% | Profit target per layer |
| `max_layers` | 3-15 | 10 | Maximum concurrent layers |
| `max_position_pct` | 50%-95% | 80% | Maximum portfolio in positions |
| `max_total_exposure` | $5000-$50000 | $10000 | Maximum total USD exposure |
| `stop_loss_pct` | 20%-50% | 30% | Emergency stop loss threshold |
| `drawdown_threshold` | 15%-40% | 25% | Drawdown for position reduction |
| `position_size_reduction` | 25%-75% | 50% | Position size reduction amount |
| `emergency_stop` | boolean | true | Enable emergency stop feature |
| `slippage` | 0.01%-0.5% | 0.05% | Trade execution slippage |

#### Risk Level: Medium

**Best For**: Risk-averse traders who want Martingale exposure with capital protection

**Example Configuration**
```yaml
- name: "Risk-Cap Martingale"
  class_path: "strategies.martingale_risk_cap.MartingaleRiskCapStrategy"
  parameters:
    base_bet: 800.0
    multiplier: 2.0
    drop_step: 0.08
    take_profit: 0.12
    max_layers: 12
    max_position_pct: 0.75    # Max 75% in positions
    max_total_exposure: 15000.0
    stop_loss_pct: 0.35       # 35% emergency stop
    drawdown_threshold: 0.20  # 20% drawdown triggers reduction
    position_size_reduction: 0.6  # 40% size reduction
    emergency_stop: true
```

#### Performance Characteristics

- **Capital Preservation**: Excellent (strong risk controls)
- **Return Potential**: Moderate (limited by risk constraints)
- **Complexity**: High (multiple risk management layers)
- **Market Conditions**: Suitable for most market conditions with some protection

### 5. DCA Hybrid Martingale

**Class Name**: `DCAHybridStrategy`

**Description**: Combines Dollar Cost Averaging with limited Martingale layers for long-term accumulation with enhanced returns.

#### Strategy Logic

```
1. Execute regular DCA purchases (weekly/monthly) at close price with slippage
2. Add Martingale layers on significant price drops (>DCA trigger threshold):
   - DCA: Time-based purchases at close price
   - Martingale: low_price <= trigger AND price < moving_average
3. Limit Martingale exposure (max_martingale_layers)
4. Use wider take-profit targets for long-term holding
5. All trades execute at close price with default 0.05% slippage
6. Continue DCA regardless of Martingale activity
```

#### Signal & Execution Model

**DCA Component (Time-Based)**:
```python
# Regular DCA purchases (weekly/monthly/daily)
if is_scheduled_dca_date():
    execute_dca_purchase()

# DCA execution at close price
dca_quantity = dca_amount / close_price
execution_price = close_price * (1 + slippage)  # BUY with slippage
```

**Martingale Component (Signal-Based)**:
```python
# Martingale layer triggers
price_below_ma = close_price < moving_average
significant_drop = close_price <= (moving_average * (1 - dca_trigger_threshold))
can_add_layer = current_martingale_layers < max_martingale_layers

martingale_signal = price_below_ma and significant_drop and can_add_layer

# Martingale execution at close price
if martingale_signal:
    layer_size = base_bet * (multiplier ^ current_martingale_layers)
    execution_price = close_price * (1 + slippage)  # BUY with slippage
```

**Sell Signals**:
```python
# Take-profit for Martingale layers only (DCA holds long-term)
target_price = layer_entry_price * (1 + take_profit)
sell_signal = high_price >= target_price and layer_type == "martingale"

# Execution at close price with slippage
execution_price = close_price * (1 - slippage)  # SELL with slippage
```

#### Dual-Strategy Components

**DCA Component**:
- Fixed periodic purchases
- Time-based accumulation
- Market exposure regardless of price action

**Martingale Component**:
- Layered buying on significant dips
- Higher entry prices averaged down
- Limited exposure for risk control

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `dca_amount` | $100-$2000 | $500 | Fixed DCA purchase amount |
| `dca_frequency` | daily/weekly/monthly | weekly | DCA purchase frequency |
| `dca_trigger_threshold` | 2%-15% | 5% | Dip percentage for Martingale activation |
| `moving_average_period` | 20-200 | 50 | MA period for trend context |
| `base_bet` | $100-$2000 | $500 | Martingale base amount |
| `multiplier` | 1.5-2.5 | 1.5 | Conservative Martingale multiplier |
| `drop_step` | 8%-20% | 15% | Wider drops for Martingale layers |
| `take_profit` | 15%-30% | 20% | Higher targets for long-term gains |
| `max_martingale_layers` | 2-6 | 3 | Limited Martingale exposure |
| `slippage` | 0.01%-0.5% | 0.05% | Trade execution slippage |

#### Risk Level: Low-Medium

**Best For**: Long-term Bitcoin accumulation with enhanced returns

**Example Configuration**
```yaml
- name: "DCA Hybrid"
  class_path: "strategies.dca_hybrid.DCAHybridStrategy"
  parameters:
    dca_amount: 1000.0
    dca_frequency: "weekly"
    dca_trigger_threshold: 0.08    # 8% below MA for Martingale
    moving_average_period: 50
    base_bet: 400.0
    multiplier: 1.8
    drop_step: 0.12            # 12% drops for Martingale
    take_profit: 0.25          # 25% targets
    max_martingale_layers: 4
```

#### Performance Characteristics

- **Long-term Focus**: Excellent (combines accumulation with opportunistic buying)
- **Risk Level**: Low-Medium (DCA provides downside protection)
- **Return Enhancement**: Moderate (Martingale adds to DCA base)
- **Market Conditions**: Works well in most markets, especially with BTC's long-term uptrend

## Traditional Strategies

### 1. Buy & Hold

**Class Name**: `BuyAndHoldStrategy`

**Description**: Simple strategy that invests all capital at the beginning and holds until the end.

#### Algorithm

```
1. Buy BTC with all initial capital on first day
2. Hold position throughout entire period
3. No selling or rebalancing
4. Final value = initial BTC * final price
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `initial_capital` | $1000-$100000 | $30000 | Total amount to invest |

#### Risk Level: Low

**Best For**: Long-term investors who believe in Bitcoin's appreciation

**Example Configuration**
```yaml
- name: "Buy & Hold"
  class_path: "strategies.buy_and_hold.BuyAndHoldStrategy"
  parameters:
    initial_capital: 30000.0
```

#### Performance Characteristics

- **Simplicity**: Maximum (buy once, hold forever)
- **Volatility Exposure**: 100% (no risk management)
- **Long-term Performance**: Historically strong for Bitcoin
- **Market Timing**: No market timing attempt

### 2. Dollar Cost Averaging (DCA)

**Class Name**: `SimpleDCAStrategy`

**Description**: Fixed periodic purchases to average out price volatility over time.

#### Algorithm

```
1. Calculate purchase amount based on frequency
2. Buy fixed amount of BTC on each schedule
3. Continue regardless of price action
4. Final value = accumulated BTC * final price
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `initial_capital` | $1000-$100000 | $30000 | Total capital to invest |
| `dca_amount` | $50-$5000 | $1000 | Fixed purchase amount |
| `dca_frequency` | daily/weekly/monthly | monthly | Purchase frequency |
| `start_immediately` | boolean | true | Buy on first day or wait for schedule |

#### Risk Level: Low

**Best For**: Risk-averse long-term accumulation

**Example Configuration**
```yaml
- name: "Monthly DCA"
  class_path: "strategies.dca_simple.SimpleDCAStrategy"
  parameters:
    initial_capital: 30000.0
    dca_amount: 1000.0
    dca_frequency: "monthly"
    start_immediately: true
```

#### Performance Characteristics

- **Price Volatility Reduction**: Excellent (averages out price fluctuations)
- **Risk Level**: Low (time diversification)
- **Capital Efficiency**: Moderate (some cash remains uninvested)
- **Market Conditions**: Works well in volatile, upward-trending markets

### 3. Trend Following (Moving Average Crossover)

**Class Name**: `TrendMACrossStrategy`

**Description**: Uses moving average crossovers to identify trend direction and trade accordingly.

#### Algorithm

```
1. Calculate short and long moving averages
2. Generate buy signal when short MA crosses above long MA
3. Generate sell signal when short MA crosses below long MA
4. Invest position_size_pct of available capital per signal
5. Maintain minimum cash reserve
```

#### Moving Average Calculations

```
Short_MA = average(closing_prices, short_ma_period)
Long_MA = average(closing_prices, long_ma_period)

Buy_Signal = Short_MA crosses above Long_MA
Sell_Signal = Short_MA crosses below Long_MA
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `initial_capital` | $1000-$100000 | $30000 | Total capital available |
| `short_ma_period` | 5-20 | 10 | Short-term moving average period |
| `long_ma_period` | 20-100 | 30 | Long-term moving average period |
| `position_size_pct` | 0.1-2.0 | 1.0 | Percentage of capital per trade |
| `min_cash_reserve` | $500-$5000 | $1000 | Minimum cash to maintain |

#### Risk Level: Medium

**Best For**: Trending markets with clear directional movements

**Example Configuration**
```yaml
- name: "Trend Following (Fast MA Cross)"
  class_path: "strategies.trend_ma_cross.TrendMACrossStrategy"
  parameters:
    initial_capital: 30000.0
    short_ma_period: 10
    long_ma_period: 30
    position_size_pct: 1.0
    min_cash_reserve: 1000.0
```

#### Performance Characteristics

- **Trend Capture**: Excellent (rides major trends)
- **Whipsaw Risk**: High (false signals in choppy markets)
- **Risk Level**: Medium (position sizing controls exposure)
- **Market Conditions**: Best in clear trending markets

### 4. Mean Reversion (Bollinger Bands)

**Class Name**: `MeanReversionStrategy`

**Description**: Trades based on price reverting to historical mean using Bollinger Bands.

#### Algorithm

```
1. Calculate Bollinger Bands (20-period SMA ± 2 standard deviations)
2. Generate signals based on band penetration:
   - Buy signal: low_price <= lower_band (oversold condition)
   - Sell signal: high_price >= upper_band or close_price >= middle_band
3. Execute trades at close price with conservative slippage modeling
4. Use position sizing based on band penetration depth
5. Maintain minimum cash reserve
```

#### Signal & Execution Model

**Buy Signals (Oversold Condition)**:
```python
# Lower band touch/cross detection
lower_band = sma_20 - (bb_std_dev * std_dev_20)
oversold_signal = low_price <= lower_band

# Position sizing based on penetration depth
penetration = (lower_band - low_price) / lower_band
position_size = base_position * (1 + penetration * 0.5)
```

**Sell Signals (Mean Reversion)**:
```python
# Target levels for profit taking
middle_band = sma_20  # Primary target
upper_band = sma_20 + (bb_std_dev * std_dev_20)  # Secondary target

mean_revert_signal = high_price >= middle_band
overbought_signal = high_price >= upper_band
sell_signal = mean_revert_signal or overbought_signal
```

**Trade Execution**: All trades execute at `close_price` with configurable slippage:
```python
execution_price = close_price * (1 + slippage)    # BUY
execution_price = close_price * (1 - slippage)    # SELL

# Realistic execution acknowledges we can't buy at exact low/high
# This prevents look-ahead bias and provides conservative results
```

#### Bollinger Band Calculations

```
Middle_Band = 20-period SMA
Upper_Band = Middle_Band + (2 * 20-period standard deviation)
Lower_Band = Middle_Band - (2 * 20-period standard deviation)
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `initial_capital` | $1000-$100000 | $30000 | Total capital available |
| `bb_period` | 10-30 | 20 | Bollinger Bands period |
| `bb_std_dev` | 1.5-3.0 | 2.0 | Standard deviation multiplier |
| `position_size_pct` | 0.1-2.0 | 1.0 | Percentage of capital per trade |
| `min_cash_reserve` | $500-$5000 | $1000 | Minimum cash to maintain |
| `slippage` | 0.01%-0.5% | 0.05% | Trade execution slippage |

#### Risk Level: Medium

**Best For**: Range-bound markets with mean-reverting characteristics

**Example Configuration**
```yaml
- name: "Mean Reversion (Bollinger Bands)"
  class_path: "strategies.mean_reversion.MeanReversionStrategy"
  parameters:
    initial_capital: 30000.0
    bb_period: 20
    bb_std_dev: 2.0
    position_size_pct: 1.0
    min_cash_reserve: 1000.0
```

#### Performance Characteristics

- **Range Trading**: Excellent in sideways/choppy markets
- **Trend Following**: Poor (loses money in strong trends)
- **Risk Level**: Medium (frequent small trades)
- **Market Conditions**: Best in range-bound markets

### 5. Breakout Trading

**Class Name**: `BreakoutStrategy`

**Description**: Trades price breakouts from support/resistance levels based on volatility.

#### Algorithm

```
1. Calculate support and resistance levels using recent price action
2. Identify volatility ranges (ATR-based) for dynamic levels
3. Generate breakout signals with realistic execution:
   - Buy breakout: high_price > resistance AND volume confirmation
   - Sell breakdown: low_price < support OR stop-loss triggered
4. Execute trades at close price with conservative slippage modeling
5. Use trailing stops for profit protection
```

#### Signal & Execution Model

**Buy Signals (Upside Breakout)**:
```python
# Resistance breakout detection
resistance = recent_high + (atr * resistance_multiplier)
volume_avg = average_volume(volume_period)
volume_confirmation = current_volume > (volume_avg * volume_multiplier)

breakout_signal = high_price > resistance and volume_confirmation

# Prevent false breakouts by requiring sustained momentum
if breakout_signal:
    execute_at_close_with_slippage()
```

**Sell Signals (Breakdown or Stop Loss)**:
```python
# Support breakdown
support = recent_low - (atr * support_multiplier)
breakdown_signal = low_price < support

# Trailing stop loss for open positions
if position_open:
    trailing_stop = calculate_trailing_stop(high_since_entry)
    stop_loss_signal = low_price <= trailing_stop

sell_signal = breakdown_signal or stop_loss_signal

# Execute at close price with slippage
execution_price = close_price * (1 - slippage)  # SELL
```

**Trade Execution**: All trades execute at `close_price` with configurable slippage:
```python
# Conservative execution model acknowledges market reality
# We can't execute at exact breakout point (high/low)
execution_price = close_price * (1 + slippage)  # BUY breakout
execution_price = close_price * (1 - slippage)  # SELL breakdown

# This provides realistic backtesting results without look-ahead bias
```

#### Breakout Calculations

```
Support = recent_low - (ATR * support_multiplier)
Resistance = recent_high + (ATR * resistance_multiplier)

Breakout_Confirmed = price > Resistance AND volume > avg_volume * volume_multiplier
```

#### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `initial_capital` | $1000-$100000 | $30000 | Total capital available |
| `lookback_period` | 10-50 | 20 | Period for support/resistance |
| `atr_period` | 10-30 | 14 | ATR calculation period |
| `atr_multiplier` | 1.0-3.0 | 2.0 | ATR multiplier for levels |
| `position_size_pct` | 0.1-2.0 | 1.0 | Percentage of capital per trade |
| `min_cash_reserve` | $500-$5000 | $1000 | Minimum cash to maintain |
| `slippage` | 0.01%-0.5% | 0.05% | Trade execution slippage |

#### Risk Level: High

**Best For**: Momentum markets with clear breakout patterns

**Example Configuration**
```yaml
- name: "Breakout Trading (20-day)"
  class_path: "strategies.breakout.BreakoutStrategy"
  parameters:
    initial_capital: 30000.0
    lookback_period: 20
    atr_period: 14
    atr_multiplier: 2.0
    position_size_pct: 1.0
    min_cash_reserve: 1000.0
```

#### Performance Characteristics

- **Momentum Capture**: Excellent in strong trending markets
- **False Breakdowns**: High risk of fake breakouts
- **Risk Level**: High (requires active management)
- **Market Conditions**: Best with confirmed breakouts and volume

## Strategy Selection Guide

### Risk Tolerance Assessment

| Risk Level | Suitable Strategies | Capital Requirement | Expected Volatility |
|------------|---------------------|-------------------|-------------------|
| **Low** | Buy & Hold, DCA | Low | High (100% exposure) |
| **Low-Medium** | DCA Hybrid | Low-Medium | Medium |
| **Medium** | Risk-Cap Martingale, Trend Following, Mean Reversion | Medium | Medium |
| **Medium-High** | Volatility-Adjusted Martingale, Trailing TP | Medium-High | Medium |
| **High** | Fixed Martingale, Breakout Trading | High | High (layer exposure) |

### Market Condition Suitability

| Market Condition | Recommended Strategies | Avoid |
|------------------|------------------------|--------|
| **Strong Uptrend** | Buy & Hold, Trend Following, Trailing TP | Mean Reversion |
| **Strong Downtrend** | DCA (accumulation), Cash | All Martingale, Trend Following |
| **Sideways/Choppy** | Mean Reversion, DCA, Volatility-Adjusted | Trend Following, Breakout |
| **High Volatility** | Volatility-Adjusted, Risk-Cap, DCA Hybrid | Fixed Martingale |
| **Low Volatility** | Fixed Martingale, Trend Following | Volatility strategies |

### Investment Horizon

| Time Horizon | Recommended Strategies | Notes |
|--------------|------------------------|-------|
| **Short-term (days-weeks)** | Breakout Trading, Mean Reversion | Active management required |
| **Medium-term (months)** | Trend Following, Volatility-Adjusted | Requires monitoring |
| **Long-term (years)** | Buy & Hold, DCA, DCA Hybrid | Set and forget approach |

### Capital Requirements

| Available Capital | Suitable Strategies | Minimum Recommended |
|------------------|---------------------|-------------------|
| **$1,000-$5,000** | DCA, Buy & Hold | Fixed Martingale (max 3 layers) |
| **$5,000-$20,000** | Most traditional strategies | Limited Martingale (5-7 layers) |
| **$20,000-$50,000** | All traditional, Risk-Cap Martingale | Full Martingale (8-10 layers) |
| **$50,000+** | All strategies including aggressive Martingale | Maximum configuration flexibility |

## Strategy Comparison

### Performance Metrics Comparison

Based on historical Bitcoin data (2020-2023):

| Strategy | Total Return | Max Drawdown | Sharpe Ratio | Hit Rate | Capital Efficiency |
|----------|--------------|--------------|--------------|----------|-------------------|
| **Buy & Hold** | 1000%+ | -76% | 0.73 | 100% | Excellent |
| **DCA Monthly** | 600-800% | -65% | 0.65 | 100% | Good |
| **Fixed Martingale** | 50-200% | -40% | 0.3-0.8 | 85-95% | Poor-Medium |
| **Risk-Cap Martingale** | 20-150% | -25% | 0.2-0.6 | 80-90% | Medium |
| **Volatility-Adjusted** | 30-180% | -35% | 0.3-0.7 | 75-88% | Medium-Good |
| **Trend Following** | 100-400% | -50% | 0.4-0.9 | 40-60% | Good |
| **Mean Reversion** | 50-200% | -30% | 0.3-0.8 | 60-75% | Good |

### Complexity Analysis

| Strategy | Implementation Complexity | Monitoring Required | Parameter Sensitivity |
|----------|--------------------------|-------------------|---------------------|
| **Buy & Hold** | Very Low | None | None |
| **DCA** | Low | Low | Low |
| **Fixed Martingale** | Medium | Medium | Medium |
| **Risk-Cap Martingale** | High | Medium | High |
| **Volatility-Adjusted** | High | Medium | High |
| **Trend Following** | Medium | High | Medium |
| **Mean Reversion** | Medium | High | Medium |
| **Breakout Trading** | High | High | High |

## Best Practices

### Parameter Optimization

1. **Backtest Multiple Time Periods**: Test across different market cycles
2. **Walk-Forward Analysis**: Optimize on training data, test on out-of-sample
3. **Monte Carlo Simulation**: Test robustness with random variations
4. **Stress Testing**: Evaluate performance under extreme market conditions

### Risk Management

1. **Position Sizing**: Never risk more than you can afford to lose
2. **Diversification**: Consider combining multiple strategies
3. **Stop Losses**: Implement emergency stops for Martingale strategies
4. **Capital Reserves**: Maintain cash buffers for unexpected opportunities

### Monitoring and Maintenance

1. **Regular Performance Reviews**: Monthly or quarterly strategy assessment
2. **Parameter Rebalancing**: Adjust parameters based on market regime changes
3. **Market Regime Detection**: Identify when strategies may underperform
4. **Tax Considerations**: Account for tax implications of frequent trading

This comprehensive guide provides the foundation for understanding, selecting, and implementing trading strategies within Investing Workbench. Remember that all strategies carry risk, and past performance does not guarantee future results.
