import pytest
from pydantic import ValidationError

from src.domain.value_objects import (
    CIDRBlock,
    IpSourceID,
    IPVersion,
    SourceName,
    SourceUrl,
    SyncInterval,
)


class TestIpSourceID:
    def test_valid_uuid(self):
        id = IpSourceID.create()
        assert id.value is not None

    def test_invalid_uuid_raises(self):
        with pytest.raises(ValidationError):
            IpSourceID(value="not-a-uuid")


class TestSourceName:
    def test_valid_name(self):
        name = SourceName(value="Googlebot")
        assert name.value == "Googlebot"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            SourceName(value="")

    def test_single_char_name_succeeds(self):
        name = SourceName(value="a")
        assert name.value == "a"

    def test_at_max_length_succeeds(self):
        name = SourceName(value="a" * 100)
        assert name.value == "a" * 100

    def test_too_long_name_raises(self):
        with pytest.raises(ValidationError):
            SourceName(value="a" * 101)

    def test_whitespace_only_name_is_accepted(self):
        # NOTE: whitespace-only names pass min_length validation.
        # Consider adding a strip_whitespace validator if this is undesired.
        name = SourceName(value="   ")
        assert name.value == "   "


class TestSourceUrl:
    def test_valid_http_url(self):
        url = SourceUrl(value="http://example.com")
        assert url.value == "http://example.com"

    def test_valid_https_url(self):
        url = SourceUrl(value="https://example.com")
        assert url.value == "https://example.com"

    def test_invalid_url_raises(self):
        with pytest.raises(ValidationError):
            SourceUrl(value="not-a-url")

    def test_url_with_path_and_query_succeeds(self):
        url = SourceUrl(value="https://example.com/path?q=1")
        assert url.value == "https://example.com/path?q=1"

    def test_non_http_scheme_raises(self):
        with pytest.raises(ValidationError):
            SourceUrl(value="ftp://example.com")


class TestSyncInterval:
    def test_valid_interval(self):
        interval = SyncInterval(value=60)
        assert interval.value == 60

    def test_at_minimum_boundary_succeeds(self):
        interval = SyncInterval(value=5)
        assert interval.value == 5

    def test_just_below_minimum_raises(self):
        with pytest.raises(ValidationError):
            SyncInterval(value=4)

    def test_below_minimum_raises(self):
        with pytest.raises(ValidationError):
            SyncInterval(value=1)

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            SyncInterval(value=-1)

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            SyncInterval(value=0)


class TestCIDRBlock:
    def test_valid_ipv4_cidr(self):
        cidr = CIDRBlock(value="192.168.1.0/24")
        assert cidr.value == "192.168.1.0/24"

    def test_valid_ipv6_cidr(self):
        cidr = CIDRBlock(value="2001:4860::/32")
        assert cidr.value == "2001:4860::/32"

    def test_host_address_cidr_succeeds(self):
        cidr = CIDRBlock(value="192.168.1.1/32")
        assert cidr.value == "192.168.1.1/32"

    def test_invalid_cidr_raises(self):
        with pytest.raises(ValidationError):
            CIDRBlock(value="not-a-cidr")

    def test_ipv4_version(self):
        cidr = CIDRBlock(value="192.168.1.0/24")
        assert cidr.ip_version == IPVersion.V4

    def test_ipv6_version(self):
        cidr = CIDRBlock(value="2001:4860::/32")
        assert cidr.ip_version == IPVersion.V6
