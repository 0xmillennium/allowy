"""Parser for Google's JSON IP range format."""

import json
import logging
from src.core.ports.parser import AbstractResponseParser
from src.domain.value_objects import CIDRBlock

logger = logging.getLogger(__name__)


class GoogleJsonParser(AbstractResponseParser):
    """Parses Google's ``prefixes`` JSON format into CIDR blocks."""

    def parse(self, data: bytes) -> list[CIDRBlock]:
        parsed = json.loads(data)
        ranges = []
        for prefix in parsed.get("prefixes", []):
            raw = prefix.get("ipv4Prefix") or prefix.get("ipv6Prefix")
            if raw:
                try:
                    ranges.append(CIDRBlock(value=raw))
                except Exception as e:
                    logger.warning("Skipping invalid CIDR", extra={"raw_cidr": raw, "error": str(e)})
        return ranges
