"""Benchmark data management for performance comparison.

This module handles downloading, caching, and processing benchmark data
from various sources including market indices and SELIC rates.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .selic import get_monthly_rate, get_or_create_selic_data

logger = logging.getLogger(__name__)


class BenchmarkData:
    """Class to manage benchmark data and operations."""

    def __init__(self, cache_dir: str = "data"):
        """Initialize benchmark data manager.

        Args:
            cache_dir: Directory to cache benchmark data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._selic_cache = {}  # Cache for SELIC DataFrames by path

    def download_market_data(self, ticker: str, start_date: str, end_date: str,
                           force_download: bool = False) -> pd.DataFrame:
        """Download market data for a given ticker.

        Args:
            ticker: Yahoo Finance ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            force_download: Force re-download even if cached data exists

        Returns:
            DataFrame with Date index and price data
        """
        cache_file = self.cache_dir / f"{ticker.replace('^', '')}_benchmark.parquet"

        # Check if cached data exists and is valid
        if not force_download and cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                df.index = pd.to_datetime(df.index)

                # Check if cached data covers the requested period
                if df.index.min() <= pd.to_datetime(start_date) and df.index.max() >= pd.to_datetime(end_date):
                    logger.info(f"Using cached benchmark data for {ticker}")
                    return df.loc[start_date:end_date]
                else:
                    logger.info(f"Cached data for {ticker} doesn't cover full period, re-downloading")
            except Exception as e:
                logger.warning(f"Error reading cached benchmark data for {ticker}: {e}")

        # Download data from Yahoo Finance
        logger.info(f"Downloading benchmark data for {ticker} from {start_date} to {end_date}")
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(start=start_date, end=end_date)

            if data.empty:
                raise ValueError(f"No data found for ticker {ticker}")

            # Use 'Close' prices for benchmark
            df = pd.DataFrame({
                'price': data['Close']
            })
            df.index = df.index.tz_localize(None)  # Remove timezone for consistency

            # Cache the data
            df.to_parquet(cache_file)
            logger.info(f"Cached benchmark data for {ticker} to {cache_file}")

            return df

        except Exception as e:
            logger.error(f"Error downloading data for {ticker}: {e}")
            raise

    def get_selic_data(self, selic_path: Optional[str] = None,
                      fallback_rate_annual: float = 0.13) -> Optional[pd.DataFrame]:
        """Get SELIC data with caching.

        Args:
            selic_path: Path to SELIC data file
            fallback_rate_annual: Annual fallback rate

        Returns:
            DataFrame with SELIC data or None if unavailable
        """
        selic_path = selic_path or "data/selic.csv"

        # Check cache first
        if selic_path in self._selic_cache:
            logger.debug(f"Using cached SELIC data for {selic_path}")
            return self._selic_cache[selic_path]

        # Load data using the selic module
        selic_data = get_or_create_selic_data(
            path=selic_path,
            use_download=False,
            fallback_rate_annual=fallback_rate_annual
        )

        # Cache the result
        if selic_data is not None:
            self._selic_cache[selic_path] = selic_data
            logger.debug(f"Cached SELIC data for {selic_path}")

        return selic_data

    def create_buy_hold_benchmark(self, price_data: pd.DataFrame,
                                initial_capital: float = 30000.0) -> pd.DataFrame:
        """Create buy-and-hold benchmark equity curve from price data.

        Args:
            price_data: DataFrame with price data
            initial_capital: Initial investment amount

        Returns:
            DataFrame with equity curve
        """
        if price_data.empty:
            return pd.DataFrame(columns=['equity'])

        # Calculate number of shares/units bought with initial capital
        initial_price = price_data['price'].iloc[0]
        shares = initial_capital / initial_price

        # Create equity curve
        equity_curve = pd.DataFrame({
            'equity': price_data['price'] * shares
        })

        return equity_curve

    def create_selic_benchmark(self, start_date: str, end_date: str,
                             initial_capital: float = 30000.0,
                             use_real_selic: bool = False,
                             selic_path: Optional[str] = None,
                             selic_fallback_rate: float = 0.13) -> pd.DataFrame:
        """Create SELIC benchmark equity curve.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            initial_capital: Initial investment amount
            use_real_selic: Whether to use real SELIC rates
            selic_path: Path to SELIC data file
            selic_fallback_rate: Fallback annual rate

        Returns:
            DataFrame with equity curve
        """
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        # Load SELIC data if using real rates
        selic_data = None
        if use_real_selic:
            selic_data = self.get_selic_data(selic_path, selic_fallback_rate)

        # Create date range for the period
        dates = pd.date_range(start=start_dt, end=end_dt, freq='D')

        # Initialize equity curve
        equity = initial_capital
        equity_values = []

        # Process each day
        current_date = start_dt
        monthly_rate_applied = False

        for date in dates:
            # Check if this is the first day of a new month
            if date.month != current_date.month or date == start_dt:
                current_date = date
                monthly_rate_applied = False

            if not monthly_rate_applied:
                # Apply monthly return on first day of month
                if use_real_selic:
                    monthly_rate = get_monthly_rate(selic_data, date.year, date.month,
                                                  selic_fallback_rate)
                else:
                    # Convert annual rate to monthly
                    monthly_rate = selic_fallback_rate / 12

                equity *= (1 + monthly_rate)
                monthly_rate_applied = True

            equity_values.append(equity)

        # Create daily equity curve
        equity_curve = pd.DataFrame({
            'equity': equity_values
        }, index=dates)

        return equity_curve

    def calculate_benchmark_metrics(self, equity_curve: pd.DataFrame,
                                  start_date: str, end_date: str) -> Dict:
        """Calculate performance metrics for a benchmark.

        Args:
            equity_curve: DataFrame with equity values
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with calculated metrics
        """
        if equity_curve.empty:
            return {
                'total_return': 0.0,
                'cagr': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'volatility': 0.0
            }

        # Filter to date range
        filtered_data = equity_curve.loc[start_date:end_date]
        if filtered_data.empty:
            return {
                'total_return': 0.0,
                'cagr': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'volatility': 0.0
            }

        equity = filtered_data['equity'].values
        initial_equity = equity[0]
        final_equity = equity[-1]

        # Calculate daily returns
        daily_returns = np.diff(equity) / equity[:-1]
        daily_returns = np.append(daily_returns, 0)  # Add 0 for last day

        # Total return
        total_return = (final_equity / initial_equity) - 1

        # CAGR (Compound Annual Growth Rate)
        days = len(filtered_data)
        years = days / 365.25
        cagr = (final_equity / initial_equity) ** (1 / years) - 1 if years > 0 else 0

        # Maximum drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_drawdown = np.min(drawdown)

        # Volatility (annualized)
        volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0

        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0

        return {
            'total_return': total_return,
            'cagr': cagr,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility
        }


def get_benchmark_data(tickers: List[str], start_date: str, end_date: str,
                      initial_capital: float = 30000.0,
                      force_download: bool = False,
                      cache_dir: str = "data") -> Dict[str, Dict]:
    """Get benchmark data for multiple tickers.

    Args:
        tickers: List of ticker symbols
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        initial_capital: Initial investment for each benchmark
        force_download: Force re-download of data
        cache_dir: Cache directory

    Returns:
        Dictionary mapping ticker names to benchmark data
    """
    benchmark_manager = BenchmarkData(cache_dir)
    benchmarks = {}

    for ticker in tickers:
        try:
            # Download price data
            price_data = benchmark_manager.download_market_data(
                ticker, start_date, end_date, force_download
            )

            # Create equity curve
            equity_curve = benchmark_manager.create_buy_hold_benchmark(
                price_data, initial_capital
            )

            # Calculate metrics
            metrics = benchmark_manager.calculate_benchmark_metrics(
                equity_curve, start_date, end_date
            )

            benchmarks[ticker] = {
                'equity_curve': equity_curve,
                'metrics': metrics,
                'price_data': price_data
            }

            logger.info(f"Successfully processed benchmark {ticker}")

        except Exception as e:
            logger.error(f"Error processing benchmark {ticker}: {e}")
            continue

    return benchmarks


def get_selic_benchmark(start_date: str, end_date: str,
                       initial_capital: float = 30000.0,
                       use_real_selic: bool = False,
                       selic_path: Optional[str] = None,
                       selic_fallback_rate: float = 0.13,
                       cache_dir: str = "data") -> Dict:
    """Get SELIC benchmark data.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        initial_capital: Initial investment
        use_real_selic: Whether to use real SELIC rates
        selic_path: Path to SELIC data file
        selic_fallback_rate: Fallback annual rate
        cache_dir: Cache directory

    Returns:
        Dictionary with SELIC benchmark data
    """
    benchmark_manager = BenchmarkData(cache_dir)

    # Create SELIC equity curve
    equity_curve = benchmark_manager.create_selic_benchmark(
        start_date, end_date, initial_capital, use_real_selic, selic_path, selic_fallback_rate
    )

    # Calculate metrics
    metrics = benchmark_manager.calculate_benchmark_metrics(equity_curve, start_date, end_date)

    return {
        'equity_curve': equity_curve,
        'metrics': metrics,
        'price_data': None  # SELIC doesn't have price data in the traditional sense
    }