# 贡献指南

欢迎给 Huamei（话梅）添砖加瓦。

## 开发设置

```bash
git clone <repo>
cd huamei
pip install -r requirements.txt
pip install -e .
```

## 项目结构速览

- `core/` — 内核（统一数据单元、引擎注册表、异步 LLM 客户端、配置）
- `refinery/` — 三级精炼塔（核心创新）
- `judge/` — 反 AI 腔质检
- `adapters/` — 内部工具适配器（datatrove / dolma）
- `engines/` — 引擎舱注册表
- `ui/` — 仪表盘输出

## 开发原则

1. **内外一体**：对外只暴露 `huamei.refine()` / `judge()` / `engines()`。内部工具（datatrove/dolma 等）必须封装在 `adapters/` 或 `engines/` 里，用户永远不直接接触
2. **Prompt 集中管理**：所有 prompt 放 `refinery/prompts.py` 或 `judge/anti_ai_rubric.py`，不要散落。历史教训：prompt 多处定义曾导致 judge 不一致、结果全灭
3. **分级验收**：Gold/Silver/Bronze 用不同严格度，这是设计本意，不要统一成一个标准
4. **免费优先**：默认 provider 用 Agnes 免费池；换 provider 要在 `core/pipeline.py` 和 `judge/anti_ai_rubric.py` 同步
5. **低内存**：用异步客户端 + 信号量，不要引入重型依赖

## 添加新引擎

1. 在 `adapters/` 写适配器（继承 `core.engine.Engine`）
2. 在 `engines/registry.py` 注册
3. 在 `README.md` 引擎舱表格里加一行

## 提交前检查

```bash
python -m huamei engines          # 引擎舱正常
python huamei/bench_full.py       # benchmark 跑通
```

## 路线图

见 `INNOVATION_ROADMAP.md`。欢迎认领其中的创新点。
