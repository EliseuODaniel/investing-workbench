"""Pairs trading helpers and backtest engine."""

from .backtest import CointegrationPairsBacktester, PairsTradingConfig, load_b3_universe_data
from .models import (
    BorrowOverride,
    ClosedPairTrade,
    OpenPairPosition,
    PairSelection,
    UniverseAsset,
)
from .statistics import (
    PairStabilityResult,
    ShortBorrowProfile,
    analyze_cointegration,
    apply_split_adjustment,
    estimate_pair_stability,
    estimate_short_borrow_profile,
    evaluate_pair_orientations,
)

__all__ = [
    "CointegrationPairsBacktester",
    "PairsTradingConfig",
    "BorrowOverride",
    "ClosedPairTrade",
    "OpenPairPosition",
    "PairSelection",
    "UniverseAsset",
    "PairStabilityResult",
    "ShortBorrowProfile",
    "apply_split_adjustment",
    "analyze_cointegration",
    "estimate_pair_stability",
    "estimate_short_borrow_profile",
    "evaluate_pair_orientations",
    "load_b3_universe_data",
]
