"""FastAPI main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..investing_workbench.infrastructure.logging import configure_logging
from ..investing_workbench.interfaces.api import services as api_services
from ..investing_workbench.interfaces.api.routers.allocations import router as allocations_router
from ..investing_workbench.interfaces.api.routers.datasets import router as datasets_router
from ..investing_workbench.interfaces.api.routers.investments import router as investments_router
from ..investing_workbench.interfaces.api.routers.pairs import router as pairs_router
from ..investing_workbench.interfaces.api.routers.research import router as research_router
from ..investing_workbench.interfaces.api.routers.runs import router as runs_router
from ..investing_workbench.interfaces.api.routers.scenarios import router as scenarios_router
from ..investing_workbench.interfaces.api.routers.system import router as system_router

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build and tear down the application service graph with the API lifecycle."""
    services = api_services.build_api_services(autostart_jobs=True)
    api_services.install_service_container(app, services)
    try:
        yield
    finally:
        api_services.shutdown_api_services(services, cancel_running=False)


app = FastAPI(
    title="Investing Workbench API",
    description="Interactive investment comparison, backtesting, and research API",
    version="1.0.0",
    lifespan=lifespan,
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

for router in (
    system_router,
    datasets_router,
    investments_router,
    runs_router,
    scenarios_router,
    research_router,
    pairs_router,
    allocations_router,
):
    app.include_router(router)
