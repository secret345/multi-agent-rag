import time
import json
import os
from datetime import datetime
from config import DATA_DIR

LOG_PATH = os.path.join(DATA_DIR, "trace.jsonl")


class TraceLogger:
    def __init__(self):
        self.steps: list[dict] = []
        self.start_time = time.time()

    def log(self, node: str, input_data: str, output_data: str, duration_ms: float):
        step = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node": node,
            "duration_ms": round(duration_ms, 1),
            "input_preview": input_data[:200] if input_data else "",
            "output_preview": output_data[:200] if output_data else "",
        }
        self.steps.append(step)

    def save(self, query: str):
        record = {
            "query": query,
            "total_ms": round((time.time() - self.start_time) * 1000, 1),
            "steps": self.steps,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def summary(self) -> str:
        lines = []
        for s in self.steps:
            lines.append(f"  {s['node']}: {s['duration_ms']}ms")
        total = round((time.time() - self.start_time) * 1000, 1)
        lines.append(f"  总耗时: {total}ms")
        return "\n".join(lines)
