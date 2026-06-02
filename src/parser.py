"""解析模块 — 从 arXiv HTML 中提取论文信息。"""

from __future__ import annotations

from lxml import html as lxml_html

from src.models import Paper


def parse_search_results(html_content: str, expected_count: int = 25) -> list[Paper]:
    """解析 arXiv 搜索结果 HTML，提取论文列表。

    Parameters
    ----------
    html_content : str
        arXiv 搜索结果页面的 HTML。
    expected_count : int
        期望的论文数量（用于 XPath 索引上限）。

    Returns
    -------
    list[Paper]
        提取到的论文列表。
    """
    tree = lxml_html.fromstring(html_content)

    # ---- 1. 提取标题 ----
    titles: list[dict] = []
    title_nodes = tree.xpath('//*[@id="main-container"]/div[2]/ol/li/p[1]')
    for node in title_nodes:
        idx = title_nodes.index(node) + 1
        text = ""
        if hasattr(node, "text") and node.text:
            text = node.text.strip()
        elif isinstance(node, str):
            text = node.strip()
        titles.append({"index": idx, "title": text})

    # ---- 2. 提取摘要 ----
    abstracts: list[dict] = []
    for i in range(1, expected_count + 1):
        xpath = f'//*[@id="main-container"]/div[2]/ol/li[{i}]/p[3]'
        nodes = tree.xpath(xpath)
        abstract_text: str | None = None
        for node in nodes:
            if hasattr(node, "text_content"):
                raw = node.text_content().strip()
            elif hasattr(node, "text"):
                raw = (node.text or "").strip()
            else:
                raw = str(node).strip()

            clean = " ".join(raw.split())
            if len(clean) > 50:  # 过滤短文本/非摘要
                abstract_text = clean
                break
        abstracts.append({"index": i, "abstract": abstract_text})

    # ---- 3. 提取日期 ----
    dates: list[dict] = []
    for i in range(1, expected_count + 1):
        xpath = f'//*[@id="main-container"]/div[2]/ol/li[{i}]/p[4]/text()[1]'
        nodes = tree.xpath(xpath)
        date_text = nodes[0].strip().rstrip(";") if nodes else None
        dates.append({"index": i, "date": date_text})

    # ---- 4. 提取链接 ----
    link_nodes = tree.xpath('//p[@class="list-title is-inline-block"]/a/@href')
    links: list[dict] = []
    for i, href in enumerate(link_nodes, 1):
        full_url = f"https://arxiv.org{href}" if href.startswith("/") else href
        links.append({"index": i, "link": full_url})

    # ---- 5. 合并 ----
    papers: list[Paper] = []
    for i in range(1, expected_count + 1):
        paper = Paper(index=i)

        t = _find_by_index(titles, i)
        if t:
            paper.title = t["title"]

        a = _find_by_index(abstracts, i)
        if a:
            paper.abstract = a["abstract"]

        d = _find_by_index(dates, i)
        if d:
            paper.date = d["date"]

        l = _find_by_index(links, i)
        if l:
            paper.link = l["link"]

        papers.append(paper)

    return papers


def _find_by_index(lst: list[dict], index: int) -> dict | None:
    """在列表中按 index 字段查找。"""
    return next((item for item in lst if item.get("index") == index), None)
