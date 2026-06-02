import requests
from lxml import html
import json
import os
from datetime import datetime

url = "https://arxiv.org/search/"

params = {
    "searchtype": "all",
    "query": "fake",
    "abstracts": "show",
    "size": 25,
    "order": "-announced_date_first"
}

# 检查本地文件是否存在，优先使用当日数据
today_date = datetime.now().strftime("%Y%m%d")
html_file = f"arXiv_{today_date}.html"

if os.path.exists(html_file):
    print(f"使用当日本地文件: {html_file}")
    with open(html_file, "r", encoding="utf8") as f:
        html_content = f.read()
else:
    print(f"当日文件不存在，从网络获取数据并保存为: {html_file}")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        with open(html_file, "w", encoding="utf8") as f:
            f.write(response.text)
        html_content = response.text
        print("成功从网络获取数据并保存到本地")
    except Exception as e:
        print(f"网络请求失败: {e}")
        exit(1)

# 解析HTML
tree = html.fromstring(html_content)

# 初始化结果数据结构
result_data = {
    "crawl_time": datetime.now().isoformat(),
    "search_params": params,
    "papers": []
}

# 1. 提取title
# print("正在提取论文标题...")
# titles_data = []
# for i in range(1, params["size"] + 1):
#     xpath_expr = f'//*[@id="main-container"]/div[2]/ol/li[{i}]/p[1]'
#     titles = tree.xpath(xpath_expr)
#     if titles:
#         for title in titles:
#             if hasattr(title, 'text') and title.text:
#                 title_text = title.text.strip()
#                 titles_data.append({"index": i, "title": title_text})
#                 # print(f"{i}. {title_text}")
#             elif isinstance(title, str):
#                 title_text = title.strip()
#                 titles_data.append({"index": i, "title": title_text})
#                 # print(f"{i}. {title_text}")
#     else:
#         titles_data.append({"index": i, "title": None})
#         print(f"{i}. Not found")
titles_data = []
xpath_expr = f'//*[@id="main-container"]/div[2]/ol/li/p[1]'
titles = tree.xpath(xpath_expr)
for title in titles:
    i = titles.index(title) + 1
    if hasattr(title, 'text') and title.text:
        title_text = title.text.strip()
        titles_data.append({"index": i, "title": title_text})
        # print(f"{i}. {title_text}")
    elif isinstance(title, str):
        title_text = title.strip()
        titles_data.append({"index": i, "title": title_text})
        # print(f"{i}. {title_text}")

# 2. 提取abstract-full
print("\n正在提取论文摘要...")
abstracts_data = []
for i in range(1, params["size"] + 1):
    xpath_expr = f'//*[@id="main-container"]/div[2]/ol/li[{i}]/p[3]'
    abstracts = tree.xpath(xpath_expr)
    if abstracts:
        for abstract in abstracts:
            if hasattr(abstract, 'text_content'):
                clean_abstract = ' '.join(abstract.text_content().strip().split())
            elif hasattr(abstract, 'text'):
                clean_abstract = ' '.join(abstract.text.strip().split())
            else:
                clean_abstract = ' '.join(str(abstract).strip().split())
            
            if clean_abstract and len(clean_abstract) > 50:  # 过滤掉短文本
                abstracts_data.append({"index": i, "abstract": clean_abstract})
                # print(f"{i}. {clean_abstract[:200]}...")
                break  # 每个li只取第一个摘要
    else:
        abstracts_data.append({"index": i, "abstract": None})
        # print(f"{i}. Abstract not found")

# 3. 提取XPath为"//*[@id=\"main-container\"]/div[2]/ol/li[?]/p[4]/text()[1]"的元素
print("\n正在提取日期信息...")
date_elements = []
for i in range(1, params["size"] + 1):
    xpath_expr = f'//*[@id="main-container"]/div[2]/ol/li[{i}]/p[4]/text()[1]'
    elements = tree.xpath(xpath_expr)
    if elements:
        date_text = elements[0].strip().rstrip(";")
        date_elements.append({"index": i, "date": date_text})
        # print(f"Li[{i}]: {date_text}")
    else:
        date_elements.append({"index": i, "date": None})
        # print(f"Li[{i}]: Not found")

# 4. 获取class为"list-title"下a标签的链接
print("\n正在提取论文链接...")
links = tree.xpath('//p[@class="list-title is-inline-block"]/a/@href')
links_data = []
for i, link in enumerate(links, 1):
    full_link = f"https://arxiv.org{link}" if link.startswith('/') else link
    links_data.append({"index": i, "link": full_link})
    # print(f"{i}. {full_link}")

# 整合数据
print("\n正在整合数据...")
for i in range(1, params["size"] + 1):
    paper_data = {"index": i}
    
    # 查找对应的标题
    title_item = next((item for item in titles_data if item["index"] == i), None)
    paper_data["title"] = title_item["title"] if title_item else None
    
    # 查找对应的摘要
    abstract_item = next((item for item in abstracts_data if item["index"] == i), None)
    paper_data["abstract"] = abstract_item["abstract"] if abstract_item else None
    
    # 查找对应的日期
    date_item = next((item for item in date_elements if item["index"] == i), None)
    paper_data["date"] = date_item["date"] if date_item else None
    
    # 查找对应的链接
    link_item = next((item for item in links_data if item["index"] == i), None)
    paper_data["link"] = link_item["link"] if link_item else None
    
    result_data["papers"].append(paper_data)

# 保存为JSON文件
json_filename = f"arxiv_papers_{datetime.now().strftime('%Y%m%d')}.json"
with open(json_filename, "w", encoding="utf8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print(f"\n数据已保存到 {json_filename}")
print(f"总共提取了 {len(result_data['papers'])} 篇论文的信息")
print(f"其中有标题的论文: {len([p for p in result_data['papers'] if p['title']])} 篇")
print(f"其中有摘要的论文: {len([p for p in result_data['papers'] if p['abstract']])} 篇")
print(f"有链接的论文: {len([p for p in result_data['papers'] if p['link']])} 篇")
