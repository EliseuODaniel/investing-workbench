"""Reproducible WEGE3 long-only strategy lab built on the dedicated Regra A scenario."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path
from typing import Any

import pandas as pd

from src.data import get_data
from src.engine import BacktestEngine
from src.strategies.regra_a_grid import LongOnlyPriceLadderStrategy


@dataclass(slots=True)
class ScenarioResult:
    name: str
    final_total: float
    final_cash: float
    final_position_value: float
    final_shares: float
    absolute_return: float
    percentage_return: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StrategyVariantSpec:
    strategy_id: str
    label: str
    description: str
    initial_investment: float = 10000.0
    base_order_notional: float = 1000.0
    buy_grid_step: float = 1.0
    sell_grid_step: float = 1.0
    buy_size_mode: str = "fixed"
    buy_multiplier: float = 1.0
    max_buy_notional: float | None = None
    sell_notional: float | None = None
    cash_reserve: float = 0.0

    def build_strategy(self) -> LongOnlyPriceLadderStrategy:
        return LongOnlyPriceLadderStrategy(
            name=self.label,
            initial_investment=self.initial_investment,
            base_order_notional=self.base_order_notional,
            buy_grid_step=self.buy_grid_step,
            sell_grid_step=self.sell_grid_step,
            initial_execution_price="open",
            buy_size_mode=self.buy_size_mode,
            buy_multiplier=self.buy_multiplier,
            max_buy_notional=self.max_buy_notional,
            sell_notional=self.sell_notional,
            cash_reserve=self.cash_reserve,
        )

    def parameters(self) -> dict[str, Any]:
        return {
            "initial_investment": self.initial_investment,
            "base_order_notional": self.base_order_notional,
            "buy_grid_step": self.buy_grid_step,
            "sell_grid_step": self.sell_grid_step,
            "buy_size_mode": self.buy_size_mode,
            "buy_multiplier": self.buy_multiplier,
            "max_buy_notional": self.max_buy_notional,
            "sell_notional": self.sell_notional or self.base_order_notional,
            "cash_reserve": self.cash_reserve,
        }


class BuyHoldNotionalStrategy:
    """Buy a fixed notional on the first session open and hold."""

    def __init__(self, notional: float) -> None:
        self.notional = notional
        self.done = False
        self.shares = 0.0

    def on_bar(self, row: pd.Series, engine) -> None:
        if self.done:
            return
        price = float(row["Open"])
        buy_notional = min(self.notional, engine.state.cash)
        if buy_notional <= 0:
            self.done = True
            return
        quantity = buy_notional / price
        if engine.buy(pd.Timestamp(row.name), price, quantity, layer_id=1):
            self.shares += quantity
        self.done = True


class CashOnlyStrategy:
    """Leave the portfolio fully in cash."""

    def on_bar(self, row: pd.Series, engine) -> None:
        return


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the WEGE3 strategy comparison lab")
    parser.add_argument("--start-date", default="2021-01-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--cache-path", default="data/wege3_sa.parquet")
    parser.add_argument("--selic-path", default="data/selic_daily.csv")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--summary-output", default="reports/wege3_regra_a_summary.json")
    parser.add_argument("--trades-output", default="reports/wege3_regra_a_trades.csv")
    return parser


def _load_data(args: argparse.Namespace) -> pd.DataFrame:
    return get_data(
        start=args.start_date,
        end=args.end_date,
        cache_path=args.cache_path,
        force_download=args.force_download,
        data_source="WEGE3",
        interval="1d",
        include_actions=True,
    )


def _run_engine(
    data: pd.DataFrame, strategy, *, initial_cash: float, selic_path: str
) -> tuple[BacktestEngine, dict[str, Any]]:
    engine = BacktestEngine(
        initial_cash=initial_cash,
        apply_cash_yield=True,
        yield_frequency="daily",
        cash_yield_timing="end_of_bar",
        use_real_selic=True,
        selic_path=selic_path,
        selic_fallback_rate=0.13,
        asset="WEGE3",
        timeframe="1d",
        close_positions_at_end=False,
    )
    result = engine.run(data, strategy)
    return engine, result


def _summarize_portfolio(
    *, initial_cash: float, final_cash: float, final_shares: float, last_price: float
) -> ScenarioResult:
    final_position_value = final_shares * last_price
    final_total = final_cash + final_position_value
    absolute_return = final_total - initial_cash
    percentage_return = absolute_return / initial_cash
    return ScenarioResult(
        name="",
        final_total=final_total,
        final_cash=final_cash,
        final_position_value=final_position_value,
        final_shares=final_shares,
        absolute_return=absolute_return,
        percentage_return=percentage_return,
    )


def _corporate_actions_summary(actions_log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for action in actions_log:
        normalized.append(
            {
                "date": pd.Timestamp(action["timestamp"]).strftime("%Y-%m-%d"),
                "type": action["type"],
                "split_factor": action.get("split_factor"),
                "dividend_per_share": action.get("dividend_per_share"),
                "cash_delta": action.get("cash_delta", 0.0),
                "notes": action.get("notes"),
            }
        )
    return normalized


def _serialize_trades_frame(
    trades_df: pd.DataFrame,
    *,
    strategy_id: str | None = None,
) -> pd.DataFrame:
    if trades_df.empty:
        columns = [
            "timestamp",
            "action",
            "price",
            "notional",
            "quantity",
            "cash_after",
            "position_after",
            "reference_after",
        ]
        if strategy_id is not None:
            columns = ["strategy_id", *columns]
        return pd.DataFrame(columns=columns)

    serialized = trades_df.copy()
    serialized["timestamp"] = pd.to_datetime(serialized["timestamp"]).dt.strftime("%Y-%m-%d")
    if strategy_id is not None:
        serialized.insert(0, "strategy_id", strategy_id)
    return serialized


def _serialize_equity_curve(equity_df: pd.DataFrame) -> pd.DataFrame:
    if equity_df.empty:
        return pd.DataFrame(columns=["date", "equity"])

    curve = equity_df.copy()
    if "timestamp" in curve.columns:
        date_values = pd.to_datetime(curve["timestamp"]).dt.strftime("%Y-%m-%d")
    else:
        date_values = pd.to_datetime(curve.index).strftime("%Y-%m-%d")

    serialized = pd.DataFrame(
        {
            "date": date_values,
            "equity": curve["equity"].astype(float),
        }
    )
    return serialized.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)


def _build_comparison_chart(
    *,
    strategy_curves: dict[str, tuple[str, pd.DataFrame]],
    benchmark_curves: dict[str, tuple[str, pd.DataFrame]],
) -> dict[str, Any]:
    series_meta: list[dict[str, Any]] = []
    merged_points: pd.DataFrame | None = None

    for series_id, (label, curve) in [*strategy_curves.items(), *benchmark_curves.items()]:
        series_meta.append(
            {
                "id": series_id,
                "label": label,
                "kind": "benchmark" if series_id in benchmark_curves else "strategy",
            }
        )
        renamed_curve = curve.rename(columns={"equity": series_id})
        merged_points = (
            renamed_curve
            if merged_points is None
            else merged_points.merge(renamed_curve, on="date", how="outer")
        )

    if merged_points is None:
        merged_points = pd.DataFrame(columns=["date"])

    merged_points = merged_points.sort_values("date").reset_index(drop=True)
    return {
        "reference_series_id": "selic_cash",
        "series": series_meta,
        "points": merged_points.to_dict(orient="records"),
    }


def _compute_equity_metrics(equity: pd.DataFrame, *, initial_cash: float) -> dict[str, float]:
    if equity.empty:
        return {
            "cagr": 0.0,
            "volatility": 0.0,
            "sharpe": 0.0,
            "sortino": 0.0,
            "max_drawdown": 0.0,
        }

    equity_series = equity["equity"].astype(float)
    returns = equity_series.pct_change().dropna()
    years = max(len(equity_series) / 252.0, 1 / 252.0)
    final_total = float(equity_series.iloc[-1])
    cagr = (final_total / initial_cash) ** (1.0 / years) - 1.0 if final_total > 0 else -1.0
    volatility = float(returns.std() * sqrt(252)) if len(returns) > 1 else 0.0
    downside = returns[returns < 0]
    sharpe = (
        float((returns.mean() / returns.std()) * sqrt(252))
        if len(returns) > 1 and returns.std() > 0
        else 0.0
    )
    sortino = (
        float((returns.mean() / downside.std()) * sqrt(252))
        if len(downside) > 1 and downside.std() > 0
        else 0.0
    )
    drawdown = (equity_series / equity_series.cummax()) - 1.0
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
    return {
        "cagr": cagr,
        "volatility": volatility,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_drawdown,
    }


def _summarize_variant(
    *,
    spec: StrategyVariantSpec,
    strategy: LongOnlyPriceLadderStrategy,
    engine: BacktestEngine,
    engine_result: dict[str, Any],
    last_close: float,
    initial_cash: float,
    include_trades: bool,
) -> tuple[dict[str, Any], pd.DataFrame]:
    trades_df = _serialize_trades_frame(strategy.trade_log_frame(), strategy_id=spec.strategy_id)
    trade_count_buy = int((trades_df["action"] == "BUY").sum()) if not trades_df.empty else 0
    trade_count_sell = int((trades_df["action"] == "SELL").sum()) if not trades_df.empty else 0
    final_position_value = strategy.position_shares * last_close
    final_total = engine.state.cash + final_position_value
    unrealized_pnl = final_position_value - strategy.cost_basis_total
    trading_pnl = (
        strategy.realized_pnl + unrealized_pnl + float(engine_result["total_dividends_received"])
    )
    metrics = _compute_equity_metrics(engine_result["equity"], initial_cash=initial_cash)

    payload = {
        "strategy_id": spec.strategy_id,
        "label": spec.label,
        "description": spec.description,
        "parameters": spec.parameters(),
        "result": {
            "saldo_final_total": final_total,
            "valor_final_caixa": engine.state.cash,
            "valor_final_posicao": final_position_value,
            "quantidade_final_acoes": strategy.position_shares,
            "retorno_absoluto": final_total - initial_cash,
            "retorno_percentual": (final_total - initial_cash) / initial_cash,
        },
        "statistics": {
            "numero_total_compras": trade_count_buy,
            "numero_total_vendas": trade_count_sell,
            "preco_medio_compra_posicao_final": strategy.final_average_price(),
            "pnl_realizado": strategy.realized_pnl,
            "pnl_nao_realizado": unrealized_pnl,
            "rendimento_acumulado_caixa": float(engine_result["total_interest_earned"]),
            "proventos_recebidos": float(engine_result["total_dividends_received"]),
        },
        "metrics": metrics,
        "decomposition": {
            "trading_pnl": trading_pnl,
            "cash_yield": float(engine_result["total_interest_earned"]),
            "dividends": float(engine_result["total_dividends_received"]),
            "position_mark_to_market": unrealized_pnl,
        },
        "trade_count": len(strategy.trade_log),
        "trades": (
            trades_df.drop(columns=["strategy_id"]).to_dict(orient="records")
            if include_trades
            else []
        ),
    }
    return payload, trades_df


def _build_standard_variants() -> list[StrategyVariantSpec]:
    return [
        StrategyVariantSpec(
            strategy_id="regra_a_base",
            label="Regra A base",
            description="A regra original: ordens fixas de R$ 1.000 a cada R$ 1,00.",
        ),
        StrategyVariantSpec(
            strategy_id="saida_mais_larga",
            label="Grid com saida mais larga",
            description=(
                "Compra no mesmo ritmo da regra base, mas deixa a venda respirar "
                "mais antes de reduzir a posicao."
            ),
            sell_grid_step=2.0,
        ),
        StrategyVariantSpec(
            strategy_id="compras_progressivas",
            label="Compras progressivas",
            description=(
                "Aumenta a mao nas quedas sucessivas para concentrar caixa "
                "nos mergulhos mais profundos."
            ),
            buy_size_mode="progressive",
            buy_multiplier=1.5,
            max_buy_notional=4000.0,
            sell_grid_step=1.5,
        ),
        StrategyVariantSpec(
            strategy_id="progressiva_com_reserva",
            label="Progressiva com reserva",
            description=(
                "Combina compras progressivas com reserva minima de caixa "
                "para evitar ficar seco cedo demais."
            ),
            buy_size_mode="progressive",
            buy_multiplier=1.5,
            max_buy_notional=3500.0,
            sell_grid_step=2.0,
            cash_reserve=8000.0,
        ),
        StrategyVariantSpec(
            strategy_id="acumulacao_ampla",
            label="Acumulacao ampla",
            description=(
                "Usa lotes maiores e saida mais espaçada, mais adequada "
                "a papeis com tendencia estrutural de alta."
            ),
            initial_investment=12000.0,
            base_order_notional=1500.0,
            buy_size_mode="progressive",
            buy_multiplier=1.25,
            max_buy_notional=4500.0,
            sell_grid_step=2.5,
            cash_reserve=5000.0,
        ),
    ]


def _build_parameter_search_specs() -> list[StrategyVariantSpec]:
    specs: list[StrategyVariantSpec] = []
    profile_id = 1
    for initial_investment in (10000.0, 15000.0):
        for base_order in (1000.0, 1500.0):
            for sell_step in (1.0, 2.0):
                for buy_multiplier in (1.0, 1.5):
                    for cash_reserve in (0.0, 5000.0, 10000.0):
                        specs.append(
                            StrategyVariantSpec(
                                strategy_id=f"search_{profile_id:03d}",
                                label=f"Perfil {profile_id:03d}",
                                description="Perfil gerado para busca de parametros.",
                                initial_investment=initial_investment,
                                base_order_notional=base_order,
                                buy_grid_step=1.0,
                                sell_grid_step=sell_step,
                                buy_size_mode="progressive" if buy_multiplier > 1.0 else "fixed",
                                buy_multiplier=buy_multiplier,
                                max_buy_notional=max(base_order * 4.0, 3000.0),
                                cash_reserve=cash_reserve,
                            )
                        )
                        profile_id += 1
    return specs


def _build_asset_profile(data: pd.DataFrame) -> dict[str, Any]:
    closes = data["Close"].astype(float)
    returns = closes.pct_change().dropna()
    rolling_peak = closes.cummax()
    drawdown = closes / rolling_peak - 1.0
    net_change = abs(float(closes.iloc[-1] - closes.iloc[0]))
    traveled = float(closes.diff().abs().sum()) if len(closes) > 1 else 0.0
    trend_efficiency = (net_change / traveled) if traveled > 0 else 0.0
    annualized_volatility = float(returns.std() * sqrt(252)) if len(returns) > 1 else 0.0
    annualized_return = float(closes.iloc[-1] / closes.iloc[0]) ** (252.0 / len(closes)) - 1.0
    lag1_autocorr = float(returns.autocorr(lag=1)) if len(returns) > 10 else 0.0
    mean_reversion_score = max(0.0, -lag1_autocorr)
    grid_fit_score = max(
        0.0,
        min(
            1.0,
            (annualized_volatility / 0.45) * 0.45
            + mean_reversion_score * 0.35
            + (1.0 - min(trend_efficiency / 0.2, 1.0)) * 0.20,
        ),
    )
    trend_fit_score = max(
        0.0,
        min(
            1.0,
            min(max(annualized_return, 0.0) / 0.30, 1.0) * 0.45
            + min(trend_efficiency / 0.2, 1.0) * 0.40
            + (1.0 - mean_reversion_score) * 0.15,
        ),
    )

    return {
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "max_drawdown": float(drawdown.min()) if not drawdown.empty else 0.0,
        "trend_efficiency": trend_efficiency,
        "lag1_return_autocorrelation": lag1_autocorr,
        "mean_reversion_score": mean_reversion_score,
        "grid_fit_score": grid_fit_score,
        "trend_fit_score": trend_fit_score,
    }


def _build_strategy_context(
    *,
    asset_profile: dict[str, Any],
    best_variant: dict[str, Any],
    benchmark_a_total: float,
    benchmark_c_total: float,
    initial_cash: float,
) -> dict[str, Any]:
    annualized_return = float(asset_profile["annualized_return"])
    trend_efficiency = float(asset_profile["trend_efficiency"])
    grid_fit_score = float(asset_profile["grid_fit_score"])
    trend_fit_score = float(asset_profile["trend_fit_score"])

    if trend_fit_score > grid_fit_score:
        fit_summary = (
            "WEGE se comporta mais como um compounder de tendencia com pullbacks do que "
            "como um papel ideal para grade curta e recorrente."
        )
    else:
        fit_summary = (
            "WEGE mostrou oscilações suficientes para trabalhar uma grade, embora ainda "
            "exija disciplina de caixa e saídas menos agressivas."
        )

    benchmark_gap = best_variant["result"]["saldo_final_total"] - benchmark_c_total
    reserve_hint = float(best_variant["parameters"]["cash_reserve"])
    initial_investment = float(best_variant["parameters"]["initial_investment"])
    sell_step = float(best_variant["parameters"]["sell_grid_step"])
    buy_multiplier = float(best_variant["parameters"]["buy_multiplier"])

    return {
        "asset_profile": asset_profile,
        "fit_summary": fit_summary,
        "ideal_context": [
            (
                "Funciona melhor em acoes com tendencia positiva de longo prazo, "
                "mas com correcoes frequentes e liquidez alta."
            ),
            (
                "Evite usar grade curta em papeis muito explosivos para cima, "
                "porque voce gira demais e mata o compounding."
            ),
            (
                "A reserva de caixa importa mais quando o papel tem quedas "
                "profundas e prolongadas antes de recuperar."
            ),
        ],
        "ideal_stock_traits": [
            "Liquidez alta e book previsivel.",
            "Tendencia estrutural de crescimento, mas com pullbacks intermediarios negociaveis.",
            "Baixo risco de evento binario que destrua a tese no meio da escada.",
        ],
        "wege_assessment": [
            (
                "WEGE teve retorno anualizado de "
                f"{annualized_return:.1%} e eficiencia de tendencia de {trend_efficiency:.1%}, "
                "o que favorece mais acumulacao e saidas largas do que uma grade curta e simetrica."
            ),
            (
                "No recorte com caixa inicial de R$ 40 mil, a melhor variante testada ficou "
                f"{benchmark_gap:,.2f} reais acima/abaixo do buy and hold integral."
            )
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
            (
                "Comparado ao benchmark misto de R$ 10 mil em WEGE + R$ 30 mil em caixa, "
                "a melhor variante terminou em "
                f"{(best_variant['result']['saldo_final_total'] - benchmark_a_total):,.2f} "
                "reais de vantagem."
            )
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
        ],
        "recommendation": {
            "best_strategy_id": best_variant["strategy_id"],
            "best_strategy_label": best_variant["label"],
            "suggested_cash_reserve": reserve_hint,
            "suggested_initial_investment": initial_investment,
            "suggested_sell_step": sell_step,
            "suggested_buy_multiplier": buy_multiplier,
            "why": (
                "A melhor variante combinou acumulacao nas quedas com saidas mais largas, "
                "reduzindo o erro central da regra base: vender cedo demais "
                "em um ativo de alta estrutural."
            ),
            "how_to_use": (
                "Se a acao continuar sendo um compounder com correcoes intermediarias, prefira "
                "comprar mais forte na queda e vender mais devagar na recuperacao."
            ),
            "what_to_watch": [
                "Desaceleracao do crescimento e perda de qualidade do negocio.",
                "Mudanca de regime em que o papel deixa de recuperar rapidamente as quedas.",
                "Volatilidade sem tendencia, que pode favorecer grade curta "
                "em vez de acumulacao ampla.",
            ],
        },
    }


def run_scenario(args: argparse.Namespace | list[str] | None = None) -> dict[str, Any]:
    parser = _build_parser()
    if isinstance(args, argparse.Namespace):
        parsed = args
    else:
        parsed = parser.parse_args(args)

    initial_cash = 40000.0
    data = _load_data(parsed)
    last_date = pd.Timestamp(data.index[-1]).strftime("%Y-%m-%d")
    last_close = float(data.iloc[-1]["Close"])
    first_date = pd.Timestamp(data.index[0]).strftime("%Y-%m-%d")
    first_open = float(data.iloc[0]["Open"])

    standard_variants = _build_standard_variants()
    comparison_payloads: list[dict[str, Any]] = []
    comparison_trade_frames: list[pd.DataFrame] = []
    comparison_equity_curves: dict[str, tuple[str, pd.DataFrame]] = {}
    base_variant_payload: dict[str, Any] | None = None
    base_variant_result: dict[str, Any] | None = None

    for spec in standard_variants:
        strategy = spec.build_strategy()
        engine, engine_result = _run_engine(
            data,
            strategy,
            initial_cash=initial_cash,
            selic_path=parsed.selic_path,
        )
        payload, trades_df = _summarize_variant(
            spec=spec,
            strategy=strategy,
            engine=engine,
            engine_result=engine_result,
            last_close=last_close,
            initial_cash=initial_cash,
            include_trades=True,
        )
        comparison_payloads.append(payload)
        comparison_trade_frames.append(trades_df)
        comparison_equity_curves[spec.strategy_id] = (
            spec.label,
            _serialize_equity_curve(engine_result["equity"]),
        )
        if spec.strategy_id == "regra_a_base":
            base_variant_payload = payload
            base_variant_result = engine_result

    if base_variant_payload is None or base_variant_result is None:
        raise RuntimeError("Base WEGE3 strategy variant was not produced")

    search_specs = _build_parameter_search_specs()
    search_payloads: list[dict[str, Any]] = []
    for spec in search_specs:
        strategy = spec.build_strategy()
        engine, engine_result = _run_engine(
            data,
            strategy,
            initial_cash=initial_cash,
            selic_path=parsed.selic_path,
        )
        payload, _ = _summarize_variant(
            spec=spec,
            strategy=strategy,
            engine=engine,
            engine_result=engine_result,
            last_close=last_close,
            initial_cash=initial_cash,
            include_trades=False,
        )
        search_payloads.append(payload)

    search_payloads.sort(
        key=lambda item: (
            float(item["result"]["saldo_final_total"]),
            float(item["decomposition"]["trading_pnl"]),
        ),
        reverse=True,
    )
    top_search_profiles = search_payloads[:10]
    best_progressive_profile = next(
        (item for item in search_payloads if float(item["parameters"]["buy_multiplier"]) > 1.0),
        None,
    )
    best_cash_reserve_profile = next(
        (item for item in search_payloads if float(item["parameters"]["cash_reserve"]) > 0.0),
        None,
    )
    best_trade_alpha_profile = max(
        search_payloads,
        key=lambda item: float(item["decomposition"]["trading_pnl"]),
    )

    benchmark_a_strategy = BuyHoldNotionalStrategy(notional=10000.0)
    benchmark_a_engine, benchmark_a_result = _run_engine(
        data,
        benchmark_a_strategy,
        initial_cash=initial_cash,
        selic_path=parsed.selic_path,
    )

    benchmark_b_strategy = CashOnlyStrategy()
    benchmark_b_engine, benchmark_b_result = _run_engine(
        data,
        benchmark_b_strategy,
        initial_cash=initial_cash,
        selic_path=parsed.selic_path,
    )

    benchmark_c_strategy = BuyHoldNotionalStrategy(notional=40000.0)
    benchmark_c_engine, benchmark_c_result = _run_engine(
        data,
        benchmark_c_strategy,
        initial_cash=initial_cash,
        selic_path=parsed.selic_path,
    )

    best_variant_by_final_total = max(
        comparison_payloads,
        key=lambda item: float(item["result"]["saldo_final_total"]),
    )
    best_variant_by_trading_pnl = max(
        comparison_payloads,
        key=lambda item: float(item["decomposition"]["trading_pnl"]),
    )
    asset_profile = _build_asset_profile(data)
    strategy_context = _build_strategy_context(
        asset_profile=asset_profile,
        best_variant=best_variant_by_final_total,
        benchmark_a_total=float(
            benchmark_a_engine.state.cash + benchmark_a_engine.ledger.total_quantity() * last_close
        ),
        benchmark_c_total=float(
            benchmark_c_engine.state.cash + benchmark_c_engine.ledger.total_quantity() * last_close
        ),
        initial_cash=initial_cash,
    )
    comparison_chart = _build_comparison_chart(
        strategy_curves=comparison_equity_curves,
        benchmark_curves={
            "selic_cash": (
                "Caixa SELIC",
                _serialize_equity_curve(benchmark_b_result["equity"]),
            ),
            "buy_hold_wege3": (
                "Buy and hold WEGE3",
                _serialize_equity_curve(benchmark_c_result["equity"]),
            ),
        },
    )

    base_trades_df = _serialize_trades_frame(pd.DataFrame(base_variant_payload["trades"]))
    summary_path = Path(parsed.summary_output)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    trades_path = Path(parsed.trades_output)
    trades_path.parent.mkdir(parents=True, exist_ok=True)
    base_trades_df.to_csv(trades_path, index=False)

    comparison_output = summary_path.with_name(
        summary_path.stem.replace("_summary", "") + "_comparison.csv"
    )
    comparison_trades_output = summary_path.with_name(
        summary_path.stem.replace("_summary", "") + "_comparison_trades.csv"
    )
    search_output = summary_path.with_name(
        summary_path.stem.replace("_summary", "") + "_search.csv"
    )

    comparison_rows = pd.DataFrame(
        [
            {
                "strategy_id": item["strategy_id"],
                "label": item["label"],
                "description": item["description"],
                "final_total": item["result"]["saldo_final_total"],
                "absolute_return": item["result"]["retorno_absoluto"],
                "percentage_return": item["result"]["retorno_percentual"],
                "trading_pnl": item["decomposition"]["trading_pnl"],
                "cash_yield": item["decomposition"]["cash_yield"],
                "dividends": item["decomposition"]["dividends"],
                "max_drawdown": item["metrics"]["max_drawdown"],
                "cagr": item["metrics"]["cagr"],
                "volatility": item["metrics"]["volatility"],
                "sharpe": item["metrics"]["sharpe"],
                "buy_multiplier": item["parameters"]["buy_multiplier"],
                "cash_reserve": item["parameters"]["cash_reserve"],
                "sell_grid_step": item["parameters"]["sell_grid_step"],
                "initial_investment": item["parameters"]["initial_investment"],
                "base_order_notional": item["parameters"]["base_order_notional"],
            }
            for item in comparison_payloads
        ]
    )
    comparison_rows.to_csv(comparison_output, index=False)
    pd.concat(comparison_trade_frames, ignore_index=True).to_csv(
        comparison_trades_output, index=False
    )

    search_rows = pd.DataFrame(
        [
            {
                "strategy_id": item["strategy_id"],
                "final_total": item["result"]["saldo_final_total"],
                "absolute_return": item["result"]["retorno_absoluto"],
                "percentage_return": item["result"]["retorno_percentual"],
                "trading_pnl": item["decomposition"]["trading_pnl"],
                "cash_yield": item["decomposition"]["cash_yield"],
                "max_drawdown": item["metrics"]["max_drawdown"],
                "sharpe": item["metrics"]["sharpe"],
                "cagr": item["metrics"]["cagr"],
                "initial_investment": item["parameters"]["initial_investment"],
                "base_order_notional": item["parameters"]["base_order_notional"],
                "sell_grid_step": item["parameters"]["sell_grid_step"],
                "buy_multiplier": item["parameters"]["buy_multiplier"],
                "cash_reserve": item["parameters"]["cash_reserve"],
            }
            for item in top_search_profiles
        ]
    )
    search_rows.to_csv(search_output, index=False)

    summary = {
        "assumptions": {
            "initial_trade_execution": "first session open",
            "intrabar_resolver": "bullish candles use O-L-H-C; bearish candles use O-H-L-C",
            "gap_resolver": (
                "levels crossed between last_trade_price and the next open "
                "execute in sequence at the threshold price"
            ),
            "cash_yield_source": "official daily Selic from BCB SGS 11 (% ao dia)",
            "cash_yield_timing": "end_of_bar on post-trade cash balance",
            "price_series_for_triggers": (
                "raw OHLC with corporate actions separated; dividends do not "
                "move trigger reference"
            ),
            "realized_pnl_convention": "strategy-level moving-average cost basis",
            "dividend_modeling": (
                "Yahoo corporate actions credited to cash separately from the "
                "trigger price series; no withholding distinction between "
                "dividends and JCP is available in the source"
            ),
            "fractional_lots": True,
            "close_positions_at_end": False,
            "comparison_scope": "long-only ladder and grid-like strategies with no short selling",
        },
        "dataset": {
            "asset": "WEGE3.SA via Yahoo Finance/yfinance",
            "start_session": first_date,
            "end_session": last_date,
            "first_open": first_open,
            "last_close": last_close,
            "rows": int(len(data)),
            "cache_path": parsed.cache_path,
            "selic_path": parsed.selic_path,
        },
        "result": base_variant_payload["result"],
        "statistics": base_variant_payload["statistics"],
        "benchmarks": {
            "benchmark_a_10000_wege3_30000_caixa": _summarize_portfolio(
                initial_cash=initial_cash,
                final_cash=benchmark_a_engine.state.cash,
                final_shares=benchmark_a_engine.ledger.total_quantity(),
                last_price=last_close,
            ).to_dict(),
            "benchmark_b_40000_caixa": _summarize_portfolio(
                initial_cash=initial_cash,
                final_cash=benchmark_b_engine.state.cash,
                final_shares=benchmark_b_engine.ledger.total_quantity(),
                last_price=last_close,
            ).to_dict(),
            "benchmark_c_40000_buy_hold_wege3": _summarize_portfolio(
                initial_cash=initial_cash,
                final_cash=benchmark_c_engine.state.cash,
                final_shares=benchmark_c_engine.ledger.total_quantity(),
                last_price=last_close,
            ).to_dict(),
        },
        "audit": {
            "trade_csv_path": str(trades_path),
            "comparison_csv_path": str(comparison_output),
            "comparison_trades_csv_path": str(comparison_trades_output),
            "search_csv_path": str(search_output),
            "corporate_actions": _corporate_actions_summary(
                base_variant_result["corporate_actions_log"]
            ),
            "data_sources": [
                "Yahoo Finance via yfinance for WEGE3 OHLC/dividends/split",
                "Banco Central do Brasil SGS 11 for daily Selic",
            ],
        },
        "comparison_variants": comparison_payloads,
        "best_strategy": {
            "by_final_total": best_variant_by_final_total,
            "by_trading_pnl": best_variant_by_trading_pnl,
        },
        "parameter_search": {
            "profile_count": len(search_payloads),
            "top_profiles": top_search_profiles,
            "best_progressive_profile": best_progressive_profile,
            "best_cash_reserve_profile": best_cash_reserve_profile,
            "best_trade_alpha_profile": best_trade_alpha_profile,
        },
        "strategy_context": strategy_context,
        "comparison_chart": comparison_chart,
    }

    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    parsed = parser.parse_args(argv)
    summary = run_scenario(parsed)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
