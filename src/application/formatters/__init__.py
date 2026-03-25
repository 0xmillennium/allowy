from src.application.formatters.base import AbstractFormatter, FormattedOutput
from src.application.formatters.nginx import NginxFormatter
from src.application.formatters.traefik import TraefikFormatter
from src.application.formatters.raw import RawFormatter

FORMATTERS = [NginxFormatter, TraefikFormatter, RawFormatter]