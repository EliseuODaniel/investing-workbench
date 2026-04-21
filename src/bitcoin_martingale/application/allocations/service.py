"""Application service for portfolio allocation planning."""

from __future__ import annotations

from src.bitcoin_martingale.domain.allocations import (
    RebalanceAction,
    RebalanceActionType,
    RebalancePlan,
    RebalancePlanRequest,
)


class AllocationPlanningService:
    """Build rebalance plans from current holdings and target weights."""

    def build_plan(self, request: RebalancePlanRequest) -> RebalancePlan:
        """Generate a portfolio rebalance plan."""
        self._validate_request(request)

        holdings_by_asset = {holding.asset: holding for holding in request.holdings}
        target_weights = {target.asset: target.target_weight for target in request.targets}
        asset_universe = sorted(set(holdings_by_asset) | set(target_weights))

        current_values = {
            asset: holding.quantity * request.prices[asset]
            for asset, holding in holdings_by_asset.items()
        }
        total_equity = request.cash + sum(current_values.values())
        if total_equity <= 0:
            raise ValueError("Portfolio equity must be positive to build a rebalance plan")

        target_weight_sum = sum(target.target_weight for target in request.targets)
        target_cash = total_equity * (1 - target_weight_sum)
        if target_cash + 1e-9 < request.reserve_cash:
            raise ValueError(
                "Target weights leave less cash than the requested reserve_cash floor"
            )

        current_cash_weight = request.cash / total_equity
        target_cash_weight = target_cash / total_equity
        max_abs_drift_weight = 0.0
        warnings: list[str] = []

        sell_actions: list[RebalanceAction] = []
        buy_actions: list[RebalanceAction] = []
        hold_actions: list[RebalanceAction] = []

        for asset in asset_universe:
            price = request.prices[asset]
            existing_holding = holdings_by_asset.get(asset)
            current_quantity = existing_holding.quantity if existing_holding else 0.0
            current_value = current_values.get(asset, 0.0)
            current_weight = current_value / total_equity
            target_weight = target_weights.get(asset, 0.0)
            target_value = target_weight * total_equity
            target_quantity = target_value / price
            notional_delta = target_value - current_value
            quantity_delta = notional_delta / price
            drift_weight = target_weight - current_weight
            max_abs_drift_weight = max(max_abs_drift_weight, abs(drift_weight))

            action = self._build_action(
                asset=asset,
                price=price,
                current_quantity=current_quantity,
                current_value=current_value,
                current_weight=current_weight,
                target_quantity=target_quantity,
                target_value=target_value,
                target_weight=target_weight,
                quantity_delta=quantity_delta,
                notional_delta=notional_delta,
                drift_weight=drift_weight,
                tolerance=request.weight_tolerance,
                min_trade_notional=request.min_trade_notional,
            )

            if action.action == RebalanceActionType.SELL:
                sell_actions.append(action)
            elif action.action == RebalanceActionType.BUY:
                buy_actions.append(action)
            else:
                hold_actions.append(action)

            if current_quantity > 0 and target_weight == 0:
                warnings.append(
                    f"Asset '{asset}' is held today but has no target weight; the plan exits it."
                )

        projected_cash = request.cash
        executed_actions: list[RebalanceAction] = []

        for action in sorted(sell_actions, key=lambda item: abs(item.notional_delta), reverse=True):
            projected_cash -= action.notional_delta
            executed_actions.append(action)

        for action in sorted(buy_actions, key=lambda item: abs(item.notional_delta), reverse=True):
            buy_notional = action.notional_delta
            if projected_cash - buy_notional + 1e-9 < request.reserve_cash:
                hold_actions.append(
                    self._to_hold_action(
                        action,
                        reason="Insufficient cash after applying reserve_cash",
                    )
                )
                warnings.append(
                    f"Skipped buy for '{action.asset}' because it would breach reserve_cash."
                )
                continue

            projected_cash -= buy_notional
            executed_actions.append(action)

        executed_actions.sort(
            key=lambda item: (
                0 if item.action == RebalanceActionType.SELL else 1,
                item.asset,
            )
        )
        hold_actions.sort(key=lambda item: item.asset)
        all_actions = [*executed_actions, *hold_actions]

        turnover_notional = sum(abs(action.notional_delta) for action in executed_actions)

        if target_cash_weight > current_cash_weight + request.weight_tolerance:
            warnings.append(
                "Target allocation increases cash weight; the portfolio is moving more defensive."
            )
        elif target_cash_weight + request.weight_tolerance < current_cash_weight:
            warnings.append(
                "Target allocation deploys more cash into risk assets; confirm position sizing."
            )

        if projected_cash + 1e-9 < request.reserve_cash:
            warnings.append(
                "Projected cash remains below reserve_cash after thresholds are applied."
            )

        return RebalancePlan(
            total_equity=total_equity,
            current_cash=request.cash,
            target_cash=target_cash,
            projected_cash=projected_cash,
            current_cash_weight=current_cash_weight,
            target_cash_weight=target_cash_weight,
            turnover_notional=turnover_notional,
            turnover_ratio=turnover_notional / total_equity,
            cash_gap_to_target=projected_cash - target_cash,
            max_abs_drift_weight=max_abs_drift_weight,
            needs_rebalance=bool(executed_actions),
            actions=all_actions,
            warnings=warnings,
        )

    def _validate_request(self, request: RebalancePlanRequest) -> None:
        if request.cash < 0:
            raise ValueError("cash must be non-negative")
        if request.reserve_cash < 0:
            raise ValueError("reserve_cash must be non-negative")
        if request.weight_tolerance < 0 or request.weight_tolerance > 1:
            raise ValueError("weight_tolerance must be between 0 and 1")
        if request.min_trade_notional < 0:
            raise ValueError("min_trade_notional must be non-negative")
        if not request.targets:
            raise ValueError("At least one target allocation is required")

        self._validate_unique_assets(
            [holding.asset for holding in request.holdings],
            "holdings",
        )
        self._validate_unique_assets(
            [target.asset for target in request.targets],
            "targets",
        )

        for holding in request.holdings:
            if holding.quantity < 0:
                raise ValueError(
                    f"Holding quantity must be non-negative for asset '{holding.asset}'"
                )

        for target in request.targets:
            if target.target_weight < 0 or target.target_weight > 1:
                raise ValueError(
                    f"target_weight must be between 0 and 1 for asset '{target.asset}'"
                )

        target_weight_sum = sum(target.target_weight for target in request.targets)
        if target_weight_sum > 1 + 1e-9:
            raise ValueError("Target weights must sum to at most 1.0")

        required_assets = {holding.asset for holding in request.holdings} | {
            target.asset for target in request.targets
        }
        missing_prices = sorted(
            asset for asset in required_assets if asset not in request.prices
        )
        if missing_prices:
            raise ValueError("Missing prices for assets: " + ", ".join(missing_prices))

        invalid_prices = sorted(
            asset for asset in required_assets if request.prices[asset] <= 0
        )
        if invalid_prices:
            raise ValueError(
                "Prices must be positive for assets: " + ", ".join(invalid_prices)
            )

    def _validate_unique_assets(self, assets: list[str], label: str) -> None:
        duplicates = sorted({asset for asset in assets if assets.count(asset) > 1})
        if duplicates:
            raise ValueError(
                f"Duplicate assets are not allowed in {label}: {', '.join(duplicates)}"
            )

    def _build_action(
        self,
        *,
        asset: str,
        price: float,
        current_quantity: float,
        current_value: float,
        current_weight: float,
        target_quantity: float,
        target_value: float,
        target_weight: float,
        quantity_delta: float,
        notional_delta: float,
        drift_weight: float,
        tolerance: float,
        min_trade_notional: float,
    ) -> RebalanceAction:
        if abs(drift_weight) <= tolerance:
            return RebalanceAction(
                asset=asset,
                action=RebalanceActionType.HOLD,
                price=price,
                current_quantity=current_quantity,
                current_value=current_value,
                current_weight=current_weight,
                target_quantity=target_quantity,
                target_value=target_value,
                target_weight=target_weight,
                quantity_delta=0.0,
                notional_delta=0.0,
                drift_weight=drift_weight,
                projected_quantity=current_quantity,
                reason="Within weight_tolerance",
            )

        if abs(notional_delta) < min_trade_notional:
            return RebalanceAction(
                asset=asset,
                action=RebalanceActionType.HOLD,
                price=price,
                current_quantity=current_quantity,
                current_value=current_value,
                current_weight=current_weight,
                target_quantity=target_quantity,
                target_value=target_value,
                target_weight=target_weight,
                quantity_delta=0.0,
                notional_delta=0.0,
                drift_weight=drift_weight,
                projected_quantity=current_quantity,
                reason="Below min_trade_notional",
            )

        action_type = RebalanceActionType.BUY if notional_delta > 0 else RebalanceActionType.SELL
        return RebalanceAction(
            asset=asset,
            action=action_type,
            price=price,
            current_quantity=current_quantity,
            current_value=current_value,
            current_weight=current_weight,
            target_quantity=target_quantity,
            target_value=target_value,
            target_weight=target_weight,
            quantity_delta=quantity_delta,
            notional_delta=notional_delta,
            drift_weight=drift_weight,
            projected_quantity=current_quantity + quantity_delta,
            reason="Move current weight toward target allocation",
        )

    def _to_hold_action(
        self,
        action: RebalanceAction,
        *,
        reason: str,
    ) -> RebalanceAction:
        return RebalanceAction(
            asset=action.asset,
            action=RebalanceActionType.HOLD,
            price=action.price,
            current_quantity=action.current_quantity,
            current_value=action.current_value,
            current_weight=action.current_weight,
            target_quantity=action.target_quantity,
            target_value=action.target_value,
            target_weight=action.target_weight,
            quantity_delta=0.0,
            notional_delta=0.0,
            drift_weight=action.drift_weight,
            projected_quantity=action.current_quantity,
            reason=reason,
        )
