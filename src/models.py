"""数据模型 — 定义论文、搜索结果等核心数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Paper:
    """单篇论文信息。"""
    index: int
    title: Optional[str] = None
    abstract: Optional[str] = None
    date: Optional[str] = None
    link: Optional[str] = None


@dataclass
class SearchResult:
    """一次搜索的完整结果。"""
    crawl_time: str = field(default_factory=lambda: datetime.now().isoformat())
    search_params: dict = field(default_factory=dict)
    papers: list[Paper] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转为可序列化的字典。"""
        return {
            "crawl_time": self.crawl_time,
            "search_params": self.search_params,
            "papers": [asdict(p) for p in self.papers],
        }

    @classmethod
    def from_dict(cls, data: dict) -> SearchResult:
        """从字典恢复。"""
        papers = [Paper(**p) for p in data.get("papers", [])]
        return cls(
            crawl_time=data.get("crawl_time", ""),
            search_params=data.get("search_params", {}),
            papers=papers,
        )
