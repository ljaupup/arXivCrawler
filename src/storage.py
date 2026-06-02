"""存储模块 — 支持文件系统与未来数据库接入。

当前实现：
  - FileStorage：将提取结果保存为 JSON 文件。

预留接口：
  - BaseStorage（抽象基类），后续可继承实现 MySQLStorage / PostgreSQLStorage。
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from src.models import SearchResult

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXTRACTED_DIR = _DEFAULT_ROOT / "data" / "extracted"


# ──────────────────────────────────────────────
# 抽象基类 — 后续数据库实现可继承
# ──────────────────────────────────────────────


class BaseStorage(ABC):
    """存储抽象基类。"""

    @abstractmethod
    def save(self, result: SearchResult, name: str | None = None) -> str:
        """保存搜索结果，返回保存后的标识符（路径 / 表名 等）。"""
        ...

    @abstractmethod
    def load(self, identifier: str) -> SearchResult | None:
        """按标识符加载搜索结果。"""
        ...


# ──────────────────────────────────────────────
# 文件系统存储
# ──────────────────────────────────────────────


class FileStorage(BaseStorage):
    """将提取结果保存为 JSON 文件到 data/extracted/ 目录。"""

    def __init__(self, directory: str | os.PathLike = DEFAULT_EXTRACTED_DIR):
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    @property
    def directory(self) -> Path:
        return self._directory

    def save(self, result: SearchResult, name: str | None = None) -> str:
        """保存到 JSON 文件。

        Parameters
        ----------
        result : SearchResult
            要保存的搜索结果。
        name : str | None
            文件名（不含路径），默认 arxiv_papers_YYYYMMDD.json。

        Returns
        -------
        str
            保存的完整文件路径。
        """
        if name is None:
            name = f"arxiv_papers_{datetime.now().strftime('%Y%m%d')}.json"

        path = self._directory / name
        path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"[SAVE] 提取数据已保存: {path}")
        return str(path)

    def load(self, identifier: str) -> SearchResult | None:
        """从 JSON 文件加载。

        Parameters
        ----------
        identifier : str
            完整文件路径或相对于 extracted 目录的文件名。

        Returns
        -------
        SearchResult | None
        """
        path = Path(identifier)
        if not path.is_absolute():
            path = self._directory / path

        if not path.exists():
            return None

        data = json.loads(path.read_text(encoding="utf-8"))
        return SearchResult.from_dict(data)


# 单例快捷入口
_default_storage = FileStorage()

save = _default_storage.save
load = _default_storage.load
