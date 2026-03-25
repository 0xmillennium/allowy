"""Read-only query functions for retrieving IP source data."""

from src.core.ports.fetcher import AbstractIPFetcher
from src.core.ports.file_operator import AbstractFileOperator
from src.core.ports.unit_of_work import AbstractUnitOfWork
from src.domain.value_objects import IpSourceID
from src.entrypoints.http.schemas import IpSourceSchema


async def get_ip_source(
    source_id: str,
    uow: AbstractUnitOfWork,
) -> IpSourceSchema | None:
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=source_id))
        if not source:
            return None
        return IpSourceSchema.from_domain(source)


async def get_all_ip_sources(
    uow: AbstractUnitOfWork,
) -> list[IpSourceSchema]:
    async with uow:
        sources = await uow.ip_sources.get_all()
        return [IpSourceSchema.from_domain(source) for source in sources]


async def get_config(
    filename: str,
    filer: AbstractFileOperator,
) -> str:
    return await filer.read(filename)


def get_supported_source_types(
    fetcher: AbstractIPFetcher,
) -> list[str]:
    return fetcher.supported_source_types()
