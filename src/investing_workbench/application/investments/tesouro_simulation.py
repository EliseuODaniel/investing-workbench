"""Tesouro Direto strategy simulation service module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from .catalog import InvestmentInstrument
from .market_simulation import build_contribution_schedule
from .retail_fixed_income import fixed_income_exit_taxes
from .tesouro_direto import TesouroDiretoStrategyDefinition, get_tesouro_direto_strategy_definition


@dataclass(frozen=True)
class _TesouroLot:
    title_key: str
    quantity: float
    buy_date: pd.Timestamp
    buy_price: float


class TesouroSimulationService:
    """Simulate rolling Treasures strategies with explicit tax and liquidity notes."""

    def __init__(
        self,
        *,
        load_tesouro_family_history: Callable[..., dict[str, Any]],
        fixed_income_exit_taxes_func: Callable[..., float] = fixed_income_exit_taxes,
    ) -> None:
        self._load_tesouro_family_history = load_tesouro_family_history
        self._fixed_income_exit_taxes = fixed_income_exit_taxes_func

    def run_strategy(
        self,
        *,
        instrument: InvestmentInstrument,
        start_date: str,
        end_date: str,
        initial_capital: float,
        monthly_contribution: float,
        force_download: bool,
    ) -> tuple[pd.Series, pd.Series, pd.Series, dict[str, Any]]:
        definition = get_tesouro_direto_strategy_definition(instrument.instrument_id)
        if definition is None:
            raise ValueError(
                f"Estrategia de Tesouro Direto desconhecida: {instrument.instrument_id}"
            )
        prepared = self._load_tesouro_family_history(
            start_date=start_date,
            end_date=end_date,
            title_type=definition.title_type,
            force_download=force_download,
        )
        quotes_by_title = prepared["quotes_by_title"]
        last_available_by_title = prepared["last_available_by_title"]
        dates = prepared["dates"]
        schedule = build_contribution_schedule(
            index=dates,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
        )

        active_title_key: str | None = None
        gross_cash = 0.0
        net_cash = 0.0
        gross_lots: list[_TesouroLot] = []
        net_lots: list[_TesouroLot] = []
        equity_values: list[float] = []
        net_liquidation_values: list[float] = []
        flow_values: list[float] = []
        realized_taxes = 0.0
        roll_count = 0
        last_estimated_exit_taxes = 0.0

        for timestamp in dates:
            flow = float(schedule.get(timestamp, 0.0))
            gross_cash += flow
            net_cash += flow

            current_quote = self._resolve_tesouro_quote_row(
                quotes_by_title.get(timestamp),
                active_title_key,
            )
            should_roll = False
            if active_title_key is None:
                should_roll = True
            elif current_quote is None:
                should_roll = True
            else:
                last_available = last_available_by_title.get(active_title_key)
                if (
                    last_available is not None
                    and timestamp == last_available
                    and timestamp != dates[-1]
                ):
                    should_roll = True
                elif not self._tesouro_quote_fits_strategy(current_quote, definition):
                    should_roll = True

            if should_roll:
                if current_quote is not None and gross_lots:
                    gross_cash += self._liquidate_tesouro_lots(
                        lots=gross_lots,
                        sell_price=float(current_quote["investor_sell_price"]),
                        sell_date=timestamp,
                        apply_taxes=False,
                    )[0]
                    net_proceeds, taxes_paid = self._liquidate_tesouro_lots(
                        lots=net_lots,
                        sell_price=float(current_quote["investor_sell_price"]),
                        sell_date=timestamp,
                        apply_taxes=True,
                    )
                    net_cash += net_proceeds
                    realized_taxes += taxes_paid
                    gross_lots = []
                    net_lots = []
                    if active_title_key is not None:
                        roll_count += 1

                candidate_quote = self._prepare_tesouro_candidate(
                    prepared=prepared,
                    definition=definition,
                    timestamp=timestamp,
                )
                active_title_key = (
                    str(candidate_quote["title_key"]) if candidate_quote is not None else None
                )
                if candidate_quote is not None:
                    gross_cash, gross_lots = self._buy_tesouro_with_cash(
                        cash=gross_cash,
                        lots=gross_lots,
                        buy_quote=candidate_quote,
                        buy_date=timestamp,
                    )
                    net_cash, net_lots = self._buy_tesouro_with_cash(
                        cash=net_cash,
                        lots=net_lots,
                        buy_quote=candidate_quote,
                        buy_date=timestamp,
                    )
                    current_quote = self._resolve_tesouro_quote_row(
                        quotes_by_title.get(timestamp),
                        active_title_key,
                    )
            elif flow > 0 and current_quote is not None:
                gross_cash, gross_lots = self._buy_tesouro_with_cash(
                    cash=gross_cash,
                    lots=gross_lots,
                    buy_quote=current_quote,
                    buy_date=timestamp,
                )
                net_cash, net_lots = self._buy_tesouro_with_cash(
                    cash=net_cash,
                    lots=net_lots,
                    buy_quote=current_quote,
                    buy_date=timestamp,
                )

            current_quote = self._resolve_tesouro_quote_row(
                quotes_by_title.get(timestamp),
                active_title_key,
            )
            if current_quote is None:
                gross_equity = gross_cash
                net_equity = net_cash
                estimated_exit_taxes = 0.0
            else:
                sell_price = float(
                    current_quote["investor_sell_price"]
                    if pd.notna(current_quote["investor_sell_price"])
                    else current_quote["base_price"]
                )
                gross_market_value = sum(lot.quantity * sell_price for lot in gross_lots)
                net_market_value = sum(lot.quantity * sell_price for lot in net_lots)
                estimated_exit_taxes = self._estimate_tesouro_exit_taxes(
                    lots=net_lots,
                    sell_price=sell_price,
                    sell_date=timestamp,
                )
                gross_equity = gross_cash + gross_market_value
                net_equity = net_cash + net_market_value - estimated_exit_taxes

            last_estimated_exit_taxes = float(estimated_exit_taxes)
            equity_values.append(float(gross_equity))
            net_liquidation_values.append(float(net_equity))
            flow_values.append(flow)

        gross_curve = pd.Series(equity_values, index=dates, dtype=float)
        flow_curve = pd.Series(flow_values, index=dates, dtype=float)
        net_curve = pd.Series(net_liquidation_values, index=dates, dtype=float)
        strategy_metadata = {
            "study_id": "retail_treasury",
            "title_type": definition.title_type,
            "family_id": definition.family_id,
            "family_label": definition.family_label,
            "target_duration_years": definition.target_duration_years,
            "selection_rule": definition.selection_rule,
            "roll_count": int(roll_count),
            "cash_drag_note": (
                "Quando um titulo deixa de ser ofertado e nao ha substituto imediato, "
                "o caixa fica parado ate surgir um papel compativel."
            ),
            "tax_model": "IR regressivo + IOF inferior a 30 dias",
            "realized_taxes": float(realized_taxes),
            "estimated_exit_taxes": float(last_estimated_exit_taxes),
            "total_taxes": float(realized_taxes + last_estimated_exit_taxes),
        }
        return gross_curve, flow_curve, net_curve, strategy_metadata

    def _prepare_tesouro_candidate(
        self,
        *,
        prepared: dict[str, Any],
        definition: TesouroDiretoStrategyDefinition,
        timestamp: pd.Timestamp,
    ) -> dict[str, Any] | None:
        cache_key = (definition.instrument_id, str(timestamp.date()))
        candidate_cache: dict[tuple[str, str], dict[str, Any] | None] = prepared["candidate_cache"]
        if cache_key in candidate_cache:
            return candidate_cache[cache_key]
        quotes = prepared["grouped_quotes"][timestamp]
        candidate = self._select_tesouro_candidate(quotes, definition)
        serialized = candidate.to_dict() if candidate is not None else None
        candidate_cache[cache_key] = serialized
        return serialized

    @staticmethod
    def _resolve_tesouro_quote_row(
        quotes: pd.DataFrame | dict[str, Any] | None,
        title_key: str | None,
    ) -> Any | None:
        if title_key is None or quotes is None:
            return None
        if isinstance(quotes, dict):
            return quotes.get(title_key)
        matched = quotes[quotes["title_key"] == title_key]
        if matched.empty:
            return None
        return matched.iloc[0]

    @staticmethod
    def _tesouro_quote_fits_strategy(
        quote: pd.Series,
        definition: TesouroDiretoStrategyDefinition,
    ) -> bool:
        if definition.selection_rule == "shortest_maturity":
            return float(quote["years_to_maturity"]) > 0.25
        years_to_maturity = float(quote["years_to_maturity"])
        min_years = definition.min_years_to_maturity
        max_years = definition.max_years_to_maturity
        if min_years is not None and years_to_maturity < min_years:
            return False
        if max_years is not None and years_to_maturity > max_years:
            return False
        return True

    @staticmethod
    def _select_tesouro_candidate(
        quotes: pd.DataFrame,
        definition: TesouroDiretoStrategyDefinition,
    ) -> pd.Series | None:
        candidates = quotes.copy()
        if candidates.empty:
            return None
        if definition.selection_rule == "shortest_maturity":
            eligible = candidates[candidates["years_to_maturity"] > 0.25]
            if eligible.empty:
                return None
            return eligible.sort_values(["years_to_maturity", "maturity_date"]).iloc[0]

        eligible = candidates.copy()
        if definition.min_years_to_maturity is not None:
            eligible = eligible[eligible["years_to_maturity"] >= definition.min_years_to_maturity]
        if definition.max_years_to_maturity is not None:
            eligible = eligible[eligible["years_to_maturity"] <= definition.max_years_to_maturity]
        if eligible.empty:
            eligible = candidates.copy()
        target_duration_years = (
            float(definition.target_duration_years)
            if definition.target_duration_years is not None
            else 0.0
        )
        eligible = eligible.assign(
            duration_gap=(eligible["years_to_maturity"] - target_duration_years).abs()
        )
        return eligible.sort_values(["duration_gap", "years_to_maturity", "maturity_date"]).iloc[0]

    def _buy_tesouro_with_cash(
        self,
        *,
        cash: float,
        lots: list[_TesouroLot],
        buy_quote: Any,
        buy_date: pd.Timestamp,
    ) -> tuple[float, list[_TesouroLot]]:
        buy_price = float(buy_quote["investor_buy_price"])
        if cash <= 0 or buy_price <= 0:
            return cash, lots
        quantity = float(cash / buy_price)
        if quantity <= 0:
            return cash, lots
        updated_lots = [
            *lots,
            _TesouroLot(
                title_key=str(buy_quote["title_key"]),
                quantity=quantity,
                buy_date=buy_date,
                buy_price=buy_price,
            ),
        ]
        return 0.0, updated_lots

    def _liquidate_tesouro_lots(
        self,
        *,
        lots: list[_TesouroLot],
        sell_price: float,
        sell_date: pd.Timestamp,
        apply_taxes: bool,
    ) -> tuple[float, float]:
        proceeds = 0.0
        taxes_paid = 0.0
        for lot in lots:
            gross_proceeds = float(lot.quantity * sell_price)
            taxes = (
                self._fixed_income_exit_taxes(
                    cost_basis=float(lot.quantity * lot.buy_price),
                    sale_value=gross_proceeds,
                    holding_days=max(1, int((sell_date - lot.buy_date).days)),
                )
                if apply_taxes
                else 0.0
            )
            proceeds += gross_proceeds - taxes
            taxes_paid += taxes
        return proceeds, taxes_paid

    def _estimate_tesouro_exit_taxes(
        self,
        *,
        lots: list[_TesouroLot],
        sell_price: float,
        sell_date: pd.Timestamp,
    ) -> float:
        return float(
            sum(
                self._fixed_income_exit_taxes(
                    cost_basis=float(lot.quantity * lot.buy_price),
                    sale_value=float(lot.quantity * sell_price),
                    holding_days=max(1, int((sell_date - lot.buy_date).days)),
                )
                for lot in lots
            )
        )


def calculate_coupon_bond_cash_flows(
    *,
    bond_type: str = "NTN-B_JUROS",
    principal_amount: float = 10000.0,
    annual_coupon_rate: float = 0.06,
    years: int = 5,
    annual_inflation_rate: float = 0.045,
    reinvest: bool = False,
) -> dict[str, Any]:
    """Calculate semiannual coupon payment schedule and tax withholding for NTN-B / NTN-F."""

    is_ntnb = "NTN-B" in bond_type.upper() or "IPCA" in bond_type.upper()
    total_semesters = max(1, years * 2)
    semiannual_coupon_rate = (1.0 + annual_coupon_rate) ** 0.5 - 1.0
    semiannual_inflation_rate = (1.0 + annual_inflation_rate) ** 0.5 - 1.0 if is_ntnb else 0.0

    current_vna = principal_amount
    coupons_schedule: list[dict[str, Any]] = []
    total_gross = 0.0
    total_net = 0.0
    total_tax = 0.0

    for s in range(1, total_semesters + 1):
        holding_days = s * 180
        if holding_days <= 180:
            tax_rate = 0.225
        elif holding_days <= 360:
            tax_rate = 0.20
        elif holding_days <= 720:
            tax_rate = 0.175
        else:
            tax_rate = 0.15

        if is_ntnb:
            current_vna *= 1.0 + semiannual_inflation_rate

        gross_coupon = current_vna * semiannual_coupon_rate
        # Tax is withheld at source based on holding days
        tax_amount = gross_coupon * tax_rate
        net_coupon = gross_coupon - tax_amount

        total_gross += gross_coupon
        total_tax += tax_amount
        total_net += net_coupon

        coupons_schedule.append(
            {
                "semester_index": s,
                "holding_days": holding_days,
                "updated_principal_vna": round(current_vna, 2),
                "gross_coupon": round(gross_coupon, 2),
                "tax_rate_pct": round(tax_rate * 100, 1),
                "tax_withheld": round(tax_amount, 2),
                "net_coupon": round(net_coupon, 2),
            }
        )

    return {
        "bond_type": bond_type,
        "principal_initial": round(principal_amount, 2),
        "principal_final_vna": round(current_vna, 2),
        "total_semesters": total_semesters,
        "total_gross_coupons": round(total_gross, 2),
        "total_tax_withheld": round(total_tax, 2),
        "total_net_coupons": round(total_net, 2),
        "effective_tax_rate_pct": (
            round((total_tax / total_gross) * 100.0, 2) if total_gross > 0 else 0.0
        ),
        "schedule": coupons_schedule,
        "tax_note": (
            "Cupons semestrais de NTN-B e NTN-F sofrem retencao de IR na fonte conforme tabela "
            "regressiva (22.5% a 15%), reduzindo a eficiencia de reinvestimento."
        ),
    }
