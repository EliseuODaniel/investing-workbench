"""Simple test to validate that non-Martingale strategies work with engine.state interface."""

import pandas as pd

from src.engine import BacktestEngine
from src.strategies.buy_and_hold import BuyAndHoldStrategy
from src.strategies.dca_simple import SimpleDCAStrategy
from src.strategies.trend_ma_cross import TrendMACrossStrategy


def test_buy_and_hold_with_engine_state():
    """Test that BuyAndHoldStrategy works with engine.state interface."""
    # Create strategy and engine
    strategy = BuyAndHoldStrategy(initial_capital=10000.0)
    engine = BacktestEngine(initial_cash=10000.0)

    # Create sample OHLCV data
    dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
    data = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "High": [101.0, 102.0, 103.0, 104.0, 105.0],
            "Low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "Close": [100.0, 101.0, 102.0, 103.0, 104.0],
            "Volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=dates,
    )

    # Process first bar - should buy
    strategy.reset()
    first_bar = data.iloc[0]
    strategy.on_bar(first_bar, engine)

    # Verify that trade was executed
    assert len(engine.state.trades) == 1
    assert engine.state.trades[0].action == "BUY"
    assert engine.state.trades[0].price == 100.0
    assert engine.state.cash < 10000.0  # Cash should be reduced

    # Verify strategy trades recorded
    assert len(strategy.trades) == 1
    assert strategy.trades[0]["action"] == "BUY"


def test_dca_simple_with_engine_state():
    """Test that SimpleDCAStrategy works with engine.state interface."""
    # Create strategy and engine
    strategy = SimpleDCAStrategy(
        initial_capital=10000.0,
        dca_amount=1000.0,
        dca_frequency="daily",
        start_immediately=True,
    )
    engine = BacktestEngine(initial_cash=10000.0)

    # Create sample OHLCV data
    dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
    data = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.0, 101.0, 102.0],
            "Volume": [1000, 1100, 1200],
        },
        index=dates,
    )

    # Process bars - should buy on first day
    strategy.reset()
    for i, (_date, row) in enumerate(data.iterrows()):
        strategy.on_bar(row, engine)
        if i == 0:  # First day should buy
            assert len(engine.state.trades) == 1
            assert engine.state.trades[0].action == "BUY"
            assert engine.state.cash < 10000.0

    # Verify strategy trades recorded
    assert len(strategy.trades) >= 1
    assert strategy.trades[0]["action"] == "BUY"


def test_trend_ma_cross_with_engine_state():
    """Test that TrendMACrossStrategy works with engine.state interface."""
    # Create strategy and engine with enough data for MA calculation
    strategy = TrendMACrossStrategy(
        initial_capital=10000.0,
        short_ma_period=3,
        long_ma_period=5,
    )
    engine = BacktestEngine(initial_cash=10000.0)

    # Create sample OHLCV data with enough points for MA
    dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
    data = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            "High": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
            "Low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
            "Close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            "Volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        },
        index=dates,
    )

    # Process bars
    strategy.reset()
    for _date, row in data.iterrows():
        strategy.on_bar(row, engine)

    # Verify that the strategy processed bars without errors
    # (We don't expect trades in this simple upward trend since MA cross may not trigger)
    assert len(strategy.price_history) == 10  # Should have recorded all prices
    assert engine.state.cash <= 10000.0  # Cash might be the same or less if trades occurred


def test_engine_state_properties():
    """Test that BacktestEngine properties work correctly."""
    engine = BacktestEngine(initial_cash=10000.0)

    # Test cash property
    assert engine.cash == 10000.0
    assert engine.state.cash == 10000.0
    assert engine.cash == engine.state.cash

    # Test layers property
    assert engine.layers == []
    assert engine.state.layers == []
    assert engine.layers == engine.state.layers

    # Simulate a trade to test state change
    dates = pd.date_range(start="2024-01-01", periods=1, freq="D")
    data = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [101.0],
            "Low": [99.0],
            "Close": [100.0],
            "Volume": [1000],
        },
        index=dates,
    )

    strategy = BuyAndHoldStrategy(initial_capital=10000.0)
    strategy.reset()

    # Execute a trade
    first_bar = data.iloc[0]
    strategy.on_bar(first_bar, engine)

    # Verify properties are still consistent
    assert engine.cash == engine.state.cash
    assert engine.layers == engine.state.layers
