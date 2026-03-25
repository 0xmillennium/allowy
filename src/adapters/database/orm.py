"""SQLAlchemy classical (imperative) ORM mappings for domain entities."""

from sqlalchemy.orm import composite, registry, relationship

from src.adapters.database.schema import ip_source_ranges_table, ip_sources_table

mapper_registry = registry()


def init_orm_mappers() -> None:
    from src.domain.model import IpRange, IpSource
    from src.domain.value_objects import (
        CIDRBlock,
        IpSourceID,
        SourceName,
        SourceStatus,
        SourceType,
        SourceUrl,
        SyncInterval,
    )

    mapper_registry.map_imperatively(
        IpRange,
        ip_source_ranges_table,
        properties={
            "source_id": composite(IpSourceID, ip_source_ranges_table.c.db_source_id),
            "cidr": composite(CIDRBlock, ip_source_ranges_table.c.db_cidr),
        },
    )

    mapper_registry.map_imperatively(
        IpSource,
        ip_sources_table,
        properties={
            "id": composite(IpSourceID, ip_sources_table.c.db_id),
            "name": composite(SourceName, ip_sources_table.c.db_name),
            "url": composite(SourceUrl, ip_sources_table.c.db_url),
            "source_type": composite(SourceType, ip_sources_table.c.db_source_type),
            "sync_interval": composite(
                SyncInterval, ip_sources_table.c.db_sync_interval
            ),
            "status": composite(SourceStatus, ip_sources_table.c.db_status),
            "fetched_at": ip_sources_table.c.db_fetched_at,
            "created_at": ip_sources_table.c.db_created_at,
            "updated_at": ip_sources_table.c.db_updated_at,
            "ip_ranges": relationship(
                IpRange,
                cascade="all, delete-orphan",
                lazy="joined",
            ),
        },
    )
