from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.bitcoin_martingale.application.pairs_trading import PairsTradingService
from src.bitcoin_martingale.application.pairs_trading.ibov_history import SnapshotResolution
from src.bitcoin_martingale.infrastructure.persistence.pairs_repo import (
    LocalPairsBacktestsRepository,
)


def _synthetic_frame(close: np.ndarray, volume: float = 5_000_000.0) -> pd.DataFrame:
    index = pd.bdate_range("2021-01-01", periods=len(close))
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Adj Close": close,
            "Volume": np.full(len(close), volume),
            "Dividends": np.zeros(len(close)),
            "Stock Splits": np.zeros(len(close)),
        },
        index=index,
    )


def _load_fixture_frames() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(11)
    x = np.cumsum(rng.normal(0, 1, 420)) + 100
    spread = np.sin(np.linspace(0, 18, 420)) * 4 + rng.normal(0, 0.4, 420)
    y = 1.05 * x + spread
    benchmark = np.linspace(100.0, 120.0, 420)
    return {
        "AAA1": _synthetic_frame(y, volume=18_000_000.0),
        "BBB1": _synthetic_frame(x, volume=20_000_000.0),
        "BOVA11.SA": _synthetic_frame(benchmark, volume=25_000_000.0),
        "^BVSP": _synthetic_frame(benchmark * 1.03, volume=25_000_000.0),
    }


def test_pairs_service_resolves_custom_universe_with_quality_report(monkeypatch, tmp_path) -> None:
    frames = _load_fixture_frames()

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        if data_source not in frames:
            raise FileNotFoundError(data_source)
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
    )
    payload = service.resolve_universe(
        tickers=["AAA1", "BBB1", "MISS3"],
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        proxy_min_short_score=0.2,
    )

    assert payload["quality_report"]["requested_ticker_count"] == 3
    assert payload["quality_report"]["loaded_ticker_count"] == 2
    assert payload["quality_report"]["eligible_ticker_count"] == 2
    assert payload["unavailable_tickers"] == {"MISS3": "MISS3"}
    assert {asset["ticker"] for asset in payload["eligible_assets"]} == {"AAA1", "BBB1"}


def test_pairs_service_screen_returns_ranked_candidates(monkeypatch, tmp_path) -> None:
    frames = _load_fixture_frames()

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
    )
    payload = service.screen_pairs(
        tickers=["AAA1", "BBB1"],
        formation_window=120,
        test_window=20,
        max_pairs=1,
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        min_return_corr=-1.0,
        min_level_corr=-1.0,
        max_coint_pvalue=0.2,
        min_half_life=1.0,
        max_half_life=80.0,
        min_stability_score=0.0,
        max_structural_break_risk=1.0,
        min_beta_abs=0.0,
        top_n=5,
        proxy_min_short_score=0.2,
        require_cointegration=False,
    )

    assert payload["summary"]["candidate_pair_count"] >= 1
    assert payload["summary"]["selected_pair_count"] == 1
    assert payload["candidate_pairs"][0]["pair_label"] in {"AAA1~BBB1", "BBB1~AAA1"}
    assert payload["candidate_pairs"][0]["stability"]["window_count"] >= 1
    assert "structural_break_risk" in payload["candidate_pairs"][0]["stability"]


def test_pairs_service_applies_borrow_snapshot_overrides(monkeypatch, tmp_path) -> None:
    frames = _load_fixture_frames()

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        if data_source not in frames:
            raise FileNotFoundError(data_source)
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    borrow_snapshot_path = tmp_path / "borrow_snapshot.csv"
    borrow_snapshot_path.write_text(
        "\n".join(
            [
                "ticker,borrow_rate_annual,short_eligible,margin_haircut",
                "AAA1,0.09,true,0.35",
                "BBB1,0.11,false,0.60",
            ]
        ),
        encoding="utf-8",
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
    )
    payload = service.resolve_universe(
        tickers=["AAA1", "BBB1"],
        borrow_snapshot_path=str(borrow_snapshot_path),
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        proxy_min_short_score=0.2,
    )

    assets = {asset["ticker"]: asset for asset in payload["assets"]}
    assert payload["quality_report"]["borrow_override_count"] == 2
    assert payload["quality_report"]["borrow_snapshot_path"] == str(borrow_snapshot_path)
    assert payload["quality_report"]["borrow_snapshot_managed_path"] == str(
        Path("data/pairs_borrow__borrow_snapshot.csv")
    )
    assert payload["quality_report"]["borrow_snapshot_dataset_id"].startswith(
        "pairs_borrow__borrow_snapshot"
    )
    assert assets["AAA1"]["borrow_source"] == "borrow_snapshot.csv"
    assert assets["AAA1"]["borrow_proxy_rate_annual"] == 0.09
    assert assets["AAA1"]["margin_haircut"] == 0.35
    assert assets["BBB1"]["borrow_source"] == "borrow_snapshot.csv"
    assert assets["BBB1"]["borrow_proxy_rate_annual"] == 0.11
    assert assets["BBB1"]["short_eligible"] is False


def test_pairs_service_run_batch_persists_manifest_and_results(monkeypatch, tmp_path) -> None:
    frames = _load_fixture_frames()

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
    )
    payload = service.run_batch(
        tickers=["AAA1", "BBB1"],
        formation_window=120,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        min_return_corr=-1.0,
        max_coint_pvalue=0.2,
        min_half_life=1.0,
        max_half_life=80.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
        benchmark_ids=["equal_weight", "selic_cash"],
        proxy_min_short_score=0.2,
    )

    assert payload["manifest"]["scenario_count"] == 3
    assert payload["robustness_report"]["rankings"]
    assert len(payload["scenarios"]) == 3
    assert payload["benchmarks"][0]["benchmark_id"] == "equal_weight"

    manifests = service.list_backtests()
    assert len(manifests) == 1
    backtest_id = manifests[0]["pairs_backtest_id"]
    assert service.get_manifest(backtest_id)["pairs_backtest_id"] == backtest_id
    assert service.get_results(backtest_id)["pairs_backtest_id"] == backtest_id


def test_pairs_service_portfolio_constraints_shape_results(monkeypatch, tmp_path) -> None:
    index = pd.bdate_range("2021-01-01", periods=420)
    rng = np.random.default_rng(31)
    base_a = np.cumsum(rng.normal(0, 2.4, len(index))) + 120
    base_b = base_a * 1.03 + np.sin(np.linspace(0, 20, len(index))) * 3
    base_c = np.cumsum(rng.normal(0, 2.1, len(index))) + 75
    base_d = base_c * 0.97 + np.cos(np.linspace(0, 18, len(index))) * 2
    benchmark = np.linspace(100.0, 120.0, len(index))
    frames = {
        "AAA1": _synthetic_frame(base_a, volume=18_000_000.0),
        "BBB1": _synthetic_frame(base_b, volume=18_000_000.0),
        "CCC1": _synthetic_frame(base_c, volume=18_000_000.0),
        "DDD1": _synthetic_frame(base_d, volume=18_000_000.0),
        "BOVA11.SA": _synthetic_frame(benchmark, volume=25_000_000.0),
        "^BVSP": _synthetic_frame(benchmark * 1.02, volume=25_000_000.0),
    }
    for frame in frames.values():
        frame.index = index

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
    )
    payload = service.run_backtest(
        tickers=["AAA1", "BBB1", "CCC1", "DDD1"],
        sector_overrides={
            "AAA1": "energy",
            "BBB1": "energy",
            "CCC1": "energy",
            "DDD1": "energy",
        },
        formation_window=120,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=2,
        pair_allocation_pct=0.45,
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        min_return_corr=-1.0,
        max_coint_pvalue=0.9,
        min_half_life=1.0,
        max_half_life=120.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
        benchmark_ids=["equal_weight"],
        proxy_min_short_score=0.0,
        require_cointegration=False,
        portfolio_construction="risk_parity",
        target_pair_volatility_annual=0.05,
        max_gross_exposure_pct=0.60,
        max_net_exposure_pct=0.05,
        max_sector_pairs=1,
    )

    scenario = payload["scenarios"][0]
    portfolio_summary = scenario["portfolio_summary"]
    quality_summary = scenario["quality_summary"]
    assert portfolio_summary["construction"] == "risk_parity"
    assert portfolio_summary["max_sector_pairs"] == 1
    assert portfolio_summary["gross_exposure_peak"] <= 60_000.0 + 1e-6
    assert portfolio_summary["open_positions_peak"] <= 1
    assert quality_summary["sector_cap_blocked_entries"] >= 1


def test_pairs_service_resolves_official_ibov_snapshot_from_history_service(
    monkeypatch,
    tmp_path,
) -> None:
    frames = _load_fixture_frames()

    class _StubIbovHistoryService:
        def resolve_snapshot(
            self, *, as_of_date: str, force_refresh: bool = False
        ) -> SnapshotResolution:
            assert as_of_date == "2021-01-01"
            assert force_refresh is False
            snapshot = {
                "index_id": "ibov",
                "snapshot_id": "ibov_2021-01-01",
                "as_of_date": "2021-01-01",
                "source_kind": "b3_bdi_pdf",
                "source_url": "https://arquivos.b3.com.br/bdi/download/bdi/2021-01-04/BDI_02_20210104.pdf",
                "validity_label": "Para Janeiro a Abril de 2021",
                "ticker_count": 2,
                "tickers": ["AAA1", "BBB1"],
                "constituents": [
                    {
                        "ticker": "AAA1",
                        "descriptor": "AAA ON",
                        "theoretical_quantity": 1,
                        "weight_pct": 1.0,
                    },
                    {
                        "ticker": "BBB1",
                        "descriptor": "BBB ON",
                        "theoretical_quantity": 1,
                        "weight_pct": 1.0,
                    },
                ],
                "imported_at": "2021-01-04T00:00:00+00:00",
            }
            return SnapshotResolution(
                snapshot=snapshot,
                requested_as_of_date="2021-01-01",
                resolved_as_of_date="2021-01-01",
                cache_status="cache_hit",
            )

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests"),
        ibov_history_service=_StubIbovHistoryService(),
    )
    payload = service.resolve_universe(
        preset_id="ibov_historical",
        start_date="2021-01-01",
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        proxy_min_short_score=0.2,
    )

    assert payload["resolved_as_of_date"] == "2021-01-01"
    assert payload["preset"]["source_kind"] == "b3_bdi_pdf"
    assert payload["preset"]["cache_status"] == "cache_hit"
    assert payload["preset"]["ticker_count"] == 2
    assert payload["requested_tickers"] == ["AAA1", "BBB1"]
    assert any("start_date" in warning for warning in payload["warnings"])


def test_pairs_service_reconstitutes_official_ibov_universe_across_segments(
    monkeypatch,
    tmp_path,
) -> None:
    index = pd.bdate_range("2021-01-01", "2021-08-31")
    rng = np.random.default_rng(23)
    base_left = np.cumsum(rng.normal(0, 1, len(index))) + 100
    base_right = base_left * 1.02 + np.sin(np.linspace(0, 12, len(index)))
    alt_left = np.cumsum(rng.normal(0, 1, len(index))) + 60
    alt_right = alt_left * 0.98 + np.cos(np.linspace(0, 10, len(index)))

    frames = {
        "AAA1": _synthetic_frame(base_left, volume=18_000_000.0),
        "BBB1": _synthetic_frame(base_right, volume=18_000_000.0),
        "CCC1": _synthetic_frame(alt_left, volume=18_000_000.0),
        "DDD1": _synthetic_frame(alt_right, volume=18_000_000.0),
        "BOVA11.SA": _synthetic_frame(np.linspace(100.0, 110.0, len(index)), volume=25_000_000.0),
        "^BVSP": _synthetic_frame(np.linspace(100.0, 108.0, len(index)), volume=25_000_000.0),
    }
    for frame in frames.values():
        frame.index = index

    class _StubIbovHistoryService:
        def resolve_snapshot(
            self,
            *,
            as_of_date: str,
            force_refresh: bool = False,
            search_direction: str = "backward",
        ) -> SnapshotResolution:
            if as_of_date == "2021-05-01" and search_direction == "forward":
                resolved = "2021-05-03"
                tickers = ["CCC1", "DDD1"]
            else:
                resolved = "2021-01-01"
                tickers = ["AAA1", "BBB1"]
            snapshot = {
                "index_id": "ibov",
                "snapshot_id": f"ibov_{resolved}",
                "as_of_date": resolved,
                "source_kind": "b3_bdi_pdf",
                "source_url": "https://arquivos.b3.com.br/example.pdf",
                "validity_label": "Para Janeiro a Abril de 2021",
                "ticker_count": 2,
                "tickers": tickers,
                "constituents": [],
                "imported_at": "2021-01-04T00:00:00+00:00",
            }
            return SnapshotResolution(
                snapshot=snapshot,
                requested_as_of_date=as_of_date,
                resolved_as_of_date=resolved,
                cache_status="cache_hit",
            )

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests"),
        ibov_history_service=_StubIbovHistoryService(),
    )
    payload = service.run_backtest(
        preset_id="ibov_historical",
        start_date="2021-01-01",
        end_date="2021-08-31",
        formation_window=60,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        min_return_corr=-1.0,
        max_coint_pvalue=0.9,
        min_half_life=1.0,
        max_half_life=120.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
        benchmark_ids=["equal_weight"],
        proxy_min_short_score=0.0,
        require_cointegration=False,
    )

    assert payload["manifest"]["reconstitution_segment_count"] == 2
    assert len(payload["universe"]["reconstitution_plan"]) == 2
    assert payload["universe"]["reconstitution_plan"][0]["requested_tickers"] == ["AAA1", "BBB1"]
    assert payload["universe"]["reconstitution_plan"][1]["requested_tickers"] == ["CCC1", "DDD1"]
    assert payload["scenarios"][0]["reconstitution_enabled"] is True
    assert len(payload["scenarios"][0]["segments"]) == 2
    assert payload["scenarios"][0]["segments"][1]["resolved_as_of_date"] == "2021-05-03"


def test_pairs_service_screen_includes_rejection_diagnostics(monkeypatch, tmp_path) -> None:
    frames = _load_fixture_frames()

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
    )
    payload = service.screen_pairs(
        tickers=["AAA1", "BBB1"],
        formation_window=120,
        test_window=20,
        max_pairs=1,
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        min_return_corr=-1.0,
        min_level_corr=0.9,
        max_coint_pvalue=0.05,
        min_half_life=1.0,
        max_half_life=10.0,
        min_stability_score=0.9,
        max_structural_break_risk=0.1,
        min_beta_abs=1.5,
        max_beta_abs=1.6,
        top_n=5,
        proxy_min_short_score=0.2,
        require_cointegration=True,
    )

    assert payload["summary"]["candidate_pair_count"] == 0
    assert payload["summary"]["rejected_pair_count"] >= 1
    assert payload["rejected_pairs"]
    assert payload["rejection_summary"]
    assert payload["rejected_pairs"][0]["rejection_reasons"]


def test_pairs_service_run_batch_exposes_alpha_decomposition(monkeypatch, tmp_path) -> None:
    frames = _load_fixture_frames()

    def fake_get_data(*, data_source: str, **_: object) -> pd.DataFrame:
        return frames[data_source]

    monkeypatch.setattr(
        "src.bitcoin_martingale.application.pairs_trading.service.get_data",
        fake_get_data,
    )

    service = PairsTradingService(
        repository=LocalPairsBacktestsRepository(base_dir=tmp_path / "pairs_backtests")
    )
    payload = service.run_backtest(
        tickers=["AAA1", "BBB1"],
        formation_window=120,
        test_window=20,
        step_window=20,
        entry_zscore=1.0,
        exit_zscore=0.1,
        stop_zscore=3.0,
        max_holding_days=15,
        max_pairs=1,
        pair_allocation_pct=0.5,
        min_price=1.0,
        min_median_notional_brl=1_000_000.0,
        min_return_corr=-1.0,
        min_level_corr=-1.0,
        max_coint_pvalue=0.2,
        min_half_life=1.0,
        max_half_life=80.0,
        min_stability_score=0.0,
        max_structural_break_risk=1.0,
        min_beta_abs=0.0,
        max_beta_abs=10.0,
        zscore_window=30,
        fee_rate=0.0,
        slippage=0.0,
        short_borrow_rate_annual=0.0,
        benchmark_ids=["equal_weight", "selic_cash"],
        proxy_min_short_score=0.2,
        batch_mode=True,
    )

    scenario = payload["scenarios"][0]
    assert "alpha_decomposition" in scenario
    assert scenario["alpha_decomposition"]["initial_capital"] == 100000.0
    assert "benchmark_comparison" in scenario["alpha_decomposition"]
