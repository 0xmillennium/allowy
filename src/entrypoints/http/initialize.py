"""HTTP endpoint for application initialization."""

from fastapi import APIRouter, Depends, status

from src.application.messagebus import AbstractMessageBus
from src.config import SourcesConfig
from src.domain.commands import InitializeApplication, SourceData
from src.entrypoints.http.dependencies import get_messagebus, get_sources_config

router = APIRouter(tags=["initialize"])


@router.post("/initialize", status_code=status.HTTP_200_OK)
async def initialize(
    mbus: AbstractMessageBus = Depends(get_messagebus),
    config: SourcesConfig = Depends(get_sources_config),
) -> None:
    await mbus.handle(
        InitializeApplication(
            sources=tuple(
                SourceData(
                    name=s.name,
                    url=s.url,
                    source_type=s.source_type,
                    sync_interval=s.sync_interval,
                )
                for s in config.sources
            )
        )
    )
