r"""三级精炼塔编排器。

Level 1: 严格验收（双轮 judge）→ Gold
Level 2: 诊断修复（多维诊断 + 定向重写）→ Silver
Level 3: 合成重构（只用问题重生成）→ Bronze / 废弃池(DPO负例)
"""
import json, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .diagnostic_judge import call_llm, diagnose, rewrite_with_diagnosis, synthesize, DIAGNOSTIC_SYSTEM


def quick_judge(q: str, a: str) -> bool:
    """Level 1 快速判定（单轮，严格）。"""
    user = f"【用户】\n{q}\n\n【回答】\n{a}\n\n回答像真人吗？只输出 PASS 或 FAIL。"
    resp = call_llm([
        {"role": "system", "content": DIAGNOSTIC_SYSTEM + "\n只输出 verdict 的 PASS 或 FAIL，不要 JSON。"},
        {"role": "user", "content": user},
    ], max_tokens=10)
    return bool(resp and "PASS" in resp.upper() and "FAIL" not in resp.upper())


def refine_one(q: str, a: str, synth_samples: int = 3) -> dict:
    """对单条数据跑完三级精炼。"""
    result = {"q": q, "original": a, "level": None, "final": None, "diag": None, "history": []}

    # Level 1: 验收
    if quick_judge(q, a):
        result["level"] = "gold"
        result["final"] = a
        return result
    result["history"].append("L1 fail")

    # Level 2: 诊断 + 定向重写
    diag = diagnose(q, a)
    result["diag"] = diag
    rewritten = rewrite_with_diagnosis(q, a, diag)
    if rewritten and quick_judge(q, rewritten):
        result["level"] = "silver"
        result["final"] = rewritten
        result["history"].append("L2 pass")
        return result
    result["history"].append("L2 fail")

    # Level 3: 合成重构（采样多次取最优）
    best = None
    for i in range(synth_samples):
        cand = synthesize(q)
        if cand and quick_judge(q, cand):
            best = cand
            break
    if best:
        result["level"] = "bronze"
        result["final"] = best
        result["history"].append("L3 pass")
    else:
        result["level"] = "rejected"
        result["final"] = None
        result["history"].append("L3 fail -> DPO negative")
    return result


class Refinery:
    def __init__(self, workers=100, synth_samples=3):
        self.workers = workers
        self.synth_samples = synth_samples

    def refine(self, pairs: list[tuple[str, str]]) -> list[dict]:
        results = []
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(refine_one, q, a, self.synth_samples): i for i, (q, a) in enumerate(pairs)}
            done = 0
            for f in as_completed(futs):
                results.append(f.result())
                done += 1
                if done % 50 == 0:
                    print(f"  refined {done}/{len(pairs)}", flush=True)
        return results

    @staticmethod
    def report(results: list[dict]) -> dict:
        from collections import Counter
        c = Counter(r["level"] for r in results)
        return {
            "total": len(results),
            "gold": c.get("gold", 0),
            "silver": c.get("silver", 0),
            "bronze": c.get("bronze", 0),
            "rejected_dpo_negatives": c.get("rejected", 0),
            "usable_rate": round((c.get("gold",0)+c.get("silver",0)+c.get("bronze",0)) / len(results), 3),
        }
