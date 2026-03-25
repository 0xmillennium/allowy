"""HTTP endpoints for IP source CRUD and lifecycle operations."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.messagebus import AbstractMessageBus
from src.application.views import (
    get_all_ip_sources,
    get_ip_source,
    get_supported_source_types,
)
from src.core.ports.fetcher import AbstractIPFetcher
from src.domain.commands import (
    CreateIpSource,
    DeleteIpSource,
    PauseAllIpSources,
    PauseIpSource,
    ResumeAllIpSources,
    ResumeIpSource,
    SourceData,
    UpdateSourceName,
    UpdateSourceType,
    UpdateSyncInterval,
)
from src.entrypoints.http.dependencies import get_fetcher, get_messagebus, get_uow
from src.entrypoints.http.schemas import IpSourceSchema

router = APIRouter(prefix="/ip-sources", tags=["ip-sources"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ip_source(
    name: str,
    url: str,
    source_type: str,
    sync_interval: int,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(
        CreateIpSource(
            source=SourceData(
                name=name,
                url=url,
                source_type=source_type,
                sync_interval=sync_interval,
            )
        )
    )


@router.get("/source-types", status_code=status.HTTP_200_OK)
async def list_supported_source_types(
    fetcher: AbstractIPFetcher = Depends(get_fetcher),
) -> list[str]:
    return get_supported_source_types(fetcher=fetcher)


@router.get("", response_model=list[IpSourceSchema])
async def list_ip_sources(
    uow=Depends(get_uow),
) -> list[IpSourceSchema]:
    return await get_all_ip_sources(uow=uow)


@router.get("/{source_id}", response_model=IpSourceSchema)
async def retrieve_ip_source(
    source_id: str,
    uow=Depends(get_uow),
) -> IpSourceSchema:
    result = await get_ip_source(source_id=source_id, uow=uow)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IpSource not found",
        )
    return result


@router.patch("/{source_id}/name", status_code=status.HTTP_200_OK)
async def update_source_name(
    source_id: str,
    name: str,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(UpdateSourceName(source_id=source_id, name=name))


@router.patch("/{source_id}/source-type", status_code=status.HTTP_200_OK)
async def update_source_type(
    source_id: str,
    source_type: str,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(UpdateSourceType(source_id=source_id, source_type=source_type))


@router.patch("/{source_id}/interval", status_code=status.HTTP_200_OK)
async def update_sync_interval(
    source_id: str,
    sync_interval: int,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(
        UpdateSyncInterval(
            source_id=source_id,
            sync_interval=sync_interval,
        )
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ip_source(
    source_id: str,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(DeleteIpSource(source_id=source_id))


@router.post("/{source_id}/pause", status_code=status.HTTP_200_OK)
async def pause_ip_source(
    source_id: str,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(PauseIpSource(source_id=source_id))


@router.post("/{source_id}/resume", status_code=status.HTTP_200_OK)
async def resume_ip_source(
    source_id: str,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(ResumeIpSource(source_id=source_id))


@router.post("/pause-all", status_code=status.HTTP_200_OK)
async def pause_all_ip_sources(
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(PauseAllIpSources())


@router.post("/resume-all", status_code=status.HTTP_200_OK)
async def resume_all_ip_sources(
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(ResumeAllIpSources())
