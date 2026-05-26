import time
from dashscope import Generation
from config import DASHSCOPE_API_KEY, LLM_MODEL

MAX_RETRIES = 3


def call_llm(prompt: str) -> str:
    if not DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY 未设置，请在 .env 文件中配置")

    for attempt in range(MAX_RETRIES):
        try:
            response = Generation.call(
                api_key=DASHSCOPE_API_KEY,
                model=LLM_MODEL,
                prompt=prompt,
            )
            if response.status_code != 200:
                raise RuntimeError(f"LLM 调用失败: {response.code} - {response.message}")
            return response.output.text
        except RuntimeError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 * (attempt + 1))
                continue
            raise
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 * (attempt + 1))
                continue
            raise RuntimeError(f"LLM 调用异常: {e}")


def call_llm_stream(prompt: str):
    if not DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY 未设置")

    for attempt in range(MAX_RETRIES):
        try:
            responses = Generation.call(
                api_key=DASHSCOPE_API_KEY,
                model=LLM_MODEL,
                prompt=prompt,
                stream=True,
                incremental_output=True,
            )
            for response in responses:
                if response.status_code != 200:
                    raise RuntimeError(f"LLM 流式调用失败: {response.code}")
                if response.output and response.output.text:
                    yield response.output.text
            return
        except RuntimeError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 * (attempt + 1))
                continue
            raise
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 * (attempt + 1))
                continue
            raise RuntimeError(f"LLM 流式调用异常: {e}")
