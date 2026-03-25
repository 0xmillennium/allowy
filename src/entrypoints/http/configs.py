"""HTTP endpoints for retrieving formatted IP range configuration files."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from src.application.views import get_config
from src.core.ports.file_operator import AbstractFileOperator
from src.entrypoints.http.dependencies import get_filer

router = APIRouter(prefix="/configs", tags=["configs"])


@router.get("/nginx")
async def get_nginx_config(
    filer: AbstractFileOperator = Depends(get_filer),
) -> Response:
    content = await get_config(filename="nginx.conf", filer=filer)
    return Response(content=content, media_type="text/plain")


@router.get("/traefik")
async def get_traefik_config(
    filer: AbstractFileOperator = Depends(get_filer),
) -> Response:
    content = await get_config(filename="traefik.yml", filer=filer)
    return Response(content=content, media_type="text/plain")


@router.get("/raw")
async def get_raw_config(
    filer: AbstractFileOperator = Depends(get_filer),
) -> Response:
    content = await get_config(filename="raw.txt", filer=filer)
    return Response(content=content, media_type="text/plain")