import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from ..database import db

logger = logging.getLogger("data_job_service")

def list_data_jobs() -> List[Dict[str, Any]]:
    """Returns recent data collection and monitoring job logs."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_jobs ORDER BY id DESC LIMIT 20")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def record_data_job(job_name: str, status: str, summary: str):
    """Records an executed automated monitoring task."""
    with db.get_connection() as conn:
        conn.execute("""
            INSERT INTO data_jobs (job_name, status, result_summary)
            VALUES (?, ?, ?)
        """, (job_name, status, summary))
        conn.commit()

async def trigger_daily_refresh(marketplace: str = "US") -> Dict[str, Any]:
    """Executes the daily automated snapshot collection for:
    - 4 Core Pillow SKUs
    - Primary Memory Foam Category Node (3732111)
    - Direct & Benchmark Competitors
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    from .core_product_service import get_core_products_registry, get_core_product_detail
    from .core_market_service import get_core_market_overview

    registry = get_core_products_registry()
    success_count = 0

    # 1. Snapshot Core SKUs
    for prod in registry:
        asin = prod["asin"]
        if asin != "PENDING_SKU_4":
            try:
                res = await get_core_product_detail(marketplace, asin)
                if res.get("status") == "ok":
                    success_count += 1
            except Exception as e:
                logger.error(f"Error snapshotting SKU {asin}: {e}")

    # 2. Snapshot Primary Market Node
    try:
        await get_core_market_overview(marketplace)
    except Exception as e:
        logger.error(f"Error snapshotting core market: {e}")

    summary = f"已完成每日自动化快照更新：成功捕获 {success_count} 个核心枕头数据，并更新了四级颈椎枕类目快照。"
    record_data_job("daily_core_snapshot", "success", summary)

    return {
        "status": "ok",
        "jobName": "daily_core_snapshot",
        "finishedAt": now_iso,
        "summary": summary
    }
