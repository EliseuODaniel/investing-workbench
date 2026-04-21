"""Multi-asset comparison runner for BRL assets and reserve-cash strategies."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from src.data import get_data
from src.engine import BacktestEngine
from src.strategies.adaptive_core_grid import AdaptiveCoreGridStrategy
from src.strategies.martingale_fixed import MartingaleFixedStrategy
from src.strategies.regra_a_grid import RegraAGridStrategy


@dataclass(slots=True)
class AssetConfig:
    code: str
    data_source: str
    cache_path: str
    synthetic_brl: bool = False


@dataclass(slots=True)
class ExecutionConfig:
    fee_rate: float = 0.0
    fixed_fee: float = 0.0
    buy_slippage: float = 0.0
    sell_slippage: float = 0.0


ASSETS: tuple[AssetConfig, ...] = (
    AssetConfig(code="WEGE3", data_source="WEGE3", cache_path="data/wege3_sa.parquet"),
    AssetConfig(code="BOVA11", data_source="BOVA11.SA", cache_path="data/bova11_sa.parquet"),
    AssetConfig(
        code="BTC",
        data_source="BTC-BRL-SYNTH",
        cache_path="data/btc_brl_synth.parquet",
        synthetic_brl=True,
    ),
)


class FixedNotionalBuyHoldStrategy:
    def __init__(self, notional: float) -> None:
        self.notional = notional
        self.done = False

    def on_bar(self, row: pd.Series, engine) -> None:
        if self.done:
            return
        price = float(row["Open"])
        buy_notional = min(self.notional, engine.state.cash)
        if buy_notional > 0:
            if self.notional >= engine.initial_cash - 1e-9:
                quantity = engine.quantity_for_buy_budget(price, buy_notional)
            else:
                quantity = buy_notional / price
            if quantity > 0:
                engine.buy(pd.Timestamp(row.name), price, quantity, layer_id=1)
        self.done = True


class CashOnlyStrategy:
    def on_bar(self, row: pd.Series, engine) -> None:
        return


class ReserveMartingaleStrategy:
    """Use the legacy martingale logic with conservative sizing for fairer comparison."""

    def __init__(self) -> None:
        self.inner = MartingaleFixedStrategy(
            base_bet=6000.0,
            multiplier=1.30,
            drop_step=0.10,
            take_profit=0.10,
            max_layers=4,
            slippage=0.0,
        )

    def on_bar(self, row: pd.Series, engine) -> None:
        self.inner.on_bar(row, engine)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare reserve-cash strategies across multiple assets"
    )
    parser.add_argument("--start-date", default="2021-01-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--selic-path", default="data/selic_daily.csv")
    parser.add_argument("--output-dir", default="reports/multi_asset_compare")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--execution-model", choices=("ideal", "realistic"), default="ideal")
    return parser


def _normalize_index(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.index = pd.to_datetime(normalized.index)
    if getattr(normalized.index, "tz", None) is not None:
        normalized.index = normalized.index.tz_localize(None)
    normalized = normalized.sort_index()
    return normalized


def _download_symbol(symbol: str, *, start: str, end: str | None) -> pd.DataFrame:
    df = yf.Ticker(symbol).history(
        start=start,
        end=end,
        auto_adjust=False,
        actions=False,
        interval="1d",
    )
    if df is None or df.empty:
        raise ValueError(f"No data for {symbol}")
    df = _normalize_index(df)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


def _load_btc_brl_synthetic(
    asset: AssetConfig, *, start: str, end: str | None, force_download: bool
) -> pd.DataFrame:
    cache_path = Path(asset.cache_path)
    requested_end = pd.Timestamp(end or pd.Timestamp.utcnow().strftime("%Y-%m-%d"))
    if cache_path.exists() and not force_download:
        cached = pd.read_parquet(cache_path)
        cached = _normalize_index(cached)
        if cached.index.min() <= pd.Timestamp(
            start
        ) and cached.index.max() >= requested_end - pd.Timedelta(days=1):
            return cached.loc[pd.Timestamp(start) : pd.Timestamp(requested_end.date())]

    btc_usd = _download_symbol("BTC-USD", start=start, end=end)
    usdbrl = _download_symbol("USDBRL=X", start=start, end=end)
    usdbrl = usdbrl.reindex(btc_usd.index).ffill()
    merged = btc_usd.join(usdbrl, lsuffix="_btc", rsuffix="_fx", how="left").dropna()

    synthetic = pd.DataFrame(index=merged.index)
    for column in ["Open", "High", "Low", "Close"]:
        synthetic[column] = merged[f"{column}_btc"] * merged[f"{column}_fx"]
    synthetic["Volume"] = merged["Volume_btc"]
    synthetic["Adj Close"] = synthetic["Close"]
    synthetic["Dividends"] = 0.0
    synthetic["Stock Splits"] = 0.0

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    synthetic.to_parquet(cache_path)
    return synthetic.loc[pd.Timestamp(start) : pd.Timestamp(requested_end.date())]


def load_asset_data(
    asset: AssetConfig, *, start: str, end: str | None, force_download: bool
) -> pd.DataFrame:
    if asset.synthetic_brl:
        return _load_btc_brl_synthetic(asset, start=start, end=end, force_download=force_download)
    return get_data(
        start=start,
        end=end,
        cache_path=asset.cache_path,
        force_download=force_download,
        data_source=asset.data_source,
        include_actions=True,
    )


def choose_absolute_step(first_open: float) -> float:
    raw_step = first_open * 0.025
    if raw_step < 2:
        return max(0.5, round(raw_step * 2) / 2)
    if raw_step < 10:
        return float(round(raw_step))
    if raw_step < 100:
        return float(round(raw_step / 5) * 5)
    if raw_step < 1000:
        return float(round(raw_step / 50) * 50)
    return float(round(raw_step / 500) * 500)


def get_execution_config(asset_code: str, execution_model: str) -> ExecutionConfig:
    if execution_model == "ideal":
        return ExecutionConfig()

    if asset_code in {"WEGE3", "BOVA11"}:
        return ExecutionConfig(
            fee_rate=0.0003,
            fixed_fee=0.0,
            buy_slippage=0.0005,
            sell_slippage=0.0005,
        )

    if asset_code == "BTC":
        return ExecutionConfig(
            fee_rate=0.0010,
            fixed_fee=0.0,
            buy_slippage=0.0010,
            sell_slippage=0.0010,
        )

    return ExecutionConfig()


def describe_execution_model(asset_code: str, execution_model: str) -> str:
    config = get_execution_config(asset_code, execution_model)
    if execution_model == "ideal":
        return "sem custos e sem slippage"
    return (
        f"fee_rate={config.fee_rate:.4%}, fixed_fee={config.fixed_fee:.2f}, "
        f"buy_slippage={config.buy_slippage:.4%}, sell_slippage={config.sell_slippage:.4%}"
    )


def _engine(
    *, asset_code: str, selic_path: str, execution_config: ExecutionConfig
) -> BacktestEngine:
    return BacktestEngine(
        initial_cash=40000.0,
        apply_cash_yield=True,
        yield_frequency="daily",
        use_real_selic=True,
        selic_path=selic_path,
        selic_fallback_rate=0.13,
        asset=asset_code,
        timeframe="1d",
        close_positions_at_end=False,
        fee_rate=execution_config.fee_rate,
        fixed_fee=execution_config.fixed_fee,
        buy_slippage=execution_config.buy_slippage,
        sell_slippage=execution_config.sell_slippage,
    )


def _run_strategy(
    data: pd.DataFrame,
    strategy,
    *,
    asset_code: str,
    selic_path: str,
    execution_config: ExecutionConfig,
) -> tuple[BacktestEngine, dict[str, Any]]:
    engine = _engine(
        asset_code=asset_code,
        selic_path=selic_path,
        execution_config=execution_config,
    )
    result = engine.run(data, strategy)
    return engine, result


def _summarize_strategy(
    *,
    name: str,
    engine: BacktestEngine,
    result: dict[str, Any],
    last_close: float,
) -> dict[str, Any]:
    trades = result["trades"].copy()
    final_shares = engine.ledger.total_quantity()
    final_position_value = final_shares * last_close
    total_cost_basis = engine.ledger.total_cost_basis()
    realized_pnl = (
        float(trades[trades["action"] == "SELL"]["pnl"].sum()) if not trades.empty else 0.0
    )
    buy_count = int((trades["action"] == "BUY").sum()) if not trades.empty else 0
    sell_count = int((trades["action"] == "SELL").sum()) if not trades.empty else 0
    final_total = engine.state.cash + final_position_value
    total_return = (final_total - 40000.0) / 40000.0
    avg_price = total_cost_basis / final_shares if final_shares > 0 else 0.0
    unrealized_pnl = final_position_value - total_cost_basis
    return {
        "strategy": name,
        "final_total": final_total,
        "final_cash": engine.state.cash,
        "final_position_value": final_position_value,
        "final_shares": final_shares,
        "absolute_return": final_total - 40000.0,
        "percentage_return": total_return,
        "buy_trades": buy_count,
        "sell_trades": sell_count,
        "total_trades": buy_count + sell_count,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "average_entry_price": avg_price,
        "cash_yield": result.get("total_interest_earned", 0.0),
        "dividends": result.get("total_dividends_received", 0.0),
        "fees_paid": result.get("total_fees_paid", 0.0),
    }


def _export_trades(
    output_dir: Path, asset_code: str, strategy_name: str, trades: pd.DataFrame, scenario_tag: str
) -> str:
    safe_name = strategy_name.lower().replace(" ", "_").replace("+", "plus")
    suffix = "" if scenario_tag == "ideal" else f"_{scenario_tag}"
    path = output_dir / f"{asset_code.lower()}_{safe_name}{suffix}_trades.csv"
    export_df = trades.copy()
    if not export_df.empty and "timestamp" in export_df.columns:
        export_df["timestamp"] = pd.to_datetime(export_df["timestamp"]).dt.strftime("%Y-%m-%d")
    export_df.to_csv(path, index=False)
    return str(path)


def run_comparison(argv: list[str] | None = None) -> dict[str, Any]:
    parser = _build_parser()
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "assumptions": {
            "initial_capital": 40000.0,
            "cash_yield": "Selic diaria oficial do BCB SGS 11",
            "reserve_cash_logic": "strategies can hold residual BRL cash earning Selic",
            "buy_hold_benchmark_apples_to_apples": "R$10k initial position + R$30k in Selic",
            "btc_brl_source": (
                "synthetic BTC-BRL built from BTC-USD * USDBRL=X "
                "with FX forward-filled on non-business days"
            ),
            "execution_model": args.execution_model,
        },
        "assets": {},
    }

    for asset in ASSETS:
        data = load_asset_data(
            asset,
            start=args.start_date,
            end=args.end_date,
            force_download=args.force_download,
        )
        data = _normalize_index(data)
        first_open = float(data.iloc[0]["Open"])
        last_close = float(data.iloc[-1]["Close"])
        step = choose_absolute_step(first_open)
        min_step = step
        execution_config = get_execution_config(asset.code, args.execution_model)

        strategies = [
            ("Selic 40k", CashOnlyStrategy()),
            ("Buy Hold 10k + Selic", FixedNotionalBuyHoldStrategy(10000.0)),
            ("Buy Hold 40k", FixedNotionalBuyHoldStrategy(40000.0)),
            (
                "Grid Absoluto",
                RegraAGridStrategy(
                    initial_investment=10000.0,
                    order_notional=1000.0,
                    grid_step=step,
                    initial_execution_price="open",
                ),
            ),
            (
                "Adaptive Core Grid",
                AdaptiveCoreGridStrategy(
                    core_notional=10000.0,
                    order_notional=1000.0,
                    min_step=min_step,
                    atr_period=14,
                    atr_multiplier=1.0,
                    max_tactical_notional=15000.0,
                    initial_execution_price="open",
                ),
            ),
            ("Martingale Fixo", ReserveMartingaleStrategy()),
        ]

        asset_results: list[dict[str, Any]] = []
        asset_report: dict[str, Any] = {
            "dataset": {
                "start": data.index[0].strftime("%Y-%m-%d"),
                "end": data.index[-1].strftime("%Y-%m-%d"),
                "rows": int(len(data)),
                "first_open": first_open,
                "last_close": last_close,
                "absolute_grid_step": step,
                "cache_path": asset.cache_path,
            },
            "execution_costs": {
                **asdict(execution_config),
                "description": describe_execution_model(asset.code, args.execution_model),
            },
            "results": asset_results,
        }

        for strategy_name, strategy in strategies:
            engine, result = _run_strategy(
                data,
                strategy,
                asset_code=asset.code,
                selic_path=args.selic_path,
                execution_config=execution_config,
            )
            summary = _summarize_strategy(
                name=strategy_name,
                engine=engine,
                result=result,
                last_close=last_close,
            )
            summary["trade_csv"] = _export_trades(
                output_dir,
                asset.code,
                strategy_name,
                result["trades"],
                args.execution_model,
            )
            asset_results.append(summary)

        asset_results.sort(key=lambda item: item["final_total"], reverse=True)
        report["assets"][asset.code] = asset_report

    report_path = output_dir / f"multi_asset_strategy_compare_{args.execution_model}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.execution_model == "ideal":
        legacy_path = output_dir / "multi_asset_strategy_compare.json"
        legacy_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


if __name__ == "__main__":
    comparison = run_comparison()
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
