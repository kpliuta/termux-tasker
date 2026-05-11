from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def tmp_dir() -> Iterator[Path]:
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path, ignore_errors=True)


def create_metadata_toml(dir_path: Path, content: str) -> Path:
    path = dir_path / "metadata.toml"
    path.write_text(content)
    return path


def create_settings_toml(dir_path: Path, content: str) -> Path:
    path = dir_path / "settings.toml"
    path.write_text(content)
    return path


def create_bundled_toml(dir_path: Path, content: str) -> Path:
    path = dir_path / "bundled.toml"
    path.write_text(content)
    return path
