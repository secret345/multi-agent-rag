# 基于 Multi-Agent + RAG 的企业智能数据分析平台

基于 LangGraph 构建的多智能体 RAG 系统，支持销售数据分析、企业知识问答、多文档分析三大场景。

## 系统架构

```
用户提问
    │
    ▼
┌─────────────┐
│  Planner    │  LLM 意图识别
│  (planner)  │  → sales_analysis / knowledge_query / document_analysis
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Rewriter   │  LLM 查询重写（指代消解）
│  (rewriter) │  → "那笔记本呢" → "笔记本销量是多少"
└──────┬──────┘
       │
       ├─────────────────┬──────────────────┐
       ▼                 ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌───────────────┐
│  SQL Agent  │  │  RAG Agent   │  │  Doc Agent    │
│             │  │              │  │               │
│ LLM→SQL    │  │ BM25 + FAISS │  │ 多文档向量检索  │
│ sqlite3执行  │  │ + Reranker   │  │ + Reranker    │
└──────┬──────┘  └──────┬───────┘  └───────┬───────┘
       │                │                  │
       └────────────────┴──────────────────┘
                        │
                        ▼
                ┌──────────────┐
                │   Writer     │  流式输出最终回答
                └──────────────┘
```

## 架构设计

### 数据流

```
用户提问 → Planner (意图识别) → Rewriter (查询重写/指代消解)
                                      │
                    ┌─────────────────┼──────────────────┐
                    ▼                 ▼                  ▼
              SQL Agent          RAG Agent          Doc Agent
            (LLM→SQL→SQLite)  (BM25+FAISS+Rerank)  (多文档向量检索)
                    │                 │                  │
                    └─────────────────┴──────────────────┘
                                      │
                                      ▼
                                  Writer (流式生成回答)
```

### 设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 工作流编排 | LangGraph StateGraph | 声明式路由，易于扩展新 Agent |
| 检索策略 | BM25 + FAISS + LLM Rerank | 关键词+语义互补，Rerank 提升精度 |
| SQL 生成 | LLM 生成 + 只读执行 | 支持灵活查询，安全校验防注入 |
| 存储方案 | JSON 平文件 | 轻量级，适合单机部署和 Streamlit Cloud |

### 1. Multi-Agent 工作流
- **Planner**: LLM 意图识别，自动路由到对应 Agent
- **Rewriter**: 多轮对话查询重写，支持指代消解
- **Writer**: 基于上下文 + 对话历史生成回答，支持流式输出

### 2. Text-to-SQL
- LLM 根据自然语言生成 SQL 查询
- sqlite3 执行，支持多维度聚合分析
- 自动总结查询结果

### 3. Hybrid RAG 检索
- **BM25**: jieba 中文分词 + 关键词匹配
- **FAISS**: Embedding 向量相似度检索
- **Reranker**: LLM 对候选结果重排序
- 支持 PDF / DOCX / TXT 文档上传，多文件同时索引

### 4. 用户系统
- 手机号注册 / 登录
- 短信验证码重置密码（模拟模式，可接入阿里云 SMS）
- 访问控制，防止 API Key 滥用

### 5. 可观测性
- 每个 Agent 节点记录耗时、输入输出
- 调用链路追踪，日志持久化
- RAG 评估脚本，量化检索准确率

## 安全设计

| 安全措施 | 实现方式 |
|---------|---------|
| SQL 注入防护 | `_validate_sql()` 只允许 SELECT 语句，禁止 DROP/DELETE/INSERT/UPDATE/ATTACH/UNION |
| SQLite 只读模式 | `PRAGMA query_only = ON`，数据库连接以只读方式打开 |
| 密码存储 | bcrypt 加盐哈希，自动迁移旧版 SHA-256 格式 |
| CORS 策略 | 指定允许的源站，不使用通配符 |
| XSRF 保护 | Streamlit 内置 XSRF 防护已启用 |
| 用户数据隔离 | 每用户独立目录，聊天记录和 API Key 按用户隔离 |

## 技术栈

| 组件 | 技术 |
|------|------|
| 工作流编排 | LangGraph |
| LLM / Embedding | DashScope (Qwen-Max / text-embedding-v3) |
| 向量检索 | FAISS (IndexFlatL2) |
| 关键词检索 | BM25 + jieba |
| 前端 | Streamlit |
| 后端 | FastAPI |
| 数据分析 | Pandas + sqlite3 |

## 项目结构

```
├── agents/
│   ├── planner.py          # 意图识别
│   ├── rewriter.py         # 查询重写
│   ├── sql_agent.py        # Text-to-SQL
│   ├── rag_agent.py        # RAG 检索调度
│   └── writer.py           # 回答生成（支持流式）
├── rag/
│   ├── bm25.py             # BM25 检索器（持久化）
│   ├── retriever.py        # FAISS 向量检索
│   ├── hybrid_retriever.py # 混合检索
│   ├── reranker.py         # LLM 重排序
│   ├── chunking.py         # 递归字符分块
│   ├── embedding.py        # Embedding 调用
│   ├── indexer.py          # 知识库索引构建
│   ├── doc_indexer.py      # 文档索引构建
│   ├── doc_retriever.py    # 文档检索
│   └── doc_parser.py       # 文档解析
├── graph/
│   └── workflow.py         # LangGraph 工作流（含链路追踪）
├── auth/
│   ├── user_auth.py        # 用户认证
│   └── sms_service.py      # 短信服务（模拟）
├── utils/
│   └── logger.py           # 调用链路日志
├── eval/
│   └── rag_eval.py         # RAG 评估脚本
├── data/
│   ├── knowledge.txt       # 企业知识库
│   ├── sales.csv           # 销售数据
│   └── eval_qa.json        # 评估测试集
├── app.py                  # Streamlit 前端
├── main.py                 # FastAPI 后端
├── llm.py                  # LLM 调用（含重试 + 流式）
└── config.py               # 配置
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env，填入你的 DashScope API Key
```

### 3. 构建知识库索引
```bash
python -m rag.indexer
```

### 4. 启动
```bash
# Streamlit 前端
streamlit run app.py

# FastAPI 后端
uvicorn main:app --reload
```

### 5. 运行 RAG 评估
```bash
python -m eval.rag_eval
```

## RAG 评估结果

| 检索方式 | 知识问答准确率 |
|---------|-------------|
| 纯向量检索 (FAISS) | 100% (8/8) |
| 混合检索 (BM25 + Vector + Reranker) | 100% (8/8) |

> 销售数据查询由 Text-to-SQL Agent 处理，不经过 RAG 检索。

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_sql_security.py -v   # SQL 安全校验
pytest tests/test_auth.py -v           # 用户认证 + bcrypt
pytest tests/test_workflow.py -v       # 工作流路由
pytest tests/test_agents.py -v         # 各 Agent 单元测试
pytest tests/test_chunking.py -v       # 文本分块
```

## 部署

### Streamlit Cloud
1. Push 到 GitHub
2. 在 [share.streamlit.io](https://share.streamlit.io) 连接仓库
3. 在 Settings → Secrets 中配置：
```
DASHSCOPE_API_KEY = "your_key"
```

### 环境变量说明

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key |
