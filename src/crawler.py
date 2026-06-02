"""爬取模块 — 从 arXiv 获取搜索结果的原始 HTML。"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import requests

ARXIV_SEARCH_URL = "https://arxiv.org/search/"

# 默认数据目录（项目根目录下的 data/）
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = _DEFAULT_ROOT / "data" / "raw"


def fetch_search_page(
    query: str,
    *,
    size: int = 25,
    searchtype: str = "all",
    order: str = "-announced_date_first",
    raw_dir: str | os.PathLike | None = None,
    use_cache: bool = True,
) -> str:
    """获取 arXiv 搜索结果页面的 HTML。

    返回 HTML 字符串。当 use_cache=True 且当日已有缓存文件时，
    直接读取本地文件，避免重复请求。

    Parameters
    ----------
    query : str
        搜索关键词。
    size : int
        搜索结果数量，默认 25。
    searchtype : str
        搜索类型，默认 "all"。
    order : str
        排序方式，默认 "-announced_date_first"。
    raw_dir : str | os.PathLike
        原始 HTML 文件的存储目录。
    use_cache : bool
        是否使用本地缓存，默认 True。

    Returns
    -------
    str
        HTML 内容。
    """
    if raw_dir is None:
        raw_dir = DEFAULT_RAW_DIR
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    html_path = raw_dir / f"arXiv_{today}.html"

    # 优先使用当日本地缓存
    if use_cache and html_path.exists():
        print(f"[CACHE] 使用当日本地缓存: {html_path}")
        return html_path.read_text(encoding="utf-8")

    # 从网络获取
    params = {
        "searchtype": searchtype,
        "query": query,
        "abstracts": "show",
        "size": size,
        "order": order,
    }

    print(f"[FETCH] 从 arXiv 获取数据 (keyword={query!r}, size={size}) ...")
    try:
        resp = requests.get(ARXIV_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        html_content = resp.text
    except requests.RequestException as e:
        raise RuntimeError(f"网络请求失败: {e}") from e

    # 保存到本地
    html_path.write_text(html_content, encoding="utf-8")
    print(f"[SAVE] 原始 HTML 已保存: {html_path}")

    return html_content
