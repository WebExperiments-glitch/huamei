r"""仪表盘 —— 精美仪器的门面。所有输出经过这里，统一视觉。"""

W = 56


def banner(version="0.1.0"):
    return f"""╔{'═'*W}╗
║  {'HUAMEI · 话梅数据精炼仪':<{W-4}}║
║  {'Data Refinery · v'+version:<{W-4}}║
╚{'═'*W}╝"""


def section(title: str) -> str:
    return f"\n┌─ {title} {'─'*(W-len(title)-4)}┐"


def close() -> str:
    return f"└{'─'*W}┘"


def row(label: str, value: str, marker: str = "") -> str:
    return f"│  {marker} {label:<{W-6}} {value:>10} │"


def bar(label: str, value: float, total: float, width=30) -> str:
    pct = value / max(total, 1)
    filled = int(width * pct)
    return f"│  {label:<12} {'█'*filled}{'░'*(width-filled)} {pct*100:5.1f}% │"


def grade_marker(grade: str) -> str:
    return {"gold": "🟡", "silver": "⚪", "bronze": "🔵", "rejected": "⚫"}.get(grade, "·")


def report_panel(report: dict) -> str:
    lines = [section("精炼报告 / REFINERY REPORT")]
    lines.append(row("输入样本", str(report.get("total", 0))))
    lines.append(row("🟡 Gold", str(report.get("gold", 0))))
    lines.append(row("⚪ Silver", str(report.get("silver", 0))))
    lines.append(row("🔵 Bronze", str(report.get("bronze", 0))))
    lines.append(row("⚫ DPO负例", str(report.get("rejected_dpo_negatives", 0))))
    lines.append(bar("可用率", report.get("usable_rate", 0) * report.get("total", 1), report.get("total", 1)))
    lines.append(close())
    return "\n".join(lines)


def engine_panel(infos) -> str:
    lines = [section("引擎舱 / ENGINE BAY")]
    for i in infos:
        mark = "●" if i.available else "○"
        lines.append(f"│  {mark} {i.name:<14} {i.vendor:<12} {i.capability:<16}│")
    lines.append(close())
    return "\n".join(lines)
