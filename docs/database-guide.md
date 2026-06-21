# 数据库接入完全指南

> 覆盖范围：Docker · PostgreSQL · SQLAlchemy ORM · 数据库选型

---

## 目录

1. [关系型数据库基础概念](#一关系型数据库基础概念)
2. [PostgreSQL vs MySQL](#二postgresql-vs-mysql)
3. [Docker 基础与实战](#三docker-基础与实战)
4. [SQLAlchemy ORM](#四sqlalchemy-orm)
5. [项目代码逐层拆解](#五项目代码逐层拆解)
6. [操作流程](#六操作流程)

---

## 一、关系型数据库基础概念

### 数据库是什么

数据库 = 有组织的数据存储仓库。比 JSON 文件强在：

| JSON 文件 | 数据库 |
|---|---|
| 读写整个文件，10 万条数据要全部加载到内存 | 按需查询（SELECT ... WHERE ...），只取需要的几行 |
| 没有结构约束，`title` 可能叫 `Title` 也可能叫 `t` | 表结构固定，列名、类型都定义好 |
| 多人同时写会覆盖 | 事务机制，并发安全 |
| 没法做关联查询 | JOIN 两张表灵活组合 |

### 核心概念

| 概念 | 类比 |
|---|---|
| **表 (Table)** | Excel 的一张 sheet |
| **行 (Row)** | Excel 里的一行数据 |
| **列 (Column)** | Excel 里的一列，有类型约束（文本/数字/时间） |
| **主键 (Primary Key)** | 每行的唯一身份证号，不能重复 |
| **索引 (Index)** | 书的目录，加速查询 |
| **SQL** | 操作数据库的语言 |

### 本项目中的表

```
papers 表（论文数据）
──────────────────────────────────────────────────
entry_id (PK)  │ title  │ summary  │ published  │ ...
──────────────────────────────────────────────────
http://...1    │ xxx    │ xxx      │ 2026-06-01 │ ...
http://...2    │ yyy    │ yyy      │ 2026-05-30 │ ...
http://...3    │ zzz    │ zzz      │ 2026-05-28 │ ...

search_log 表（搜索记录）
──────────────────────────────────
id (PK)  │ keyword  │ size  │ crawl_time  │ ...
──────────────────────────────────
1        │ fake     │ 5     │ 2026-06-02  │ ...
2        │ quantum  │ 10    │ 2026-06-03  │ ...
```

---

## 二、PostgreSQL vs MySQL

### 它们是什么

两者都是主流**关系型数据库**，都支持 SQL，都可以用 SQLAlchemy 连。

### 核心区别

| 维度 | PostgreSQL | MySQL |
|---|---|---|
| **类型系统** | 更丰富：原生支持数组、JSON、JSONB、网络地址、几何类型 | 基础类型够用，数组需要用 JSON 模拟 |
| **数组类型** | ✅ 原生 `TEXT[]`、`INTEGER[]` | ❌ 不支持 |
| **JSON 支持** | JSON + JSONB（二进制，可索引） | JSON（功能少一些） |
| **SQL 标准** | 更严格遵循 SQL 标准 | 有自己的方言，有些不标准 |
| **ACID 事务** | ✅ 从一开始就完整支持 | ✅ InnoDB 引擎支持 |
| **全文搜索** | 内置，支持中文分词扩展 | 内置，但功能弱一些 |
| **并发性能** | 写并发更好（MVCC 实现更成熟） | 读并发好，写并发稍弱 |
| **默认端口** | 5432 | 3306 |
| **流行度** | 技术圈更受推崇 | Web 开发更普遍 |
| **学习曲线** | 稍陡（功能多） | 平缓 |

### 对本项目的影响

```python
# PostgreSQL 连接字符串
postgresql://crawler:crawler_pass@localhost:5432/arxiv_crawler

# MySQL 连接字符串
mysql+pymysql://crawler:crawler_pass@localhost:3306/arxiv_crawler
```

**最大的差异在代码层面**：authors 和 categories 用数组还是用关联表。

```
PostgreSQL（本项目当前方案）:
  authors TEXT[]   → 直接存 ["张三", "李四"]
  categories TEXT[] → 直接存 ["cs.CV", "cs.AI"]

MySQL（如果要换）:
  authors TEXT      → 存 JSON 字符串 '["张三", "李四"]'
  或者单独建 paper_authors 表
```

### 选型建议

| 场景 | 推荐 |
|---|---|
| **个人项目、学习、原型** | **PostgreSQL**（功能丰富，免费，此项目用的就是它） |
| 团队已有 MySQL 基础设施 | MySQL（减少运维成本） |
| 需要地理位置查询 | PostgreSQL（PostGIS 扩展） |
| 需要高性能简单读 | MySQL |

---

## 三、Docker 基础与实战

### Docker 解决什么问题

> "在我电脑上能跑啊" → 环境不一致导致的经典问题。

没有 Docker 时装 PostgreSQL：

```
1. 打开浏览器 → 搜索 "PostgreSQL Windows 下载"
2. 下载 200MB 的安装包
3. 运行安装程序 → 一路 Next → 设置密码
4. 安装程序注册系统服务，开机自启
5. 打开命令行试 psql → 报错 "不是内部命令"
6. 加环境变量 → 重启电脑
7. 想换个版本 → 先卸载，再重新下载安装
8. 想换 MySQL → 一样再来一遍
```

有 Docker 时：

```
1. 写 docker-compose.yml（20 行 YAML）
2. docker compose up -d
3. 搞定
4. 想换版本 → 改一行 image 版本号 → 重新 up
5. 想换 MySQL → 改 image 为 mysql:8 → 改端口 → 重新 up
6. 想清空数据 → docker compose down -v → 重新 up
```

### 三个核心概念（再回顾一次）

```
┌────────────────────────────────────────────────────────┐
│                    Docker                              │
│                                                        │
│  镜像 (Image)        容器 (Container)    数据卷 (Volume) │
│  ┌─────────┐        ┌───────────┐        ┌──────────┐  │
│  │ postgres│  run   │ 运行中的    │  持久化 │  外接硬盘 │  │
│  │  :16    │ ─────→ │ PostgreSQL│ ←───── │  pgdata  │  │
│  │  安装包  │        │  进程      │        │  数据不丢 │  │
│  └─────────┘        └───────────┘        └──────────┘  │
│                                                        │
│    类比：              类比：                 类比：      │
│    类/安装程序         类的实例/进程           外接移动硬盘  │
└────────────────────────────────────────────────────────┘
```

### docker-compose.yml 详解

```yaml
# docker-compose.yml 是 Docker 容器的"配置文件"
# 声明你要跑什么服务、用什么镜像、暴露什么端口

services:                    # 定义一组服务
  postgres:                  # 服务名称（随便起）
    image: postgres:16       # 镜像名:标签（16 代表大版本）
    container_name: arxivcrawler-postgres  # 容器名字（方便 docker ps 辨认）
    environment:             # 传给容器的环境变量
      POSTGRES_DB: arxiv_crawler    # 自动创建这个库
      POSTGRES_USER: crawler         # 自动创建这个用户
      POSTGRES_PASSWORD: crawler_pass # 用户密码
    ports:
      - "5432:5432"          # 宿主机端口:容器端口
    volumes:
      - pgdata:/var/lib/postgresql/data  # 命名卷:容器内数据路径
    restart: unless-stopped  # 重启策略

volumes:
  pgdata:                    # 声明命名卷
```

**ports 的机制：**

```
你电脑的 5432 端口 ──→ Docker 转发 ──→ 容器的 5432 端口
（Python 连这个）       （透明）       （PostgreSQL 在听这个）
```

所以你的代码连 `localhost:5432`，Docker 把它转给容器里的 PostgreSQL。

**volumes 的机制：**

```
容器删除时：容器本身消失，但 pgdata 卷还在。
下次 docker compose up -d 创建一个新容器，挂载同一个卷 → 数据回来了。

docker compose down -v：停止容器 + 删除卷 → 数据彻底清空。
```

### 常用命令速查

```bash
# 启动（-d = 后台运行，不占终端）
docker compose up -d

# 查看运行状态
docker ps

# 查看日志
docker compose logs -f

# 进入数据库终端
docker compose exec postgres psql -U crawler -d arxiv_crawler

# 停止（保留数据）
docker compose down

# 停止 + 清空数据
docker compose down -v

# 重启
docker compose restart
```

### 为什么项目根目录放 docker-compose.yml 而不是 Dockerfile？

- Dockerfile = 构建你自己的 Python 应用的镜像（后续 PaperMind 会用）
- docker-compose.yml = 编排服务，目前只跑一个 PostgreSQL
- 等你做 PaperMind 第 8 周时，会在 compose 里加 Python API 服务 + ChromaDB 服务

---

## 四、SQLAlchemy ORM

### 什么是 ORM

**ORM = Object Relational Mapping（对象关系映射）**

没有 ORM 时，你要写裸 SQL：

```python
# 裸 SQL 方式
cursor.execute("INSERT INTO papers (entry_id, title) VALUES (%s, %s)", (id, title))
rows = cursor.fetchall()  # 返回元组，用 columns[0] 访问
```

有 ORM 时，你操作 Python 对象：

```python
# ORM 方式
paper = PaperModel(entry_id="...", title="...")
session.add(paper)
session.commit()
```

**ORM 的价值：**
- Python 对象 ↔ 数据库表行 的转换自动完成
- 不用写 SQL 字符串（避免拼写错误和 SQL 注入）
- 切换数据库（PostgreSQL → MySQL）只需改连接字符串，代码几乎不变

### SQLAlchemy 核心组件

```
┌───────────────────────────────────────────────────────────────┐
│  SQLAlchemy 分层架构                                           │
│                                                               │
│  你的代码                                                      │
│    │                                                          │
│    ▼                                                          │
│  ORM 层：操作 Python 对象，不直接写 SQL                           │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Session（会话）→ 增删改查的入口                            │  │
│  │  Model（模型）→ Python 类 ↔ 数据库表                       │  │
│  │  Query（查询）→ 构建查询条件                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│    │                                                          │
│    ▼                                                          │
│  Core 层：执行 SQL，管理连接                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Engine（引擎）→ 连接池，执行 SQL                          │   │
│  │  Connection（连接）→ 实际的数据库连接                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│    │                                                          │
│    ▼                                                          │
│  psycopg2（数据库驱动）→ 和 PostgreSQL 通信                      │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Engine（引擎）

```python
from sqlalchemy import create_engine

# 创建一个引擎（连接池，不立即连数据库）
engine = create_engine("postgresql://crawler:crawler_pass@localhost:5432/arxiv_crawler")

# 引擎是"懒惰"的：第一次执行 SQL 时才真正建立连接
# pool_pre_ping=True 表示每次从连接池拿连接前先 ping 一下，避免拿到断开的连接
```

### Session（会话）

```python
from sqlalchemy.orm import Session

# 方式 1：上下文管理器（推荐）
with Session(engine) as session:
    session.add(some_object)
    session.commit()  # 提交事务

# 方式 2：手动管理
session = Session(engine)
try:
    session.add(some_object)
    session.commit()
except:
    session.rollback()  # 出错时回滚
    raise
finally:
    session.close()
```

**Session 的重要理解：**
- Session = 一次数据库对话的工作单元
- `session.add()` 不会立即写数据库，只是标记
- `session.commit()` 才真正把更改写入（事务提交）
- 如果 `commit()` 之前程序崩溃，数据库不会变

### Model（模型）

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 1. 定义基类（所有模型的父类）
class Base(DeclarativeBase):
    pass

# 2. 定义模型 = 定义一个表
class PaperModel(Base):
    __tablename__ = "papers"  # 表名

    # 列名: 类型 = mapped_column(实际类型, 约束)
    entry_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    published: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    authors: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
```

**Mapped 是什么？**
- `Mapped[str]` 告诉类型检查器"这个属性是 str 类型"
- `mapped_column(String, ...)` 告诉 SQLAlchemy "这个列在数据库中是 VARCHAR/Text 类型"

**nullable / default 的含义：**

| 约束 | 效果 |
|---|---|
| `nullable=False` | 插入时必须提供值，不能为 NULL |
| `nullable=True` | 可以为 NULL |
| `default=""` | 不提供值时用空字符串 |
| `default=list` | 不提供值时用空列表 `[]` |
| `server_default=func.now()` | 数据库自动生成当前时间 |

### 创建表

```python
# create_all 会检查 Base 的所有子类，在数据库中创建表
# 如果表已存在，不会重复创建（幂等操作）
Base.metadata.create_all(engine)
```

等价于在 psql 里执行 CREATE TABLE IF NOT EXISTS。

### upsert（插入或更新）

```python
from sqlalchemy.dialects.postgresql import Insert

stmt = (
    Insert(PaperModel)
    .values(entry_id="...", title="...", ...)
    .on_conflict_do_update(
        index_elements=[PaperModel.entry_id],  # 主键冲突时
        set_={"title": "...", ...},            # 更新这些字段
    )
)
session.execute(stmt)
```

翻译成 SQL：

```sql
INSERT INTO papers (entry_id, title, ...)
VALUES ('...', '...', ...)
ON CONFLICT (entry_id) DO UPDATE SET
    title = EXCLUDED.title,
    ...;
```

**EXCLUDED** 是 PostgreSQL 的关键字，指你试图插入的那行新数据。

### 本项目中的完整调用链

```python
# main.py
storage = PostgresStorage()
storage.save(result)

# PostgresStorage.save() 内部：
with Session(engine) as session:
    for paper in result.papers:        # 遍历每篇论文
        upsert_paper(session, data)     #   INSERT ... ON CONFLICT
    session.add(search_log)             # 记录搜索日志
    session.commit()                    # 一次性提交所有更改
```

---

## 五、项目代码逐层拆解

### 第 1 层：数据模型 `src/models.py`

```python
@dataclass
class Paper:
    entry_id: str
    title: str
    summary: str
    published: datetime
    authors: list[str]
    ...
```

**`dataclass` 是什么？**
- 自动生成 `__init__`、`__repr__`、`__eq__` 等方法
- 纯粹的数据容器，没有业务逻辑
- 和数据库无关，只是一个"传数据的结构"

### 第 2 层：数据库模型 `src/database.py`

```python
class PaperModel(Base):
    __tablename__ = "papers"
    entry_id: Mapped[str] = mapped_column(String, primary_key=True)
    ...
```

**和 `Paper` 的关系：**
- `Paper` = 普通 Python 对象，在代码各处传递
- `PaperModel` = SQLAlchemy ORM 模型，对应数据库表
- `PostgresStorage` 负责在两者之间转换

### 第 3 层：存储层 `src/storage.py`

```python
class PostgresStorage(BaseStorage):
    def save(self, result: SearchResult) -> str:
        with Session(self._engine) as session:
            for paper in result.papers:
                upsert_paper(session, _paper_to_dict(paper))
            log = SearchLogModel(...)
            session.add(log)
            session.commit()

    def load(self, identifier: str) -> SearchResult | None:
        with Session(self._engine) as session:
            log = session.get(SearchLogModel, int(identifier))
            papers = session.query(PaperModel).filter(...).all()
            return SearchResult(...)
```

**为什么用抽象基类 `BaseStorage`？**
- 你可以在 JSON 和数据库之间自由切换
- 将来换 MySQL 只需新增一个 `MySQLStorage(BaseStorage)`
- `main.py` 不关心具体存储实现，只调 `save()` / `load()`

### 第 4 层：入口 `main.py`

```python
# JSON 模式
storage = FileStorage()
storage.save(result)

# 数据库模式（--db 参数）
storage = PostgresStorage()
storage.save(result)
```

**切换存储方式不需要改业务逻辑。** 这就是分层设计的目的。

---

## 六、操作流程

### 完整流程（从零开始）

```bash
# 第 1 步：启动 PostgreSQL
cd E:\arXivCrawler
docker compose up -d

# 第 2 步：确认启动成功
docker ps
# CONTAINER ID   IMAGE          ...   STATUS        PORTS                    NAMES
# abc123456789   postgres:16    ...   Up 2 minutes  0.0.0.0:5432->5432/tcp   arxivcrawler-postgres

# 第 3 步：安装依赖
uv sync

# 第 4 步：爬取数据并写入数据库
python main.py -k "transformer" -s 10 --db

# 第 5 步：进入数据库查看
docker compose exec postgres psql -U crawler -d arxiv_crawler

# 第 6 步：在 psql 中执行查询
\dt                    # 列出所有表
\d papers              # 查看 papers 表结构
SELECT count(*) FROM papers;               # 论文总数
SELECT title FROM papers LIMIT 3;           # 前 3 篇论文标题
SELECT * FROM search_log ORDER BY id DESC;  # 最近一次搜索日志
\q                     # 退出
```

### Docker 补充说明

数据库已经在运行了，关闭电脑再打开后：

```bash
# Docker Desktop 会自动启动，容器会自动运行（restart: unless-stopped）
# 你只需确认一下
docker ps

# 如果没自动启动
docker compose up -d

# 直接就能用
python main.py -k "quantum" -s 20 --db
```

### 如果报"端口被占用"

```bash
# 查看谁占了 5432
netstat -ano | findstr :5432

# 找到 PID 后结束进程
taskkill /PID <数字> /F

# 或者改 docker-compose.yml 的端口
ports:
  - "5433:5432"     # 左边改成 5433

# 代码里也要改连接字符串（或启动时指定）
python main.py -k "test" -s 5 --db "postgresql://crawler:crawler_pass@localhost:5433/arxiv_crawler"
```
