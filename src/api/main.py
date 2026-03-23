"""FastAPI main application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from ..bitcoin_martingale.application.runs import RunBacktestService
from ..bitcoin_martingale.infrastructure.logging import configure_logging
from ..bitcoin_martingale.interfaces.api.errors import to_http_exception
from .models import BacktestRequest, BacktestResponse, ConfigInfo

configure_logging()
logger = logging.getLogger(__name__)
service = RunBacktestService()

app = FastAPI(
    title="Bitcoin Martingale Backtest API",
    description="Interactive backtesting API for Bitcoin Martingale strategies",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Bitcoin Martingale Backtest API", "version": "1.0.0"}


@app.get("/configs", response_model=list[ConfigInfo])
async def get_configs():
    """List available configuration files."""
    try:
        return service.list_configs()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run backtest with specified parameters."""
    try:
        return service.run(request)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/reports/{strategy}/download")
async def download_csv(strategy: str):
    """Download CSV with trades and equity data for a strategy."""
    try:
        csv_content = service.download_csv(strategy)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{strategy}_latest_trades.csv"'},
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}")
async def get_run_manifest(run_id: str):
    """Return the persisted manifest for a run."""
    try:
        return service.get_run_manifest(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/response")
async def get_run_response(run_id: str):
    """Return the persisted response payload for a run."""
    try:
        return service.get_run_response(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/config")
async def get_run_config(run_id: str):
    """Return the resolved config snapshot for a run."""
    try:
        return service.get_run_config_snapshot(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/data-profile")
async def get_run_data_profile(run_id: str):
    """Return the dataset profile for a run."""
    try:
        return service.get_run_data_profile(run_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/report.html")
async def get_run_html_report(run_id: str):
    """Download the persisted HTML report for a run."""
    try:
        html_report = service.get_run_html_report(run_id)
        return Response(
            content=html_report,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{run_id}_report.html"'},
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs")
async def list_runs():
    """List persisted runs."""
    try:
        return service.list_runs()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@app.get("/runs/{run_id}/strategies/{strategy_name}/trades.csv")
async def download_run_strategy_csv(run_id: str, strategy_name: str):
    """Download a persisted strategy trades CSV."""
    try:
        csv_content = service.get_trades_csv(run_id, strategy_name)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{run_id}_{strategy_name}_trades.csv"'
                )
            },
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc
