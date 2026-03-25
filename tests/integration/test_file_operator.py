from pathlib import Path

import pytest

from src.adapters.file_operator import LocalFileOperator
from src.core.exceptions.exceptions import FileReadError, FileWriteError


@pytest.fixture
def file_operator(tmp_path: Path) -> LocalFileOperator:
    return LocalFileOperator(output_dir=tmp_path)


class TestLocalFileOperator:
    async def test_write_and_read_round_trip(self, file_operator):
        await file_operator.write("allow 192.168.1.0/24;", "nginx.conf")
        content = await file_operator.read("nginx.conf")
        assert content == "allow 192.168.1.0/24;"

    async def test_read_nonexistent_raises_file_read_exception(self, file_operator):
        with pytest.raises(FileReadError):
            await file_operator.read("nonexistent.conf")

    async def test_write_to_invalid_path_raises_file_write_exception(self, tmp_path):
        operator = LocalFileOperator(output_dir=tmp_path)
        # Create a directory where the file should be
        # — write will fail with IsADirectoryError
        (tmp_path / "blocked.conf").mkdir()
        with pytest.raises(FileWriteError):
            await operator.write("content", "blocked.conf")

    async def test_overwrite_existing_file(self, file_operator):
        await file_operator.write("old content", "test.conf")
        await file_operator.write("new content", "test.conf")
        content = await file_operator.read("test.conf")
        assert content == "new content"
