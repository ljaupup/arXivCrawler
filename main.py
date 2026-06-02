#!/usr/bin/env python3
"""arXiv Crawler — 主入口。

用法：
    python main.py --keyword "machine learning" --size 50
    python main.py -k "transformer" -s 100 --no-cache
"""

from __future__ import annotations

import argparse
import sys

from src.crawler import fetch_search_page
from src.parser import parse_search_results
from src.storage import FileStorage
from src.models import SearchResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="arXiv 论文爬虫 — 搜索并提取论文信息",
    )
    parser.add_argument(
        "-k", "--keyword",
        default="fake",
        help="搜索关键词（默认: fake）",
    )
    parser.add_argument(
        "-s", "--size",
        type=int,
        default=25,
        help="搜索结果数量（默认: 25）",
    )
    parser.add_argument(
        "--searchtype",
        default="all",
        choices=("all", "title", "abstract", "author", "commentary", "journal"),
        help="搜索类型（默认: all）",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="忽略本地缓存，强制从网络获取",
    )
    parser.add_argument(
        "--raw-dir",
        default=None,
        help="原始 HTML 存储目录（默认: data/raw/）",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="提取结果输出目录（默认: data/extracted/）",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 1. 爬取
    html = fetch_search_page(
        query=args.keyword,
        size=args.size,
        searchtype=args.searchtype,
        raw_dir=args.raw_dir,
        use_cache=not args.no_cache,
    )

    # 2. 解析
    papers = parse_search_results(html, expected_count=args.size)
    result = SearchResult(
        search_params={
            "keyword": args.keyword,
            "size": args.size,
            "searchtype": args.searchtype,
        },
        papers=papers,
    )

    # 3. 统计 & 保存
    print(f"\n[STATS] 提取结果统计:")
    print(f"   - 论文总数: {len(papers)}")
    print(f"   - 有标题:   {sum(1 for p in papers if p.title)}")
    print(f"   - 有摘要:   {sum(1 for p in papers if p.abstract)}")
    print(f"   - 有链接:   {sum(1 for p in papers if p.link)}")

    storage = FileStorage(args.output_dir) if args.output_dir else FileStorage()
    storage.save(result)

    print("[DONE] 完成。")


if __name__ == "__main__":
    main()
