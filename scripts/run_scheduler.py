#!/usr/bin/env python3
"""
Standalone scheduler daemon process.

Used in production when you want a dedicated worker/container for running scheduled jobs
isolated from the web servers (ENABLE_SCHEDULER=False on web servers).

Usage:
  python scripts/run_scheduler.py
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import db
from app.core.redis import redis_client
from app.schedulers import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scheduler_daemon")


async def main():
    logger.info("Starting standalone scheduler daemon...")
    db.connect()

    try:
        await redis_client.connect()
    except Exception as e:
        logger.warning("Redis could not be connected: %s", e)

    start_scheduler()
    logger.info("Scheduler daemon is active. Press Ctrl+C to terminate.")

    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("Termination signal received. Stopping scheduler daemon...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows fallback
            pass

    try:
        await stop_event.wait()
    finally:
        stop_scheduler(wait=True)
        await db.disconnect()
        if redis_client.client:
            await redis_client.close()
        logger.info("Scheduler daemon stopped cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass

