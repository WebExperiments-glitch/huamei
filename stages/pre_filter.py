r"""Pre-filter stage: cheap deterministic filters before expensive LLM judging.

Order (by cost, cheap first):
  1. MinHash approximate dedup (datatrove)
  2. Gopher/C4 heuristic quality (dolma rules, Chinese-aware)
Only survivors go to the LLM tower. This is the missing link the review identified.
"""
from dataclasses import dataclass, field


@dataclass
class FilterStats:
    total: int = 0
    dedup_removed: int = 0
    quality_removed: int = 0
    survived: int = 0


def prefilter(pairs: list[tuple[str, str]], use_dedup=True, use_quality=True):
    """Return (surviving pairs, stats)."""
    from ..adapters.datatrove_adapter import MinHashDeduplicator
    from ..adapters.dolma_adapter import passes_gopher, passes_c4

    stats = FilterStats(total=len(pairs))
    dedup = MinHashDeduplicator()
    out = []
    for q, a in pairs:
        if use_dedup and dedup.is_duplicate(a):
            stats.dedup_removed += 1
            continue
        if use_quality and not (passes_gopher(a) or passes_c4(a)):
            stats.quality_removed += 1
            continue
        out.append((q, a))
    stats.survived = len(out)
    return out, stats
