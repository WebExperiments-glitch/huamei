r"""Huamei — a unified data refinery for language models.

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
