"""SQLAlchemy table definitions and custom column types."""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Dialect,
    ForeignKey,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    TypeDecorator,
)


class TZDateTime(TypeDecorator[datetime]):
    """Stores datetimes as naive UTC and returns them as timezone-aware UTC objects."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is not None:
            return value.replace(tzinfo=timezone.utc)
        return value


metadata = MetaData()


ip_sources_table = Table(
    "ip_sources",
    metadata,
    Column("id", String(36), key="db_id", primary_key=True),
    Column("name", String(100), key="db_name", unique=True, nullable=False),
    Column("url", String(255), key="db_url", unique=True, nullable=False),
    Column("source_type", String(50), key="db_source_type", nullable=False),
    Column("sync_interval", Integer, key="db_sync_interval", nullable=False),
    Column("status", String(20), key="db_status", nullable=False),
    Column("fetched_at", TZDateTime, key="db_fetched_at", nullable=True),
    Column("created_at", TZDateTime, key="db_created_at", nullable=False),
    Column("updated_at", TZDateTime, key="db_updated_at", nullable=False),
)


ip_source_ranges_table = Table(
    "ip_source_ranges",
    metadata,
    Column(
        "source_id",
        String(36),
        ForeignKey("ip_sources.db_id", ondelete="CASCADE"),
        key="db_source_id",
        nullable=False,
    ),
    Column("cidr", String(50), key="db_cidr", nullable=False),
    PrimaryKeyConstraint("db_source_id", "db_cidr", name="ip_source_ranges_pk"),
)
