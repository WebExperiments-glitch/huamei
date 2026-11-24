r"""python -m huamei 入口。"""
import argparse
from .ui.panel import banner


def main():
    p = argparse.ArgumentParser(prog="huamei", description="Huamei · 话梅数据精炼仪")
    sub = p.add_subparsers(dest="cmd")
    rp = sub.add_parser("refine", help="三级精炼")
    rp.add_argument("parquet")
    rp.add_argument("--workers", type=int, default=500)
    rp.add_argument("--output", default=None)
    jp = sub.add_parser("judge", help="严格质检")
    jp.add_argument("parquet")
    sub.add_parser("engines", help="查看引擎舱")
    args = p.parse_args()

    if args.cmd == "refine":
        from .api import refine
        refine(args.parquet, output=args.output, workers=args.workers)
    elif args.cmd == "judge":
        from .api import judge
        judge(args.parquet)
    elif args.cmd == "engines":
        import huamei
        print(banner())
        print(huamei.engines())
    else:
        p.print_help()


if __name__ == "__main__":
    main()
