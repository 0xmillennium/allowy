"""Base formatter defining the contract for converting CIDR blocks to output files."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from src.domain.value_objects import CIDRBlock, IPVersion


@dataclass(frozen=True)
class FormattedOutput:
    filename: str
    content: str


class AbstractFormatter(ABC):
    """Formats CIDR blocks into provider-specific output files.

    Uses the Template Method pattern: ``format()`` splits ranges by IP
    version and delegates to ``_format()`` which subclasses implement.
    """

    @classmethod
    def format(cls, ranges: list[CIDRBlock]) -> FormattedOutput:
        """Splits ranges by IP version and produces a formatted output file."""
        ipv4 = [r for r in ranges if r.ip_version == IPVersion.V4]
        ipv6 = [r for r in ranges if r.ip_version == IPVersion.V6]
        return FormattedOutput(
            filename=cls.filename(),
            content=cls._format(ipv4, ipv6),
        )

    @classmethod
    @abstractmethod
    def filename(cls) -> str: ...

    @classmethod
    @abstractmethod
    def _format(cls, ipv4: list[CIDRBlock], ipv6: list[CIDRBlock]) -> str: ...