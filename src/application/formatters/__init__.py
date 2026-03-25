__all__ = [
    "AbstractFormatter",
    "FormattedOutput",
    "NginxFormatter",
    "RawFormatter",
    "TraefikFormatter",
    "FORMATTERS",
]

from src.application.formatters.base import AbstractFormatter, FormattedOutput
from src.application.formatters.nginx import NginxFormatter
from src.application.formatters.raw import RawFormatter
from src.application.formatters.traefik import TraefikFormatter

FORMATTERS = [NginxFormatter, TraefikFormatter, RawFormatter]
