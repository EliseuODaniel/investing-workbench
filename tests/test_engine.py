"""Tests for backtest engine."""

import pytest
import pandas as pd
from unittest.mock import Mock

from src.engine import BacktestEngine, State, Trade, Layer


class TestBacktestEngine:
    """Test backtest engine functionality."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = BacktestEngine(initial_cash=30000.0)

        assert engine.initial_cash == 30000.0
        assert engine.state.cash == 30000.0
        assert engine.state.equity_history == []
        assert engine.state.trades == []
        assert engine.state.layers == []

    def test_buy_execution(self):
        """Test buy order execution."""
        engine = BacktestEngine(initial_cash=30000.0)
        timestamp = pd.Timestamp("2023-01-01")

        # Successful buy
        result = engine.buy(timestamp, 50000.0, 0.1)  # 0.1 BTC at $50k = $5k

        assert result == True
        assert len(engine.state.layers) == 1
        assert len(engine.state.trades) == 1
        assert engine.state.cash == 25000.0  # 30k - 5k

        trade = engine.state.trades[0]
        assert trade.action == "BUY"
        assert trade.price == 50000.0
        assert trade.quantity == 0.1

        layer = engine.state.layers[0]
        assert layer.entry_price == 50000.0
        assert layer.quantity == 0.1

    def test_insufficient_funds_buy(self):
        """Test buy execution with insufficient funds."""
        engine = BacktestEngine(initial_cash=1000.0)
        timestamp = pd.Timestamp("2023-01-01")

        # Should fail due to insufficient funds
        result = engine.buy(timestamp, 50000.0, 1.0)  # 1 BTC at $50k = $50k

        assert result == False
        assert len(engine.state.layers) == 0
        assert len(engine.state.trades) == 0
        assert engine.state.cash == 1000.0

    def test_sell_execution(self):
        """Test sell order execution."""
        engine = BacktestEngine(initial_cash=30000.0)
        timestamp = pd.Timestamp("2023-01-01")

        # First buy to create a layer
        engine.buy(timestamp, 50000.0, 0.1)
        layer_id = engine.state.layers[0].layer_id

        # Sell the layer
        result = engine.sell(timestamp, 55000.0, 0.1, layer_id)

        assert result == True
        assert len(engine.state.layers) == 0  # Layer should be removed
        assert len(engine.state.trades) == 2  # Buy + Sell
        assert engine.state.cash > 30000.0  # Should have profit

        # Check sell trade
        sell_trade = engine.state.trades[-1]
        assert sell_trade.action == "SELL"
        assert sell_trade.price == 55000.0
        assert sell_trade.quantity == 0.1
        assert sell_trade.pnl == 500.0  # 0.1 * (55000 - 50000)

    def test_partial_sell(self):
        """Test partial position sell."""
        engine = BacktestEngine(initial_cash=30000.0)
        timestamp = pd.Timestamp("2023-01-01")

        # Buy 0.2 BTC
        engine.buy(timestamp, 50000.0, 0.2)
        layer_id = engine.state.layers[0].layer_id

        # Sell half (0.1 BTC)
        result = engine.sell(timestamp, 55000.0, 0.1, layer_id)

        assert result == True
        assert len(engine.state.layers) == 1  # Layer should remain with reduced quantity
        assert len(engine.state.trades) == 2

        remaining_layer = engine.state.layers[0]
        assert remaining_layer.quantity == 0.1  # Half sold
        # Original cost: $10,000, sold half: cost basis = $5,000
        # Remaining cost should be: $10,000 - $5,000 = $5,000
        assert abs(remaining_layer.cost - 5000.0) < 0.01  # Remaining cost

    def test_sell_invalid_layer(self):
        """Test sell execution for non-existent layer."""
        engine = BacktestEngine(initial_cash=30000.0)
        timestamp = pd.Timestamp("2023-01-01")

        # Try to sell non-existent layer
        result = engine.sell(timestamp, 55000.0, 0.1, 999)

        assert result == False
        assert len(engine.state.layers) == 0
        assert len(engine.state.trades) == 0

    def test_equity_tracking(self):
        """Test equity value tracking."""
        engine = BacktestEngine(initial_cash=30000.0)
        # Strategy that buys once on the first bar
        class BuyOnceStrategy:
            def __init__(self):
                self.done = False

            def on_bar(self, row, eng):
                if not self.done:
                    eng.buy(row.name, float(row["Close"]), 0.2)
                    self.done = True

        strategy = BuyOnceStrategy()

        # Two bars so equity captures the open position on the second bar
        data = pd.DataFrame(
            [
                {"Open": 50000.0, "High": 52000.0, "Low": 48000.0, "Close": 50000.0, "Volume": 1000.0},
                {"Open": 50500.0, "High": 52000.0, "Low": 50000.0, "Close": 51000.0, "Volume": 1000.0},
            ],
            index=[pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")],
        )

        engine.run(data, strategy)

        # Check equity tracking
        assert len(engine.state.equity_history) > 0
        assert len(engine.state.cash_history) > 0
        assert len(engine.state.timestamp_history) > 0

        # Final equity should be: cash + (BTC quantity * price)
        final_equity = engine.state.equity_history[-1]
        expected_equity = engine.state.cash  # All positions closed at end of run
        assert abs(final_equity - expected_equity) < 0.01
        # Engine should have captured equity including the open position on the second bar
        assert final_equity > engine.initial_cash

    def test_force_close_positions(self):
        """Test force close of all positions."""
        engine = BacktestEngine(initial_cash=30000.0)
        timestamp1 = pd.Timestamp("2023-01-01")
        timestamp2 = pd.Timestamp("2023-01-02")

        # Create multiple layers
        engine.buy(timestamp1, 50000.0, 0.1, layer_id=1)
        engine.buy(timestamp1, 45000.0, 0.15, layer_id=2)

        assert len(engine.state.layers) == 2

        # Force close at end price
        engine._close_all_positions(timestamp2, 48000.0)

        # All layers should be closed
        assert len(engine.state.layers) == 0
        sell_trades = [t for t in engine.state.trades if t.action == "SELL"]
        assert len(sell_trades) == 2
        # LIFO: last layer (id 2) should be sold first
        assert sell_trades[0].layer == 2
        assert abs(sell_trades[0].quantity - 0.15) < 1e-6
        assert sell_trades[1].layer == 1
        assert abs(sell_trades[1].quantity - 0.1) < 1e-6


class TestStateManagement:
    """Test state management functionality."""

    def test_state_initialization(self):
        """Test state initialization."""
        state = State(cash=30000.0)

        assert state.cash == 30000.0
        assert state.layers == []
        assert state.equity_history == []
        assert state.cash_history == []
        assert state.trades == []
        assert state.max_equity == 0.0

    def test_max_equity_tracking(self):
        """Test maximum equity tracking."""
        state = State(cash=30000.0)

        # Update equity history
        state.equity_history.append(30000.0)
        state.equity_history.append(32000.0)
        state.equity_history.append(31000.0)  # Lower than peak
        state.equity_history.append(35000.0)  # New peak

        # Update max equity manually (engine normally does this)
        state.max_equity = 35000.0

        assert state.max_equity == 35000.0

    def test_cash_yield_initialization(self):
        """Test engine initialization with cash yield parameters."""
        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=True,
            selic_rate_annual=0.12,
            yield_frequency="monthly"
        )

        assert engine.apply_cash_yield == True
        assert engine.selic_rate_annual == 0.12
        assert engine.yield_frequency == "monthly"
        assert engine._last_yield_month is None

    def test_cash_yield_disabled_by_default(self):
        """Test that cash yield is disabled by default."""
        engine = BacktestEngine(initial_cash=10000.0)

        assert engine.apply_cash_yield == False
        assert engine.selic_rate_annual == 0.13  # Default value
        assert engine.yield_frequency == "monthly"

    def test_apply_cash_yield_monthly(self):
        """Test monthly cash yield application."""
        from datetime import datetime

        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=True,
            selic_rate_annual=0.12,  # 12% annual = 1% monthly
            yield_frequency="monthly"
        )

        # Initial cash
        assert engine.state.cash == 10000.0
        assert engine.state.total_interest_earned == 0.0

        # Apply yield for January
        jan_timestamp = pd.Timestamp("2023-01-15")
        engine._apply_cash_yield(jan_timestamp)

        # Should apply 1% interest: 10000 * 0.01 = 100
        expected_cash = 10000.0 + 100.0
        expected_interest = 100.0

        assert engine.state.cash == expected_cash
        assert engine.state.total_interest_earned == expected_interest
        assert engine._last_yield_month == (1, 2023)  # January 2023

        # Apply yield for February
        feb_timestamp = pd.Timestamp("2023-02-15")
        engine._apply_cash_yield(feb_timestamp)

        # Should apply 1% interest on new cash: 10100 * 0.01 = 101
        expected_cash = 10100.0 + 101.0
        expected_interest = 100.0 + 101.0

        assert engine.state.cash == expected_cash
        assert engine.state.total_interest_earned == expected_interest
        assert engine._last_yield_month == (2, 2023)  # February 2023

    def test_no_yield_when_disabled(self):
        """Test that no yield is applied when cash yield is disabled."""
        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=False,
            selic_rate_annual=0.12
        )

        initial_cash = engine.state.cash
        initial_interest = engine.state.total_interest_earned

        # Try to apply yield
        timestamp = pd.Timestamp("2023-01-15")
        engine._apply_cash_yield(timestamp)

        # Cash should remain unchanged
        assert engine.state.cash == initial_cash
        assert engine.state.total_interest_earned == initial_interest
        assert engine._last_yield_month is None

    def test_no_duplicate_yield_in_same_month(self):
        """Test that yield is not applied multiple times in the same month."""
        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=True,
            selic_rate_annual=0.12,
            yield_frequency="monthly"
        )

        # Apply yield twice in January
        jan_timestamp1 = pd.Timestamp("2023-01-10")
        jan_timestamp2 = pd.Timestamp("2023-01-20")

        engine._apply_cash_yield(jan_timestamp1)
        first_cash = engine.state.cash
        first_interest = engine.state.total_interest_earned

        engine._apply_cash_yield(jan_timestamp2)

        # Should not apply yield again in same month
        assert engine.state.cash == first_cash
        assert engine.state.total_interest_earned == first_interest
        assert engine._last_yield_month == (1, 2023)

    def test_cash_yield_integration_with_backtest(self):
        """Test cash yield integration with simple backtest."""
        # Create test data spanning 3 months
        dates = pd.date_range("2023-01-01", "2023-03-31", freq="D")
        prices = [50000.0 + i * 10 for i in range(len(dates))]  # Slight uptrend

        data = pd.DataFrame({
            "Open": prices,
            "High": [p * 1.02 for p in prices],
            "Low": [p * 0.98 for p in prices],
            "Close": prices,
            "Volume": [1000] * len(dates)
        }, index=dates)

        # Mock strategy that does nothing (no trades)
        class MockStrategy:
            def on_bar(self, data, engine):
                pass

        # Run backtest with cash yield
        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=True,
            selic_rate_annual=0.12,  # 12% annual
            yield_frequency="monthly"
        )

        strategy = MockStrategy()
        result = engine.run(data, strategy)

        # Check that interest was earned (should be > 0 after 3 months)
        assert result["total_interest_earned"] > 0.0
        assert result["cash_yield_enabled"] == True
        assert result["selic_rate_annual"] == 0.12

        # Check that final cash includes interest
        expected_interest = 10000.0 * (0.12 / 12) * 3  # Rough estimate for 3 months
        assert result["final_cash"] > 10000.0

    def test_cash_yield_results_without_trades(self):
        """Test cash yield results when no trades are made."""
        # Create test data spanning 2 months
        dates = pd.date_range("2023-01-01", "2023-02-28", freq="D")
        prices = [50000.0] * len(dates)

        data = pd.DataFrame({
            "Open": prices,
            "High": prices,
            "Low": prices,
            "Close": prices,
            "Volume": [1000] * len(dates)
        }, index=dates)

        # Mock strategy that does nothing
        class MockStrategy:
            def on_bar(self, data, engine):
                pass

        # Run backtest with cash yield
        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=True,
            selic_rate_annual=0.12,
            yield_frequency="monthly"
        )

        strategy = MockStrategy()
        result = engine.run(data, strategy)

        # Should have earned interest but no trades
        assert result["total_interest_earned"] > 0.0
        assert result["total_trades"] == 0
        assert result["final_cash"] > 10000.0


class TestTradeAndLayer:
    """Test Trade and Layer dataclasses."""

    def test_trade_creation(self):
        """Test trade record creation."""
        timestamp = pd.Timestamp("2023-01-01")
        trade = Trade(
            timestamp=timestamp,
            action="BUY",
            price=50000.0,
            quantity=0.1,
            cost=5000.0,
            pnl=None,
            layer=1,
        )

        assert trade.timestamp == timestamp
        assert trade.action == "BUY"
        assert trade.price == 50000.0
        assert trade.quantity == 0.1
        assert trade.cost == 5000.0
        assert trade.pnl is None
        assert trade.layer == 1

    def test_layer_creation(self):
        """Test layer record creation."""
        timestamp = pd.Timestamp("2023-01-01")
        layer = Layer(
            entry_price=50000.0,
            quantity=0.1,
            cost=5000.0,
            timestamp=timestamp,
            layer_id=1,
        )

        assert layer.entry_price == 50000.0
        assert layer.quantity == 0.1
        assert layer.cost == 5000.0
        assert layer.timestamp == timestamp
        assert layer.layer_id == 1


if __name__ == "__main__":
    pytest.main([__file__])
