r"""Reproducible benchmark. Usage: python bench_full.py <parquet> [--workers N] [--seed N]

Reports honest metrics: rejection rate, error rate, wall time, and peak RSS via resource.getrusage.
"""
import argparse, sys, time, random, resource, json
from pathlib import Path
import pyarrow.parquet as pq


def main():
    p = argparse.ArgumentParser()
    p.add_argument("parquet", help="input parquet with a 'messages' column")
    p.add_argument("--workers", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    random.seed(args.seed)
    import huamei
    path = Path(args.parquet)
    rows = pq.read_table(path).to_pylist()

    t0 = time.time()
    r = huamei.refine(str(path), workers=args.workers, quiet=True)
    dt = time.time() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    report = {
        "input": str(path),
        "samples": r["total"],
        "workers": args.workers,
        "seed": args.seed,
        "wall_seconds": round(dt, 2),
        "samples_per_second": round(r["total"] / dt, 2),
        "peak_rss_mb": round(rss_mb, 1),
        "grade_counts": {k: r[k] for k in ["gold", "silver", "bronze", "rejected_dpo_negatives"]},
        "usable_rate": r["usable_rate"],
        "rejection_rate": round(r["rejected_dpo_negatives"] / max(r["total"], 1), 3),
        "note": "provider from env; no manual eval included; RSS includes native memory",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
