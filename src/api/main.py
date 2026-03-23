"""FastAPI main application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
        service.download_csv(strategy)
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
