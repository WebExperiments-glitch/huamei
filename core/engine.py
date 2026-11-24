r"""引擎舱 —— 7 个开源工具被封装成统一接口，对外不可见。

每个引擎实现 Engine 接口：name / capabilities / run。
 orchestrator 按配方调度，用户只看到 huamei 的统一流程。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EngineInfo:
    name: str
    vendor: str
    capability: str
    available: bool = True


class Engine(ABC):
    info: EngineInfo

    @abstractmethod
    def run(self, data: Any, **params) -> Any:
        ...


class EngineRegistry:
    """引擎注册表：统一管理所有内部工具。"""

    def __init__(self):
        self._engines: dict[str, Engine] = {}

    def register(self, engine: Engine):
        self._engines[engine.info.name] = engine

    def get(self, name: str) -> Engine:
        if name not in self._engines:
            raise KeyError(f"未注册的引擎: {name}。可用: {list(self._engines)}")
        return self._engines[name]

    def list(self) -> list[EngineInfo]:
        return [e.info for e in self._engines.values()]

    def status(self) -> str:
        lines = ["  ENGINE BAY / 引擎舱", "  " + "-" * 40]
        for e in self.list():
            mark = "●" if e.available else "○"
            lines.append(f"  {mark} {e.name:<16} {e.vendor:<12} {e.capability}")
        return "\n".join(lines)


_registry = EngineRegistry()


def get_registry() -> EngineRegistry:
    return _registry
