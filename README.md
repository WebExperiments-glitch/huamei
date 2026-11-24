# Huamei

**A unified data refinery for large language models.** Huamei cleans, judges, and rebuilds training data across every stage — pretraining, continued pretraining (CPT), supervised fine-tuning (SFT), and reinforcement learning (RL) — behind a single, minimal API.

 under the hood, it orchestrates a set of proven open-source engines (datatrove, Dolma) together with two original components: a three-level refinery tower and an anti-AI-tone judge. Users never see the individual tools; they see one coherent instrument with one interface.

---

## Why Huamei

Training data quality is the ceiling of model quality. In practice, however, data cleaning is fragmented:

- One tool handles deduplication, another handles heuristic filtering, yet another handles LLM-based judging.
- Each has its own data format, config style, and CLI.
- There is no unified way to take raw data — for pretraining or for SFT — and get clean, graded, ready-to-use output.

Huamei closes this gap. It provides:

1. **One data format** across all stages (`HuameiDoc`).
2. **One configuration surface** (YAML recipes + a small config dataclass).
3. **One API**: `huamei.refine()`, `huamei.judge()`, `huamei.engines()`.
4. **A unified engine bay** where internal tools are pluggable implementation details.

---

## Core ideas

### 1. Three-level refinery tower

Raw data goes through three levels, each with a different quality bar and a different recovery strategy:

| Level | Action | Output grade |
|---|---|---|
| L1 — Accept | A strict judge decides whether the sample is good as-is | 🟡 Gold |
| L2 — Diagnose & Repair | A multi-dimensional diagnosis identifies *why* it failed (AI tone, fabrication, off-topic, missing empathy, unnatural phrasing, length), then a targeted rewrite is generated | ⚪ Silver |
| L3 — Synthesize | The original answer is discarded; a fresh answer is generated from the question alone | 🔵 Bronze |
| Final reject | Unsalvageable samples | ⚫ Rejected — kept as DPO negatives |

This graded design is the central innovation. A single strict filter throws away everything below its bar; the tower *recovers* most of it. In our benchmark, L1 accepted 327/529 samples, and L2 recovered another 201 — data that a single-stage filter would have lost.

### 2. Graded judging

Gold, Silver, and Bronze use deliberately different judging standards. This matches the semantics of the grades: a Silver sample is not expected to satisfy the strictest bar, only the Silver bar. Applying one uniform standard to all levels is a common design mistake that causes recovery to fail.

### 3. Anti-AI-tone judge

Most public data-cleaning tools check toxicity, deduplication, and perplexity. Few check whether a response *sounds like a real person*. Our judge targets a specific failure mode common in LLM-generated SFT data: template empathy and formulaic phrasing — e.g. "I completely understand how you feel," "hug you," "firstly / secondly / finally," "the questioner..." — and rewards responses that take the user's side first, cite concrete details from the prompt, and stay concise and natural.

### 4. Chinese-specific adapters

Off-the-shelf English cleaning rules (Gopher, C4) fail on Chinese text: they rely on whitespace tokenization and sentence-ending punctuation like `.?!`. Our adapters use character n-grams and Chinese punctuation, making the same rules work correctly for Chinese corpora.

### 5. Instrument-style encapsulation

All internal engines — including third-party tools — sit behind a single package interface. There is no exposed tool-specific config, no tool-specific data format, and no tool-specific CLI. Internally, everything shares one async LLM client with a semaphore, one data format, and one rate-limit/backoff policy.

---

## Benchmark

Full run on 529 SFT samples, 500 concurrent workers, Agnes free API:

| Metric | Value |
|---|---:|
| Throughput | **5.7 samples/s** |
| Peak memory | **43.9 MB** |
| Gold (L1) | 327 (62%) |
| Silver (L2 recovered) | 201 (38%) |
| Bronze (L3 recovered) | 1 |
| Rejected | 0 |
| **Usable rate** | **100%** |

*Measured on 2026-11-24. Numbers depend on the judge model and API rate limits.*

---

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

Set an API key for the judge (Agnes or DeepSeek):

```bash
export AGNES_API_KEY=sk-...
# or create a .env file (see .env.example)
export DEEPSEEK_API_KEY=sk-...
```

---

## Usage

### Python API

```python
import huamei

# Three-level refinery — the main entry point
report = huamei.refine("data/raw.parquet", workers=500)
# outputs: raw_gold.parquet, raw_silver.parquet, raw_bronze.parquet, raw_rejected.parquet

# Strict quality check only
report = huamei.judge("data/raw.parquet")

# Inspect the internal engine bay
print(huamei.engines())
```

### CLI

```bash
python -m huamei refine data/raw.parquet --workers 500
python -m huamei judge data/raw.parquet
python -m huamei engines
```

---

## Architecture

```
huamei/
  __init__.py            # public API: refine / judge / engines
  api.py                 # unified entry points
  core/
    document.py          # HuameiDoc — one data format for all stages
    engine.py            # engine registry
    pipeline.py          # unified async LLM client + semaphore
    config.py            # config dataclass
    secrets.py           # API keys from environment, never hardcoded
  engines/
    registry.py          # engine registration
  adapters/
    datatrove_adapter.py # MinHash dedup + filters
    dolma_adapter.py     # Gopher/C4 rules, Chinese-specific
  refinery/
    async_tower.py       # async L1 -> L2 -> L3
    diagnostic_judge.py  # 6-dimension diagnosis
    prompts.py           # centralized prompts
  judge/
    anti_ai_rubric.py    # anti-AI-tone judge
  ui/
    panel.py             # instrument-style output
  recipes/               # YAML recipes
  .github/workflows/ci.yml  # secret scan + smoke test
```

---

## Internal engines

| Engine | Source | Capability |
|---|---|---|
| minhash | datatrove | approximate deduplication |
| quality | Dolma | Gopher/C4 quality rules |
| judge | huamei | anti-AI-tone judging |
| refinery | huamei | three-level tower |

---

## Security

- No API keys are stored in the repository. All keys are read from environment variables (see `core/secrets.py` and `.env.example`).
- CI includes a secret-scan job that fails the build if a hardcoded `sk-` key appears anywhere.
- `.env` is gitignored.

---

## Roadmap

See `INNOVATION_ROADMAP.md` for research-grounded next steps, including multi-judge score calibration (DS2), diversity-aware selection, latent-space filtering against model collapse, bandit-based routing, and training-feedback loops.

---

## License

MIT
