"""Inspect isolated failure modes using the supplied variant factory."""

import argparse

from lab8.shapes import SHAPES
from lab9.trace_case import main as trace_main
from lab9.variant_agent import make_shape


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bug",
        required=True,
        choices=["stale_clause", "sibling_refund"],
    )
    parser.add_argument("--claim", required=True)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()

    name = f"inspect_{args.bug}"
    SHAPES[name] = make_shape(name, {"no_override", args.bug})

    return trace_main([
        "--shape", name,
        "--claim", args.claim,
        "--seed", str(args.seed),
    ])


if __name__ == "__main__":
    raise SystemExit(main())