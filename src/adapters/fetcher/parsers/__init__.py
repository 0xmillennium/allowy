from src.adapters.fetcher.parsers.google import GoogleJsonParser
from src.core.ports.parser import AbstractResponseParser

PARSERS: dict[str, AbstractResponseParser] = {
    "google": GoogleJsonParser(),
}
