"""Local filesystem implementation of the file operator port."""

import logging
from pathlib import Path

import aiofiles

from src.core.exceptions.exceptions import FileReadError, FileWriteError
from src.core.ports.file_operator import AbstractFileOperator

logger = logging.getLogger(__name__)


class LocalFileOperator(AbstractFileOperator):
    """Reads and writes files on the local filesystem."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def write(self, content: str, filename: str) -> None:
        path = self._output_dir / filename
        logger.debug(
            "Writing output file",
            extra={"path": str(path), "content_length": len(content)},
        )
        try:
            async with aiofiles.open(path, mode="w") as f:
                await f.write(content)
            logger.info("Output written", extra={"path": str(path)})
        except OSError as e:
            raise FileWriteError(msg=str(e))

    async def read(self, filename: str) -> str:
        path = self._output_dir / filename
        try:
            async with aiofiles.open(path, mode="r") as f:
                return await f.read()
        except OSError as e:
            raise FileReadError(msg=str(e))
