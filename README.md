# arXivKeyWordCrawler

arXiv 论文搜索与信息提取工具。基于 [arxiv.py](https://github.com/lukasschwab/arxiv.py) 官方 API 封装，自动提取标题、摘要、作者、分类、PDF 链接等结构化信息，保存为 JSON。

## 功能特点

- 基于 arXiv API，数据规范稳定，无需解析 HTML
- 自动提取：**标题 / 摘要 / 发布日期 / 更新日期 / 作者列表 / 主分类 + 全部分类 / PDF 直链 / DOI**
- 模块化架构：爬取、转换、存储职责分离
- CLI 命令行入口，支持参数定制
- 内置 API 请求退避与重试，遵守 arXiv 使用政策
- 存储层抽象 — 当前支持 JSON 文件输出，预留 `BaseStorage` 接口便于后续接入 MySQL / PostgreSQL

## 环境要求

- Python >= 3.10
- 依赖：`arxiv>=4.0.0`

## 项目结构

```
arXivCrawler/
├── main.py                  # CLI 入口
├── src/
│   ├── models.py            # 数据模型（Paper, SearchResult）
│   ├── crawler.py           # arxiv API 客户端封装
│   ├── parser.py            # arxiv.Result → Paper 模型转换
│   └── storage.py           # 存储层（FileStorage + BaseStorage 抽象基类）
├── data/
│   └── extracted/           # 提取的结构化 JSON 数据
├── pyproject.toml
└── README.md
```

## 快速开始

### 1. 安装依赖

推荐使用 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync
```

或使用 pip：

```bash
pip install -e .
```

### 2. 运行

```bash
# 搜索关键词 "transformer"，获取 25 条结果（默认）
python main.py -k "transformer"

# 搜索 50 条
python main.py -k "machine learning" -s 50

# 查看所有参数
python main.py --help
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-k`, `--keyword` | `fake` | 搜索关键词 |
| `-s`, `--size` | `25` | 搜索结果数量 |
| `--output-dir` | `data/extracted/` | 提取结果输出目录 |

## JSON 输出结构示例

```json
{
  "crawl_time": "2026-06-02T16:24:04.050442",
  "search_params": { "keyword": "fake", "size": 5 },
  "papers": [
    {
      "entry_id": "http://arxiv.org/abs/2606.01843v1",
      "title": "Suppressing Forgery-Specific Shortcuts ...",
      "summary": "Abstract: Deepfake detection suffers from ...",
      "published": "2026-06-01T07:54:58+00:00",
      "updated": "2026-06-01T07:54:58+00:00",
      "authors": ["Yihui Wang", "Yonghui Yang", "Jilong Liu"],
      "primary_category": "cs.CV",
      "categories": ["cs.CV"],
      "pdf_url": "https://arxiv.org/pdf/2606.01843v1",
      "comment": null,
      "journal_ref": null,
      "doi": null
    }
  ]
}
```

## 数据存储

### 文件系统（当前）

运行后自动生成：

```
data/extracted/arxiv_papers_YYYYMMDD.json
```

### 数据库（预留）

`storage.py` 定义了 `BaseStorage` 抽象基类，后续接入数据库只需继承实现：

```python
from src.storage import BaseStorage
from src.models import SearchResult

class PostgreSQLStorage(BaseStorage):
    def save(self, result: SearchResult, name: str | None = None) -> str:
        # INSERT INTO papers (...) VALUES (...)
        ...

    def load(self, identifier: str) -> SearchResult | None:
        # SELECT * FROM papers WHERE ...
        ...
```

## 注意事项

- arxiv.py 内置请求延迟和重试机制，自动遵守 [arXiv API 使用政策](https://info.arxiv.org/help/api/tou.html)
- 如需高级查询语法，直接传入 arXiv 查询字符串即可，例如 `au:del_maestro AND ti:checkerboard`