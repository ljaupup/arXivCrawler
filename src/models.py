"""数据模型 — 定义论文、搜索结果等核心数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Paper:
    """单篇论文信息。"""

    entry_id: str
    """arXiv 唯一 URL (eg. https://arxiv.org/abs/2606.01843v1)。"""

    title: str
    """论文标题。"""

    summary: str
    """摘要 (abstract)。"""

    published: datetime
    """原始发布日期。"""

    updated: datetime
    """最后更新日期。"""

    authors: list[str]
    """作者姓名列表。"""

    primary_category: str
    """主分类 (eg. cs.CV)。"""

    categories: list[str]
    """全部分类列表。"""

    pdf_url: str
    """PDF 直链。"""

    comment: Optional[str] = None
    """作者备注 (如页码、图表数)。"""

    journal_ref: Optional[str] = None
    """期刊引用。"""

    doi: Optional[str] = None
    """DOI 标识。"""


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
        papers = []
        for p in data.get("papers", []):
            pp = p.copy()
            pp["published"] = datetime.fromisoformat(pp["published"])
            pp["updated"] = datetime.fromisoformat(pp["updated"])
            papers.append(Paper(**pp))
        return cls(
            crawl_time=data.get("crawl_time", ""),
            search_params=data.get("search_params", {}),
            papers=papers,
        )
