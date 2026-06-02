"""爬取模块 — 通过 arxiv API 获取论文数据。"""

from __future__ import annotations

from typing import Iterator

import arxiv

from src.models import Paper
from src.parser import arxiv_result_to_paper


# 默认客户端（连接池复用 + 内置退避重试）
_DEFAULT_CLIENT: arxiv.Client | None = None


def _get_client() -> arxiv.Client:
    """获取全局共享的 API 客户端。"""
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3,
        )
    return _DEFAULT_CLIENT


def search(
    query: str,
    *,
    max_results: int = 25,
    sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
    client: arxiv.Client | None = None,
) -> list[Paper]:
    """按关键词搜索 arXiv，返回论文列表。

    Parameters
    ----------
    query : str
        搜索关键词。支持 arXiv 高级查询语法。
    max_results : int
        最大返回数量，默认 25。
    sort_by : arxiv.SortCriterion
        排序方式，默认按提交日期降序。
    client : arxiv.Client | None
        自定义 API 客户端；为 None 时使用全局默认客户端。

    Returns
    -------
    list[Paper]
        论文列表（按排序顺序）。
    """
    _client = client or _get_client()

    search_obj = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=arxiv.SortOrder.Descending,
    )

    results: list[Paper] = []
    for r in _client.results(search_obj):
        results.append(arxiv_result_to_paper(r))

    return results


def search_by_ids(id_list: list[str], *, client: arxiv.Client | None = None) -> dict[str, Paper]:
    """按 arXiv ID 列表批量查询论文。

    Parameters
    ----------
    id_list : list[str]
        arXiv 论文 ID 列表 (eg. ``["2606.01843v1", "2606.01050"]``)。
    client : arxiv.Client | None
        自定义 API 客户端。

    Returns
    -------
    dict[str, Paper]
        ID → Paper 的映射。
    """
    _client = client or _get_client()

    search_obj = arxiv.Search(id_list=id_list)
    result_map: dict[str, Paper] = {}
    for r in _client.results(search_obj):
        paper = arxiv_result_to_paper(r)
        result_map[r.get_short_id()] = paper

    return result_map


def iter_results(
    query: str,
    *,
    max_results: int = 25,
    client: arxiv.Client | None = None,
) -> Iterator[Paper]:
    """惰性迭代搜索结果（节省内存）。"""
    _client = client or _get_client()
    search_obj = arxiv.Search(query=query, max_results=max_results)

    for r in _client.results(search_obj):
        yield arxiv_result_to_paper(r)
