from __future__ import annotations

import shutil
from pathlib import Path


class FileSystemHelper:
    """Encapsulates all file-system operations used across BDD steps."""

    @staticmethod
    def write_text(path: Path, content: str) -> None:
        path.write_text(content)

    @staticmethod
    def append_text(path: Path, content: str) -> None:
        with open(path, "a") as f:
            f.write(content)

    @staticmethod
    def copy_directory(src: Path, dst: Path, exist_ok: bool = True) -> Path:
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=exist_ok)
        return dst

    @staticmethod
    def delete_directory(path: Path, ignore_errors: bool = True) -> None:
        shutil.rmtree(path, ignore_errors=ignore_errors)

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def touch(path: Path) -> None:
        path.touch()

    @staticmethod
    def exists(path: Path) -> bool:
        return path.exists()
