"""Strategy catalog and score metadata for local backtest workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_strategy_catalog_payload() -> dict[str, Any]:
    """Return explainable strategy metadata for the backtest workspace."""

    strategies = [
        {
            "strategy_id": "martingale_v1",
            "label": "Martingale controlado",
            "family": "position_sizing",
            "direction": "long",
            "required_inputs": ["base_bet", "multiplier", "drop_step", "take_profit"],
            "parameter_defaults": {
                "base_bet": 1000,
                "multiplier": 1.35,
                "drop_step": 0.05,
                "take_profit": 0.08,
                "max_layers": 5,
            },
            "universe_defaults": ["BOVA11"],
            "supported_timeframes": ["daily"],
            "execution_notes": [
                "Comece com limite explicito de camadas antes de testar sensibilidade.",
                "Compare contra buy and hold e Selic para separar retorno de risco assumido.",
            ],
            "risk_notes": [
                "Aumenta exposicao quando o preco cai.",
                "Exige limite de camadas, liquidez e capital de reserva.",
            ],
        },
        {
            "strategy_id": "buy_and_hold",
            "label": "Buy and hold",
            "family": "benchmark",
            "direction": "long",
            "required_inputs": ["initial_capital"],
            "parameter_defaults": {
                "initial_capital": 10000,
                "monthly_contribution": 500,
            },
            "universe_defaults": ["BOVA11", "IVVB11", "SELIC_PROXY"],
            "supported_timeframes": ["daily"],
            "execution_notes": [
                "Use como regua base antes de aceitar complexidade operacional.",
                "Compare janelas com e sem aportes para entender dependencia do fluxo.",
            ],
            "risk_notes": [
                "Serve como regua simples de custo de oportunidade.",
                "Nao controla drawdown nem volatilidade pelo caminho.",
            ],
        },
        {
            "strategy_id": "pairs_cointegration",
            "label": "Pairs por cointegracao",
            "family": "market_neutral",
            "direction": "long_short",
            "required_inputs": ["formation_window", "entry_zscore", "exit_zscore"],
            "parameter_defaults": {
                "formation_window": 252,
                "entry_zscore": 2.0,
                "exit_zscore": 0.5,
                "stop_zscore": 3.5,
            },
            "universe_defaults": ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3"],
            "supported_timeframes": ["daily"],
            "execution_notes": [
                "Exija liquidez, aluguel e custo antes de tratar o par como investivel.",
                "Revalide cointegracao por janelas para evitar relacao quebrada.",
            ],
            "risk_notes": [
                "Depende de validade temporal da relacao estatistica.",
                "Custos, aluguel e liquidez podem mudar o resultado investivel.",
            ],
        },
    ]

    return {
        "title": "Catalogo de estrategias",
        "plain_language_summary": (
            "Camada inicial para explicar familias de backtest, parametros esperados e "
            "como o score deve ser lido antes de criar um radar de setups."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "strategies": strategies,
        "score_dimensions": [
            {
                "dimension_id": "expected_value",
                "label": "EV por trade",
                "description": "Quanto cada trade agregou em media depois de custos modelados.",
            },
            {
                "dimension_id": "drawdown",
                "label": "Drawdown",
                "description": "Maior perda de pico a vale durante o teste.",
            },
            {
                "dimension_id": "robustness",
                "label": "Robustez",
                "description": "Consistencia por janelas, parametros e numero de trades.",
            },
            {
                "dimension_id": "execution_quality",
                "label": "Qualidade de execucao",
                "description": "Custos, slippage, liquidez e preenchimento parcial.",
            },
        ],
        "radar_plan": [
            "Salvar favoritos locais de estrategias e parametros.",
            "Rankear backtests por score explicavel, nao por retorno isolado.",
            "Mostrar validade do resultado e dados/cache usados em cada simulacao.",
        ],
    }


def build_strategy_setup_plan(payload: dict[str, Any]) -> dict[str, Any]:
    """Build an explainable execution plan from a saved strategy setup draft."""

    strategy_id = str(payload.get("strategy_id") or "").strip()
    label = str(payload.get("label") or strategy_id or "Setup").strip()
    family = str(payload.get("family") or "strategy")
    parameters = _clean_mapping(payload.get("parameter_values"))
    universe = [str(item).upper() for item in payload.get("universe", []) if str(item).strip()]
    timeframe = str(payload.get("timeframe") or "daily")
    setup_notes = [str(item) for item in payload.get("setup_notes", []) if str(item).strip()]

    route_hint = "/backtest"
    run_request: dict[str, Any] = {
        "config_path": _config_path(strategy_id),
        "strategies": [_strategy_name(strategy_id)],
        "start_date": None,
        "end_date": None,
        "include_selic_benchmark": True,
        "include_buy_hold_benchmark": True,
        "force_download": False,
    }
    warnings: list[str] = []

    if strategy_id == "pairs_cointegration":
        route_hint = "/pairs/backtests"
        run_request = {
            "preset_id": "custom",
            "tickers": universe,
            "start_date": None,
            "end_date": None,
            "formation_window": parameters.get("formation_window", 252),
            "entry_zscore": parameters.get("entry_zscore", 2.0),
            "exit_zscore": parameters.get("exit_zscore", 0.5),
            "force_download": False,
        }
        warnings.append(
            "Antes de executar, confirme aluguel, liquidez, custos e elegibilidade de short."
        )
    else:
        run_request.update(parameters)
        if universe:
            run_request["data_source"] = universe[0]

    if not universe:
        warnings.append("Defina um universo ou ativo antes de tratar o plano como executavel.")
    if not parameters:
        warnings.append("Revise parametros do setup antes de executar.")

    return {
        "plan_id": f"strategy_setup_plan_{strategy_id or 'draft'}",
        "strategy_id": strategy_id,
        "label": label,
        "family": family,
        "timeframe": timeframe,
        "route_hint": route_hint,
        "readiness": "ready_to_review" if universe and parameters else "needs_inputs",
        "run_request": run_request,
        "assumptions": [
            "Plano gerado a partir do rascunho salvo no radar de setups.",
            "A execucao real ainda deve validar dados, custos, liquidez e janela.",
            "O plano nao e recomendacao; e uma preparacao auditavel para backtest.",
        ],
        "warnings": warnings,
        "setup_notes": setup_notes,
        "next_actions": [
            "Conferir janela de datas e fonte de dados.",
            "Executar o backtest pela rota indicada.",
            "Comparar resultado contra benchmark simples e score de robustez.",
        ],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _strategy_name(strategy_id: str) -> str:
    names = {
        "martingale_v1": "Fixed Martingale",
        "buy_and_hold": "Buy & Hold",
    }
    return names.get(strategy_id, strategy_id)


def _config_path(strategy_id: str) -> str:
    paths = {
        "martingale_v1": "configs/martingale.yaml",
        "buy_and_hold": "configs/test.yaml",
    }
    return paths.get(strategy_id, "configs/martingale.yaml")


def _clean_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(item, str | int | float | bool) or item is None
    }
