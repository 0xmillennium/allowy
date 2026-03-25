import httpx
import pytest

from src.adapters.fetcher import HttpIPFetcher
from src.core.exceptions.exceptions import (
    FetcherNetworkError,
    FetcherParseError,
    UnsupportedSourceTypeError,
)
from src.domain.model import IpSource

VALID_GOOGLE_RESPONSE = {
    "prefixes": [
        {"ipv4Prefix": "66.249.64.0/19"},
        {"ipv6Prefix": "2001:4860:4801::/48"},
        {"ipv4Prefix": "66.249.96.0/20"},
    ]
}


def _make_transport(
    status_code: int = 200,
    json_data: dict | None = None,
    error: Exception | None = None,
):
    def handler(request: httpx.Request) -> httpx.Response:
        if error:
            raise error
        return httpx.Response(
            status_code=status_code,
            json=json_data or {},
        )

    return httpx.MockTransport(handler)


class TestHttpIPFetcherSync:
    async def test_parses_valid_response(self, sample_source):
        transport = _make_transport(json_data=VALID_GOOGLE_RESPONSE)
        async with httpx.AsyncClient(transport=transport) as client:
            fetcher = HttpIPFetcher(client=client)
            ranges = await fetcher.sync(sample_source)
            assert len(ranges) == 3
            values = [r.value for r in ranges]
            assert "66.249.64.0/19" in values
            assert "2001:4860:4801::/48" in values

    async def test_raises_network_exception_on_http_error(self, sample_source):
        transport = _make_transport(status_code=500, json_data={})
        async with httpx.AsyncClient(transport=transport) as client:
            fetcher = HttpIPFetcher(client=client)
            with pytest.raises(FetcherNetworkError):
                await fetcher.sync(sample_source)

    async def test_raises_network_exception_on_connect_error(self, sample_source):
        transport = _make_transport(error=httpx.ConnectError("connection refused"))
        async with httpx.AsyncClient(transport=transport) as client:
            fetcher = HttpIPFetcher(client=client)
            with pytest.raises(FetcherNetworkError):
                await fetcher.sync(sample_source)

    async def test_raises_parse_exception_on_malformed_json(self, sample_source):
        transport = _make_transport(json_data="not-a-dict")
        async with httpx.AsyncClient(transport=transport) as client:
            fetcher = HttpIPFetcher(client=client)
            with pytest.raises(FetcherParseError):
                await fetcher.sync(sample_source)

    async def test_raises_unsupported_source_type(self):
        source = IpSource.create(
            name="Unknown",
            url="https://example.com",
            source_type="unsupported",
            sync_interval=60,
        )
        transport = _make_transport(json_data={})
        async with httpx.AsyncClient(transport=transport) as client:
            fetcher = HttpIPFetcher(client=client)
            with pytest.raises(UnsupportedSourceTypeError):
                await fetcher.sync(source)


class TestHttpIPFetcherSupportedTypes:
    def test_returns_registered_source_types(self):
        async def noop():
            pass

        transport = _make_transport()
        client = httpx.AsyncClient(transport=transport)
        fetcher = HttpIPFetcher(client=client)
        types = fetcher.supported_source_types()
        assert "google" in types
