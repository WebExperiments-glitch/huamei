r"""Huamei（话梅）— 对话数据精炼仪。

像腌制一枚话梅那样，把粗糙的对话数据，反复漂洗、浸渍、晾晒，
去掉苦涩，留下酸甜回甘。

    import huamei
    huamei.refine("data/raw.parquet")
"""
__version__ = "0.1.0"

from .core.document import HuameiDoc
from .core.config import HuameiConfig
from .engines.registry import build_registry
from .ui.panel import banner, report_panel, engine_panel


def refine(path: str, **kwargs):
    """统一入口：三级精炼。"""
    from .api import refine as _refine
    return _refine(path, **kwargs)


def judge(path: str, **kwargs):
    """统一入口：质检。"""
    from .api import judge as _judge
    return _judge(path, **kwargs)


def engines():
    """查看内部引擎舱。"""
    return engine_panel(build_registry().list())


__all__ = ["refine", "judge", "engines", "HuameiDoc", "HuameiConfig", "__version__"]
