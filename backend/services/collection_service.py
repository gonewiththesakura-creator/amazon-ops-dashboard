import logging
import json
import asyncio
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional
from ..mcp_client import mcp_client
from ..database import db

logger = logging.getLogger("collection_service")

async def collect_asin_package(asin: str, marketplace: str = "US", force_refresh: bool = False) -> Dict[str, Any]:
    """1. Commodity Full Package (商品全量包):
    Calls asin_detail + keepa_info + asin_sales_trend concurrently/sequentially.
    Archives raw response and normalizes into:
    asin_snapshots, asin_price_history, asin_bsr_history, asin_sales_history.
    """
    asin = asin.strip().upper()
    marketplace = marketplace.upper()
    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = date.today().isoformat()

    # If not force_refresh, check if we already have fresh local snapshot today
    if not force_refresh:
        local_snap = db.get_latest_asin_snapshot(asin)
        if local_snap and local_snap.get("snapshot_date") == today_str:
            logger.info(f"[COLLECTION] Local fresh snapshot found for {asin}, reading from local warehouse.")
            return {
                "status": "ok",
                "source": "local_warehouse",
                "asin": asin,
                "fetchedAt": local_snap.get("fetched_at", now_iso),
                "isLocalWarehouse": True,
                "message": "本地数据库今日已有最新数据资产，已直接读取本地（一查即入库、优先读本地）",
                "data": {
                    "asin": asin,
                    "title": local_snap.get("title") or asin,
                    "price": local_snap.get("price"),
                    "estimatedUnits": local_snap.get("estimated_units"),
                    "estimatedRevenue": local_snap.get("estimated_revenue"),
                    "bsr": local_snap.get("bsr"),
                    "rating": local_snap.get("rating"),
                    "reviews": local_snap.get("reviews"),
                    "priceHistoryPoints": len(db.get_price_history(asin)),
                    "bsrHistoryPoints": len(db.get_bsr_history(asin))
                }
            }

    results_summary = {
        "asin_detail": "pending",
        "keepa_info": "pending",
        "asin_sales_trend": "pending"
    }

    # 1. Call asin_detail
    detail_env = await mcp_client.call_tool("asin_detail", {
        "marketplace": marketplace,
        "asin": asin
    })
    results_summary["asin_detail"] = detail_env.get("status", "error")
    detail_data = detail_env.get("data") or {}

    title = detail_data.get("title") or detail_data.get("item_name") or asin
    price = detail_data.get("price") or detail_data.get("current_price")
    brand = detail_data.get("brand") or ""
    bsr = detail_data.get("bsr") or detail_data.get("rank")
    rating = detail_data.get("rating") or detail_data.get("star")
    reviews = detail_data.get("reviews") or detail_data.get("review_count")
    units = detail_data.get("units") or detail_data.get("monthly_units")
    revenue = detail_data.get("revenue") or detail_data.get("monthly_revenue")

    # 2. Call keepa_info for historical time-series
    keepa_env = await mcp_client.call_tool("keepa_info", {
        "marketplace": marketplace,
        "asin": asin
    })
    results_summary["keepa_info"] = keepa_env.get("status", "error")
    keepa_data = keepa_env.get("data") or {}

    price_points_added = 0
    bsr_points_added = 0
    if isinstance(keepa_data, dict):
        p_hist = keepa_data.get("priceHistory") or keepa_data.get("price_history") or []
        b_hist = keepa_data.get("bsrHistory") or keepa_data.get("bsr_history") or []
        
        if p_hist:
            db.batch_insert_price_history(asin, p_hist, source="keepa")
            price_points_added = len(p_hist)
        if b_hist:
            db.batch_insert_bsr_history(asin, b_hist, source="keepa")
            bsr_points_added = len(b_hist)

    # 3. Call asin_sales_trend
    trend_env = await mcp_client.call_tool("asin_sales_trend", {
        "marketplace": marketplace,
        "asin": asin
    })
    results_summary["asin_sales_trend"] = trend_env.get("status", "error")
    trend_data = trend_env.get("data") or {}

    sales_points_added = 0
    if isinstance(trend_data, list):
        db.batch_insert_sales_history(asin, trend_data, source="sellersprite_mcp")
        sales_points_added = len(trend_data)
    elif isinstance(trend_data, dict) and "history" in trend_data:
        db.batch_insert_sales_history(asin, trend_data["history"], source="sellersprite_mcp")
        sales_points_added = len(trend_data["history"])

    # 4. Standardized Upsert into asin_snapshots
    with db.get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO asin_snapshots 
            (asin, snapshot_date, price, estimated_units, estimated_revenue, bsr, rating, reviews, source, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'collection_asin_package', ?)
        """, (asin, today_str, price, units, revenue, bsr, rating, reviews, now_iso))
        conn.commit()

    return {
        "status": "ok",
        "source": "sellersprite_mcp_and_local",
        "asin": asin,
        "fetchedAt": now_iso,
        "isLocalWarehouse": False,
        "toolsStatus": results_summary,
        "message": f"商品全量包采集完成并已入库！新增价格点: {price_points_added}, BSR点: {bsr_points_added}, 销量点: {sales_points_added}",
        "data": {
            "asin": asin,
            "title": title,
            "brand": brand,
            "price": price,
            "estimatedUnits": units,
            "estimatedRevenue": revenue,
            "bsr": bsr,
            "rating": rating,
            "reviews": reviews,
            "priceHistoryPointsAdded": price_points_added,
            "bsrHistoryPointsAdded": bsr_points_added,
            "salesHistoryPointsAdded": sales_points_added
        }
    }

async def collect_category_package(node_id_path: str, marketplace: str = "US", force_refresh: bool = False) -> Dict[str, Any]:
    """2. Category Full Package (类目全量包):
    Calls market_price_distribution + product_node + product_research.
    Stores market_snapshots, market_distribution_snapshots, category_product_snapshots.
    """
    node_id_path = node_id_path.strip()
    marketplace = marketplace.upper()
    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = date.today().isoformat()

    # 1. Price Distribution
    dist_env = await mcp_client.call_tool("market_price_distribution", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })
    raw_prices = dist_env.get("data")
    if isinstance(raw_prices, dict) and "data" in raw_prices:
        raw_prices = raw_prices["data"]
    raw_prices_list = [it for it in raw_prices if isinstance(it, dict)] if isinstance(raw_prices, list) else []

    total_units = sum(it.get("units", 0) for it in raw_prices_list) if raw_prices_list else None
    total_revenue = round(sum(it.get("revenue", 0.0) for it in raw_prices_list), 2) if raw_prices_list else None
    product_count = sum(it.get("products", 0) for it in raw_prices_list) if raw_prices_list else None
    avg_price = round(total_revenue / total_units, 2) if (total_units and total_units > 0 and total_revenue) else None

    # Archive distribution snapshot
    if raw_prices_list:
        db.insert_market_distribution_snapshot(node_id_path, today_str, "price", json.dumps(raw_prices_list, ensure_ascii=False))

    # Archive market snapshot
    if total_units is not None:
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO market_snapshots 
                (node_id_path, snapshot_date, products, units, revenue, avg_price, source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, 'collection_category_package', ?)
            """, (node_id_path, today_str, product_count, total_units, total_revenue, avg_price, now_iso))
            conn.commit()

    # 2. Collect Category TOP Products via product_research
    prod_env = await mcp_client.call_tool("product_research", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path,
            "size": 20
        }
    })
    prod_data = prod_env.get("data")
    items = []
    if isinstance(prod_data, dict):
        items = prod_data.get("items", [])
    elif isinstance(prod_data, list):
        items = prod_data

    saved_products = []
    for rank_idx, pi in enumerate(items, 1):
        if isinstance(pi, dict) and pi.get("asin"):
            p_asin = pi.get("asin")
            p_entry = {
                "rank": rank_idx,
                "asin": p_asin,
                "title": pi.get("title", ""),
                "brand": pi.get("brand", ""),
                "price": pi.get("price"),
                "units": pi.get("units") or pi.get("estimatedUnits"),
                "revenue": pi.get("revenue") or pi.get("estimatedRevenue"),
                "bsr": pi.get("bsr"),
                "rating": pi.get("rating"),
                "reviews": pi.get("reviews")
            }
            saved_products.append(p_entry)

    if saved_products:
        db.insert_category_product_snapshots(node_id_path, today_str, saved_products, source="collection_category_package")

    return {
        "status": "ok",
        "nodeIdPath": node_id_path,
        "fetchedAt": now_iso,
        "message": f"类目全量包采集完成！累计沉淀 {len(saved_products)} 款类目热销品快照",
        "data": {
            "nodeIdPath": node_id_path,
            "marketCapacityUnits": total_units,
            "marketRevenue": total_revenue,
            "productCount": product_count,
            "avgPrice": avg_price,
            "topProductsCollected": len(saved_products),
            "sampleProducts": saved_products[:5]
        }
    }

async def collect_keywords_package(keywords_input: Any, marketplace: str = "US") -> Dict[str, Any]:
    """3. Keywords Full Package (关键词全量包):
    Supports multiline text or list of keywords.
    Calls keyword_miner, archives raw responses, stores in keyword_history.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    marketplace = marketplace.upper()

    if isinstance(keywords_input, str):
        kw_list = [k.strip() for k in keywords_input.replace("\r", "\n").split("\n") if k.strip()]
    elif isinstance(keywords_input, list):
        kw_list = [str(k).strip() for k in keywords_input if str(k).strip()]
    else:
        kw_list = []

    collected_rows = []
    total_searches = 0

    for kw in kw_list[:20]: # Cap to 20 per run
        try:
            miner_env = await mcp_client.call_tool("keyword_miner", {
                "request": {
                    "marketplace": marketplace,
                    "keyword": kw,
                    "size": 5
                }
            })
            m_data = miner_env.get("data")
            items = []
            if isinstance(m_data, dict):
                items = m_data.get("items", [])
            elif isinstance(m_data, list):
                items = m_data

            if items and isinstance(items[0], dict):
                first = items[0]
                s_cnt = first.get("searches") or 0
                p_cnt = first.get("purchases") or 0
                p_rate = float(first.get("purchaseRate")) if first.get("purchaseRate") is not None else 0.0
                pr_cnt = first.get("prodsCount") or 0

                # Save to database
                with db.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO keyword_history 
                        (keyword, marketplace, searches, purchases, purchase_rate, prods_count, source, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'collection_keywords_package', ?)
                    """, (kw, marketplace, s_cnt, p_cnt, p_rate, pr_cnt, now_iso))
                    conn.commit()

                total_searches += s_cnt
                collected_rows.append({
                    "keyword": kw,
                    "searches": s_cnt,
                    "purchases": p_cnt,
                    "purchaseRate": p_rate,
                    "prodsCount": pr_cnt,
                    "status": "ok"
                })
            else:
                # No data returned
                collected_rows.append({
                    "keyword": kw,
                    "searches": 0,
                    "purchases": 0,
                    "purchaseRate": 0.0,
                    "prodsCount": 0,
                    "status": "no_data"
                })
        except Exception as e:
            logger.warning(f"Error collecting keyword '{kw}': {e}")
            collected_rows.append({
                "keyword": kw,
                "searches": 0,
                "purchases": 0,
                "purchaseRate": 0.0,
                "prodsCount": 0,
                "status": f"error: {str(e)}"
            })

    return {
        "status": "ok",
        "fetchedAt": now_iso,
        "keywordsCount": len(kw_list),
        "totalSearches": total_searches,
        "message": f"成功批量采集 {len(collected_rows)} 个关键词数据资产",
        "data": {
            "keywords": collected_rows,
            "totalSearches": total_searches
        }
    }

async def run_batch_asin_job(job_id: int, asins: List[str], marketplace: str = "US"):
    """Background runner for batch ASIN collection."""
    success = 0
    failure = 0
    details = []

    for asin in asins:
        try:
            res = await collect_asin_package(asin, marketplace=marketplace, force_refresh=False)
            if res.get("status") == "ok":
                success += 1
                details.append({"asin": asin, "status": "success", "source": res.get("source")})
            else:
                failure += 1
                details.append({"asin": asin, "status": "failed", "error": res.get("error")})
        except Exception as e:
            failure += 1
            details.append({"asin": asin, "status": "error", "error": str(e)})

        # Update progress after each ASIN
        db.update_collection_job(
            job_id,
            status="running",
            success_count=success,
            failure_count=failure,
            details_json=json.dumps(details, ensure_ascii=False)
        )

    # Complete job
    db.update_collection_job(
        job_id,
        status="completed",
        success_count=success,
        failure_count=failure,
        details_json=json.dumps(details, ensure_ascii=False),
        finished=True
    )
    logger.info(f"[BATCH JOB] Job {job_id} completed: {success} succeeded, {failure} failed.")

def start_batch_asins_collection(asins_input: Any, marketplace: str = "US") -> Dict[str, Any]:
    """4. Batch ASINs Collection Package:
    Creates a job in manual_collection_jobs and starts background execution.
    """
    if isinstance(asins_input, str):
        asin_list = [a.strip().upper() for a in asins_input.replace("\r", "\n").replace(",", "\n").split("\n") if a.strip()]
    elif isinstance(asins_input, list):
        asin_list = [str(a).strip().upper() for a in asins_input if str(a).strip()]
    else:
        asin_list = []

    # Filter unique valid-looking ASINs (length 10)
    valid_asins = list(dict.fromkeys([a for a in asin_list if len(a) >= 9]))
    if not valid_asins:
        return {"status": "error", "message": "未检测到有效 ASIN 列表 (格式示例: B0GYH8WT22)"}

    # Create job in database
    job_id = db.create_collection_job(
        job_type="batch_asins",
        target_type="asin_list",
        target_value=f"{len(valid_asins)} ASINs",
        tools_json=json.dumps(["asin_detail", "keepa_info", "asin_sales_trend"])
    )

    # Launch background task
    asyncio.create_task(run_batch_asin_job(job_id, valid_asins, marketplace))

    return {
        "status": "ok",
        "jobId": job_id,
        "totalAsins": len(valid_asins),
        "message": f"批量采集任务 #{job_id} 已启动，共 {len(valid_asins)} 个 ASIN。系统将在后台自动入库并积累时序资产。"
    }
