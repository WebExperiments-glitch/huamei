r"""异步三级精炼塔 —— 快！准！狠！

所有 LLM 调用走统一异步客户端，全批量并发。
"""
import asyncio
import json
from .prompts import QUICK_JUDGE_SYS, DIAGNOSTIC_SYS, REWRITE_SYS, SYNTH_SYS
from ..judge.anti_ai_rubric import JUDGE_SYSTEM


# 分级验收标准：Gold 最严，Silver 中等，Bronze 宽松（符合分级本意）
LEVEL_SYS = {
    "gold": JUDGE_SYSTEM,
    "silver": """判断回答是否像真人说话。基本要求：一段自然中文、先回应情绪、不编造、没有明显AI套话（我太懂你/抱抱你/首先其次/题主）。满足就输出 PASS，否则 FAIL。只输出一个词。""",
    "bronze": """判断回答是否基本合格：是中文、有内容、不像纯机器人。宽松判断，基本能看就输出 PASS。只输出一个词。""",
}

async def _judge(client, q, a, level="gold"):
    resp = await client.chat([
        {"role": "system", "content": LEVEL_SYS[level]},
        {"role": "user", "content": f"【用户】\n{q}\n\n【回答】\n{a}\n\n只输出 PASS 或 FAIL。"},
    ], max_tokens=10)
    return bool(resp and "PASS" in resp.upper() and "FAIL" not in resp.upper())


async def _diagnose(client, q, a):
    resp = await client.chat([
        {"role": "system", "content": DIAGNOSTIC_SYS},
        {"role": "user", "content": f"【用户】\n{q}\n\n【回答】\n{a}\n\n输出诊断JSON。"},
    ], max_tokens=300)
    if not resp:
        return {"fix": "", "failures": []}
    try:
        s, e = resp.find("{"), resp.rfind("}")
        return json.loads(resp[s:e+1]) if s >= 0 and e > s else {"fix": "", "failures": []}
    except Exception:
        return {"fix": "", "failures": []}


async def _rewrite(client, q, a, diag):
    resp = await client.chat([
        {"role": "system", "content": REWRITE_SYS},
        {"role": "user", "content": f"【用户】\n{q}\n\n【原回答】\n{a}\n\n【修复建议】\n{diag.get('fix','')}\n只输出改写后的回答。"},
    ], max_tokens=400)
    return resp


async def _synthesize(client, q):
    return await client.chat([
        {"role": "system", "content": SYNTH_SYS},
        {"role": "user", "content": f"【用户问题】\n{q}\n\n写一段温暖的回答。"},
    ], max_tokens=400)


async def refine_one_async(client, q, a, synth_samples=2):
    # L1: 严格验收 -> Gold
    if await _judge(client, q, a, level="gold"):
        return {"q": q, "final": a, "grade": "gold", "original": a}
    # L2: 诊断修复 -> 次级标准验收 -> Silver
    diag = await _diagnose(client, q, a)
    rewritten = await _rewrite(client, q, a, diag)
    if rewritten and await _judge(client, q, rewritten, level="silver"):
        return {"q": q, "final": rewritten, "grade": "silver", "original": a, "diag": diag}
    # L3: 合成重构 -> 宽松标准验收 -> Bronze
    for _ in range(synth_samples):
        cand = await _synthesize(client, q)
        if cand and await _judge(client, q, cand, level="bronze"):
            return {"q": q, "final": cand, "grade": "bronze", "original": a}
    return {"q": q, "final": None, "grade": "rejected", "original": a}


async def refine_batch(pairs, workers=200, synth_samples=2, provider=None):
    from ..core.pipeline import LLMClient
    from ..core.secrets import get_default_provider
    client = LLMClient(provider=provider or get_default_provider(), max_concurrency=workers)
    tasks = [refine_one_async(client, q, a, synth_samples) for q, a in pairs]
    return await asyncio.gather(*tasks)
