import json
from llm import call_llm

INTENTS = ["sales_analysis", "knowledge_query", "document_analysis"]


def planner_agent(query: str) -> dict:
    prompt = f"""你是任务规划器。分析用户输入，输出 JSON。

用户输入：{query}

输出格式（仅 JSON）：
{{
  "intent": "sales_analysis 或 knowledge_query 或 document_analysis",
  "tasks": ["task1", "task2"]
}}

规则：
- intent 只能是 sales_analysis、knowledge_query 或 document_analysis
- 如果用户提到上传的文档、文件内容、文档分析等，intent 为 document_analysis
- 如果用户询问销售数据、销量统计等，intent 为 sales_analysis
- 其他问题 intent 为 knowledge_query
- tasks 用英文描述
- 只输出 JSON，无任何额外文字"""

    result = call_llm(prompt)

    try:
        parsed = json.loads(result)
        if parsed.get("intent") not in INTENTS:
            parsed["intent"] = "knowledge_query"
        return parsed
    except json.JSONDecodeError:
        return {"intent": "knowledge_query", "tasks": ["answer the query"]}


