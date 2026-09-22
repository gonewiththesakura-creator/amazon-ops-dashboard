import json
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional
from .database import db

logger = logging.getLogger("repository")

class DataRepository:
    """Local-first Data Repository pattern for Amazon Ops Intelligence.
    Ensures local SQLite acts as the primary asset, external MCP is the provider.
    """

    def is_asin_fresh(self, asin: str, max_hours: float = 24.0) -> bool:
        """Checks if local database has a fresh snapshot within max_hours."""
        snap = db.get_latest_asin_snapshot(asin)
        if not snap or not snap.get("fetched_at"):
            return False
        try:
            fetched_dt = datetime.fromisoformat(str(snap["fetched_at"]).replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            return (now_dt - fetched_dt).total_seconds() < (max_hours * 3600)
        except Exception:
            return False

    def get_local_asin_summary(self, asin: str) -> Optional[Dict[str, Any]]:
        """Retrieves latest snapshot and time-series history directly from local warehouse."""
        snap = db.get_latest_asin_snapshot(asin)
        if not snap:
            return None

        prices = db.get_price_history(asin)
        bsrs = db.get_bsr_history(asin)

        return {
            "asin": asin,
            "price": snap.get("price"),
            "estimated_units": snap.get("estimated_units"),
            "estimated_revenue": snap.get("estimated_revenue"),
            "bsr": snap.get("bsr"),
            "rating": snap.get("rating"),
            "reviews": snap.get("reviews"),
            "coupon": snap.get("coupon"),
            "source": snap.get("source") or "local_warehouse",
            "snapshot_date": snap.get("snapshot_date"),
            "fetched_at": snap.get("fetched_at"),
            "priceHistory": prices,
            "bsrHistory": bsrs
        }

    def persist_asin_full_sync(
        self,
        asin: str,
        price: Optional[float],
        units: Optional[int],
        revenue: Optional[float],
        bsr: Optional[int],
        rating: Optional[float],
        reviews: Optional[int],
        coupon: Optional[str] = None,
        price_points: Optional[List[Dict[str, Any]]] = None,
        bsr_points: Optional[List[Dict[str, Any]]] = None,
        sales_points: Optional[List[Dict[str, Any]]] = None,
        source: str = "sellersprite_mcp"
    ):
        """Persists current snapshot and backfills historical time-series into SQLite."""
        now_iso = datetime.now(timezone.utc).isoformat()
        today_str = date.today().isoformat()

        # 1. Snapshot
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO asin_snapshots (
                    asin, snapshot_date, price, estimated_units, estimated_revenue, bsr, rating, reviews, coupon, source, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (asin, today_str, price, units, revenue, bsr, rating, reviews, coupon, source, now_iso))
            conn.commit()

        # 2. Backfill historical time series
        if price_points:
            db.batch_insert_price_history(asin, price_points, source="keepa")
        if bsr_points:
            db.batch_insert_bsr_history(asin, bsr_points, source="keepa")
        if sales_points:
            db.batch_insert_sales_history(asin, sales_points, source="sellersprite_mcp")

        # 3. Archive audit trail into mcp_raw_responses
        try:
            audit_payload = {
                "asin": asin,
                "price": price,
                "units": units,
                "revenue": revenue,
                "bsr": bsr,
                "rating": rating,
                "reviews": reviews,
                "price_points_count": len(price_points or []),
                "bsr_points_count": len(bsr_points or []),
                "sales_points_count": len(sales_points or [])
            }
            db.archive_raw_response(
                tool_name="warehouse_full_sync",
                request_json=json.dumps({"asin": asin}, ensure_ascii=False),
                response_json=json.dumps(audit_payload, ensure_ascii=False),
                entity_type="asin",
                entity_id=asin,
                verification_status="verified"
            )
        except Exception as ex:
            logger.warning(f"Failed to record warehouse sync audit: {ex}")

        logger.info(f"[WAREHOUSE] Successfully synced & archived full dataset for ASIN {asin}")

    def get_data_traceability(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Returns traceability metadata for any entity (source, tool, timestamp)."""
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT tool_name, fetched_at, verification_status 
                FROM mcp_raw_responses 
                WHERE entity_id = ? 
                ORDER BY fetched_at DESC LIMIT 1
            """, (entity_id,))
            row = c.fetchone()
            if row:
                return {
                    "source": "SellerSprite MCP Official",
                    "tool": row["tool_name"],
                    "externalFetchedAt": row["fetched_at"],
                    "verified": row["verification_status"] == "verified",
                    "storageLocation": "Local SQLite Warehouse"
                }
            return {
                "source": "Local Registry / Default",
                "tool": "local_database",
                "externalFetchedAt": datetime.now(timezone.utc).isoformat(),
                "verified": True,
                "storageLocation": "Local SQLite Warehouse"
            }

repository = DataRepository()
