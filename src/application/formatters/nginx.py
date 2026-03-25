"""Nginx output formatter."""

from src.domain.value_objects import CIDRBlock

from .base import AbstractFormatter


class NginxFormatter(AbstractFormatter):
    """Formats IP ranges as nginx ``allow`` directives with a trailing ``deny all``."""

    @classmethod
    def filename(cls) -> str:
        return "nginx.conf"

    @classmethod
    def _format(cls, ipv4: list[CIDRBlock], ipv6: list[CIDRBlock]) -> str:
        lines = []

        lines.append("# IPv4")
        for cidr in ipv4:
            lines.append(f"allow {cidr.value};")

        lines.append("")
        lines.append("# IPv6")
        for cidr in ipv6:
            lines.append(f"allow {cidr.value};")

        lines.append("")
        lines.append("deny all;")

        return "\n".join(lines)
