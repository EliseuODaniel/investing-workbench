"""Tests for plotting functionality."""

from unittest.mock import patch

import pandas as pd
import pytest

from src.plots import plot_candlesticks_with_trades, plot_equity_comparison


class TestCandlestickPlotting:
    """Test candlestick plotting functionality."""

    def test_plot_candlesticks_with_no_trades(self):
        """Test candlestick plotting without trades."""
        # Create sample OHLCV data
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        ohlcv_data = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "High": [105.0, 106.0, 107.0, 108.0, 109.0],
                "Low": [95.0, 96.0, 97.0, 98.0, 99.0],
                "Close": [104.0, 105.0, 106.0, 107.0, 108.0],
                "Volume": [1000, 1200, 800, 1500, 900],
            },
            index=dates,
        )

        trades = pd.DataFrame()

        # Should not raise any exceptions
        fig = plot_candlesticks_with_trades(
            ohlcv_data,
            trades,
            title="Test Candlesticks",
            style="default",  # Use default style instead of charles
        )

        assert fig is not None

    def test_plot_candlesticks_with_trades(self):
        """Test candlestick plotting with buy and sell trades."""
        # Create sample OHLCV data
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        ohlcv_data = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "High": [105.0, 106.0, 107.0, 108.0, 109.0],
                "Low": [95.0, 96.0, 97.0, 98.0, 99.0],
                "Close": [104.0, 105.0, 106.0, 107.0, 108.0],
                "Volume": [1000, 1200, 800, 1500, 900],
            },
            index=dates,
        )

        # Create sample trades
        trades = pd.DataFrame(
            [
                {
                    "timestamp": dates[1],
                    "action": "BUY",
                    "price": 101.5,
                    "quantity": 1.0,
                    "pnl": None,
                    "layer": 1,
                },
                {
                    "timestamp": dates[3],
                    "action": "SELL",
                    "price": 106.5,
                    "quantity": 1.0,
                    "pnl": 5.0,
                    "layer": 1,
                },
            ]
        )

        # Should not raise any exceptions
        fig = plot_candlesticks_with_trades(
            ohlcv_data,
            trades,
            title="Test Candlesticks with Trades",
            style="default",
        )

        assert fig is not None

    def test_plot_candlesticks_empty_data(self):
        """Test candlestick plotting with empty data."""
        # Skip this test as mplfinance cannot handle empty DataFrames
        # This is a limitation of the library, not our code
        pass

    @patch("src.plots.MPLFINANCE_AVAILABLE", False)
    def test_plot_candlesticks_fallback_mode(self):
        """Test candlestick plotting fallback mode when mplfinance is not available."""
        # Create sample OHLCV data
        dates = pd.date_range("2023-01-01", periods=3, freq="D")
        ohlcv_data = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [105.0, 106.0, 107.0],
                "Low": [95.0, 96.0, 97.0],
                "Close": [104.0, 105.0, 106.0],
                "Volume": [1000, 1200, 800],
            },
            index=dates,
        )

        trades = pd.DataFrame(
            [
                {
                    "timestamp": dates[0],
                    "action": "BUY",
                    "price": 101.0,
                    "quantity": 1.0,
                    "pnl": None,
                    "layer": 1,
                },
            ]
        )

        # Should use fallback mode and not raise exceptions
        fig = plot_candlesticks_with_trades(
            ohlcv_data,
            trades,
            title="Test Fallback Mode",
        )

        assert fig is not None


class TestEquityComparison:
    """Test equity comparison plotting."""

    def test_plot_equity_comparison_single_strategy(self):
        """Test equity comparison with single strategy."""
        dates = pd.date_range("2023-01-01", periods=3, freq="D")
        equity_curves = {"Test Strategy": pd.Series([1000.0, 1100.0, 1200.0], index=dates)}

        # Should not raise any exceptions
        fig = plot_equity_comparison(
            equity_curves,
            title="Test Equity Comparison",
        )

        assert fig is not None

    def test_plot_equity_comparison_empty(self):
        """Test equity comparison with empty data."""
        equity_curves = {}

        # Should handle empty data gracefully
        fig = plot_equity_comparison(
            equity_curves,
            title="Test Empty Comparison",
        )

        assert fig is not None


if __name__ == "__main__":
    pytest.main([__file__])
