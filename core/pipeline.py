r"""统一流水线内核 —— 内外一体的协同引擎。

所有阶段（L1/L2/L3）共享同一个异步 LLM 客户端 + 令牌池，
批量并发，避免逐条同步调用。这是"快"的核心。
"""
import asyncio
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor


class LLMClient:
    """统一异步 LLM 客户端（内部所有引擎共用）。"""

    def __init__(self, provider="agnes", max_concurrency=500):
        self.provider = provider
        self.sem = asyncio.Semaphore(max_concurrency)
        from .secrets import get_key
        if provider == "deepseek":
            self.url = "https://api.deepseek.com/chat/completions"
            self.key = get_key("deepseek")
        else:
            self.url = "https://apihub.agnes-ai.com/v1/chat/completions"
            self.key = get_key("agnes")

    async def chat(self, messages, max_tokens=400, retries=3):
        async with self.sem:
            body = {"model": "deepseek-flash" if self.provider == "deepseek" else "agnes-3.0-flash",
                    "messages": messages, "max_tokens": max_tokens, "stream": False}
            if self.provider == "deepseek":
                body["thinking"] = {"type": "disabled"}
            data = json.dumps(body).encode()
            for attempt in range(retries):
                try:
                    # 用 asyncio.to_thread 避免阻塞事件循环
                    return await asyncio.to_thread(self._post, data)
                except Exception as e:
                    if attempt < retries - 1:
                        is_429 = "429" in str(e)
                        delay = min(2 ** attempt, 30) if is_429 else min(2 ** attempt, 4)
                        await asyncio.sleep(delay)
            return None

    def _post(self, data):
        req = urllib.request.Request(self.url, data=data, headers={
            "Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.loads(r.read().decode())
        return res["choices"][0]["message"]["content"].strip()
