"""Compatibility facade for the refactored backtest engine."""

from src.bitcoin_martingale.domain.backtest import BacktestCoreEngine, Layer, State, Trade


class BacktestEngine(BacktestCoreEngine):
    """Legacy import path preserved while the core engine lives in the new domain layer."""


__all__ = ["BacktestEngine", "Layer", "State", "Trade"]
