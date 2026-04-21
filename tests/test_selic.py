"""Tests for SELIC real monthly rates functionality."""

import os
import tempfile

import pandas as pd
import pytest

from src.engine import BacktestEngine
from src.selic import (
    _aggregate_daily_rates_to_monthly,
    generate_fake_selic_data,
    get_monthly_rate,
    get_or_create_selic_data,
    load_selic_data,
    save_selic_data,
    validate_selic_data,
)


class TestSELICData:
    """Test SELIC data generation and loading."""

    def test_generate_fake_selic_data(self):
        """Test fake SELIC data generation."""
        df = generate_fake_selic_data()

        assert not df.empty
        assert len(df) == 5 * 12  # 5 years (2020-2024) * 12 months
        assert list(df.columns) == ["year", "month", "rate"]
        assert df["year"].min() >= 2020
        assert df["year"].max() <= 2024
        assert df["month"].min() >= 1
        assert df["month"].max() <= 12
        assert df["rate"].min() > 0
        assert df["rate"].max() < 0.05  # Max ~5% monthly

    def test_save_and_load_selic_data(self):
        """Test saving and loading SELIC data."""
        # Create test data
        test_data = pd.DataFrame(
            {"year": [2023, 2023, 2024], "month": [1, 2, 1], "rate": [0.01, 0.011, 0.012]}
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_selic_data(test_data, temp_path)

            # Load and verify
            loaded_data = load_selic_data(temp_path)
            assert loaded_data is not None
            assert len(loaded_data) == 3
            assert list(loaded_data.columns) == ["year", "month", "rate"]
            assert loaded_data.iloc[0]["year"] == 2023
            assert loaded_data.iloc[0]["month"] == 1
            assert loaded_data.iloc[0]["rate"] == 0.01

        finally:
            os.unlink(temp_path)

    def test_get_monthly_rate_exact_match(self):
        """Test getting monthly rate with exact match."""
        selic_data = pd.DataFrame(
            {"year": [2023, 2023, 2023], "month": [1, 2, 3], "rate": [0.01, 0.011, 0.012]}
        )

        # Test exact matches
        rate = get_monthly_rate(selic_data, 2023, 1)
        assert rate == 0.01

        rate = get_monthly_rate(selic_data, 2023, 2)
        assert rate == 0.011

        rate = get_monthly_rate(selic_data, 2023, 3)
        assert rate == 0.012

    def test_get_monthly_rate_fallback_to_last(self):
        """Test fallback to last available rate."""
        selic_data = pd.DataFrame({"year": [2023], "month": [1], "rate": [0.015]})

        # Test fallback to last available
        rate = get_monthly_rate(selic_data, 2023, 12)  # Month not in data
        assert rate == 0.015  # Should use last available rate

    def test_get_monthly_rate_fallback_to_configured(self):
        """Test fallback to configured annual rate."""
        selic_data = pd.DataFrame()  # Empty data

        # Test fallback to annual rate converted to monthly
        rate = get_monthly_rate(selic_data, 2023, 6, fallback_rate_annual=0.12)
        expected_monthly = (1 + 0.12) ** (1 / 12) - 1
        assert abs(rate - expected_monthly) < 1e-6

    def test_validate_selic_data(self):
        """Test SELIC data validation."""
        # Valid data
        valid_data = pd.DataFrame({"year": [2023, 2023], "month": [1, 2], "rate": [0.01, 0.011]})
        assert validate_selic_data(valid_data)

        # Empty data
        assert not validate_selic_data(pd.DataFrame())
        assert not validate_selic_data(None)

        # Missing columns
        invalid_data = pd.DataFrame(
            {
                "year": [2023],
                "month": [1],
                # Missing 'rate' column
            }
        )
        assert not validate_selic_data(invalid_data)

        # Invalid year range
        invalid_year = pd.DataFrame({"year": [1800], "month": [1], "rate": [0.01]})
        assert not validate_selic_data(invalid_year)

        # Invalid month range
        invalid_month = pd.DataFrame({"year": [2023], "month": [13], "rate": [0.01]})
        assert not validate_selic_data(invalid_month)

        # Invalid rate range
        invalid_rate = pd.DataFrame(
            {"year": [2023], "month": [1], "rate": [0.1]}  # 10% monthly is too high
        )
        assert not validate_selic_data(invalid_rate)

    def test_get_or_create_selic_data_with_file(self):
        """Test getting/creating SELIC data when file exists."""
        # Create temporary file with test data
        test_data = pd.DataFrame({"year": [2023], "month": [1], "rate": [0.01]})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_selic_data(test_data, temp_path)

            # Should load existing file
            loaded_data = get_or_create_selic_data(
                path=temp_path, use_download=False  # Don't try to download
            )

            assert loaded_data is not None
            assert len(loaded_data) == 1
            assert loaded_data.iloc[0]["year"] == 2023

        finally:
            os.unlink(temp_path)

    def test_aggregate_daily_rates_to_monthly(self):
        """Daily SELIC should be compounded into an effective monthly rate."""
        daily = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2023-01-02",
                        "2023-01-03",
                        "2023-01-04",
                        "2023-02-01",
                        "2023-02-02",
                    ]
                ),
                "rate": [0.001, 0.002, 0.003, 0.004, 0.005],
            }
        )

        monthly = _aggregate_daily_rates_to_monthly(daily)

        assert len(monthly) == 2
        january_rate = (1.001 * 1.002 * 1.003) - 1
        february_rate = (1.004 * 1.005) - 1
        assert monthly.iloc[0]["year"] == 2023
        assert monthly.iloc[0]["month"] == 1
        assert monthly.iloc[0]["rate"] == pytest.approx(january_rate)
        assert monthly.iloc[1]["month"] == 2
        assert monthly.iloc[1]["rate"] == pytest.approx(february_rate)

    def test_invalid_monthly_cache_is_rebuilt_from_download(self, monkeypatch):
        """An invalid cached monthly file should be replaced by a valid download."""
        invalid_cache = pd.DataFrame(
            {
                "year": [2023, 2023],
                "month": [1, 2],
                "rate": [0.1365, 0.1390],
            }
        )
        downloaded_daily = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2023-01-02",
                        "2023-01-03",
                        "2023-02-01",
                        "2023-02-02",
                    ]
                ),
                "rate": [0.0004, 0.0004, 0.0005, 0.0005],
            }
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_selic_data(invalid_cache, temp_path)

            monkeypatch.setattr(
                "src.selic.download_daily_selic_data",
                lambda start_date=None, end_date=None: downloaded_daily.copy(),
            )

            rebuilt = get_or_create_selic_data(
                path=temp_path,
                use_download=True,
                start_date="2023-01-01",
                end_date="2023-02-28",
            )

            assert rebuilt is not None
            assert rebuilt["rate"].max() < 0.05
            reloaded = load_selic_data(temp_path)
            assert reloaded is not None
            assert reloaded["rate"].max() < 0.05
        finally:
            os.unlink(temp_path)


class TestBacktestEngineWithSELIC:
    """Test BacktestEngine with real SELIC rates."""

    def test_engine_with_real_selic_enabled(self):
        """Test BacktestEngine initialization with real SELIC."""
        # Create temporary SELIC file
        selic_data = pd.DataFrame(
            {
                "year": [2023, 2023, 2023],
                "month": [1, 2, 3],
                "rate": [0.01, 0.011, 0.012],  # 1%, 1.1%, 1.2%
            }
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_selic_data(selic_data, temp_path)

            # Initialize engine with real SELIC
            engine = BacktestEngine(
                initial_cash=10000.0,
                apply_cash_yield=True,
                use_real_selic=True,
                selic_path=temp_path,
                selic_fallback_rate=0.13,
            )

            assert engine.use_real_selic
            assert engine.selic_path == temp_path
            assert engine.selic_data is not None
            assert len(engine.selic_data) == 3

        finally:
            os.unlink(temp_path)

    def test_engine_with_real_selic_disabled(self):
        """Test BacktestEngine with real SELIC disabled."""
        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=True,
            use_real_selic=False,
            selic_rate_annual=0.12,
        )

        assert not engine.use_real_selic
        assert engine.selic_data is None  # Should not load SELIC data

    def test_cash_yield_with_real_rates(self):
        """Test cash yield application with real monthly rates."""
        # Create test data with different monthly rates
        selic_data = pd.DataFrame(
            {"year": [2023, 2023], "month": [1, 2], "rate": [0.02, 0.03]}  # 2%, 3% monthly
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_selic_data(selic_data, temp_path)

            # Initialize engine
            engine = BacktestEngine(
                initial_cash=10000.0,
                apply_cash_yield=True,
                use_real_selic=True,
                selic_path=temp_path,
            )

            # Simulate January yield application
            jan_timestamp = pd.Timestamp("2023-01-15")
            engine._apply_cash_yield(jan_timestamp)

            # Should apply January rate (2%)
            assert abs(engine.state.cash - 10200.0) < 0.01
            assert abs(engine.state.total_interest_earned - 200.0) < 0.01
            assert "2023-01" in engine.state.selic_rates_used
            assert engine.state.selic_rates_used["2023-01"] == 0.02

            # Simulate February yield application
            feb_timestamp = pd.Timestamp("2023-02-15")
            engine._apply_cash_yield(feb_timestamp)

            # Should apply February rate (3%) on new cash balance
            assert abs(engine.state.cash - 10506.0) < 0.01
            assert abs(engine.state.total_interest_earned - 506.0) < 0.01
            assert "2023-02" in engine.state.selic_rates_used
            assert engine.state.selic_rates_used["2023-02"] == 0.03

        finally:
            os.unlink(temp_path)

    def test_real_selic_with_missing_month(self):
        """Test real SELIC with missing month data."""
        # Create test data missing February
        selic_data = pd.DataFrame(
            {"year": [2023, 2023], "month": [1, 3], "rate": [0.01, 0.015]}  # 1%, 1.5%
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_selic_data(selic_data, temp_path)

            engine = BacktestEngine(
                initial_cash=10000.0,
                apply_cash_yield=True,
                use_real_selic=True,
                selic_path=temp_path,
            )

            # Apply January (exists)
            jan_timestamp = pd.Timestamp("2023-01-15")
            engine._apply_cash_yield(jan_timestamp)
            jan_cash = engine.state.cash

            # Apply February (should use fallback - last available which is March's 1.5%)
            feb_timestamp = pd.Timestamp("2023-02-15")
            engine._apply_cash_yield(feb_timestamp)
            expected_feb_cash = jan_cash * (1 + 0.015)  # Use last available rate (March's 1.5%)

            assert abs(engine.state.cash - expected_feb_cash) < 0.01
            assert "2023-02" in engine.state.selic_rates_used
            assert (
                engine.state.selic_rates_used["2023-02"] == 0.015
            )  # Should use last available rate

        finally:
            os.unlink(temp_path)

    def test_results_include_selic_metrics(self):
        """Test that results include SELIC rate information."""
        selic_data = pd.DataFrame({"year": [2023], "month": [1], "rate": [0.015]})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_selic_data(selic_data, temp_path)

            engine = BacktestEngine(
                initial_cash=10000.0,
                apply_cash_yield=True,
                use_real_selic=True,
                selic_path=temp_path,
            )

            # Apply cash yield
            timestamp = pd.Timestamp("2023-01-15")
            engine._apply_cash_yield(timestamp)

            # Get results
            results = engine._get_results()

            # Check SELIC-related fields
            assert results["use_real_selic"]
            assert "selic_rates_used" in results
            assert isinstance(results["selic_rates_used"], dict)
            assert "2023-01" in results["selic_rates_used"]
            assert results["selic_rates_used"]["2023-01"] == 0.015

        finally:
            os.unlink(temp_path)

    def test_backward_compatibility_fixed_rate(self):
        """Test that fixed rate mode still works (backward compatibility)."""
        engine = BacktestEngine(
            initial_cash=10000.0,
            apply_cash_yield=True,
            use_real_selic=False,  # Use fixed rate
            selic_rate_annual=0.12,  # 12% annual = 1% monthly
        )

        # Apply cash yield
        timestamp = pd.Timestamp("2023-01-15")
        engine._apply_cash_yield(timestamp)

        # Should apply fixed monthly rate (12% / 12 = 1%)
        assert abs(engine.state.cash - 10100.0) < 0.01
        assert abs(engine.state.total_interest_earned - 100.0) < 0.01

        # Results should indicate real SELIC is disabled
        results = engine._get_results()
        assert not results["use_real_selic"]
