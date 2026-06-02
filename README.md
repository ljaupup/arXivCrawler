# arXivKeyWordCrawler

arXiv 论文搜索与信息提取工具。根据关键词搜索 arXiv 论文，自动提取标题、摘要、日期、链接等信息，保存为结构化 JSON。

## 功能特点

- 支持关键词搜索 arXiv 论文
- 自动提取论文标题、摘要、发布日期和链接
- 搜索结果缓存（原始 HTML 本地化，避免重复请求）
- 模块化架构：爬取、解析、存储职责分离
- CLI 命令行入口，支持参数定制
- 存储层抽象 — 当前支持 JSON 文件输出，预留 `BaseStorage` 接口便于后续接入 MySQL / PostgreSQL

## 环境要求

- Python >= 3.14
- 依赖：`requests`, `lxml`

## 项目结构

```
arXivCrawler/
├── main.py                  # CLI 入口
├── src/
│   ├── models.py            # 数据模型（Paper, SearchResult）
│   ├── crawler.py           # arXiv HTML 爬取 + 本地缓存管理
│   ├── parser.py            # HTML 解析 → 结构化论文信息
│   └── storage.py           # 存储层（FileStorage + BaseStorage 抽象基类）
├── data/
│   ├── raw/                 # 爬取的原始 HTML（按日缓存）
│   └── extracted/           # 提取的结构化 JSON 数据
├── base.py                  # （旧版单文件脚本，保留参考）
├── pyproject.toml
└── README.md
```

## 快速开始

### 1. 安装依赖

项目使用 `pyproject.toml` 管理依赖，推荐使用 [uv](https://docs.astral.sh/uv/)：

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

# 搜索 50 条，忽略本地缓存强制从网络获取
python main.py -k "machine learning" -s 50 --no-cache

# 查看所有参数
python main.py --help
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-k`, `--keyword` | `fake` | 搜索关键词 |
| `-s`, `--size` | `25` | 搜索结果数量 |
| `--searchtype` | `all` | 搜索类型 (`all`, `title`, `abstract`, `author`) |
| `--no-cache` | — | 忽略当日缓存，强制从 arXiv 重新获取 |
| `--raw-dir` | `data/raw/` | 原始 HTML 存储目录 |
| `--output-dir` | `data/extracted/` | 提取结果输出目录 |

## 数据存储

### 文件系统（当前）

运行后自动生成以下文件：

```
data/raw/arXiv_20260602.html                # 原始 HTML 缓存
data/extracted/arxiv_papers_20260602.json   # 提取的结构化数据
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

- 同一天内重复运行会优先使用 `data/raw/` 中的本地缓存 HTML 文件，避免重复请求
- 使用 `--no-cache` 参数可强制重新从 arXiv 获取
- 请遵守 [arXiv 的使用政策](https://info.arxiv.org/help/api/tou.html)，避免频繁请求