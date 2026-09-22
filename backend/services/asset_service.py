import logging
from typing import Dict, Any, List, Optional
from ..database import db

logger = logging.getLogger("asset_service")

def get_warehouse_stats() -> Dict[str, Any]:
    """Returns local warehouse asset statistics across 8 core dimensions."""
    stats = db.get_asset_stats()
    return {
        "status": "ok",
        "data": stats
    }

def search_warehouse_assets(query: str, asset_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Unified global asset search across ASINs, keywords, category snapshots, and raw traces."""
    results = db.search_assets(query, asset_type=asset_type, limit=limit)
    return {
        "status": "ok",
        "query": query,
        "count": len(results),
        "data": results
    }

def get_raw_response_detail(raw_id: int) -> Dict[str, Any]:
    """Retrieves immutable audit trail raw response JSON."""
    raw = db.get_raw_response(raw_id)
    if not raw:
        return {"status": "error", "message": f"Raw response #{raw_id} not found"}
    return {
        "status": "ok",
        "data": raw
    }
