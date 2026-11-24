r"""密钥管理 —— 所有 API key 从环境变量读取，绝不硬编码。

用法：
    export AGNES_API_KEY=sk-xxx
    export DEEPSEEK_API_KEY=sk-xxx

或 .env 文件（已被 .gitignore 忽略）：
    AGNES_API_KEY=sk-xxx
    DEEPSEEK_API_KEY=sk-xxx
"""
import os
from pathlib import Path


def _load_dotenv():
    """轻量 .env 加载（不引入额外依赖）。"""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[1] / ".env",  # huamei/ 包目录
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"\''))


_load_dotenv()


def get_key(provider: str) -> str:
    """获取对应 provider 的 API key。"""
    env_map = {
        "agnes": "AGNES_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    env_name = env_map.get(provider)
    if not env_name:
        raise ValueError(f"未知 provider: {provider}")
    key = os.environ.get(env_name)
    if not key:
        raise RuntimeError(
            f"缺少环境变量 {env_name}。请设置：\n"
            f"  export {env_name}=sk-xxx\n"
            f"或写入 .env 文件（见 .env.example）"
        )
    return key
