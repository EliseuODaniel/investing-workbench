"""Tests for benchmark functionality."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.benchmarks import BenchmarkData, get_benchmark_data, get_selic_benchmark
from src.config import BenchmarkConfig, BacktestConfig, AppConfig, StrategyConfig


class TestBenchmarkData:
    """Test BenchmarkData class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.benchmark_manager = BenchmarkData(cache_dir="test_data")
        self.test_cache_dir = Path("test_data")
        self.test_cache_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove test cache files
        for file in self.test_cache_dir.glob("*_benchmark.parquet"):
            file.unlink()
        self.test_cache_dir.rmdir()

    @patch('src.benchmarks.yf.Ticker')
    def test_download_market_data_success(self, mock_ticker):
        """Test successful market data download."""
        # Mock yfinance data
        mock_data = pd.DataFrame({
            'Close': [100, 105, 102, 108, 110]
        })
        mock_data.index = pd.date_range('2023-01-01', periods=5, freq='D')

        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance

        result = self.benchmark_manager.download_market_data(
            'TEST', '2023-01-01', '2023-01-05', force_download=True
        )

        assert isinstance(result, pd.DataFrame)
        assert 'price' in result.columns
        assert len(result) == 5
        assert result['price'].iloc[0] == 100

    @patch('src.benchmarks.yf.Ticker')
    def test_download_market_data_empty(self, mock_ticker):
        """Test handling of empty market data."""
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance

        with pytest.raises(ValueError, match="No data found for ticker"):
            self.benchmark_manager.download_market_data(
                'EMPTY', '2023-01-01', '2023-01-05', force_download=True
            )

    def test_create_buy_hold_benchmark(self):
        """Test buy-and-hold benchmark creation."""
        # Create test price data
        price_data = pd.DataFrame({
            'price': [100, 105, 102, 108, 110]
        })

        result = self.benchmark_manager.create_buy_hold_benchmark(price_data, 10000)

        assert isinstance(result, pd.DataFrame)
        assert 'equity' in result.columns
        assert len(result) == len(price_data)
        # Initial equity should equal initial capital
        assert abs(result['equity'].iloc[0] - 10000) < 0.01
        # Final equity should be proportional to price change
        expected_final = 10000 * (110 / 100)
        assert abs(result['equity'].iloc[-1] - expected_final) < 0.01

    def test_create_buy_hold_benchmark_empty(self):
        """Test buy-and-hold benchmark with empty data."""
        price_data = pd.DataFrame({'price': []})
        result = self.benchmark_manager.create_buy_hold_benchmark(price_data, 10000)

        assert isinstance(result, pd.DataFrame)
        assert 'equity' in result.columns
        assert len(result) == 0

    @patch('src.benchmarks.get_monthly_rate')
    def test_create_selic_benchmark_fixed_rate(self, mock_get_monthly_rate):
        """Test SELIC benchmark creation with fixed rate."""
        mock_get_monthly_rate.return_value = 0.01  # 1% monthly

        result = self.benchmark_manager.create_selic_benchmark(
            '2023-01-01', '2023-03-31', 10000, use_real_selic=False
        )

        assert isinstance(result, pd.DataFrame)
        assert 'equity' in result.columns
        assert len(result) > 0
        # Should apply monthly returns
        assert result['equity'].iloc[-1] > 10000

    @patch('src.benchmarks.get_or_create_selic_data')
    def test_create_selic_benchmark_real_rate(self, mock_get_selic_data):
        """Test SELIC benchmark creation with real rates."""
        # Mock SELIC DataFrame
        mock_selic_df = pd.DataFrame({
            'year': [2023, 2023, 2023],
            'month': [1, 2, 3],
            'rate': [0.008, 0.009, 0.010]  # Jan, Feb, Mar rates
        })
        mock_get_selic_data.return_value = mock_selic_df

        result = self.benchmark_manager.create_selic_benchmark(
            '2023-01-01', '2023-03-31', 10000, use_real_selic=True
        )

        assert isinstance(result, pd.DataFrame)
        assert 'equity' in result.columns
        assert len(result) > 0

        # Verify that get_selic_data was called
        mock_get_selic_data.assert_called_once()

    def test_get_selic_data_caching(self):
        """Test SELIC data caching functionality."""
        with patch('src.benchmarks.get_or_create_selic_data') as mock_get_data:
            # Mock SELIC DataFrame
            mock_selic_df = pd.DataFrame({
                'year': [2023],
                'month': [1],
                'rate': [0.01]
            })
            mock_get_data.return_value = mock_selic_df

            # First call should load data
            result1 = self.benchmark_manager.get_selic_data("test_path.csv")

            # Second call should use cache
            result2 = self.benchmark_manager.get_selic_data("test_path.csv")

            # Should only call get_or_create_selic_data once due to caching
            mock_get_data.assert_called_once()
            assert result1 is result2  # Should be the same cached object

    @patch('src.benchmarks.get_or_create_selic_data')
    def test_create_selic_benchmark_with_caching(self, mock_get_selic_data):
        """Test that SELIC benchmark uses cached data correctly."""
        # Mock SELIC DataFrame
        mock_selic_df = pd.DataFrame({
            'year': [2023, 2023],
            'month': [1, 2],
            'rate': [0.01, 0.011]
        })
        mock_get_selic_data.return_value = mock_selic_df

        # Create multiple benchmarks with same SELIC path
        result1 = self.benchmark_manager.create_selic_benchmark(
            '2023-01-01', '2023-01-31', 10000, use_real_selic=True, selic_path="test.csv"
        )

        result2 = self.benchmark_manager.create_selic_benchmark(
            '2023-02-01', '2023-02-28', 10000, use_real_selic=True, selic_path="test.csv"
        )

        # Should only call get_or_create_selic_data once due to caching
        mock_get_selic_data.assert_called_once()

        # Both results should be valid DataFrames
        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)
        assert 'equity' in result1.columns
        assert 'equity' in result2.columns

    def test_calculate_benchmark_metrics(self):
        """Test benchmark metrics calculation."""
        # Create test equity curve with dates and 20% return
        dates = pd.date_range('2023-01-01', periods=5, freq='D')
        equity_curve = pd.DataFrame({
            'equity': [10000, 10500, 11000, 11500, 12000]
        }, index=dates)

        result = self.benchmark_manager.calculate_benchmark_metrics(
            equity_curve, '2023-01-01', '2023-01-05'
        )

        assert 'total_return' in result
        assert 'cagr' in result
        assert 'max_drawdown' in result
        assert 'sharpe_ratio' in result
        assert 'volatility' in result

        # Check total return (should be 20%)
        assert abs(result['total_return'] - 0.20) < 0.01

    def test_calculate_benchmark_metrics_empty(self):
        """Test metrics calculation with empty data."""
        equity_curve = pd.DataFrame({'equity': []})

        result = self.benchmark_manager.calculate_benchmark_metrics(
            equity_curve, '2023-01-01', '2023-01-05'
        )

        # Should return zeros for empty data
        assert result['total_return'] == 0.0
        assert result['cagr'] == 0.0
        assert result['max_drawdown'] == 0.0

    @patch('src.benchmarks.yf.Ticker')
    def test_get_benchmark_data(self, mock_ticker):
        """Test get_benchmark_data function."""
        # Mock yfinance data
        mock_data = pd.DataFrame({
            'Close': [100, 105, 102, 108, 110]
        })
        mock_data.index = pd.date_range('2023-01-01', periods=5, freq='D')

        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance

        result = get_benchmark_data(
            tickers=['TEST1', 'TEST2'],
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_capital=10000
        )

        assert isinstance(result, dict)
        assert 'TEST1' in result
        assert 'TEST2' in result
        assert 'equity_curve' in result['TEST1']
        assert 'metrics' in result['TEST1']

    @patch('src.benchmarks.get_monthly_rate')
    def test_get_selic_benchmark(self, mock_get_monthly_rate):
        """Test get_selic_benchmark function."""
        mock_get_monthly_rate.return_value = 0.01

        result = get_selic_benchmark(
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_capital=10000
        )

        assert isinstance(result, dict)
        assert 'equity_curve' in result
        assert 'metrics' in result
        assert isinstance(result['equity_curve'], pd.DataFrame)
        assert 'equity' in result['equity_curve'].columns


class TestBenchmarkConfig:
    """Test benchmark configuration."""

    def test_benchmark_config_creation(self):
        """Test BenchmarkConfig creation."""
        config = BenchmarkConfig(
            ticker='^BVSP',
            name='IBOVESPA',
            enabled=True
        )

        assert config.ticker == '^BVSP'
        assert config.name == 'IBOVESPA'
        assert config.enabled is True

    def test_benchmark_config_defaults(self):
        """Test BenchmarkConfig default values."""
        config = BenchmarkConfig(
            ticker='SPY',
            name='S&P 500'
        )

        assert config.enabled is True  # Default value

    def test_backtest_config_with_benchmarks(self):
        """Test BacktestConfig with benchmark settings."""
        benchmarks = [
            BenchmarkConfig('^BVSP', 'IBOVESPA', True),
            BenchmarkConfig('SPY', 'S&P 500', False)
        ]

        config = BacktestConfig(
            initial_capital=30000,
            benchmarks=benchmarks,
            include_selic_benchmark=True,
            include_buy_hold_benchmark=False
        )

        assert len(config.benchmarks) == 2
        assert config.include_selic_benchmark is True
        assert config.include_buy_hold_benchmark is False
        assert config.benchmarks[0].enabled is True
        assert config.benchmarks[1].enabled is False

    def test_app_config_with_benchmarks(self):
        """Test AppConfig with benchmark configurations."""
        benchmarks = [
            BenchmarkConfig('^BVSP', 'IBOVESPA', True)
        ]

        backtest_config = BacktestConfig(
            benchmarks=benchmarks,
            include_selic_benchmark=True
        )

        strategy = StrategyConfig(
            name="Test Strategy",
            class_path="strategies.test.TestStrategy",
            parameters={}
        )

        app_config = AppConfig(
            backtest=backtest_config,
            strategies=[strategy]
        )

        assert app_config.backtest.benchmarks is not None
        assert len(app_config.backtest.benchmarks) == 1
        assert app_config.backtest.include_selic_benchmark is True


class TestBenchmarkIntegration:
    """Test integration of benchmarks with configuration."""

    def test_config_serialization_with_benchmarks(self):
        """Test that configuration with benchmarks can be serialized."""
        benchmarks = [
            BenchmarkConfig('^BVSP', 'IBOVESPA', True),
            BenchmarkConfig('ETH-USD', 'Ethereum', False)
        ]

        backtest_config = BacktestConfig(
            initial_capital=25000,
            benchmarks=benchmarks,
            include_selic_benchmark=True,
            include_buy_hold_benchmark=False
        )

        strategy = StrategyConfig(
            name="Test Strategy",
            class_path="strategies.test.TestStrategy",
            parameters={}
        )

        app_config = AppConfig(
            backtest=backtest_config,
            strategies=[strategy]
        )

        # Test serialization
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            app_config.to_file(temp_path)

            # Read and verify content
            with open(temp_path, 'r') as f:
                content = f.read()

            # Check that benchmark fields are present
            assert 'benchmarks:' in content
            assert 'ticker: ^BVSP' in content
            assert 'name: IBOVESPA' in content
            assert 'enabled: true' in content
            assert 'include_selic_benchmark: true' in content
            assert 'include_buy_hold_benchmark: false' in content

            # Test deserialization
            loaded_config = AppConfig.from_file(temp_path)
            assert len(loaded_config.backtest.benchmarks) == 2
            assert loaded_config.backtest.include_selic_benchmark is True
            assert loaded_config.backtest.include_buy_hold_benchmark is False

        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])