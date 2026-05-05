"""Investment comparison API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.models import (
    InvestmentCatalogResponseModel,
    InvestmentCompareRequestModel,
    InvestmentCompareResponseModel,
    InvestmentMarketRankingsRequestModel,
    InvestmentMarketRankingsResponseModel,
    InvestmentProductDataRefreshRequestModel,
    InvestmentProductDataRefreshResponseModel,
    SavedInvestmentPortfolioModel,
    SavedPairsRadarItemModel,
    SavedStrategyRadarItemModel,
    SavedStrategySetupRunModel,
    StrategySetupScoreModel,
)
from src.investing_workbench.interfaces.api.deps import get_service
from src.investing_workbench.interfaces.api.errors import to_http_exception

router = APIRouter(tags=["investments"])


@router.get("/investments/catalog", response_model=InvestmentCatalogResponseModel)
async def get_investment_catalog(request: Request) -> InvestmentCatalogResponseModel:
    """Return the curated B3 investment catalog used by the didactic comparison flow."""
    try:
        return get_service(request, "investment_comparison_service").list_catalog()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/investments/compare", response_model=InvestmentCompareResponseModel)
async def compare_investments(
    payload: InvestmentCompareRequestModel,
    request: Request,
) -> InvestmentCompareResponseModel:
    """Compare the same cash-flow schedule across selected B3 investment alternatives."""
    try:
        return get_service(request, "investment_comparison_service").compare(
            asset_ids=payload.asset_ids,
            custom_portfolios=[item.model_dump() for item in payload.custom_portfolios],
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_capital=payload.initial_capital,
            monthly_contribution=payload.monthly_contribution,
            benchmark_ids=payload.benchmark_ids,
            fixed_income_study_mode=payload.fixed_income_study_mode,
            fixed_income_tax_treatment=payload.fixed_income_tax_treatment,
            fixed_income_window_frequency=payload.fixed_income_window_frequency,
            decision_profile=payload.decision_profile.model_dump(),
            force_download=payload.force_download,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/investments/market-rankings", response_model=InvestmentMarketRankingsResponseModel)
async def build_market_rankings_snapshot(
    payload: InvestmentMarketRankingsRequestModel,
    request: Request,
) -> InvestmentMarketRankingsResponseModel:
    """Build a compact rankings/screeners snapshot for the market explorer."""
    try:
        return get_service(request, "investment_comparison_service").build_market_rankings_snapshot(
            preset_id=payload.preset_id,
            asset_ids=payload.asset_ids,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_capital=payload.initial_capital,
            monthly_contribution=payload.monthly_contribution,
            benchmark_ids=payload.benchmark_ids,
            decision_profile=payload.decision_profile.model_dump(),
            force_download=payload.force_download,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post(
    "/investments/product-data/refresh",
    response_model=InvestmentProductDataRefreshResponseModel,
)
async def refresh_product_data_source(
    payload: InvestmentProductDataRefreshRequestModel,
    request: Request,
) -> InvestmentProductDataRefreshResponseModel:
    """Refresh one external product-data source into the local cache."""
    try:
        return get_service(request, "product_data_source_service").refresh_source(
            source_id=payload.source_id,
            force=payload.force,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get(
    "/investments/workspaces/portfolios",
    response_model=list[SavedInvestmentPortfolioModel],
)
async def list_saved_investment_portfolios(request: Request) -> list[SavedInvestmentPortfolioModel]:
    """List reusable custom portfolios saved by the Investments workspace."""
    try:
        return [
            SavedInvestmentPortfolioModel.model_validate(item)
            for item in get_service(request, "investment_workspace_service").list_portfolios()
        ]
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/investments/workspaces/portfolios", response_model=SavedInvestmentPortfolioModel)
async def save_investment_portfolio(
    payload: SavedInvestmentPortfolioModel,
    request: Request,
) -> SavedInvestmentPortfolioModel:
    """Persist one reusable custom portfolio."""
    try:
        return SavedInvestmentPortfolioModel.model_validate(
            get_service(request, "investment_workspace_service").save_portfolio(
                payload.model_dump()
            )
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.delete("/investments/workspaces/portfolios/{portfolio_id}", status_code=204)
async def delete_investment_portfolio(portfolio_id: str, request: Request) -> None:
    """Delete one saved custom portfolio."""
    try:
        get_service(request, "investment_workspace_service").delete_portfolio(portfolio_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/investments/workspaces/pairs-radar", response_model=list[SavedPairsRadarItemModel])
async def list_pairs_radar_items(request: Request) -> list[SavedPairsRadarItemModel]:
    """List saved pairs radar favorites."""
    try:
        return [
            SavedPairsRadarItemModel.model_validate(item)
            for item in get_service(request, "investment_workspace_service").list_pairs_radar()
        ]
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/investments/workspaces/pairs-radar", response_model=SavedPairsRadarItemModel)
async def save_pairs_radar_item(
    payload: SavedPairsRadarItemModel,
    request: Request,
) -> SavedPairsRadarItemModel:
    """Persist one pairs radar favorite."""
    try:
        return SavedPairsRadarItemModel.model_validate(
            get_service(request, "investment_workspace_service").save_pairs_radar_item(
                payload.model_dump()
            )
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.delete("/investments/workspaces/pairs-radar/{pairs_backtest_id}", status_code=204)
async def delete_pairs_radar_item(pairs_backtest_id: str, request: Request) -> None:
    """Delete one pairs radar favorite."""
    try:
        get_service(request, "investment_workspace_service").delete_pairs_radar_item(
            pairs_backtest_id
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get(
    "/investments/workspaces/strategy-radar",
    response_model=list[SavedStrategyRadarItemModel],
)
async def list_strategy_radar_items(request: Request) -> list[SavedStrategyRadarItemModel]:
    """List saved strategy radar favorites."""
    try:
        return [
            SavedStrategyRadarItemModel.model_validate(item)
            for item in get_service(request, "investment_workspace_service").list_strategy_radar()
        ]
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post(
    "/investments/workspaces/strategy-radar",
    response_model=SavedStrategyRadarItemModel,
)
async def save_strategy_radar_item(
    payload: SavedStrategyRadarItemModel,
    request: Request,
) -> SavedStrategyRadarItemModel:
    """Persist one strategy radar favorite."""
    try:
        return SavedStrategyRadarItemModel.model_validate(
            get_service(request, "investment_workspace_service").save_strategy_radar_item(
                payload.model_dump()
            )
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.delete("/investments/workspaces/strategy-radar/{strategy_id}", status_code=204)
async def delete_strategy_radar_item(strategy_id: str, request: Request) -> None:
    """Delete one strategy radar favorite."""
    try:
        get_service(request, "investment_workspace_service").delete_strategy_radar_item(strategy_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get(
    "/investments/workspaces/strategy-setup-runs",
    response_model=list[SavedStrategySetupRunModel],
)
async def list_strategy_setup_runs(request: Request) -> list[SavedStrategySetupRunModel]:
    """List persisted strategy setup execution summaries."""
    try:
        return [
            SavedStrategySetupRunModel.model_validate(item)
            for item in get_service(
                request, "investment_workspace_service"
            ).list_strategy_setup_runs()
        ]
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post(
    "/investments/workspaces/strategy-setup-runs",
    response_model=SavedStrategySetupRunModel,
)
async def save_strategy_setup_run(
    payload: SavedStrategySetupRunModel,
    request: Request,
) -> SavedStrategySetupRunModel:
    """Persist one strategy setup execution summary."""
    try:
        return SavedStrategySetupRunModel.model_validate(
            get_service(request, "investment_workspace_service").save_strategy_setup_run(
                payload.model_dump()
            )
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get(
    "/investments/workspaces/strategy-setup-scores",
    response_model=list[StrategySetupScoreModel],
)
async def list_strategy_setup_scores(request: Request) -> list[StrategySetupScoreModel]:
    """List explainable scores for strategy setups with persisted runs."""
    try:
        return [
            StrategySetupScoreModel.model_validate(item)
            for item in get_service(
                request, "investment_workspace_service"
            ).list_strategy_setup_scores()
        ]
    except Exception as exc:
        raise to_http_exception(exc) from exc
