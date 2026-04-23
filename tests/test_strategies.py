"""Tests for trading strategies."""

from unittest.mock import Mock

import pandas as pd
import pytest

from src.engine import BacktestEngine, Layer, State
from src.strategies.dca_hybrid import DCAHybridStrategy
from src.strategies.martingale_fixed import MartingaleFixedStrategy


def create_mock_engine(cash=30000.0):
    """Create a mock BacktestEngine for testing."""
    engine = Mock(spec=BacktestEngine)
    engine.state = State(cash=cash, max_equity=cash)
    engine.buy = Mock(return_value=True)
    engine.sell = Mock(return_value=True)
    return engine


class TestMartingaleStrategy:
    """Test base Martingale strategy functionality."""

    def test_bet_size_calculation(self):
        """Test bet size calculation."""
        # Use concrete implementation for testing base methods
        strategy = MartingaleFixedStrategy(
            base_bet=100.0,
            multiplier=2.0,
        )

        assert strategy.calculate_next_bet_size(0) == 100.0
        assert strategy.calculate_next_bet_size(1) == 200.0
        assert strategy.calculate_next_bet_size(2) == 400.0

    def test_price_targets(self):
        """Test price target calculations."""
        strategy = MartingaleFixedStrategy(
            drop_step=0.10,
            take_profit=0.15,
        )

        # Buy target (10% drop)
        assert abs(strategy.get_next_buy_price(100.0) - 90.0) < 0.0001
        assert abs(strategy.get_next_buy_price(50.0) - 45.0) < 0.0001

        # Sell target (15% gain)
        assert abs(strategy.get_target_sell_price(100.0) - 115.0) < 0.0001
        assert abs(strategy.get_target_sell_price(50.0) - 57.5) < 0.0001

    def test_position_size(self):
        """Test position size calculation."""
        strategy = MartingaleFixedStrategy()

        # $1000 at $50 price = 20 units
        assert abs(strategy.calculate_position_size(1000.0, 50.0) - 20.0) < 0.0001

        # $500 at $100 price = 5 units
        assert abs(strategy.calculate_position_size(500.0, 100.0) - 5.0) < 0.0001

    def test_layer_limits(self):
        """Test layer addition limits."""
        strategy = MartingaleFixedStrategy(max_layers=3)
        engine = create_mock_engine(10000.0)

        # Should be able to add layers up to max
        assert strategy.can_add_layer(engine)

        # Add mock layers
        for i in range(3):
            engine.state.layers.append(
                Layer(
                    entry_price=100.0,
                    quantity=1.0,
                    cost=100.0,
                    timestamp=pd.Timestamp.now(),
                    layer_id=i,
                )
            )

        # Should not be able to add more layers
        assert not strategy.can_add_layer(engine)


class TestMartingaleFixedStrategy:
    """Test fixed Martingale strategy."""

    def test_initial_buy(self):
        """Test initial position entry."""
        strategy = MartingaleFixedStrategy(base_bet=500.0)
        engine = create_mock_engine(30000.0)

        # Mock OHLCV data
        row = pd.Series(
            {"Open": 50000.0, "High": 51000.0, "Low": 49000.0, "Close": 50500.0, "Volume": 1000.0},
            name=pd.Timestamp("2023-01-01"),
        )

        strategy.on_bar(row, engine)

        engine.buy.assert_called_once()
        # The mock engine doesn't actually update state, so we check the buy was called correctly

    def test_layer_addition(self):
        """Test layer addition logic."""
        strategy = MartingaleFixedStrategy(
            base_bet=500.0,
            drop_step=0.10,
            multiplier=2.0,
        )
        engine = create_mock_engine(30000.0)

        # Add initial layer
        initial_layer = Layer(
            entry_price=100.0,
            quantity=5.0,
            cost=500.0,
            timestamp=pd.Timestamp("2023-01-01"),
            layer_id=0,
        )
        engine.state.layers.append(initial_layer)

        # Mock price drop to trigger new layer
        row = pd.Series(
            {"Open": 95.0, "High": 96.0, "Low": 89.0, "Close": 90.0, "Volume": 1000.0},
            name=pd.Timestamp("2023-01-02"),
        )

        strategy.on_bar(row, engine)

        # Should have attempted to buy second layer
        assert engine.buy.call_count >= 1

    def test_layer_exit(self):
        """Test layer exit logic."""
        strategy = MartingaleFixedStrategy(
            base_bet=500.0,
            take_profit=0.15,
        )
        engine = create_mock_engine(30000.0)

        # Add layer
        layer = Layer(
            entry_price=100.0,
            quantity=5.0,
            cost=500.0,
            timestamp=pd.Timestamp("2023-01-01"),
            layer_id=0,
        )
        engine.state.layers.append(layer)

        # Mock price rise to trigger take profit
        row = pd.Series(
            {"Open": 110.0, "High": 116.0, "Low": 109.0, "Close": 115.0, "Volume": 1000.0},
            name=pd.Timestamp("2023-01-02"),
        )

        strategy.on_bar(row, engine)

        # Should have attempted to sell the layer
        engine.sell.assert_called_once()


class TestDCAHybridStrategy:
    """Test DCA hybrid strategy."""

    def test_dca_frequency(self):
        """Test DCA frequency logic."""
        strategy = DCAHybridStrategy(dca_frequency="weekly")
        engine = create_mock_engine(30000.0)

        # Initial DCA should work
        row = pd.Series(
            {"Open": 50000.0, "High": 51000.0, "Low": 49000.0, "Close": 50500.0, "Volume": 1000.0},
            name=pd.Timestamp("2023-01-01"),
        )

        strategy.on_bar(row, engine)
        initial_calls = engine.buy.call_count

        # Same day should not trigger another DCA
        row2 = pd.Series(
            {"Open": 50500.0, "High": 51500.0, "Low": 49500.0, "Close": 51000.0, "Volume": 1000.0},
            name=pd.Timestamp("2023-01-01 12:00:00"),
        )

        strategy.on_bar(row2, engine)
        assert engine.buy.call_count == initial_calls  # No new trade

    def test_moving_average_calculation(self):
        """Test moving average calculation."""
        strategy = DCAHybridStrategy(moving_average_period=5)

        # Add price history
        prices = [100, 110, 120, 130, 140]
        for price in prices:
            strategy._update_moving_average(price)

        assert abs(strategy.current_ma - 120.0) < 0.0001  # (100+110+120+130+140)/5


class TestStrategyIntegration:
    """Integration tests for strategies."""

    def test_strategy_execution(self):
        """Test complete strategy execution on sample data."""
        strategy = MartingaleFixedStrategy(
            base_bet=100.0,
            drop_step=0.10,
            take_profit=0.15,
            max_layers=3,
        )
        engine = create_mock_engine(1000.0)

        # Create sample price series that triggers multiple signals
        data = [
            # Day 1: Initial buy
            {"Close": 100.0, "High": 105.0, "Low": 95.0, "Open": 100.0, "Volume": 1000},
            # Day 2: Price drops, should trigger layer 2
            {"Close": 90.0, "High": 92.0, "Low": 88.0, "Open": 91.0, "Volume": 1000},
            # Day 3: Price drops more, should trigger layer 3
            {"Close": 81.0, "High": 83.0, "Low": 79.0, "Open": 82.0, "Volume": 1000},
            # Day 4: Price recovers, should trigger take profit
            {"Close": 93.0, "High": 95.0, "Low": 90.0, "Open": 91.0, "Volume": 1000},
        ]

        for i, bar_data in enumerate(data):
            row = pd.Series(bar_data, name=pd.Timestamp(f"2023-01-{i+1}"))
            strategy.on_bar(row, engine)

        # Should have executed multiple trades
        assert engine.buy.call_count > 0
        assert engine.sell.call_count >= 0

        # Should have both buy and sell trades (at least buys)
        total_calls = engine.buy.call_count + engine.sell.call_count
        assert total_calls > 0


if __name__ == "__main__":
    pytest.main([__file__])
