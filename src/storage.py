"""存储模块 — 支持文件系统与关系型数据库。

当前实现：
  - FileStorage：将提取结果保存为 JSON 文件。
  - PostgresStorage：将提取结果写入 PostgreSQL。

扩展方式：
  继承 BaseStorage 抽象基类，实现 save() / load() 即可。
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.database import (
    DEFAULT_DATABASE_URL,
    PaperModel,
    SearchLogModel,
    init_db,
    upsert_paper,
)
from src.models import Paper, SearchResult

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXTRACTED_DIR = _DEFAULT_ROOT / "data" / "extracted"


# ──────────────────────────────────────────────
# 抽象基类
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
        if name is None:
            name = f"arxiv_papers_{datetime.now().strftime('%Y%m%d')}.json"

        path = self._directory / name
        path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"[SAVE] JSON: {path}")
        return str(path)

    def load(self, identifier: str) -> SearchResult | None:
        path = Path(identifier)
        if not path.is_absolute():
            path = self._directory / path
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return SearchResult.from_dict(data)


# ──────────────────────────────────────────────
# PostgreSQL 存储
# ──────────────────────────────────────────────


class PostgresStorage(BaseStorage):
    """将提取结果写入 PostgreSQL。"""

    def __init__(self, database_url: str = DEFAULT_DATABASE_URL):
        self._engine = init_db(database_url)
        self._database_url = database_url

    def save(self, result: SearchResult, name: str | None = None) -> str:
        """写入数据库。

        - 论文数据 upsert 到 ``papers`` 表
        - 搜索记录写入 ``search_log`` 表

        Returns
        -------
        str
            搜索日志记录的 ID（字符串形式）。
        """
        with Session(self._engine) as session:
            # 1) 逐条 upsert 论文
            for paper in result.papers:
                upsert_paper(session, _paper_to_dict(paper))

            # 2) 记录搜索日志
            log = SearchLogModel(
                keyword=result.search_params.get("keyword", ""),
                size=result.search_params.get("size", 0),
                crawl_time=datetime.fromisoformat(result.crawl_time),
                paper_entry_ids=[p.entry_id for p in result.papers],
            )
            session.add(log)
            session.commit()

            log_id = str(log.id)

        print(f"[SAVE] PostgreSQL: 写入 {len(result.papers)} 篇论文 (搜索日志 id={log_id})")
        return log_id

    def load(self, identifier: str) -> SearchResult | None:
        """按搜索日志 ID 加载。

        Parameters
        ----------
        identifier : str
            搜索日志的数字 ID。

        Returns
        -------
        SearchResult | None
        """
        with Session(self._engine) as session:
            log = session.get(SearchLogModel, int(identifier))
            if log is None:
                return None

            papers_db = (
                session.query(PaperModel)
                .filter(PaperModel.entry_id.in_(log.paper_entry_ids))
                .all()
            )
            # 按 IDs 原始顺序排序
            id_order = {pid: i for i, pid in enumerate(log.paper_entry_ids)}
            papers_db.sort(key=lambda p: id_order.get(p.entry_id, 999))

            papers = [_paper_from_orm(p) for p in papers_db]

            return SearchResult(
                crawl_time=log.crawl_time.isoformat(),
                search_params={"keyword": log.keyword, "size": log.size},
                papers=papers,
            )


# ──────────────────────────────────────────────
# 内部辅助
# ──────────────────────────────────────────────


def _paper_to_dict(paper: Paper) -> dict:
    """Paper → dict（与 PaperModel 列名对齐）。"""
    return {
        "entry_id": paper.entry_id,
        "title": paper.title,
        "summary": paper.summary,
        "published": paper.published,
        "updated": paper.updated,
        "authors": paper.authors,
        "primary_category": paper.primary_category,
        "categories": paper.categories,
        "pdf_url": paper.pdf_url,
        "comment": paper.comment,
        "journal_ref": paper.journal_ref,
        "doi": paper.doi,
    }


def _paper_from_orm(row: PaperModel) -> Paper:
    """ORM 行 → Paper dataclass。"""
    return Paper(
        entry_id=row.entry_id,
        title=row.title,
        summary=row.summary,
        published=row.published,
        updated=row.updated,
        authors=list(row.authors) if row.authors else [],
        primary_category=row.primary_category,
        categories=list(row.categories) if row.categories else [],
        pdf_url=row.pdf_url,
        comment=row.comment,
        journal_ref=row.journal_ref,
        doi=row.doi,
    )


# 单例快捷入口
_default_file_storage = FileStorage()
_default_pg_storage: PostgresStorage | None = None

save = _default_file_storage.save
load = _default_file_storage.load


def use_postgres(database_url: str = DEFAULT_DATABASE_URL) -> PostgresStorage:
    """获取全局 PostgreSQL 存储实例。"""
    global _default_pg_storage
    if _default_pg_storage is None or _default_pg_storage._database_url != database_url:
        _default_pg_storage = PostgresStorage(database_url)
    return _default_pg_storage

