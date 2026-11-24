# Contributing

Contributions to Huamei are welcome.

## Development setup

```bash
git clone <repo>
cd huamei
pip install -r requirements.txt
pip install -e .
```

## Project structure

- `core/` — kernel (unified data unit, engine registry, async LLM client, config)
- `refinery/` — three-level refinery tower (core innovation)
- `judge/` — anti-AI-tone judge
- `adapters/` — internal tool adapters (datatrove / dolma)
- `engines/` — engine registration
- `ui/` — instrument-style output
- `recipes/` — YAML recipes

## Development principles

1. **Unified surface**: expose only `huamei.refine()` / `judge()` / `engines()`. Internal tools (datatrove, dolma, etc.) must stay wrapped under `adapters/` or `engines/` — users never touch them directly.
2. **Centralized prompts**: keep all prompts in `refinery/prompts.py` or `judge/anti_ai_rubric.py`. Do not scatter them. Lesson learned: duplicated prompt definitions once caused judge inconsistency and zero pass rates.
3. **Graded judging**: Gold / Silver / Bronze intentionally use different strictness. Do not collapse them into a single standard — that breaks recovery.
4. **Free-tier friendly**: default provider is the free Agnes tier. When switching providers, update both `core/pipeline.py` and `judge/anti_ai_rubric.py`.
5. **Low memory**: use the async client + semaphore; avoid heavy dependencies.

## Adding a new engine

1. Write an adapter under `adapters/` (subclass `core.engine.Engine`).
2. Register it in `engines/registry.py`.
3. Add a row to the engine table in `README.md`.

## Pre-submit checks

```bash
python -m huamei engines          # engine bay loads
python huamei/bench_full.py       # benchmark runs
```

## Roadmap

See `INNOVATION_ROADMAP.md`. Pick any item and open a PR.
