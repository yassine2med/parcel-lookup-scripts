"""Command line interface."""
from __future__ import annotations

import argparse
import sys

from . import core


def _table(parcels: list[core.Parcel]) -> str:
    lines = [f"{'ID':<7} {'Address':<22} {'Owner':<24} {'Zone':<5} {'Sqft':>6} {'$/sqft':>7}"]
    for p in parcels:
        lines.append(f"{p.parcel_id:<7} {p.address:<22} {p.owner:<24} {p.zoning:<5} "
                     f"{p.lot_sqft:>6} {p.value_per_sqft:>7.2f}")
    lines.append(f"{len(parcels)} parcel(s)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the tool and return an exit code."""
    parser = argparse.ArgumentParser(prog="parcel_lookup", description="Query a parcel CSV extract.")
    parser.add_argument("--data", default="data/parcels.csv", help="parcel CSV (default data/parcels.csv)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("id", help="show one parcel")
    one.add_argument("parcel_id")
    find = sub.add_parser("search", help="filter parcels")
    find.add_argument("text", nargs="?", default="")
    find.add_argument("--zoning", default="")
    find.add_argument("--min-sqft", type=int, default=0)
    sub.add_parser("summary", help="totals per zoning district")
    args = parser.parse_args(argv)
    try:
        parcels = core.load(args.data)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.cmd == "id":
        p = core.by_id(parcels, args.parcel_id)
        if p is None:
            print(f"no parcel {args.parcel_id}", file=sys.stderr)
            return 1
        print(_table([p]))
    elif args.cmd == "search":
        print(_table(core.search(parcels, args.text, args.zoning, args.min_sqft)))
    else:
        print(f"{'Zone':<6}{'Parcels':>8}{'Acres':>9}{'$/sqft':>9}")
        for zone, s in core.summary(parcels).items():
            print(f"{zone:<6}{int(s['count']):>8}{s['acres']:>9.2f}{s['value_per_sqft']:>9.2f}")
    return 0
