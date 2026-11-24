r"""多维诊断 judge —— 不只判 PASS/FAIL，还输出具体失败维度和修复建议。

Level 2 的核心：让失败可解释、可定点修复。
"""
import json, urllib.request, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.secrets import get_key
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

DIAGNOSTIC_SYSTEM = """你是严格的中文对话数据质检员。评估一条 AI 回答是否像真人，并给出多维度诊断。

输出 JSON（不要其他内容）：
{
  "verdict": "PASS" 或 "FAIL",
  "scores": {
    "ai_tone": 0-10,        // AI套话程度，10=完全没有人味
    "fabrication": 0-10,    // 编造用户没说过的细节，10=严重编造
    "relevance": 0-10,      // 答非所问程度，10=完全跑题
    "empathy": 0-10,        // 情绪回应缺失，10=冷冰冰/先讲道理
    "naturalness": 0-10,    // 机器翻译腔/啰嗦，10=非常不自然
    "length": 0-10          // 长度问题，10=过长或过短
  },
  "failures": ["具体失败原因1", "原因2"],
  "fix": "针对性的修复建议（一句话）"
}

判定标准：先站用户这边回应情绪，引用具体细节，不编造，不套话，80-400字，口语自然。
任一维度 ≥7 则 verdict=FAIL。"""

REWRITE_SYS = """你是一位中文对话文案专家。根据诊断结果，把一条不合格的回答改写成像真人的回复。

【改写要求】
1. 一段中等长度（80-400字）的自然中文。
2. 用户倾诉委屈时，先站用户这边，先回应具体处境，不先讲道理。
3. 引用用户话里的具体细节，不编造没说过的东西。
4. 禁止套话：我太懂你/我完全理解/抱抱你/我听到了/这确实让人/首先其次/当然可以/题主/楼主/建议寻求专业帮助/表情符号/列表。
5. 温暖、克制、口语化，像真人在微信认真回朋友。

只输出改写后的回答文本，不要解释。"""

SYNTH_SYS = """你是一位中文对话文案专家。根据用户的问题，从零写一段像真人的温暖回复。

【要求】
1. 一段中等长度（80-400字）的自然中文。
2. 先站用户这边，回应具体情绪和处境，不先讲道理。
3. 引用问题里的具体细节，不编造。
4. 禁止套话：我太懂你/我完全理解/抱抱你/我听到了/首先其次/当然可以/题主/楼主/建议寻求专业帮助/表情符号/列表。
5. 温暖、克制、口语化。

只输出回答文本。"""


def call_llm(messages, max_tokens=500, retries=5):
    body = {"model": "deepseek-flash", "messages": messages, "stream": False,
            "max_tokens": max_tokens, "thinking": {"type": "disabled"}}
    data = json.dumps(body).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(DEEPSEEK_URL, data=data, headers={
                "Authorization": "Bearer " + get_key("deepseek"), "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                res = json.loads(r.read().decode())
            return res["choices"][0]["message"]["content"].strip()
        except Exception:
            if attempt < retries - 1:
                time.sleep(min(2 ** attempt, 8) + random.random())
    return None


def diagnose(q: str, a: str) -> dict:
    """多维诊断，返回结构化结果。"""
    user = f"【用户】\n{q}\n\n【回答】\n{a}\n\n请输出诊断 JSON。"
    resp = call_llm([
        {"role": "system", "content": DIAGNOSTIC_SYSTEM},
        {"role": "user", "content": user},
    ], max_tokens=400)
    if not resp:
        return {"verdict": "ERROR", "scores": {}, "failures": ["API失败"], "fix": ""}
    try:
        # 提取 JSON
        s = resp.find("{"); e = resp.rfind("}")
        return json.loads(resp[s:e+1]) if s >= 0 and e > s else {"verdict": "ERROR", "raw": resp[:200]}
    except Exception:
        return {"verdict": "ERROR", "raw": resp[:200]}


def rewrite_with_diagnosis(q: str, a: str, diag: dict) -> str | None:
    """带诊断的定向重写。"""
    fix = diag.get("fix", "")
    failures = "；".join(diag.get("failures", []))
    user = f"【用户】\n{q}\n\n【原回答（不合格）】\n{a}\n\n【诊断失败原因】\n{failures}\n【修复建议】\n{fix}\n\n请按诊断改写，只输出改写后的回答。"
    return call_llm([
        {"role": "system", "content": REWRITE_SYS},
        {"role": "user", "content": user},
    ])


def synthesize(q: str) -> str | None:
    """只用问题从零生成。"""
    return call_llm([
        {"role": "system", "content": SYNTH_SYS},
        {"role": "user", "content": f"【用户问题】\n{q}\n\n请写一段温暖的回答。"},
    ])
