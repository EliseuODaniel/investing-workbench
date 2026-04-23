"""Application service for optimization planning."""

from __future__ import annotations

from random import Random

from src.config import AppConfig, StrategyConfig
from src.investing_workbench.domain.optimizations import (
    OptimizationMode,
    OptimizationPlan,
    OptimizationRequest,
    OptimizationSearchSpace,
    OptimizationTrialCandidate,
    build_parameter_combinations,
)


class OptimizationPlanningService:
    """Build reproducible optimization trial plans without executing them yet."""

    def build_plan(self, request: OptimizationRequest) -> OptimizationPlan:
        """Create a deterministic trial plan from a config and discrete search space."""
        config = AppConfig.from_file(request.config_path)
        strategies = self._resolve_strategies(config, request.strategy_names)
        warnings: list[str] = []
        all_trials: list[OptimizationTrialCandidate] = []

        for strategy_config in strategies:
            spaces, strategy_warnings = self._resolve_spaces(strategy_config, request)
            warnings.extend(strategy_warnings)
            if not spaces:
                continue

            base_parameters = dict(strategy_config.parameters)
            combinations = build_parameter_combinations(spaces)
            for combination in combinations:
                trial_parameters = dict(base_parameters)
                trial_parameters.update(combination)
                all_trials.append(
                    OptimizationTrialCandidate(
                        trial_id="pending",
                        strategy_name=strategy_config.name,
                        parameters=trial_parameters,
                    )
                )

        if not all_trials:
            raise ValueError(
                "No optimization trials could be generated from the provided search space"
            )

        selected_trials, truncated = self._select_trials(
            trials=all_trials,
            mode=request.mode,
            max_trials=request.max_trials,
            random_seed=request.random_seed,
        )

        materialized_trials = [
            OptimizationTrialCandidate(
                trial_id=f"trial_{index:04d}",
                strategy_name=trial.strategy_name,
                parameters=trial.parameters,
            )
            for index, trial in enumerate(selected_trials, start=1)
        ]

        if truncated:
            warnings.append(f"Trial plan was truncated to {len(materialized_trials)} candidates")

        return OptimizationPlan(
            config_path=request.config_path,
            objective=request.objective,
            direction=request.direction,
            mode=request.mode,
            random_seed=request.random_seed,
            strategy_names=[strategy.name for strategy in strategies],
            trials=materialized_trials,
            warnings=warnings,
            truncated=truncated,
        )

    def _resolve_strategies(
        self,
        config: AppConfig,
        requested_strategy_names: list[str] | None,
    ) -> list[StrategyConfig]:
        strategies = config.strategies
        if requested_strategy_names:
            strategies = [
                strategy for strategy in strategies if strategy.name in requested_strategy_names
            ]

        if not strategies:
            raise ValueError("No strategies available for optimization")

        return strategies

    def _resolve_spaces(
        self,
        strategy_config: StrategyConfig,
        request: OptimizationRequest,
    ) -> tuple[list[OptimizationSearchSpace], list[str]]:
        warnings: list[str] = []
        merged_space = dict(request.parameter_space)
        merged_space.update(request.strategy_parameter_spaces.get(strategy_config.name, {}))

        spaces: list[OptimizationSearchSpace] = []
        for parameter_name, raw_space in merged_space.items():
            if parameter_name not in strategy_config.parameters:
                warnings.append(
                    f"Skipping parameter '{parameter_name}' for strategy '{strategy_config.name}'"
                )
                continue
            spaces.append(OptimizationSearchSpace.from_raw(parameter_name, raw_space))

        if not spaces:
            warnings.append(
                "No valid search-space parameters were provided for strategy "
                f"'{strategy_config.name}'"
            )

        return spaces, warnings

    def _select_trials(
        self,
        trials: list[OptimizationTrialCandidate],
        mode: OptimizationMode,
        max_trials: int | None,
        random_seed: int,
    ) -> tuple[list[OptimizationTrialCandidate], bool]:
        if mode == OptimizationMode.RANDOM:
            random = Random(random_seed)
            if max_trials is None or max_trials >= len(trials):
                selected = list(trials)
                random.shuffle(selected)
                return selected, False
            return random.sample(trials, k=max_trials), False

        if max_trials is not None and max_trials < len(trials):
            return trials[:max_trials], True

        return list(trials), False
