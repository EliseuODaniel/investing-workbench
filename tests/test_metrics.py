"""Tests for performance metrics calculation."""

import pytest
import pandas as pd
import numpy as np

from src.metrics import calculate_metrics, compare_strategies


class TestMetricsCalculation:
    """Test performance metrics calculation."""

    def test_basic_return_calculation(self):
        """Test basic return calculation."""
        # Simple equity curve: 30k -> 33k = 10% return
        dates = pd.date_range("2023-01-01", periods=4, freq="D")
        equity = pd.Series([30000.0, 31000.0, 32000.0, 33000.0], index=dates)
        trades = pd.DataFrame()
        initial_capital = 30000.0

        metrics = calculate_metrics(equity, trades, initial_capital)

        assert metrics["total_return"] == 0.1  # 10%
        assert metrics["cagr"] > 0
        assert metrics["max_drawdown"] <= 0

    def test_drawdown_calculation(self):
        """Test drawdown calculation."""
        # Equity curve with peak and drawdown
        dates = pd.date_range("2023-01-01", periods=6, freq="D")
        equity = pd.Series([30000.0, 35000.0, 40000.0, 35000.0, 32000.0, 38000.0], index=dates)
        trades = pd.DataFrame()
        initial_capital = 30000.0

        metrics = calculate_metrics(equity, trades, initial_capital)

        # Max drawdown should be from 40k to 32k = 20%
        assert abs(metrics["max_drawdown"] - (-0.2)) < 0.01

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation."""
        # Create a more realistic equity curve
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 100)  # Daily returns
        equity_values = [30000.0]

        for ret in returns:
            equity_values.append(equity_values[-1] * (1 + ret))

        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        equity = pd.Series(equity_values[1:], index=dates)  # Exclude initial value
        trades = pd.DataFrame()
        initial_capital = 30000.0

        metrics = calculate_metrics(equity, trades, initial_capital)

        # Sharpe ratio should be calculated
        assert isinstance(metrics["sharpe_ratio"], float)
        assert not np.isnan(metrics["sharpe_ratio"])

    def test_trade_statistics(self):
        """Test trade statistics calculation."""
        dates = pd.date_range("2023-01-01", periods=3, freq="D")
        equity = pd.Series([30000.0, 32000.0, 34000.0], index=dates)
        trades = pd.DataFrame([
            {"action": "BUY", "price": 100.0, "quantity": 10.0, "cost": 1000.0, "timestamp": dates[0]},
            {"action": "SELL", "price": 110.0, "quantity": 10.0, "cost": 1000.0, "pnl": 100.0, "timestamp": dates[1]},
            {"action": "SELL", "price": 95.0, "quantity": 5.0, "cost": 500.0, "pnl": -25.0, "timestamp": dates[2]},
        ])
        initial_capital = 30000.0

        metrics = calculate_metrics(equity, trades, initial_capital)

        assert metrics["total_trades"] == 3
        assert metrics["buy_trades"] == 1
        assert metrics["sell_trades"] == 2

        # Hit rate should be 50% (1 win, 1 loss)
        assert abs(metrics["hit_rate"] - 0.5) < 0.01

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_equity = pd.Series([])
        empty_trades = pd.DataFrame()
        initial_capital = 30000.0

        metrics = calculate_metrics(empty_equity, empty_trades, initial_capital)

        assert "error" in metrics

    def test_layer_pnl_calculation(self):
        """Test PnL calculation by layer."""
        dates = pd.date_range("2023-01-01", periods=2, freq="D")
        equity = pd.Series([30000.0, 31000.0], index=dates)
        trades = pd.DataFrame([
            {"action": "SELL", "price": 110.0, "quantity": 10.0, "cost": 1000.0, "pnl": 100.0, "layer": 1, "timestamp": dates[0]},
            {"action": "SELL", "price": 105.0, "quantity": 8.0, "cost": 800.0, "pnl": 40.0, "layer": 1, "timestamp": dates[0]},
            {"action": "SELL", "price": 95.0, "quantity": 5.0, "cost": 500.0, "pnl": -25.0, "layer": 2, "timestamp": dates[1]},
        ])
        initial_capital = 30000.0

        metrics = calculate_metrics(equity, trades, initial_capital)

        # Should calculate PnL by layer
        assert "layer_pnl" in metrics
        assert isinstance(metrics["layer_pnl"], dict)
        assert 1 in metrics["layer_pnl"]  # Layer 1 should exist
        assert 2 in metrics["layer_pnl"]  # Layer 2 should exist


class TestStrategyComparison:
    """Test strategy comparison functionality."""

    def test_single_strategy_comparison(self):
        """Test comparison with single strategy."""
        strategy_name = "Test Strategy"
        dates = pd.date_range("2023-01-01", periods=3)
        equity = pd.Series([30000.0, 32000.0, 34000.0], index=dates)
        trades = pd.DataFrame()

        results = {
            strategy_name: {
                "equity": pd.DataFrame({"equity": equity}, index=dates),
                "trades": trades,
                "start_price": 100.0,
                "end_price": 113.33,  # Approximate
            }
        }

        comparison = compare_strategies(results, 30000.0)

        assert len(comparison) == 1
        assert comparison.iloc[0]["Strategy"] == strategy_name

    def test_multiple_strategy_comparison(self):
        """Test comparison with multiple strategies."""
        dates = pd.date_range("2023-01-01", periods=3)

        # Strategy A: Better performance
        equity_a = pd.Series([30000.0, 33000.0, 36000.0], index=dates)
        trades_a = pd.DataFrame()

        # Strategy B: Worse performance
        equity_b = pd.Series([30000.0, 31000.0, 32000.0], index=dates)
        trades_b = pd.DataFrame()

        results = {
            "Strategy A": {
                "equity": pd.DataFrame({"equity": equity_a}, index=dates),
                "trades": trades_a,
                "start_price": 100.0,
                "end_price": 120.0,
            },
            "Strategy B": {
                "equity": pd.DataFrame({"equity": equity_b}, index=dates),
                "trades": trades_b,
                "start_price": 100.0,
                "end_price": 106.67,
            },
        }

        comparison = compare_strategies(results, 30000.0)

        assert len(comparison) == 2
        # Strategy A should be first (better performance)
        assert comparison.iloc[0]["Strategy"] == "Strategy A"
        assert comparison.iloc[1]["Strategy"] == "Strategy B"

        # Verify returns
        assert comparison.iloc[0]["total_return"] > comparison.iloc[1]["total_return"]

    def test_empty_results_handling(self):
        """Test handling of empty results."""
        empty_results = {}
        comparison = compare_strategies(empty_results, 30000.0)

        assert comparison.empty

    def test_invalid_results_handling(self):
        """Test handling of invalid results."""
        invalid_results = {
            "Invalid Strategy": {
                "equity": pd.DataFrame(),  # Empty equity
                "trades": pd.DataFrame(),
            }
        }

        comparison = compare_strategies(invalid_results, 30000.0)

        assert comparison.empty


if __name__ == "__main__":
    pytest.main([__file__])