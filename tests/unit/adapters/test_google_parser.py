import json

from src.adapters.fetcher.parsers.google import GoogleJsonParser

VALID_GOOGLE_RESPONSE = {
    "prefixes": [
        {"ipv4Prefix": "66.249.64.0/19"},
        {"ipv6Prefix": "2001:4860:4801::/48"},
        {"ipv4Prefix": "66.249.96.0/20"},
    ]
}


class TestGoogleJsonParser:
    def test_parses_valid_response(self):
        parser = GoogleJsonParser()
        data = json.dumps(VALID_GOOGLE_RESPONSE).encode()
        ranges = parser.parse(data)
        assert len(ranges) == 3
        values = [r.value for r in ranges]
        assert "66.249.64.0/19" in values
        assert "2001:4860:4801::/48" in values

    def test_handles_ipv4_and_ipv6(self):
        parser = GoogleJsonParser()
        data = json.dumps(VALID_GOOGLE_RESPONSE).encode()
        ranges = parser.parse(data)
        ipv4 = [r for r in ranges if r.ip_version.value == "v4"]
        ipv6 = [r for r in ranges if r.ip_version.value == "v6"]
        assert len(ipv4) == 2
        assert len(ipv6) == 1

    def test_skips_invalid_cidr(self):
        response = {
            "prefixes": [
                {"ipv4Prefix": "66.249.64.0/19"},
                {"ipv4Prefix": "not-a-cidr"},
            ]
        }
        parser = GoogleJsonParser()
        data = json.dumps(response).encode()
        ranges = parser.parse(data)
        assert len(ranges) == 1

    def test_returns_empty_when_no_prefixes(self):
        parser = GoogleJsonParser()
        data = json.dumps({"prefixes": []}).encode()
        ranges = parser.parse(data)
        assert ranges == []

    def test_returns_empty_when_prefixes_key_missing(self):
        parser = GoogleJsonParser()
        data = json.dumps({}).encode()
        ranges = parser.parse(data)
        assert ranges == []
