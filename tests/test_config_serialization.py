import os
import tempfile

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
            selic_fallback_rate=0.11,
            fee_rate=0.0003,
            buy_slippage=0.0005,
            sell_slippage=0.0005,
            max_volume_participation=0.1,
            allow_partial_fills=False,
            min_fill_quantity=0.01,
        )

        strategies = [
            StrategyConfig(
                name="Test Strategy",
                class_path="strategies.test.TestStrategy",
                parameters={"param1": "value1"},
            )
        ]

        app_config = AppConfig(
            backtest=backtest_config, strategies=strategies, plotting={"save_plots": True}
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Save config
            app_config.to_file(temp_path)

            # Read saved file and verify content
            with open(temp_path, "r") as f:
                content = f.read()

            # Check that all SELIC fields are present
            assert "apply_cash_yield: true" in content
            assert "selic_rate_annual: 0.12" in content
            assert "yield_frequency: monthly" in content
            assert "use_real_selic: true" in content
            assert "selic_path: custom/selic_data.csv" in content
            assert "selic_fallback_rate: 0.11" in content
            assert "fee_rate: 0.0003" in content
            assert "buy_slippage: 0.0005" in content
            assert "sell_slippage: 0.0005" in content
            assert "max_volume_participation: 0.1" in content
            assert "allow_partial_fills: false" in content
            assert "min_fill_quantity: 0.01" in content

            # Check backtest structure
            assert "initial_capital: 25000.0" in content
            assert "strategies:" in content

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
                selic_fallback_rate=0.12,
                fee_rate=0.0004,
                fixed_fee=2.5,
                buy_slippage=0.0005,
                sell_slippage=0.0007,
                max_volume_participation=0.15,
                allow_partial_fills=True,
                min_fill_quantity=0.005,
            ),
            strategies=[
                StrategyConfig(
                    name="Test Strategy",
                    class_path="strategies.test.TestStrategy",
                    parameters={"test_param": "test_value"},
                )
            ],
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Save config
            original_config.to_file(temp_path)

            # Load config back
            loaded_config = AppConfig.from_file(temp_path)

            # Verify all fields are preserved
            assert loaded_config.backtest.initial_capital == 30000.0
            assert loaded_config.backtest.apply_cash_yield
            assert loaded_config.backtest.selic_rate_annual == 0.13
            assert loaded_config.backtest.yield_frequency == "monthly"
            assert loaded_config.backtest.use_real_selic
            assert loaded_config.backtest.selic_path == "data/selic.csv"
            assert loaded_config.backtest.selic_fallback_rate == 0.12
            assert loaded_config.backtest.fee_rate == 0.0004
            assert loaded_config.backtest.fixed_fee == 2.5
            assert loaded_config.backtest.buy_slippage == 0.0005
            assert loaded_config.backtest.sell_slippage == 0.0007
            assert loaded_config.backtest.max_volume_participation == 0.15
            assert loaded_config.backtest.allow_partial_fills
            assert loaded_config.backtest.min_fill_quantity == 0.005
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Save config
            app_config.to_file(temp_path)

            # Read and verify defaults are included
            with open(temp_path, "r") as f:
                content = f.read()

            # Should include all fields even with defaults
            assert "apply_cash_yield: false" in content
            assert "selic_rate_annual: 0.13" in content
            assert "yield_frequency: monthly" in content  # Accept with or without quotes
            assert "use_real_selic: false" in content
            assert "selic_path: data/selic.csv" in content
            assert "selic_fallback_rate: 0.13" in content
            assert "fee_rate: 0.0" in content
            assert "fixed_fee: 0.0" in content
            assert "buy_slippage: 0.0" in content
            assert "sell_slippage: 0.0" in content
            assert "allow_partial_fills: true" in content
            assert "min_fill_quantity: 0.0" in content

        finally:
            os.unlink(temp_path)
