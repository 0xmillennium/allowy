"""FastAPI application setup, lifecycle management, and database initialization."""

import httpx
import logging
from pathlib import Path
from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import StaticPool
from src.config import settings
from src.adapters.fetcher import HttpIPFetcher
from src.adapters.scheduler import APScheduler
from src.adapters.file_operator import LocalFileOperator
from src.adapters.http_trigger import HttpSyncTrigger
from src.entrypoints.http.sync import router as sync_router
from src.entrypoints.http.configs import router as configs_router
from src.entrypoints.http.ip_sources import router as ip_sources_router
from src.entrypoints.http.health import router as health_router
from src.entrypoints.http.initialize import router as initialize_router
from src.adapters.database.orm import init_orm_mappers
from src.adapters.database.schema import metadata
from src.core.exceptions.handlers import EXCEPTION_HANDLERS
from src.core.exceptions import DatabaseInitializationException, ApplicationStartupException


logger = logging.getLogger(__name__)


async def init_db(engine: AsyncEngine) -> None:
    try:
        init_orm_mappers()
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical("Database initialization failed", extra={"error": str(e)})
        raise DatabaseInitializationException(msg=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = None
    fetcher_client = None
    trigger_client = None
    scheduler_adapter = None

    try:

        # infrastructure
        engine = create_async_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False
        )
        trigger_client = httpx.AsyncClient(
            base_url=f"http://localhost:{settings.server_port}",
            timeout=settings.http_timeout
        )
        fetcher_client = httpx.AsyncClient(
            timeout=settings.http_timeout
        )
        scheduler = AsyncIOScheduler(
            timezone=settings.scheduler_timezone
        )

        # initialize database
        await init_db(engine)

        # adapters
        scheduler_adapter = APScheduler(scheduler=scheduler)
        fetcher = HttpIPFetcher(client=fetcher_client)
        filer = LocalFileOperator(output_dir=settings.output_dir)
        trigger = HttpSyncTrigger(client=trigger_client)

        # store in app state
        app.state.session_factory = session_factory
        app.state.scheduler = scheduler_adapter
        app.state.fetcher = fetcher
        app.state.filer = filer
        app.state.trigger = trigger

        # start scheduler
        await scheduler_adapter.start()

        logger.info("Application started successfully")

        yield

    except Exception as e:
        logger.critical("Application startup failed", extra={"error": str(e)})
        raise ApplicationStartupException(msg=str(e))

    finally:
        logger.info("Application shutting down")
        if scheduler_adapter:
            await scheduler_adapter.stop()
        if trigger_client:
            await trigger_client.aclose()
        if fetcher_client:
            await fetcher_client.aclose()
        if engine:
            await engine.dispose()
        logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Allowy",
        description="IP allowlist syncing service for multiple providers",
        version="1.0.0",
        lifespan=lifespan,
    )

    # routers
    app.include_router(sync_router)
    app.include_router(configs_router)
    app.include_router(ip_sources_router)
    app.include_router(health_router)
    app.include_router(initialize_router)

    # exception handlers
    for exc_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)

    return app


app = create_app()

