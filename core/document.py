r"""统一数据单元 —— 所有阶段、所有引擎之间流动的唯一格式。

像精密仪器的标准接口：不管内部引擎用什么格式，进来出去都是 HuameiDoc。
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HuameiDoc:
    """Unified data unit for all stages."""
    text: str
    id: str = ""
    source: str = ""
    messages: list[dict] | None = None       # 对话数据
    metadata: dict[str, Any] = field(default_factory=dict)
    grade: str | None = None                  # gold/silver/bronze/rejected

    @classmethod
    def from_text(cls, text: str, **kw):
        return cls(text=text, **kw)

    @classmethod
    def from_messages(cls, messages: list[dict], **kw):
        text = "\n".join(m.get("content", "") for m in messages)
        return cls(text=text, messages=messages, **kw)

    def to_dict(self) -> dict:
        d = {"text": self.text, "id": self.id, "source": self.source,
             "metadata": self.metadata, "grade": self.grade}
        if self.messages:
            d["messages"] = self.messages
        return d
