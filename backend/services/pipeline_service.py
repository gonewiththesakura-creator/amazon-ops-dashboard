import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..mcp_client import mcp_client
from ..database import db

logger = logging.getLogger("pipeline_service")

async def get_pipeline_products_list(marketplace: str = "US") -> Dict[str, Any]:
    """Retrieves memory foam supply chain relatives from database and decorates with real MCP metrics.
    Zero fabricated numbers.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    marketplace = marketplace.upper()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pipeline_products ORDER BY id ASC")
        rows = [dict(r) for r in cursor.fetchall()]

    enriched_candidates = []

    for r in rows:
        node_id = r.get("node_id_path")
        price_env = await mcp_client.call_tool("market_price_distribution", {
            "request": {
                "marketplace": marketplace,
                "nodeIdPath": node_id
            }
        }) if node_id else {"code": "NO_NODE"}

        raw_prices = price_env.get("data")
        if isinstance(raw_prices, dict) and "data" in raw_prices:
            raw_prices = raw_prices["data"]
        raw_prices_list = [it for it in raw_prices if isinstance(it, dict)] if isinstance(raw_prices, list) else []

        total_units = sum(it.get("units", 0) for it in raw_prices_list) if raw_prices_list else None
        total_revenue = round(sum(it.get("revenue", 0.0) for it in raw_prices_list), 2) if raw_prices_list else None
        product_count = sum(it.get("products", 0) for it in raw_prices_list) if raw_prices_list else None
        avg_price = round(total_revenue / total_units, 2) if (total_units and total_units > 0 and total_revenue) else None

        enriched_candidates.append({
            "id": r["id"],
            "name": r["name"],
            "categoryLevel": r["category_level"],
            "keyword": r["keyword"],
            "nodeIdPath": r["node_id_path"],
            "status": r["status"],
            "decision": r["decision"],
            "rationale": r["rationale"],
            "riskFlag": r["risk_flag"],
            "metrics": {
                "marketCapacityUnits": total_units,
                "marketRevenue": total_revenue,
                "productCount": product_count,
                "avgPrice": avg_price,
                "isDataAvailable": total_units is not None
            }
        })

    return {
        "status": "ok",
        "source": "pipeline_service",
        "fetchedAt": now_iso,
        "data": {
            "candidates": enriched_candidates,
            "totalCount": len(enriched_candidates),
            "supplyChainCapability": "现有记忆棉注塑/发泡产线，模具定制周期 20-30 天"
        },
        "error": None
    }

def add_pipeline_product(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Adds a new memory foam supply chain candidate."""
    with db.get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO pipeline_products (id, name, category_level, keyword, node_id_path, status, decision, rationale, risk_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_data["id"],
            product_data["name"],
            product_data.get("categoryLevel", "四类 (需自行调取)"),
            product_data["keyword"],
            product_data.get("nodeIdPath"),
            product_data.get("status", "调研中"),
            product_data.get("decision", "继续观察"),
            product_data.get("rationale", ""),
            product_data.get("riskFlag", "无明显带电合规风险")
        ))
        conn.commit()
    return {"status": "ok", "message": "待开发候选产品已入库"}
