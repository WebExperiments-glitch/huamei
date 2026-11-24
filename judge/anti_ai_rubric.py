r"""反 AI 腔质检 —— 我们这几轮踩坑总结的核心创新。

用一个强 LLM（DeepSeek/Agnes）做 judge，判断一条 SFT 回答是否"像真人"。
规则来自 rubric_v2.txt + 阿奈人设的提炼。

关键：默认拒绝，双轮独立投票才通过（借鉴 judgecurate 论文的一致性校准）。
"""
import json, urllib.request, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed

JUDGE_SYSTEM = """你是极端严格的数据质量审查员，默认拒绝。判断一条中文对话回答是否像真人在认真回应朋友，用于训练温暖陪伴型 AI 助手。

必须全部满足：
1. 一段中等长度（80-400字）的自然中文，不是碎片短句，也不是超长文章。
2. 没有 AI 腔套话：我太懂你/我完全理解/抱抱你（滥用）/我听到了/这确实让人/首先其次/当然可以/作为AI/题主/楼主/建议你寻求专业帮助/表情符号/列表。
3. 用户倾诉委屈时，回答先站用户这边、先回应具体处境，而不是上来讲道理或给建议。
4. 引用了用户话里的具体细节，不是能套在任何对话上的万能模板。
5. 紧扣用户情绪和问题，不编造事实、不臆测没说过的细节、不答非所问。
6. 句子通顺自然、口语化，有真人说话的节奏，无重复啰嗦、无机器翻译腔。
7. 温暖、克制、有分寸，不过度甜腻，不冷冰冰说教。

输出：第一行只写 PASS 或 FAIL，第二行不超过30字说明原因。不要输出其他内容。"""

from ..core.secrets import get_key
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
AGNES_URL = "https://apihub.agnes-ai.com/v1/chat/completions"


def call_llm(messages, provider="agnes", max_tokens=80, retries=5):
    if provider == "deepseek":
        body = {"model": "deepseek-flash", "messages": messages, "stream": False,
                "max_tokens": max_tokens, "thinking": {"type": "disabled"}}
        url, key = DEEPSEEK_URL, get_key("deepseek")
    else:
        body = {"model": "agnes-3.0-flash", "messages": messages, "max_tokens": max_tokens}
        url, key = AGNES_URL, get_key("agnes")
    data = json.dumps(body).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers={
                "Authorization": "Bearer " + key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                res = json.loads(r.read().decode())
            return res["choices"][0]["message"]["content"].strip()
        except Exception as e:
            is_rate_limit = "429" in str(e)
            if attempt < retries - 1:
                # 429 用更长退避（限流恢复需要时间）
                delay = min(2 ** attempt, 30) + random.random() * 2 if is_rate_limit else min(2 ** attempt, 8) + random.random()
                time.sleep(delay)
    return None


def judge_one(q: str, a: str, provider="agnes") -> tuple[str, str]:
    user = f"【用户消息】\n{q}\n\n【助手回复】\n{a}\n\n请严格审查，输出 PASS 或 FAIL 及原因。"
    resp = call_llm([
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": user},
    ], provider=provider)
    if not resp:
        return "ERROR", ""
    first = resp.split("\n")[0].strip().upper()
    return ("PASS" if first == "PASS" else "FAIL", resp.split("\n")[1].strip()[:50] if "\n" in resp else "")


def judge_batch(pairs: list[tuple[str, str]], workers=200, provider="agnes", rounds=2):
    """双轮独立投票，全部 PASS 才保留。"""
    results = [[] for _ in pairs]
    for _ in range(rounds):
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(judge_one, q, a, provider): i for i, (q, a) in enumerate(pairs)}
            for f in as_completed(futs):
                results[futs[f]].append(f.result())
    kept = []
    for i, (q, a) in enumerate(pairs):
        if all(v[0] == "PASS" for v in results[i]):
            kept.append((q, a))
    return kept, results

