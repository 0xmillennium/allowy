"""HTTP-based IP range fetcher using httpx."""

import logging
import httpx
from src.domain.model import IpSource
from src.domain.value_objects import CIDRBlock
from src.core.ports.fetcher import AbstractIPFetcher
from src.core.exceptions.exceptions import (
    FetcherNetworkException,
    FetcherParseException,
    UnsupportedSourceTypeException,
)
from src.adapters.fetcher.parsers import PARSERS

logger = logging.getLogger(__name__)


class HttpIPFetcher(AbstractIPFetcher):
    """Fetches IP ranges from upstream providers over HTTP using httpx."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._parsers = PARSERS

    async def sync(self, source: IpSource) -> list[CIDRBlock]:
        parser = self._parsers.get(source.source_type.value)
        if parser is None:
            raise UnsupportedSourceTypeException(
                msg=f"No parser registered for source type: {source.source_type.value}"
            )

        logger.debug("Fetching from upstream", extra={"url": source.url.value, "source_type": source.source_type.value})
        try:
            response = await self._client.get(source.url.value)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning("Fetch returned non-OK status", extra={"url": source.url.value, "status_code": e.response.status_code})
            raise FetcherNetworkException(msg=str(e))
        except httpx.NetworkError as e:
            raise FetcherNetworkException(msg=str(e))

        logger.info("Fetched IP ranges", extra={"source_type": source.source_type.value, "url": source.url.value})

        logger.debug("Parsing response", extra={"source_type": source.source_type.value, "content_length": len(response.content)})
        try:
            return parser.parse(response.content)
        except Exception as e:
            raise FetcherParseException(msg=str(e))

    def supported_source_types(self) -> list[str]:
        return list(self._parsers.keys())
