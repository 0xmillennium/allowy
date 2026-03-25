"""Traefik output formatter."""

from src.domain.value_objects import CIDRBlock

from .base import AbstractFormatter


class TraefikFormatter(AbstractFormatter):
    """Formats IP ranges as a Traefik YAML middleware ipWhiteList configuration."""

    @classmethod
    def filename(cls) -> str:
        return "traefik.yml"

    @classmethod
    def _format(cls, ipv4: list[CIDRBlock], ipv6: list[CIDRBlock]) -> str:
        lines = []

        lines.append("http:")
        lines.append("  middlewares:")
        lines.append("    google-ip-whitelist:")
        lines.append("      ipWhiteList:")
        lines.append("        sourceRange:")

        lines.append("          # IPv4")
        for cidr in ipv4:
            lines.append(f'          - "{cidr.value}"')

        lines.append("          # IPv6")
        for cidr in ipv6:
            lines.append(f'          - "{cidr.value}"')

        return "\n".join(lines)
