#!/usr/bin/env python3
"""
CLI runner for scheduled jobs.

Usage examples:
  # List all registered scheduled jobs
  python scripts/run_job.py --list

  # Run a specific job immediately
  python scripts/run_job.py update_public_stats

  # Run all registered jobs sequentially
  python scripts/run_job.py --all
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import db
from app.core.redis import redis_client
from app.schedulers import get_all_jobs, run_job_by_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_job")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or inspect scheduled jobs")
    parser.add_argument("job_name", nargs="?", help="Name of the job to execute")
    parser.add_argument("--list", action="store_true", help="List all registered jobs")
    parser.add_argument("--all", action="store_true", help="Run all registered jobs")
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    jobs = get_all_jobs()

    if args.list:
        print("\nRegistered Scheduled Jobs:")
        print("─" * 60)
        for name, job in jobs.items():
            print(f"  • {name:<25} {job.description}")
        print("─" * 60)
        print(f"Total: {len(jobs)} job(s)\n")
        return 0

    # Ensure DB & Redis are ready
    db.connect()
    try:
        await redis_client.connect()
    except Exception as e:
        logger.warning("Redis could not be connected: %s", e)

    try:
        if args.all:
            print(f"Running all {len(jobs)} registered job(s)...")
            has_failure = False
            for name in jobs:
                print(f"\n▶ Executing: {name}")
                res = await run_job_by_name(name)
                print(f"Result: {json.dumps(res, default=str, indent=2)}")
                if res.get("status") == "failed":
                    has_failure = True
            return 1 if has_failure else 0

        if not args.job_name:
            print("Error: Specify a job name or use --list / --all", file=sys.stderr)
            return 1

        if args.job_name not in jobs:
            print(f"Error: Job '{args.job_name}' not found.", file=sys.stderr)
            print(f"Available jobs: {list(jobs.keys())}", file=sys.stderr)
            return 1

        print(f"▶ Executing job: {args.job_name}")
        res = await run_job_by_name(args.job_name)
        print(f"\nResult: {json.dumps(res, default=str, indent=2)}")
        return 0 if res.get("status") != "failed" else 1

    finally:
        await db.disconnect()
        if redis_client.client:
            await redis_client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

