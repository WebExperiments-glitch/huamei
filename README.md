# Huamei · 话梅

> 像腌制一枚话梅那样，把粗糙的对话数据，反复漂洗、浸渍、晾晒，
> 去掉苦涩，留下酸甜回甘。

**Huamei（话梅）** 是一台对话数据精炼仪——一套覆盖「预训练 / CPT / SFT / RL」全阶段的统一数据清洗系统。

## 为什么叫话梅

- **说书先生含话梅润口才能继续说下去** → 我们精炼的是**对话（话）数据**
- **腌制去涩、反复晾晒，留下酸甜精华** → 数据清洗：去杂质、留精华
- **酸甜咸甘四味** → 数据的多维度质量（6 维诊断）
- **生津止渴、值得回味** → 让数据"值得回味"

## 核心创新

1. **三级精炼塔**：L1 严格验收 → L2 诊断修复 → L3 合成重构，失败品转 DPO 负例
2. **分级验收**：Gold/Silver/Bronze 用不同严格度，符合质量分级本意
3. **反 AI 腔质检**：独家 rubric，专治「我太懂你这种感觉了」式套话
4. **中文特化**：解决英文清洗工具对中文全部误杀的问题
5. **内外一体的仪器化封装**：7 个开源工具隐藏为引擎舱，对外只有一个 `huamei`
6. **低内存异步引擎**：统一 LLM 客户端 + 信号量，43MB 内存

## Benchmark（v0.1，全量 529 条）

| 指标 | 数值 |
|---|---:|
| 速度 | **5.7 样本/秒**（500 并发）|
| 内存峰值 | **43.9 MB** |
| 🟡 Gold（L1 直接通过）| 327 (62%) |
| ⚪ Silver（L2 诊断修复）| 201 (38%) |
| 🔵 Bronze（L3 合成重构）| 1 |
| ⚫ Rejected | 0 |
| **可用率** | **100%** |

> 全程使用 Agnes 免费 API，零成本。

## 快速开始

```python
import huamei

# 三级精炼（对外只有这一个动作）
report = huamei.refine("data/raw.parquet")

# 纯质检
report = huamei.judge("data/raw.parquet")

# 查看内部引擎舱
print(huamei.engines())
```

```bash
# CLI
python -m huamei refine data/raw.parquet --workers 500
python -m huamei judge data/raw.parquet
```

## 架构

```
huamei/                    # 对外：一台仪器
  __init__.py              # 统一 API: refine / judge / engines
  api.py                   # 统一入口
  core/                    # 内核
    document.py            # 统一数据单元 HuameiDoc
    engine.py              # 引擎注册表
    pipeline.py            # 统一异步 LLM 客户端
    config.py              # 统一配置
  engines/                 # 引擎舱（内部，7个工具藏在这里）
    registry.py
  adapters/                # 工具适配器
    datatrove_adapter.py   # MinHash 去重
    dolma_adapter.py       # Gopher/C4（中文特化）
  refinery/                # ⭐ 三级精炼塔
    async_tower.py         # 异步 L1→L2→L3
    diagnostic_judge.py    # 6维诊断
    prompts.py             # 校准参数（集中管理）
  judge/
    anti_ai_rubric.py      # 反 AI 腔 judge
  ui/panel.py              # 仪表盘输出
  recipes/                 # YAML 配方
```

## 引擎舱（内部）

| 引擎 | 来源 | 能力 |
|---|---|---|
| minhash | datatrove | 近似去重 |
| quality | dolma | Gopher/C4 质量规则 |
| judge | huamei | 反 AI 腔质检 |
| refinery | huamei | 三级精炼 |

## 路线图

见 `INNOVATION_ROADMAP.md` —— 基于 2026 前沿调研（DS2 多样性校正、LSF 防坍塌、自适应选择、影响函数等）。
