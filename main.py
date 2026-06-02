#!/usr/bin/env python3
"""arXiv Crawler — 主入口。

用法：
    python main.py -k "machine learning" -s 50
    python main.py -k "transformer" -s 100
"""

from __future__ import annotations

import argparse

from src.crawler import search
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
        "--output-dir",
        default=None,
        help="提取结果输出目录（默认: data/extracted/）",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print(f"[SEARCH] 关键词: {args.keyword!r}, 数量: {args.size}")
    papers = search(query=args.keyword, max_results=args.size)

    result = SearchResult(
        search_params={
            "keyword": args.keyword,
            "size": args.size,
        },
        papers=papers,
    )

    print(f"\n[STATS] 提取结果统计:")
    print(f"   - 论文总数: {len(papers)}")
    if papers:
        print(f"   - 示例标题: {papers[0].title[:60]}...")
        print(f"   - 示例分类: {papers[0].primary_category}")
        print(f"   - 示例作者: {', '.join(papers[0].authors[:3])}...")

    storage = FileStorage(args.output_dir) if args.output_dir else FileStorage()
    storage.save(result)

    print("[DONE] 完成。")


if __name__ == "__main__":
    main()
