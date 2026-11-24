r"""Huamei 统一 API —— 用户唯一需要知道的接口。

内部引擎协同，对外只暴露精炼/质检两个动作，输出分级数据。
"""
from pathlib import Path
import json
import pyarrow as pa
import pyarrow.parquet as pq

from .ui.panel import banner, report_panel, section, close, row


def _load(path):
    return pq.read_table(path).to_pylist()


def _pairs(rows):
    return [(r["messages"][1]["content"], r["messages"][2]["content"])
            for r in rows if "messages" in r and len(r["messages"]) >= 3]


def refine(path: str, output: str = None, workers: int = 200, limit: int = 0, quiet: bool = False):
    """三级精炼：L1验收 → L2诊断修复 → L3合成重构。"""
    import asyncio
    from .refinery.async_tower import refine_batch
    from .stages.pre_filter import prefilter
    rows = _load(path)
    if limit:
        rows = rows[:limit]
    pairs = _pairs(rows)
    if not quiet:
        print(banner())
        print(section("INPUT"))
        print(row("loaded", str(len(pairs))))
        print(close())

    # Cheap deterministic pre-filter BEFORE LLM judging
    pairs, fstats = prefilter(pairs)
    if not quiet:
        print(section("PRE-FILTER (dedup + heuristics)"))
        print(row("dedup removed", str(fstats.dedup_removed)))
        print(row("quality removed", str(fstats.quality_removed)))
        print(row("survived", str(fstats.survived)))
        print(close())

    results = asyncio.run(refine_batch(pairs, workers=workers, synth_samples=2))
    from collections import Counter
    c = Counter(r["grade"] for r in results)
    report = {
        "total": len(results),
        "prefilter_dedup_removed": fstats.dedup_removed,
        "prefilter_quality_removed": fstats.quality_removed,
        "gold": c.get("gold", 0),
        "silver": c.get("silver", 0),
        "bronze": c.get("bronze", 0),
        "rejected_dpo_negatives": c.get("rejected", 0),
        "usable_rate": round((c.get("gold",0)+c.get("silver",0)+c.get("bronze",0))/max(len(results),1), 3),
    }

    # 分级输出
    outdir = Path(output) if output else Path(path).parent
    outdir = outdir if outdir.is_dir() else outdir.parent
    base = Path(path).stem
    written = {}
    for level in ["gold", "silver", "bronze", "rejected"]:
        subset = [r for r in results if r.get("grade") == level]
        if not subset:
            continue
        out_rows = []
        for r in subset:
            sysmsg = next((x["messages"][0] for x in rows
                           if x["messages"][1]["content"] == r["q"]),
                          {"role": "system", "content": ""})
            out_rows.append({
                "messages": [sysmsg, {"role": "user", "content": r["q"]},
                             {"role": "assistant", "content": r["final"] or r["original"]}],
                "grade": level,
            })
        p = outdir / f"{base}_{level}.parquet"
        pq.write_table(pa.Table.from_pylist(out_rows), p)
        written[level] = str(p)

    report["outputs"] = written
    if not quiet:
        print(report_panel(report))
        for k, v in written.items():
            print(f"  → {k}: {v}")
    return report


def judge(path: str, rounds: int = 2, quiet: bool = False):
    """双轮严格质检，输出通过率。"""
    from .judge.anti_ai_rubric import judge_batch
    rows = _load(path)
    pairs = _pairs(rows)
    if not quiet:
        print(banner())
        print(section("品尝 / TASTE"))
        print(row("输入样本", str(len(pairs))))
        print(close())
    kept, _ = judge_batch(pairs, rounds=rounds)
    report = {"total": len(pairs), "passed": len(kept),
              "pass_rate": round(len(kept)/len(pairs), 3)}
    if not quiet:
        print(report_panel({"total": len(pairs), "gold": len(kept),
                            "usable_rate": report["pass_rate"]}))
    return report
