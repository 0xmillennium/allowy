"""Abstract sync trigger defining the contract for initiating source syncs."""

from abc import ABC, abstractmethod


class AbstractSyncTrigger(ABC):
    """Triggers a sync operation for an IP source.

    Provides indirection between the scheduler and the message bus,
    since scheduler callbacks cannot dispatch commands directly.
    """

    @abstractmethod
    async def sync(self, source_id: str) -> None:
        """Triggers a sync for the given source.

        Args:
            source_id: UUID string identifying the IP source.

        Raises:
            SyncTriggerError: If the sync trigger fails.
        """
        ...
