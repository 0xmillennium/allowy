"""Raw plain-text output formatter."""

from src.domain.value_objects import CIDRBlock
from .base import AbstractFormatter


class RawFormatter(AbstractFormatter):
    """Formats IP ranges as plain-text CIDR blocks, one per line."""

    @classmethod
    def filename(cls) -> str:
        return "raw.txt"

    @classmethod
    def _format(cls, ipv4: list[CIDRBlock], ipv6: list[CIDRBlock]) -> str:
        lines = []

        lines.append("# IPv4")
        for cidr in ipv4:
            lines.append(cidr.value)

        lines.append("")
        lines.append("# IPv6")
        for cidr in ipv6:
            lines.append(cidr.value)

        return "\n".join(lines)