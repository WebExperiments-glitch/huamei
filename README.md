# Huamei

[English](#english) · [中文](#中文)

---

<a name="english"></a>
## English

**Huamei is a v0.1 prototype for Chinese dialogue data curation.** It provides a three-level refinery tower and an anti-AI-tone judge behind a single API. It is a research prototype, not a production-ready cleaning tool.

### What it does

`huamei.refine()` reads a parquet file with a `messages` column and runs:

1. **Pre-filter** — MinHash deduplication (datatrove) and Gopher/C4 heuristic rules (Dolma), before any LLM call.
2. **L1 — Accept**: a strict LLM judge decides whether the answer is good as-is → `gold`.
3. **L2 — Diagnose & Repair**: a 6-dimension diagnosis (ai_tone, fabrication, relevance, empathy, naturalness, length) identifies why it failed; a targeted rewrite is generated → `silver`.
4. **L3 — Synthesize**: the original answer is discarded and a fresh one is generated from the question alone → `bronze`.
5. Unsalvageable samples are kept as `rejected` (usable as DPO negatives).

`huamei.judge()` runs strict quality checking only. `huamei.engines()` lists internal engines.

### Honest status (v0.1)

This is a prototype with a complete product narrative but incomplete implementation:

- The LLM tower (judge + refinery) is the main working path. MinHash and Gopher/C4 are wired in as a pre-filter, but **Data-Juicer and NeMo-Curator are downloaded but not integrated** — they are listed in `curation_tools/` for future work, not used at runtime.
- **No automated tests yet.**
- The benchmark in this repo is a single private run on a local dataset. It is **not a reproducible public benchmark** — no seed-controlled public dataset, no baseline, no downstream model evaluation.
- **"100% usable rate" reflects the design of the graded gates, not data quality.** A filter that never rejects is closer to rewriting than cleaning. The rejection rate is the more informative metric.
- Performance numbers (throughput, memory) came from one machine with `tracemalloc` and an asyncio semaphore; both under-report true cost. Treat them as indicative only.
- Only single-turn `messages[1]`/`messages[2]` pairs are supported. Multi-turn, tool calls, and system-prompt variations are not handled.

### What is genuinely useful here

- **Anti-AI-tone rubric** (`judge/anti_ai_rubric.py`): a concrete set of rules for Chinese companion dialogue — ban template phrases, require taking the user's side first, cite concrete details, avoid fabrication. This rubric is the main reusable artifact.
- **6-dimension diagnosis** (`refinery/diagnostic_judge.py`): outputs `failures` + `fix` instead of a bare PASS/FAIL, suitable for a human review queue.
- **Graded judging**: Gold/Silver/Bronze use different strictness, matching the semantics of the grades.

### Install & run

```bash
pip install -r requirements.txt
pip install -e .
export AGNES_API_KEY=sk-...       # or DEEPSEEK_API_KEY
export HUAMEI_PROVIDER=agnes      # default
```

```python
import huamei
report = huamei.refine("data/raw.parquet", workers=200)
report = huamei.judge("data/raw.parquet")
print(huamei.engines())
```

Reproducible benchmark (no hardcoded paths):

```bash
python bench_full.py data/raw.parquet --workers 200 --seed 42
```

### License

MIT

---

<a name="中文"></a>
## 中文

**Huamei 是一个中文对话数据整理的 v0.1 原型。** 它在单一 API 后面提供三级精炼塔和反 AI 腔质检器。这是研究原型，不是可直接用于生产的数据清洗工具。

### 它做什么

`huamei.refine()` 读取含 `messages` 列的 parquet，依次执行：

1. **预过滤** — 先做 MinHash 去重（datatrove）和 Gopher/C4 启发式规则（Dolma），再调用 LLM。
2. **L1 验收** — 严格 judge 判断回答是否合格 → `gold`。
3. **L2 诊断修复** — 6 维诊断（AI 腔、编造、相关性、共情、自然度、长度）定位问题，定向重写 → `silver`。
4. **L3 合成重构** — 丢弃原回答，仅根据问题重新生成 → `bronze`。
5. 无法救回的样本保留为 `rejected`（可作 DPO 负例）。

`huamei.judge()` 只做严格质检。`huamei.engines()` 列出内部引擎。

### 诚实的现状（v0.1）

这是产品叙事完整、但实现尚未跟上的原型：

- LLM 精炼塔（judge + refinery）是主要可用路径。MinHash 和 Gopher/C4 已接入预过滤，但 **Data-Juicer 和 NeMo-Curator 只是下载了、并未集成** —— 它们在 `curation_tools/` 里作为后续工作，运行时不调用。
- **暂无自动化测试。**
- 仓库里的 benchmark 是一次私有数据集上的本地跑分，**不是可复现的公开基准** —— 没有受控种子的公开数据集、没有 baseline、没有下游模型评测。
- **“100% 可用率”是分级闸门设计出来的结果，不代表数据质量。** 一个从不拒绝的过滤器更接近“重写”而非“清洗”。拒绝率才是更有意义的指标。
- 性能指标（吞吐、内存）来自单机 `tracemalloc` 和 asyncio 信号量，都低估了真实开销，仅供参考。
- 仅支持单轮 `messages[1]`/`messages[2]` 对；多轮、工具调用、系统提示变体均不支持。

### 真正有价值的部分

- **反 AI 腔 rubric**（`judge/anti_ai_rubric.py`）：针对中文陪伴对话的具体规则 —— 禁用模板话术、要求先站用户这边、引用具体细节、避免编造。这是最值得复用的产物。
- **6 维诊断**（`refinery/diagnostic_judge.py`）：输出 `failures` + `fix`，而非简单的 PASS/FAIL，适合接入人工复核队列。
- **分级判定**：Gold/Silver/Bronze 采用不同严格度，与等级语义一致。

### 安装与运行

```bash
pip install -r requirements.txt
pip install -e .
export AGNES_API_KEY=sk-...       # 或 DEEPSEEK_API_KEY
export HUAMEI_PROVIDER=agnes      # 默认
```

```python
import huamei
report = huamei.refine("data/raw.parquet", workers=200)
report = huamei.judge("data/raw.parquet")
print(huamei.engines())
```

可复现跑分（无硬编码路径）：

```bash
python bench_full.py data/raw.parquet --workers 200 --seed 42
```

### 许可

MIT
