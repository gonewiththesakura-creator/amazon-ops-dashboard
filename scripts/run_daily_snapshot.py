#!/usr/bin/env python
"""
Standalone Runner Script for Daily Automated Snapshot.
Can be executed directly via Windows Task Scheduler or crontab.
"""
import os
import sys
import asyncio

# Ensure project root is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.config import settings
from backend.services.data_job_service import trigger_daily_refresh

async def main():
    print("=" * 65)
    print("  [*] Amazon AI Opportunity Intelligence - Scheduled Daily Snapshot")
    print("=" * 65)
    try:
        res = await trigger_daily_refresh("US")
        print(f"Status: {res.get('jobStatus')}")
        print(f"Summary: {res.get('summary')}")
        print(f"Duration: {res.get('durationSeconds')}s")
        print("  [SUCCESS] Daily snapshot finished.")
    except Exception as e:
        print(f"  [ERROR] Daily snapshot failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
