import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .database import db

logger = logging.getLogger("scheduler")

# Background Scheduler for Daily 08:30 Snapshot (Asia/Shanghai)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

def start_scheduler():
    """Initializes and starts the daily scheduled snapshot task."""
    from .services.data_job_service import trigger_daily_refresh
    try:
        scheduler.add_job(
            trigger_daily_refresh,
            CronTrigger(hour=8, minute=30, timezone="Asia/Shanghai"),
            id="daily_amazon_snapshot",
            name="Daily Amazon Ops Snapshot (08:30 CST)",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600
        )
        if not scheduler.running:
            scheduler.start()
        logger.info("[SCHEDULER] Daily snapshot job scheduled for 08:30 CST. Running: True")
    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to start scheduler: {e}")

def stop_scheduler():
    """Stops the scheduler safely."""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("[SCHEDULER] Scheduler shut down.")
    except Exception as e:
        logger.warning(f"[SCHEDULER] Error shutting down scheduler: {e}")

def get_live_scheduler_status() -> Dict[str, Any]:
    """Dynamically inspects live scheduler state, job next run time, and real DB monitored entities.
    Strictly factual, ZERO hardcoding.
    """
    is_running = scheduler.running
    job = scheduler.get_job("daily_amazon_snapshot") if is_running else None
    
    next_run_str = None
    if job and job.next_run_time:
        next_run_str = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S (北京时间)")
    else:
        # Fallback calculation if scheduler is not running
        now = datetime.now(timezone.utc)
        beijing_now = now + timedelta(hours=8)
        target_today = beijing_now.replace(hour=8, minute=30, second=0, microsecond=0)
        if beijing_now >= target_today:
            next_target = target_today + timedelta(days=1)
        else:
            next_target = target_today
        next_run_str = next_target.strftime("%Y-%m-%d 08:30:00 (北京时间)")

    # Real counts from database
    target_stats = db.count_real_monitored_targets()

    # Query last job record from data_jobs table
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM data_jobs ORDER BY id DESC LIMIT 1")
        last_row = c.fetchone()

    last_job = dict(last_row) if last_row else None
    details = {}
    if last_job and last_job.get("details_json"):
        try:
            import json
            details = json.loads(last_job["details_json"])
        except Exception:
            details = {}

    last_status = last_job.get("status") if last_job else "never"
    last_success = last_job.get("items_success", 0) if last_job else 0
    last_failed = last_job.get("items_failed", 0) if last_job else 0

    return {
        "isSchedulerActive": bool(is_running),
        "cronSchedule": "08:30 CST",
        "scheduleTime": "每天 08:30 (北京时间)",
        "nextRunAt": next_run_str,
        "nextRunTime": next_run_str,
        "monitoredTargetsCount": target_stats["total"],
        "targetBreakdown": target_stats,
        "confirmedCompetitorsCount": target_stats["directCompetitorsCount"],
        "lastRunStatus": last_status,
        "lastRunDurationSeconds": last_job.get("duration_seconds", 0.0) if last_job else 0.0,
        "lastRunItemsSuccess": last_success,
        "lastRunItemsFailed": last_failed,
        "lastRun": {
            "status": last_status,
            "runAt": last_job.get("run_at") if last_job else None,
            "durationSeconds": last_job.get("duration_seconds", 0.0) if last_job else 0.0,
            "itemsTotal": last_job.get("items_total", 0) if last_job else 0,
            "itemsSuccess": last_success,
            "itemsFailed": last_failed,
            "summary": last_job.get("result_summary") if last_job else "尚无执行记录，请点击上方立即采集",
            "details": details
        }
    }
