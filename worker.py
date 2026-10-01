"""
worker.py

Dedicated Background Scheduler Worker.
Runs the Tender Monitoring & Synchronization job on a scheduled interval
without blocking web requests.

Usage:
    python worker.py
"""

import os
import time
import signal
import sys
import schedule
from dotenv import load_dotenv

load_dotenv()

from main import main
from config import logger

# Configurable interval in hours (default: every 6 hours)
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
RUN_ON_STARTUP = os.getenv("RUN_ON_STARTUP", "true").lower() in ("true", "1", "yes")

running = True


def signal_handler(signum, frame):
    global running
    print("\nReceived termination signal. Gracefully stopping scheduler worker...")
    logger.info("Worker received stop signal.")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def scheduled_job():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled tender monitoring job...")
    logger.info("Starting scheduled tender monitoring job via worker...")
    try:
        result = main()
        logger.info(f"Scheduled tender monitoring completed: {result}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Job completed successfully: {result}")
    except Exception as e:
        logger.exception(f"Scheduled tender monitoring failed: {e}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Job failed: {e}")


def start_worker():
    print("=" * 70)
    print("      Tender Monitoring Background Scheduler Worker")
    print(f"      Scheduled Interval: Every {SCRAPE_INTERVAL_HOURS} hour(s)")
    print("=" * 70)

    # Schedule the recurring job
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(scheduled_job)

    # Run on startup if configured
    if RUN_ON_STARTUP:
        print("Running initial tender check on worker startup...")
        scheduled_job()

    print(f"Worker is active and listening for scheduled triggers. Press Ctrl+C to stop.\n")

    while running:
        schedule.run_pending()
        time.sleep(1)

    print("Worker stopped.")
    sys.exit(0)


if __name__ == "__main__":
    start_worker()
