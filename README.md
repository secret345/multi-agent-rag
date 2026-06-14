# 基于 Multi-Agent + RAG 的企业智能数据分析平台

基于 LangGraph 构建的多智能体 RAG 系统，支持销售数据分析、企业知识问答、多文档分析三大场景。前端采用 Vue 3 + Element Plus，后端采用 FastAPI，支持 SSE 流式对话。

## 系统架构

```
                    ┌─────────────────────────────────────┐
                    │         Vue 3 + Element Plus        │
                    │  (SSE 流式对话 / JWT 认证 / Plotly)   │
                    └──────────────┬──────────────────────┘
                                   │ REST API + SSE
                    ┌──────────────┴──────────────────────┐
                    │           FastAPI 后端               │
                    │  (认证 / 聊天 / 文档 / 设置 端点)      │
                    └──────────────┬──────────────────────┘
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    ▼                              ▼                              ▼
┌─────────────┐            ┌─────────────┐               ┌──────────────┐
│   Planner   │───intent──▶│  Rewriter   │────rewrite───▶│    Router    │
│  LLM 意图分类 │            │ 指代消解/查询改写│               │  路由到对应Agent│
└─────────────┘            └─────────────┘               └──────┬───────┘
                                                                │
                           ┌────────────────┬───────────────────┤
                           ▼                ▼                   ▼
                    ┌─────────────┐  ┌──────────────┐   ┌──────────────┐
                    │  SQL Agent  │  │  RAG Agent   │   │  Doc Agent   │
                    │             │  │              │   │              │
                    │ LLM → SQL   │  │ HyDE + BM25  │   │ 多文档向量检索  │
                    │ SQLite 执行  │  │ + FAISS +    │   │ + Reranker   │
                    │             │  │ RRF + Rerank │   │              │
                    └──────┬──────┘  └──────┬───────┘   └──────┬───────┘
                           │                │                   │
                           └────────────────┴───────────────────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │    Writer     │  SSE 流式输出最终回答
                                    └──────────────┘
```

## 核心特性

### 1. 多智能体协作工作流
- **Planner**: LLM 意图识别，自动路由到对应 Agent（销量分析 / 知识问答 / 文档分析）
- **Rewriter**: 多轮对话查询重写，支持指代消解（"那笔记本呢" → "笔记本销量是多少"）
- **Writer**: 基于上下文 + 对话历史生成回答，SSE 流式输出

### 2. RAG 检索优化（四层管线）

| 层级 | 技术 | 说明 |
|------|------|------|
| 查询扩展 | HyDE | LLM 生成假设性回答，用回答向量替代原始查询做语义检索，提升召回率 |
| 关键词检索 | BM25 + jieba | 中文分词 + BM25 打分，擅长精确匹配和专业术语 |
| 向量检索 | FAISS + DashScope Embedding | text-embedding-v3 生成向量，L2 距离相似度搜索 |
| 融合排序 | RRF | Reciprocal Rank Fusion 按排名加权融合双路结果，替代简单去重 |
| 重排序 | bge-reranker / LLM | 优先使用本地 bge-reranker-v2-m3 CrossEncoder，自动降级到 LLM Rerank |

### 3. Text-to-SQL
- LLM 根据自然语言生成 SQL 查询
- sqlite3 只读执行，`_validate_sql()` 安全校验防注入
- 自动总结查询结果

### 4. 前后端分离
- **前端**: Vue 3 + TypeScript + Element Plus + Plotly.js
- **后端**: FastAPI REST API + SSE 流式接口
- **认证**: JWT Token 无状态认证，contextvars 请求级 API Key 注入
- **通信**: SSE (Server-Sent Events) 实现逐字流式输出

### 5. 用户系统
- 手机号注册 / 登录（bcrypt 加盐哈希）
- 短信验证码重置密码（模拟模式，可接入阿里云 SMS）
- 用户数据隔离：聊天记录、文档、API Key 按用户独立存储

### 6. 可观测性
- 每个 Agent 节点记录耗时、输入输出
- 调用链路追踪，日志持久化
- RAG 评估脚本，量化检索准确率

## 安全设计

| 安全措施 | 实现方式 |
|---------|---------|
| SQL 注入防护 | `_validate_sql()` 只允许 SELECT 语句，去除注释后校验，禁止多语句执行 |
| SQLite 只读模式 | `PRAGMA query_only = ON`，数据库连接以只读方式打开 |
| 密码存储 | bcrypt 加盐哈希，自动迁移旧版 SHA-256 格式 |
| 验证码安全 | `secrets` 密码学安全随机数，速率限制（每分钟 3 次发送，5 次验证尝试） |
| 文件上传安全 | 文件名过滤路径穿越字符，`os.path.basename` 清洗 |
| XSS 防护 | DOMPurify 白名单过滤 + HTML 实体转义 |
| 认证安全 | JWT Token + 72 小时过期 + 401 自动跳转登录 |
| 用户数据隔离 | MySQL 按用户隔离，聊天记录、文档、API Key 独立存储 |

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端框架 | Vue 3 + TypeScript |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia |
| 构建工具 | Vite |
| 数据可视化 | Plotly.js |
| 后端框架 | FastAPI |
| 工作流编排 | LangGraph |
| LLM / Embedding | DashScope (Qwen-Max / text-embedding-v3) |
| 向量检索 | FAISS (IndexFlatL2) |
| 关键词检索 | BM25 + jieba |
| 重排序 | bge-reranker-v2-m3 / LLM Rerank |
| 数据分析 | Pandas + sqlite3 |
| 数据存储 | MySQL 8.0 |
| 认证 | JWT (PyJWT) + bcrypt |

## 项目结构

```
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── LoginPage.vue   # 登录/注册
│   │   │   ├── ResetPasswordPage.vue
│   │   │   └── ChatPage.vue    # 主聊天界面
│   │   ├── components/         # 通用组件
│   │   │   ├── ChatMessage.vue # 消息气泡（XSS 安全渲染）
│   │   │   ├── ChatInput.vue   # 输入框
│   │   │   └── SalesChart.vue  # Plotly 图表
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── api/                # Axios 客户端
│   │   └── router/             # Vue Router
│   ├── vite.config.ts
│   └── package.json
├── api/                        # FastAPI API 层
│   ├── auth_deps.py            # JWT 认证依赖
│   ├── auth_router.py          # 认证端点
│   ├── chat_router.py          # 聊天 + SSE 流式端点
│   ├── docs_router.py          # 文档管理端点
│   └── settings_router.py      # 用户设置端点
├── agents/                     # 智能体模块
│   ├── planner.py              # 意图识别
│   ├── rewriter.py             # 查询重写
│   ├── sql_agent.py            # Text-to-SQL
│   ├── rag_agent.py            # RAG 检索调度
│   └── writer.py               # 回答生成（支持流式）
├── rag/                        # RAG 检索管线
│   ├── hybrid_retriever.py     # HyDE + BM25 + FAISS + RRF 融合
│   ├── reranker.py             # bge-reranker + LLM 降级
│   ├── bm25.py                 # BM25 检索器（持久化）
│   ├── retriever.py            # FAISS 向量检索
│   ├── chunking.py             # 递归字符分块
│   ├── embedding.py            # Embedding 调用
│   ├── indexer.py              # 知识库索引构建
│   ├── doc_indexer.py          # 文档索引构建
│   ├── doc_retriever.py        # 文档检索
│   └── doc_parser.py           # 文档解析
├── graph/
│   └── workflow.py             # LangGraph 工作流（含链路追踪）
├── auth/
│   ├── user_auth.py            # 用户认证
│   └── sms_service.py          # 短信服务（模拟）
├── utils/
│   └── logger.py               # 调用链路日志
├── eval/
│   └── rag_eval.py             # RAG 评估脚本
├── data/
│   ├── knowledge.txt           # 企业知识库
│   ├── sales.csv               # 销售数据
│   └── eval_qa.json            # 评估测试集
├── main.py                     # FastAPI 应用入口
├── llm.py                      # LLM 调用（含重试 + 流式）
├── db.py                       # MySQL 数据库连接
├── config.py                   # 配置（contextvars API Key 注入）
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend && npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DashScope API Key、MySQL 连接信息和 JWT_SECRET_KEY
```

### 3. 构建知识库索引

```bash
python -m rag.indexer
```

### 4. 启动

```bash
# 后端
uvicorn main:app --reload --port 8000

# 前端（另一个终端）
cd frontend && npm run dev
```

访问 http://localhost:5173

### 5. 运行评估

```bash
# RAG 评估
python -m eval.rag_eval

# 单元测试
pytest tests/ -v
```

## 环境变量说明

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key |
| `MYSQL_HOST` | MySQL 主机地址（默认 localhost）|
| `MYSQL_PORT` | MySQL 端口（默认 3306）|
| `MYSQL_USER` | MySQL 用户名（默认 root）|
| `MYSQL_PASSWORD` | MySQL 密码 |
| `MYSQL_DATABASE` | MySQL 数据库名（默认 multi_agent_rag）|
| `JWT_SECRET_KEY` | JWT 签名密钥（生产环境请更换）|
