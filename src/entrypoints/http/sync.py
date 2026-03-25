"""HTTP endpoint for triggering IP source sync."""

from fastapi import APIRouter, Depends, status

from src.application.messagebus import AbstractMessageBus
from src.domain.commands import SyncIpSource
from src.entrypoints.http.dependencies import get_messagebus

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/{source_id}", status_code=status.HTTP_200_OK)
async def sync_ip_source(
    source_id: str,
    mbus: AbstractMessageBus = Depends(get_messagebus),
) -> None:
    await mbus.handle(SyncIpSource(source_id=source_id))
