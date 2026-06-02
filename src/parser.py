"""解析模块 — 将 arxiv 包原生 Result 转换为内部 Paper 模型。"""

from __future__ import annotations

import arxiv

from src.models import Paper


def arxiv_result_to_paper(r: arxiv.Result) -> Paper:
    """将 ``arxiv.Result`` 转换为项目内部的 ``Paper`` 模型。

    Parameters
    ----------
    r : arxiv.Result
        arxiv 包返回的原始结果对象。

    Returns
    -------
    Paper
    """
    return Paper(
        entry_id=r.entry_id,
        title=r.title.strip() if r.title else "",
        summary=r.summary.strip() if r.summary else "",
        published=r.published,
        updated=r.updated,
        authors=[str(a) for a in r.authors],
        primary_category=r.primary_category,
        categories=r.categories,
        pdf_url=r.pdf_url,
        comment=r.comment,
        journal_ref=r.journal_ref,
        doi=r.doi,
    )
