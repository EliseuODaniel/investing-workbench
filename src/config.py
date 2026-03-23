"""Configuration management for backtesting."""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class BenchmarkConfig:
    """Configuration for a market benchmark."""
    ticker: str
    name: str
    enabled: bool = True


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    initial_capital: float = 30000.0
    start_date: str = "2020-01-01"
    end_date: str = None  # None means today
    data_source: str = "BTC-BRL"
    cache_path: str = "data/btc_brl.parquet"
    output_dir: str = "reports"
    apply_cash_yield: bool = False
    selic_rate_annual: float = 0.13
    yield_frequency: str = "monthly"
    use_real_selic: bool = False
    selic_path: str = "data/selic.csv"
    selic_fallback_rate: float = 0.13
    benchmarks: List[BenchmarkConfig] = None
    include_selic_benchmark: bool = False
    include_buy_hold_benchmark: bool = True


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy."""
    name: str
    class_path: str
    parameters: Dict[str, Any]


@dataclass
class AppConfig:
    """Application configuration."""
    backtest: BacktestConfig
    strategies: List[StrategyConfig]
    plotting: Dict[str, Any] = None

    @classmethod
    def from_file(cls, config_path: str) -> "AppConfig":
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            AppConfig instance
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        # Parse backtest config
        backtest_data = config_data.get("backtest", {})

        # Parse benchmarks
        benchmarks = []
        for benchmark_data in backtest_data.get("benchmarks", []):
            benchmark = BenchmarkConfig(
                ticker=benchmark_data["ticker"],
                name=benchmark_data["name"],
                enabled=benchmark_data.get("enabled", True)
            )
            benchmarks.append(benchmark)

        # Set defaults for optional benchmark fields
        if benchmarks is None:
            benchmarks = []

        backtest_data["benchmarks"] = benchmarks
        backtest = BacktestConfig(**backtest_data)

        # Parse strategies
        strategies = []
        for strategy_data in config_data.get("strategies", []):
            strategy = StrategyConfig(
                name=strategy_data["name"],
                class_path=strategy_data["class_path"],
                parameters=strategy_data.get("parameters", {}),
            )
            strategies.append(strategy)

        # Parse plotting config (optional)
        plotting = config_data.get("plotting", {})

        return cls(backtest=backtest, strategies=strategies, plotting=plotting)

    def to_file(self, config_path: str) -> None:
        """Save configuration to YAML file.

        Args:
            config_path: Path to save configuration file
        """
        config_data = {
            "backtest": {
                "initial_capital": self.backtest.initial_capital,
                "start_date": self.backtest.start_date,
                "end_date": self.backtest.end_date,
                "data_source": self.backtest.data_source,
                "cache_path": self.backtest.cache_path,
                "output_dir": self.backtest.output_dir,
                "apply_cash_yield": self.backtest.apply_cash_yield,
                "selic_rate_annual": self.backtest.selic_rate_annual,
                "yield_frequency": self.backtest.yield_frequency,
                "use_real_selic": self.backtest.use_real_selic,
                "selic_path": self.backtest.selic_path,
                "selic_fallback_rate": self.backtest.selic_fallback_rate,
                "benchmarks": [
                    {
                        "ticker": benchmark.ticker,
                        "name": benchmark.name,
                        "enabled": benchmark.enabled
                    }
                    for benchmark in (self.backtest.benchmarks or [])
                ],
                "include_selic_benchmark": self.backtest.include_selic_benchmark,
                "include_buy_hold_benchmark": self.backtest.include_buy_hold_benchmark,
            },
            "strategies": [
                {
                    "name": strategy.name,
                    "class_path": strategy.class_path,
                    "parameters": strategy.parameters,
                }
                for strategy in self.strategies
            ],
        }

        if self.plotting:
            config_data["plotting"] = self.plotting

        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)


def load_strategy(config: StrategyConfig):
    """Dynamically load strategy class from configuration.

    Args:
        config: Strategy configuration

    Returns:
        Instantiated strategy object
    """
    # Parse module path and class name
    # Example: "strategies.martingale_fixed.MartingaleFixedStrategy"
    module_path, class_name = config.class_path.rsplit(".", 1)

    # Import module dynamically
    try:
        if module_path.startswith("strategies."):
            # Import from src.strategies
            module_name = f"src.{module_path}"
            import importlib
            module = importlib.import_module(module_name)
        else:
            # Absolute import
            import importlib
            module = importlib.import_module(module_path)

        strategy_class = getattr(module, class_name)
        return strategy_class(**config.parameters)

    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to load strategy {config.class_path}: {e}")


def create_default_config() -> AppConfig:
    """Create default configuration.

    Returns:
        Default AppConfig instance
    """
    backtest = BacktestConfig()

    strategies = [
        StrategyConfig(
            name="Fixed Martingale",
            class_path="strategies.martingale_fixed.MartingaleFixedStrategy",
            parameters={
                "base_bet": 500.0,
                "multiplier": 2.0,
                "drop_step": 0.10,
                "take_profit": 0.15,
                "max_layers": 10,
            },
        ),
        StrategyConfig(
            name="Volatility-Adjusted Martingale",
            class_path="strategies.martingale_vol_adj.MartingaleVolatilityStrategy",
            parameters={
                "base_bet": 500.0,
                "multiplier": 2.0,
                "drop_step": 0.10,
                "take_profit": 0.15,
                "max_layers": 8,
                "volatility_period": 20,
                "vol_multiplier": 1.0,
            },
        ),
        StrategyConfig(
            name="Trailing TP Martingale",
            class_path="strategies.martingale_trailing_tp.MartingaleTrailingTPStrategy",
            parameters={
                "base_bet": 500.0,
                "multiplier": 2.0,
                "drop_step": 0.10,
                "take_profit": 0.20,
                "max_layers": 8,
                "trailing_percent": 0.05,
            },
        ),
        StrategyConfig(
            name="DCA Hybrid",
            class_path="strategies.dca_hybrid.DCAHybridStrategy",
            parameters={
                "dca_amount": 500.0,
                "dca_frequency": "weekly",
                "max_martingale_layers": 3,
                "base_bet": 500.0,
                "multiplier": 1.5,
                "drop_step": 0.15,
                "take_profit": 0.20,
                "dca_trigger_threshold": 0.05,
            },
        ),
    ]

    plotting = {
        "save_plots": True,
        "show_plots": False,
        "plot_format": "png",
        "dpi": 300,
    }

    return AppConfig(backtest=backtest, strategies=strategies, plotting=plotting)