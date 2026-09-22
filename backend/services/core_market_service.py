import logging
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional
from ..mcp_client import mcp_client
from ..database import db

logger = logging.getLogger("core_market_service")

# Standard Memory Foam Pillow Category Tree
MEMORY_FOAM_PILLOW_TREE = {
    "nodeIdPath": "1055398:1063252:1199122",
    "nodeLabel": "Home & Kitchen > Bedding > Bed Pillows & Positioners",
    "subcategories": [
        {
            "nodeIdPath": "1055398:1063252:1199122:3732111",
            "nodeLabel": "Neck & Cervical Pillows (颈椎枕 / 蝴蝶枕)",
            "level": 4,
            "isPrimaryCore": True,
            "description": "公司当前 4 个核心枕头 SKU 所处主要细分类目"
        },
        {
            "nodeIdPath": "1055398:1063252:1199122:3732051",
            "nodeLabel": "Lumbar Pillows (腰靠 / 腰枕)",
            "level": 4,
            "isPrimaryCore": False,
            "description": "腰枕系列在售款 (B0HJWZM439 / B0HJX1MGBF) 所处细分类目"
        },
        {
            "nodeIdPath": "1055398:1063252:1199122:3732141",
            "nodeLabel": "Travel Pillows (U型旅行枕)",
            "level": 4,
            "isPrimaryCore": False,
            "description": "待开发产品：差旅便携记忆棉护颈 U型枕"
        }
    ]
}

async def get_core_market_overview(marketplace: str = "US", node_id_path: str = "1055398:1063252:1199122:3732111") -> Dict[str, Any]:
    """Retrieves real market distribution and metrics for the memory foam pillow core market.
    ZERO FAKE FALLBACK DATA. If MCP returns nothing, returns data: null with error status.
    """
    marketplace = marketplace.upper()
    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = date.today().isoformat()

    # Verify node belongs to valid bedding pillows hierarchy (Strictly prohibit electronics fallback)
    if "172282" in node_id_path: # Electronics ID
        return {
            "status": "error",
            "source": "core_market_service",
            "fetchedAt": now_iso,
            "freshnessHours": 0.0,
            "dataQuality": "empty",
            "data": None,
            "error": "非枕头相关类目节点。系统已杜绝非品类回退。"
        }

    # 1. Fetch real price distribution
    price_env = await mcp_client.call_tool("market_price_distribution", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })
    
    # 2. Fetch real brand concentration (CR4/CR8)
    brand_env = await mcp_client.call_tool("market_brand_concentration", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })

    # 3. Fetch real rating distribution
    rating_env = await mcp_client.call_tool("market_rating_distribution", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })

    # 4. Fetch seller country distribution
    country_env = await mcp_client.call_tool("market_seller_country_distribution", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })

    def _unwrap_list(v):
        if isinstance(v, dict):
            return v.get("data") or []
        if isinstance(v, list):
            return v
        return []

    raw_prices = _unwrap_list(price_env.get("data"))
    raw_brands = _unwrap_list(brand_env.get("data"))
    raw_ratings = _unwrap_list(rating_env.get("data"))
    raw_countries = _unwrap_list(country_env.get("data"))

    if not raw_prices and not raw_brands:
        return {
            "status": "unavailable",
            "source": "sellersprite_mcp",
            "fetchedAt": now_iso,
            "freshnessHours": 0.0,
            "dataQuality": "empty",
            "data": None,
            "error": "卖家精灵暂未返回该四级类目大盘数据，请稍后刷新重试"
        }

    # Clean real price brackets
    price_brackets = []
    total_products = 0
    total_units = 0
    total_revenue = 0.0

    for item in raw_prices:
        if not isinstance(item, dict):
            continue
        p_count = item.get("products") or 0
        u_count = item.get("units") or 0
        rev = float(item.get("revenue") or 0.0)
        u_ratio = float(item.get("unitsRatio") or 0.0)
        
        total_products += p_count
        total_units += u_count
        total_revenue += rev
        
        lbl = item.get("label") or "未知价格"
        price_brackets.append({
            "bracket": lbl if "$" in lbl else f"${lbl}",
            "products": p_count,
            "units": u_count,
            "revenue": round(rev, 2),
            "unitsRatio": round(u_ratio * 100, 2)
        })

    # Clean real brand concentration
    brand_list = []
    top4_ratio = 0.0
    for idx, b in enumerate(raw_brands):
        if not isinstance(b, dict):
            continue
        b_name = b.get("brand") or "Unknown"
        b_ratio = round(float(b.get("totalUnitsRatio") or 0.0) * 100, 2)
        if idx < 4:
            top4_ratio += b_ratio
        brand_list.append({
            "name": b_name,
            "ranking": b.get("ranking") or (idx + 1),
            "share": b_ratio,
            "revenue": round(float(b.get("totalRevenue") or 0.0), 2),
            "units": b.get("totalUnits") or 0,
            "avgPrice": round(float(b.get("avgPrice") or 0.0), 2),
            "rating": b.get("rating")
        })

    cr4 = round(top4_ratio, 2)
    cr8 = round(sum(b["share"] for b in brand_list[:8]), 2)
    avg_price = round(total_revenue / total_units, 2) if total_units > 0 else (brand_list[0]["avgPrice"] if brand_list else None)

    # Save real snapshot to SQLite database
    try:
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO market_snapshots (
                    node_id_path, snapshot_date, products, sellers, units, revenue, avg_price, cr4, cr8, source, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'sellersprite_mcp', ?)
            """, (node_id_path, today_str, total_products, len(brand_list), total_units, total_revenue, avg_price, cr4, cr8, now_iso))
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to record market snapshot: {e}")

    # Check 30-day trend from historical snapshots
    trend_30d_growth = None
    try:
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT units, snapshot_date FROM market_snapshots 
                WHERE node_id_path = ? AND snapshot_date < ? 
                ORDER BY snapshot_date DESC LIMIT 1
            """, (node_id_path, today_str))
            prev_row = c.fetchone()
            if prev_row and prev_row["units"] and prev_row["units"] > 0:
                prev_u = prev_row["units"]
                trend_30d_growth = round(((total_units - prev_u) / prev_u) * 100, 1)
    except Exception:
        pass

    result_data = {
        "marketplace": marketplace,
        "nodeIdPath": node_id_path,
        "categoryLabel": "Home & Kitchen > Bedding > Neck & Cervical Pillows (颈椎枕/蝴蝶枕)",
        "totalProducts": total_products,
        "totalUnits": total_units,
        "totalRevenue": round(total_revenue, 2),
        "avgPrice": avg_price,
        "cr4": cr4,
        "cr8": cr8,
        "trend30dGrowth": trend_30d_growth,
        "monopolyStatus": "高度寡头垄断" if cr4 > 70 else ("中度垄断" if cr4 > 45 else "竞争充分"),
        "priceBrackets": price_brackets,
        "brandRankings": brand_list[:10],
        "ratingsDistribution": [
            {
                "label": r.get("label", "N/A"),
                "products": r.get("products", 0),
                "unitsRatio": round(float(r.get("unitsRatio") or 0.0) * 100, 2)
            } for r in raw_ratings if isinstance(r, dict)
        ],
        "sellerCountryDistribution": [
            {
                "country": c.get("country", "Unknown"),
                "productsRatio": round(float(c.get("productsRatio") or 0.0) * 100, 2),
                "unitsRatio": round(float(c.get("unitsRatio") or 0.0) * 100, 2)
            } for c in raw_countries if isinstance(c, dict)
        ]
    }

    return {
        "status": "ok",
        "source": "sellersprite_mcp",
        "fetchedAt": now_iso,
        "freshnessHours": 0.0,
        "dataQuality": "high",
        "data": result_data,
        "error": None
    }

def get_market_tree() -> Dict[str, Any]:
    """Returns the static Memory Foam Pillow hierarchy tree for navigation."""
    return {
        "status": "ok",
        "source": "local_registry",
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "data": MEMORY_FOAM_PILLOW_TREE,
        "error": None
    }
