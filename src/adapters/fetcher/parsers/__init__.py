from src.core.ports.parser import AbstractResponseParser
from src.adapters.fetcher.parsers.google import GoogleJsonParser

PARSERS: dict[str, AbstractResponseParser] = {
    "google": GoogleJsonParser(),
}
