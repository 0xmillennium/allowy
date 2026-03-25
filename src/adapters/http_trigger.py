"""HTTP-based sync trigger that dispatches sync requests via POST."""

import logging

import httpx

from src.core.exceptions.exceptions import SyncTriggerError
from src.core.ports.trigger import AbstractSyncTrigger

logger = logging.getLogger(__name__)


class HttpSyncTrigger(AbstractSyncTrigger):
    """Triggers source syncs by posting to the application's own HTTP endpoint."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def sync(self, source_id: str) -> None:
        logger.debug("Triggering sync via HTTP", extra={"source_id": source_id})
        try:
            response = await self._client.post(f"/sync/{source_id}")
            response.raise_for_status()
        except Exception as e:
            raise SyncTriggerError(
                msg=f"Failed to trigger sync for {source_id}: {e}"
            ) from e
