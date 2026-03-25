"""HTTP endpoints for liveness and readiness health checks."""

import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from src.core.ports.scheduler import AbstractScheduler
from src.core.ports.unit_of_work import AbstractUnitOfWork
from src.entrypoints.http.dependencies import get_scheduler, get_uow
from src.entrypoints.http.schemas import ComponentHealthSchema, HealthCheckSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/ready")
async def readiness(
    uow: AbstractUnitOfWork = Depends(get_uow),
    scheduler: AbstractScheduler = Depends(get_scheduler),
) -> JSONResponse:
    components: list[ComponentHealthSchema] = []

    components.append(await _check_database(uow))
    components.append(_check_scheduler(scheduler))

    all_healthy = all(c.status == "healthy" for c in components)
    overall_status = "healthy" if all_healthy else "unhealthy"
    http_status = (
        status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    result = HealthCheckSchema(status=overall_status, components=components)

    return JSONResponse(
        status_code=http_status,
        content={
            "status": result.status,
            "components": [
                {"name": c.name, "status": c.status, "detail": c.detail}
                for c in result.components
            ],
        },
    )


async def _check_database(uow: AbstractUnitOfWork) -> ComponentHealthSchema:
    try:
        async with uow:
            await uow.ip_sources.get_all()
        return ComponentHealthSchema(name="database", status="healthy", detail=None)
    except Exception as e:
        logger.warning("Database health check failed", extra={"error": str(e)})
        return ComponentHealthSchema(name="database", status="unhealthy", detail=str(e))


def _check_scheduler(scheduler: AbstractScheduler) -> ComponentHealthSchema:
    try:
        if scheduler.is_running():
            return ComponentHealthSchema(
                name="scheduler", status="healthy", detail=None
            )
        return ComponentHealthSchema(
            name="scheduler", status="unhealthy", detail="Scheduler is not running"
        )
    except Exception as e:
        logger.warning("Scheduler health check failed", extra={"error": str(e)})
        return ComponentHealthSchema(
            name="scheduler", status="unhealthy", detail=str(e)
        )
