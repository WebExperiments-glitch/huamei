import sys, time, tracemalloc
sys.path.insert(0, r"H:\xunlian")
import huamei
path = r"H:\xunlian\data\eq_rewritten.parquet"
print("Full-scale perf test (all 529, 500 workers)...")
tracemalloc.start()
t0 = time.time()
r = huamei.refine(path, workers=500, quiet=True)
dt = time.time() - t0
cur, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"time: {dt:.1f}s for {r['total']} = {r['total']/dt:.1f} samples/s")
print(f"memory peak: {peak/1048576:.1f}MB")
print(f"grades: gold={r['gold']} silver={r['silver']} bronze={r['bronze']} rejected={r['rejected_dpo_negatives']}")
