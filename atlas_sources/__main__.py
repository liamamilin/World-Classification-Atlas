import argparse
from pathlib import Path
from .registry import load, validate


def main():
    parser = argparse.ArgumentParser(description="World Classification Atlas source registry and local collection")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    collect = sub.add_parser("collect")
    collect.add_argument("--resource", action="append", help="repeat to select resource IDs; default all")
    collect.add_argument("--refresh", action="store_true", help="fetch and detect upstream byte changes")
    collect.add_argument("--freeze", action="store_true", help="pin only previously unpinned successful snapshots")
    sub.add_parser("verify")
    sub.add_parser("normalize")
    sub.add_parser("report")
    sub.add_parser("discover")
    sub.add_parser("audit")
    sub.add_parser("economy", help="enrich ISIC4/5 and parse official correspondence into local research outputs")
    sub.add_parser("reproduce-economy", help="rebuild ISIC in a fresh directory from pinned inputs and compare bytes offline")
    sub.add_parser("furniture", help="align the furniture branch across NACE and both ISIC editions")
    sub.add_parser("reproduce-furniture", help="rebuild furniture research from pinned originals offline")
    sub.add_parser("cpc", help="build the offline CPC 3.0 source catalogue from pinned originals")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(error)
        return 1
    registry, resources = load(root)
    if args.command == "validate":
        print(f"Valid: {len(registry['sources'])} sources, {len(registry['domains'])} domains, {len(resources)} resources")
        return 0
    if args.command == "collect":
        from .acquire import collect as run
        if args.resource:
            unknown = set(args.resource) - {r['id'] for r in resources}
            if unknown:
                parser.error(f"unknown resources: {sorted(unknown)}")
            resources = [r for r in resources if r['id'] in args.resource]
        result = run(root, resources, args.refresh, args.freeze)
        # A documented permission block is not a transport failure.
        return int(any(r['status'] in ('failed', 'drift') for r in result))
    if args.command in ("verify", "normalize"):
        from .normalize import process
        return process(root, resources, write=args.command == "normalize")
    if args.command == "report":
        from .report import build
        build(root, registry, resources)
    if args.command == "discover":
        from .discover import discover
        return discover(root)
    if args.command == "audit":
        from .audit import audit
        return audit(root, registry)
    if args.command == "economy":
        from .isic import run
        return run(root, resources)
    if args.command == "reproduce-economy":
        from .isic_reproduce import reproduce
        return reproduce(root, resources)
    if args.command == "furniture":
        from .furniture import run
        return run(root, resources)
    if args.command == "reproduce-furniture":
        from .furniture import reproduce
        return reproduce(root, resources)
    if args.command == "cpc":
        from .cpc import run
        return run(root, resources)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
