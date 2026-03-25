import pytest
from src.domain.value_objects import CIDRBlock
from src.application.formatters.nginx import NginxFormatter
from src.application.formatters.traefik import TraefikFormatter
from src.application.formatters.raw import RawFormatter


IPV4_RANGES = [
    CIDRBlock(value="192.168.1.0/24"),
    CIDRBlock(value="10.0.0.0/8"),
]
IPV6_RANGES = [
    CIDRBlock(value="2001:4860::/32"),
    CIDRBlock(value="2607:f8b0::/32"),
]
ALL_RANGES = IPV4_RANGES + IPV6_RANGES


class TestNginxFormatter:

    def test_filename(self):
        assert NginxFormatter.filename() == "nginx.conf"

    def test_output_contains_allow_directives(self):
        output = NginxFormatter.format(ALL_RANGES)
        assert "allow 192.168.1.0/24;" in output.content
        assert "allow 2001:4860::/32;" in output.content

    def test_output_contains_deny_all(self):
        output = NginxFormatter.format(ALL_RANGES)
        assert "deny all;" in output.content

    def test_output_separates_ipv4_and_ipv6(self):
        output = NginxFormatter.format(ALL_RANGES)
        assert "# IPv4" in output.content
        assert "# IPv6" in output.content

    def test_ipv4_comes_before_ipv6(self):
        output = NginxFormatter.format(ALL_RANGES)
        ipv4_pos = output.content.index("# IPv4")
        ipv6_pos = output.content.index("# IPv6")
        assert ipv4_pos < ipv6_pos

    def test_returns_formatted_output(self):
        output = NginxFormatter.format(ALL_RANGES)
        assert output.filename == "nginx.conf"
        assert output.content is not None

    def test_empty_ranges_still_has_deny_all(self):
        output = NginxFormatter.format([])
        assert "deny all;" in output.content


class TestTraefikFormatter:

    def test_filename(self):
        assert TraefikFormatter.filename() == "traefik.yml"

    def test_output_contains_yaml_structure(self):
        output = TraefikFormatter.format(ALL_RANGES)
        assert "http:" in output.content
        assert "middlewares:" in output.content
        assert "ipWhiteList:" in output.content
        assert "sourceRange:" in output.content

    def test_output_contains_cidr_ranges(self):
        output = TraefikFormatter.format(ALL_RANGES)
        assert '"192.168.1.0/24"' in output.content
        assert '"2001:4860::/32"' in output.content

    def test_output_separates_ipv4_and_ipv6(self):
        output = TraefikFormatter.format(ALL_RANGES)
        assert "# IPv4" in output.content
        assert "# IPv6" in output.content

    def test_returns_formatted_output(self):
        output = TraefikFormatter.format(ALL_RANGES)
        assert output.filename == "traefik.yml"
        assert output.content is not None

    def test_empty_ranges(self):
        output = TraefikFormatter.format([])
        assert output.filename == "traefik.yml"
        assert output.content is not None

    def test_only_ipv4_ranges(self):
        output = TraefikFormatter.format(IPV4_RANGES)
        assert "192.168.1.0/24" in output.content
        assert "2001:4860::" not in output.content

    def test_single_range(self):
        output = TraefikFormatter.format([CIDRBlock(value="10.0.0.0/8")])
        assert "10.0.0.0/8" in output.content


class TestRawFormatter:

    def test_filename(self):
        assert RawFormatter.filename() == "raw.txt"

    def test_output_contains_cidr_ranges(self):
        output = RawFormatter.format(ALL_RANGES)
        assert "192.168.1.0/24" in output.content
        assert "2001:4860::/32" in output.content

    def test_output_separates_ipv4_and_ipv6(self):
        output = RawFormatter.format(ALL_RANGES)
        assert "# IPv4" in output.content
        assert "# IPv6" in output.content

    def test_returns_formatted_output(self):
        output = RawFormatter.format(ALL_RANGES)
        assert output.filename == "raw.txt"
        assert output.content is not None

    def test_empty_ranges(self):
        output = RawFormatter.format([])
        assert output.filename == "raw.txt"
        assert output.content is not None

    def test_only_ipv6_ranges(self):
        output = RawFormatter.format(IPV6_RANGES)
        assert "2001:4860::/32" in output.content
        assert "192.168.1.0/24" not in output.content

    def test_single_range(self):
        output = RawFormatter.format([CIDRBlock(value="10.0.0.0/8")])
        assert "10.0.0.0/8" in output.content