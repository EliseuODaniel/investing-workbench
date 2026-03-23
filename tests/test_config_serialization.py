"""Tests for AppConfig serialization with SELIC fields."""

import pytest
import tempfile
import os
from pathlib import Path

from src.config import AppConfig, BacktestConfig, StrategyConfig


class TestConfigSerialization:
    """Test AppConfig serialization with SELIC fields."""

    def test_to_file_includes_selic_fields(self):
        """Test that to_file includes all SELIC-related fields."""
        # Create config with SELIC settings
        backtest_config = BacktestConfig(
            initial_capital=25000.0,
            apply_cash_yield=True,
            selic_rate_annual=0.12,
            yield_frequency="monthly",
            use_real_selic=True,
            selic_path="custom/selic_data.csv",
            selic_fallback_rate=0.11
        )

        strategies = [
            StrategyConfig(
                name="Test Strategy",
                class_path="strategies.test.TestStrategy",
                parameters={"param1": "value1"}
            )
        ]

        app_config = AppConfig(
            backtest=backtest_config,
            strategies=strategies,
            plotting={"save_plots": True}
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            # Save config
            app_config.to_file(temp_path)

            # Read saved file and verify content
            with open(temp_path, 'r') as f:
                content = f.read()

            # Check that all SELIC fields are present
            assert 'apply_cash_yield: true' in content
            assert 'selic_rate_annual: 0.12' in content
            assert 'yield_frequency: monthly' in content
            assert 'use_real_selic: true' in content
            assert 'selic_path: custom/selic_data.csv' in content
            assert 'selic_fallback_rate: 0.11' in content

            # Check backtest structure
            assert 'initial_capital: 25000.0' in content
            assert 'strategies:' in content

        finally:
            os.unlink(temp_path)

    def test_round_trip_serialization(self):
        """Test that config can be saved and loaded with SELIC fields preserved."""
        # Create original config
        original_config = AppConfig(
            backtest=BacktestConfig(
                initial_capital=30000.0,
                apply_cash_yield=True,
                selic_rate_annual=0.13,
                yield_frequency="monthly",
                use_real_selic=True,
                selic_path="data/selic.csv",
                selic_fallback_rate=0.12
            ),
            strategies=[
                StrategyConfig(
                    name="Test Strategy",
                    class_path="strategies.test.TestStrategy",
                    parameters={"test_param": "test_value"}
                )
            ]
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            # Save config
            original_config.to_file(temp_path)

            # Load config back
            loaded_config = AppConfig.from_file(temp_path)

            # Verify all fields are preserved
            assert loaded_config.backtest.initial_capital == 30000.0
            assert loaded_config.backtest.apply_cash_yield == True
            assert loaded_config.backtest.selic_rate_annual == 0.13
            assert loaded_config.backtest.yield_frequency == "monthly"
            assert loaded_config.backtest.use_real_selic == True
            assert loaded_config.backtest.selic_path == "data/selic.csv"
            assert loaded_config.backtest.selic_fallback_rate == 0.12
            assert len(loaded_config.strategies) == 1
            assert loaded_config.strategies[0].name == "Test Strategy"

        finally:
            os.unlink(temp_path)

    def test_default_selic_values_in_serialization(self):
        """Test that default SELIC values are properly serialized."""
        # Create config with default SELIC values (most should be False/defaults)
        backtest_config = BacktestConfig(
            initial_capital=10000.0
            # SELIC fields will use defaults
        )

        app_config = AppConfig(backtest=backtest_config, strategies=[])

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            # Save config
            app_config.to_file(temp_path)

            # Read and verify defaults are included
            with open(temp_path, 'r') as f:
                content = f.read()

            # Should include all fields even with defaults
            assert 'apply_cash_yield: false' in content
            assert 'selic_rate_annual: 0.13' in content
            assert 'yield_frequency: monthly' in content  # Accept with or without quotes
            assert 'use_real_selic: false' in content
            assert 'selic_path: data/selic.csv' in content
            assert 'selic_fallback_rate: 0.13' in content

        finally:
            os.unlink(temp_path)