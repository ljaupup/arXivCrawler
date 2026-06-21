"""数据库模块 — SQLAlchemy ORM 模型 + 引擎管理。

支持 PostgreSQL，后续可扩展 MySQL（只需修改连接字符串）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import (
    Insert,
    TSVECTOR,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# ──────────────────────────────────────────────
# 连接配置
# ──────────────────────────────────────────────

# 默认连接字符串（匹配 docker-compose.yml 的配置）
DEFAULT_DATABASE_URL = "postgresql://crawler:crawler_pass@localhost:5432/arxiv_crawler"


# ──────────────────────────────────────────────
# ORM 基类
# ──────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────
# 表模型
# ──────────────────────────────────────────────


class PaperModel(Base):
    """论文表 — 对应 models.Paper 数据模型。"""

    __tablename__ = "papers"

    entry_id: Mapped[str] = mapped_column(String, primary_key=True, comment="arXiv 唯一 URL")
    title: Mapped[str] = mapped_column(Text, nullable=False, comment="论文标题")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", comment="摘要")
    published: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="发布日期")
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="更新日期")
    authors: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list, comment="作者列表")
    primary_category: Mapped[str] = mapped_column(String, nullable=False, default="", comment="主分类")
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list, comment="全部分类")
    pdf_url: Mapped[str] = mapped_column(String, nullable=False, default="", comment="PDF 链接")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="作者备注")
    journal_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True, comment="期刊引用")
    doi: Mapped[Optional[str]] = mapped_column(String, nullable=True, comment="DOI")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="记录创建时间"
    )

    def __repr__(self) -> str:
        return f"<PaperModel(entry_id={self.entry_id!r}, title={self.title!r})>"


class SearchLogModel(Base):
    """搜索日志表 — 记录每次搜索操作及命中的论文。"""

    __tablename__ = "search_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String, nullable=False, comment="搜索关键词")
    size: Mapped[int] = mapped_column(Integer, nullable=False, comment="请求数量")
    crawl_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="爬取时间"
    )
    paper_entry_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list, comment="本次搜索命中的论文 ID 列表"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="记录创建时间"
    )

    def __repr__(self) -> str:
        return f"<SearchLogModel(id={self.id}, keyword={self.keyword!r})>"


# ──────────────────────────────────────────────
# 引擎与会话工厂
# ──────────────────────────────────────────────


def create_db_engine(database_url: str = DEFAULT_DATABASE_URL):
    """创建 SQLAlchemy 引擎。"""
    return create_engine(database_url, pool_pre_ping=True)


def init_db(database_url: str = DEFAULT_DATABASE_URL, engine=None):
    """初始化数据库：创建所有表（幂等，已存在则跳过）。

    Parameters
    ----------
    database_url : str
        数据库连接字符串，仅在 engine 为 None 时使用。
    engine : Engine | None
        可传入已有引擎，此时忽略 database_url。
    """
    if engine is None:
        engine = create_db_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


# ──────────────────────────────────────────────
# upsert 工具（INSERT … ON CONFLICT DO UPDATE）
# ──────────────────────────────────────────────


def upsert_paper(session: Session, paper_data: dict) -> None:
    """插入或更新一篇论文。

    Parameters
    ----------
    session : Session
        SQLAlchemy 会话。
    paper_data : dict
        与 PaperModel 列名一致的字段字典。
    """
    stmt = (
        Insert(PaperModel)
        .values(**paper_data)
        .on_conflict_do_update(
            index_elements=[PaperModel.entry_id],
            set_={
                k: v
                for k, v in paper_data.items()
                if k != "entry_id"
            },
        )
    )
    session.execute(stmt)
