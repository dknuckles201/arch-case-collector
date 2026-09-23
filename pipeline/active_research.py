"""Generate Phase 5 active research priorities and incremental queries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research_loop import generate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path, help="Phase 4 batch directory")
    parser.add_argument("--max-queries", type=int, default=40)
    parser.add_argument("--max-fetches", type=int, default=24)
    parser.add_argument("--max-review-minutes", type=int, default=180)
    args = parser.parse_args()
    if args.max_queries < 0 or args.max_fetches < 0 or args.max_review_minutes < 0:
        parser.error("budgets must be non-negative")
    priorities, queries, budget = generate(
        args.batch,
        max_queries=args.max_queries,
        max_fetches=args.max_fetches,
        max_review_minutes=args.max_review_minutes,
    )
    print(f"priorities={len(priorities)} queries={len(queries)} allocated_queries={budget['allocated_queries']}")
    print(f"human_review_required={sum(1 for row in priorities if row['requires_human_review'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
