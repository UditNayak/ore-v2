"""CLI for the evaluation harness.

Examples:
  python -m app.eval.run_eval --limit 1 --fresh        # quick check (low token use)
  python -m app.eval.run_eval --fresh --delay 8        # full run, paced for Groq free tier
"""

import argparse
import asyncio

from app.core.logging import configure_logging
from app.eval.runner import run_eval


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ORE evaluation harness.")
    parser.add_argument("--limit", type=int, default=None, help="run only the first N scenarios")
    parser.add_argument("--scenario", type=str, default=None, help="run only this scenario id")
    parser.add_argument(
        "--delay", type=float, default=0.0, help="seconds to wait between scenarios (free-tier TPM)"
    )
    parser.add_argument(
        "--fresh", action="store_true", help="clear learning events first (clean V1 baseline)"
    )
    args = parser.parse_args()

    configure_logging("INFO")
    summary = asyncio.run(
        run_eval(limit=args.limit, scenario_id=args.scenario, delay=args.delay, fresh=args.fresh)
    )

    print("\n=== Evaluation summary ===")
    for key, value in summary.items():
        if key != "targets":
            print(f"  {key}: {value}")
    print("  targets:")
    for name, ok in summary["targets"].items():
        mark = "—" if ok is None else ("PASS" if ok else "FAIL")
        print(f"    {name}: {mark}")
    print("\nReport written to eval_results/latest.md")


if __name__ == "__main__":
    main()
