r"""统一配置 —— 一份配方管全程，像仪器的控制面板。"""
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class HuameiConfig:
    """话梅精炼配方。"""
    name: str = "default"
    input_path: str = ""
    output_path: str = ""
    # 引擎选择（对外表现为"工艺强度"等语义化参数）
    stage: str = "sft"                # pretrain / cpt / sft / rl
    strength: str = "normal"          # gentle / normal / strict
    grade_output: bool = True         # 是否分级输出
    reuse_dpo: bool = True            # 失败样本转 DPO 负例
    workers: int = 200
    judge_rounds: int = 2
    api_provider: str = "deepseek"
    recipe: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path):
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(
            name=raw.get("name", "default"),
            input_path=raw.get("input", {}).get("path", ""),
            output_path=raw.get("output", {}).get("path", ""),
            stage=raw.get("stage", "sft"),
            strength=raw.get("strength", "normal"),
            workers=raw.get("runtime", {}).get("workers", 200),
            recipe=raw,
        )
