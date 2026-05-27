import os
import re
import sqlite3
import pandas as pd
from config import DATA_DIR
from llm import call_llm

_db_conn = None

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|ATTACH|DETACH|CREATE|REPLACE|TRUNCATE|EXEC|UNION|PRAGMA)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> None:
    """Raise ValueError if the SQL is not a safe SELECT query."""
    # Strip inline comments (/* ... */) and line comments (-- ...)
    cleaned = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    cleaned = re.sub(r"--[^\n]*", " ", cleaned)
    normalized = cleaned.strip().rstrip(";").strip()
    if not normalized.upper().startswith("SELECT"):
        raise ValueError(f"只允许 SELECT 查询，收到: {normalized[:60]}")
    if _FORBIDDEN_KEYWORDS.search(normalized):
        raise ValueError(f"SQL 包含禁止的关键字: {normalized[:60]}")
    # Reject multiple statements (semicolons in the middle)
    if ";" in normalized:
        raise ValueError("不允许执行多条 SQL 语句")


def _get_db() -> sqlite3.Connection:
    global _db_conn
    if _db_conn is None:
        csv_path = os.path.join(DATA_DIR, "sales.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError("数据文件不存在")
        df = pd.read_csv(csv_path)
        _db_conn = sqlite3.connect(":memory:", uri=True)
        _db_conn.execute("PRAGMA query_only = ON")
        df.to_sql("sales", _db_conn, index=False, if_exists="replace")
    return _db_conn


TABLE_SCHEMA = """
表名: sales
列:
  - product (TEXT): 产品名称，值有：手机、笔记本、平板、耳机
  - quantity (INTEGER): 销售数量
  - price (INTEGER): 单价（元）
  - revenue (INTEGER): 销售额 = quantity * price
  - region (TEXT): 地区，值有：华北、华东、华南
  - date (TEXT): 月份，格式 YYYY-MM，如 2024-01
"""


def _generate_sql(query: str) -> str:
    prompt = f"""你是一个 SQL 专家。根据用户问题，生成可在 SQLite 上执行的 SQL 查询。

表结构：
{TABLE_SCHEMA}

要求：
- 只输出 SQL 语句，不要任何解释
- 列名和表名必须严格按上面的定义
- 使用标准 SQLite 语法
- 如果需要聚合，使用 GROUP BY
- 如果用户问的是"最好/最高/最多"等，使用 ORDER BY + LIMIT 1
- 只允许 SELECT 语句，不要输出任何 INSERT/UPDATE/DELETE/DROP 等修改语句

用户问题：{query}"""

    result = call_llm(prompt)
    sql = result.strip()
    sql = re.sub(r"^```sql\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    return sql.strip()


def _summarize(query: str, sql: str, columns: list, rows: list) -> str:
    if not rows:
        return "查询结果为空，没有匹配的数据。"

    row_text = "\n".join([", ".join(str(v) for v in row) for row in rows[:20]])
    col_text = ", ".join(columns)

    prompt = f"""你是数据分析助手。根据以下信息回答用户问题。

用户问题：{query}
执行的 SQL：{sql}
查询结果（列: {col_text}）：
{row_text}

要求：
- 用中文总结查询结果
- 如果有数值，保留原始精度
- 回答要简洁准确
- 如果结果只有一行一列，直接给出数值"""

    return call_llm(prompt)


def sql_agent(query: str) -> str:
    try:
        conn = _get_db()
        sql = _generate_sql(query)
        _validate_sql(sql)
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return _summarize(query, sql, columns, rows)
    except ValueError as e:
        return f"SQL 安全校验失败：{e}"
    except sqlite3.OperationalError as e:
        return f"SQL 执行出错：{e}。请尝试换个方式提问。"
    except Exception as e:
        return f"数据分析出错：{e}"
