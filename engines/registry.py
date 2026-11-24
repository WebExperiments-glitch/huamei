r"""构建引擎注册表 —— 启动时探测哪些工具可用。"""
import sys
from pathlib import Path
from ..core.engine import EngineRegistry, EngineInfo, Engine


class MinHashEngine(Engine):
    """内部：datatrove 的 MinHash 去重。"""
    info = EngineInfo("minhash", "datatrove", "近似去重", True)

    def __init__(self):
        self._impl = None

    def run(self, data, **params):
        if self._impl is None:
            from ..adapters.datatrove_adapter import MinHashDeduplicator
            self._impl = MinHashDeduplicator()
        return self._impl.is_duplicate(data, **params)


class QualityEngine(Engine):
    """内部：Dolma Gopher/C4 质量规则。"""
    info = EngineInfo("quality", "dolma", "质量打分", True)

    def run(self, data, **params):
        from ..adapters.dolma_adapter import passes_gopher, passes_c4
        return {"gopher": passes_gopher(data), "c4": passes_c4(data)}


class JudgeEngine(Engine):
    """内部：LLM-as-judge（反 AI 腔）。"""
    info = EngineInfo("judge", "huamei", "反AI腔质检", True)

    def run(self, data, **params):
        from ..judge.anti_ai_rubric import judge_one
        q, a = data
        return judge_one(q, a)


class RefineryEngine(Engine):
    """内部：三级精炼塔。"""
    info = EngineInfo("refinery", "huamei", "三级精炼", True)

    def run(self, data, **params):
        from ..refinery import Refinery
        return Refinery().refine(data)


def build_registry() -> EngineRegistry:
    reg = EngineRegistry()
    reg.register(MinHashEngine())
    reg.register(QualityEngine())
    reg.register(JudgeEngine())
    reg.register(RefineryEngine())
    return reg

