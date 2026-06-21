# Repository Guidelines

## 项目结构与模块组织

本仓库是一个用于搜索 arXiv 并保存论文结构化信息的 Python CLI 工具。根目录 `main.py` 是命令行入口。核心代码位于 `src/`：`crawler.py` 封装 arXiv API 调用，`parser.py` 将 API 结果转换为本地模型，`models.py` 定义 `Paper` 和 `SearchResult`，`storage.py` 负责 JSON 与 PostgreSQL 存储，`database.py` 定义 SQLAlchemy 模型与数据库辅助函数。生成的 JSON 数据应写入 `data/extracted/`，该目录已被 Git 忽略。补充文档位于 `docs/`。

## 构建、测试与开发命令

- `uv sync`：根据 `pyproject.toml` 和 `uv.lock` 创建或更新本地环境。
- `python main.py --help`：查看 CLI 参数。
- `python main.py -k "transformer" -s 25`：运行爬取任务，并将结果保存为 JSON。
- `docker compose up -d postgres`：启动本地 PostgreSQL 服务。
- `python main.py -k "nlp" -s 30 --db`：使用 `docker-compose.yml` 中的默认连接写入 PostgreSQL。

## 编码风格与命名约定

使用 Python 3.10+ 语法。模块应保持单一职责，新增功能优先放入已有职责对应的文件。遵循 PEP 8：4 空格缩进，函数和变量使用 snake_case，类名使用 PascalCase，常量使用 UPPER_CASE。公共函数、存储层和数据库边界应尽量保留类型标注。CLI 输出保持简洁，现有状态前缀包括 `[SEARCH]`、`[SAVE]` 和 `[DONE]`。

## 测试指南

当前仓库尚未提交测试目录。修改解析、模型、存储或数据库逻辑时，应在 `tests/` 下添加测试。建议使用 `pytest` 约定：测试文件命名为 `test_*.py`，测试函数命名为 `test_*`。优先编写不依赖真实 arXiv 网络请求的单元测试；使用模拟 API 数据，并用临时目录测试文件存储。只有在修改表结构或 upsert 行为时，才添加 PostgreSQL 集成测试。

## 提交与 Pull Request 规范

现有 Git 历史使用 Conventional Commit 风格前缀，例如 `feat:` 和 `refactor:`。继续沿用该模式，例如 `feat: add postgres search log loader` 或 `fix: handle missing pdf urls`。Pull Request 应说明行为变更、列出已运行的命令或测试、标明数据库 schema 或输出格式变化，并关联相关 issue。修改爬取或存储行为时，附上示例 CLI 输出或 JSON 片段。

## 安全与配置建议

不要提交生成的爬取结果、虚拟环境、数据库卷或真实凭据。默认 PostgreSQL URL 仅用于本地 Docker 开发。自定义数据库凭据应通过 `--db` 参数或环境专用配置传入，不要硬编码到源码中。
