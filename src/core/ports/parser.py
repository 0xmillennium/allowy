"""Abstract parser defining the contract for converting
upstream responses to CIDR blocks."""

from abc import ABC, abstractmethod

from src.domain.value_objects import CIDRBlock


class AbstractResponseParser(ABC):
    """Parses raw upstream HTTP response data into CIDR blocks."""

    @abstractmethod
    def parse(self, data: bytes) -> list[CIDRBlock]:
        """Parses raw response bytes into a list of valid CIDR blocks.

        Unparseable entries are skipped rather than raising.

        Args:
            data: Raw bytes from the upstream HTTP response.
        """
        ...
