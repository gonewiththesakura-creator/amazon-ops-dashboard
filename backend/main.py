import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .database import db
from .mcp_client import mcp_client
from .services.core_market_service import get_core_market_overview, get_market_tree
from .services.core_product_service import (
    get_core_products_registry,
    get_core_product_detail,
    get_core_product_competitors,
    get_core_products_comparison,
    add_direct_competitor,
    confirm_suggested_competitor,
    remove_direct_competitor,
    ignore_candidate_competitor
)
from .services.pipeline_service import (
    get_pipeline_products_list,
    add_pipeline_product,
    get_pipeline_product_detail,
    update_pipeline_decision,
    trigger_pipeline_research
)
from .services.opportunity_lab_service import (
    conduct_new_category_research,
    get_all_research_projects,
    get_research_project_by_id
)
from .services.rule_diagnostics import get_executive_briefing, generate_rule_diagnostics
from .services.data_job_service import list_data_jobs, trigger_daily_refresh, get_automation_status
from .services.replenishment_service import calculate_replenishment
from .services.trend_service import get_dashboard_trends
from .services.collection_service import (
    collect_asin_package,
    collect_category_package,
    collect_keywords_package,
    start_batch_asins_collection
)
from .services.asset_service import (
    get_warehouse_stats,
    search_warehouse_assets,
    get_raw_response_detail
)

from .scheduler import start_scheduler, stop_scheduler, get_live_scheduler_status

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        await mcp_client.scan_and_sync_tool_registry()
    except Exception as e:
        logger.warning(f"Initial MCP scan deferred: {e}")
    yield
    stop_scheduler()

app = FastAPI(title="Amazon AI Opportunity Intelligence API", version="2.5.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Models -----------------
class ResearchRequest(BaseModel):
    userQuestion: str
    marketplace: Optional[str] = "US"

class PipelineAddRequest(BaseModel):
    id: str
    name: str
    keyword: str
    categoryLevel: Optional[str] = "四类 (需自行调取)"
    nodeIdPath: Optional[str] = None
    status: Optional[str] = "调研中"
    decision: Optional[str] = "继续观察"
    rationale: Optional[str] = ""
    riskFlag: Optional[str] = ""

class DirectCompetitorRequest(BaseModel):
    competitorAsin: str
    notes: Optional[str] = "人工添加直接竞品"

class PipelineDecisionRequest(BaseModel):
    decision: str
    rationale: Optional[str] = None

class CollectionAsinRequest(BaseModel):
    asin: str
    marketplace: Optional[str] = "US"
    forceRefresh: Optional[bool] = False

class CollectionCategoryRequest(BaseModel):
    nodeIdPath: str
    marketplace: Optional[str] = "US"
    forceRefresh: Optional[bool] = False

class CollectionKeywordsRequest(BaseModel):
    keywords: Any
    marketplace: Optional[str] = "US"

class CollectionBatchAsinsRequest(BaseModel):
    asins: Any
    marketplace: Optional[str] = "US"

class ReplenishRequest(BaseModel):
    stock: int = 200
    dailySales: int = 50
    seaDays: int = 30
    batchSize: int = 10000
    unitCost: float = 50.0
    seaShippingRate: float = 12.0
    airShippingRate: float = 45.0

# ----------------- Health -----------------
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "Amazon AI Opportunity Intelligence",
        "version": "2.6.0",
        "mcp_url": settings.MCP_URL
    }

# ----------------- Executive Briefing -----------------
@app.get("/api/dashboard/briefing")
async def api_dashboard_briefing(marketplace: str = "US"):
    market_overview = await get_core_market_overview(marketplace)
    comparison = await get_core_products_comparison(marketplace)
    briefing = get_executive_briefing(market_overview, comparison)
    return {
        "status": "ok",
        "data": briefing
    }

# ----------------- Module 1: Core Market -----------------
@app.get("/api/core-market/overview")
async def api_market_overview(marketplace: str = "US", nodeIdPath: str = "1055398:1063252:1199122:3732111"):
    return await get_core_market_overview(marketplace, nodeIdPath)

@app.get("/api/core-market/tree")
async def api_market_tree():
    return get_market_tree()

# ----------------- Module 2: Core 4 SKUs & Competitors -----------------
@app.get("/api/core-products")
async def api_get_core_products():
    return {
        "status": "ok",
        "data": get_core_products_registry()
    }

@app.get("/api/core-products/comparison")
async def api_core_products_comparison(marketplace: str = "US"):
    return await get_core_products_comparison(marketplace)

@app.get("/api/core-products/{asin}")
async def api_get_core_product_detail(asin: str, marketplace: str = "US"):
    return await get_core_product_detail(marketplace, asin)

@app.get("/api/core-products/{asin}/competitors")
async def api_get_core_product_competitors(asin: str, marketplace: str = "US"):
    return await get_core_product_competitors(marketplace, asin)

@app.post("/api/core-products/{asin}/competitors/manual")
async def api_add_manual_competitor(asin: str, req: DirectCompetitorRequest):
    try:
        res = await add_direct_competitor(asin, req.competitorAsin.strip().upper(), req.notes or "运营手工录入直接竞品")
        return {
            "status": "ok",
            "success": True,
            "ownerAsin": asin,
            "competitorAsin": req.competitorAsin.strip().upper(),
            "message": f"已成功将 ASIN {req.competitorAsin} 验证并加入已确认直接竞品池，已同步历史走势与数据快照",
            "data": res
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding manual competitor: {e}")
        raise HTTPException(status_code=500, detail=f"添加竞品失败: {str(e)}")

@app.post("/api/core-products/{asin}/competitors/confirm")
async def api_confirm_competitor(asin: str, req: DirectCompetitorRequest):
    try:
        res = await confirm_suggested_competitor(asin, req.competitorAsin.strip().upper())
        return {
            "status": "ok",
            "success": True,
            "ownerAsin": asin,
            "competitorAsin": req.competitorAsin.strip().upper(),
            "message": f"已将系统建议竞品 {req.competitorAsin} 验证并转为已确认直接竞品，已同步最新数据",
            "data": res
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error confirming competitor: {e}")
        raise HTTPException(status_code=500, detail=f"确认竞品失败: {str(e)}")

@app.delete("/api/core-products/{asin}/competitors/{comp_asin}")
async def api_delete_competitor(asin: str, comp_asin: str):
    success = remove_direct_competitor(asin, comp_asin.strip().upper())
    return {
        "status": "ok",
        "success": success,
        "ownerAsin": asin,
        "competitorAsin": comp_asin.strip().upper(),
        "message": f"已从直接竞品池移除 {comp_asin}"
    }

@app.post("/api/core-products/{asin}/competitors/{comp_asin}/ignore")
async def api_ignore_competitor(asin: str, comp_asin: str):
    success = ignore_candidate_competitor(asin, comp_asin.strip().upper())
    return {
        "status": "ok",
        "success": success,
        "ownerAsin": asin,
        "competitorAsin": comp_asin.strip().upper(),
        "message": f"已忽略候选竞品 {comp_asin}，后续将不再向您推荐"
    }

# ----------------- Dashboard Trend Cockpit (V2.4) -----------------
@app.get("/api/dashboard/trends")
async def api_dashboard_trends(range: str = "12m"):
    return get_dashboard_trends(time_range=range)

# ----------------- Module 3: Pipeline (Memory Foam Supply Chain) -----------------
@app.get("/api/pipeline")
async def api_get_pipeline(marketplace: str = "US"):
    return await get_pipeline_products_list(marketplace)

@app.post("/api/pipeline")
async def api_add_pipeline(req: PipelineAddRequest):
    return add_pipeline_product(req.dict())

@app.get("/api/pipeline/{item_id}")
async def api_get_pipeline_detail(item_id: str, marketplace: str = "US"):
    detail = await get_pipeline_product_detail(item_id, marketplace)
    if not detail:
        raise HTTPException(status_code=404, detail="Pipeline candidate not found")
    return {"status": "ok", "data": detail}

@app.patch("/api/pipeline/{item_id}/status")
@app.post("/api/pipeline/{item_id}/decision")
async def api_update_pipeline_decision(item_id: str, req: PipelineDecisionRequest):
    return update_pipeline_decision(item_id, req.decision, req.rationale)

@app.post("/api/pipeline/{item_id}/research")
async def api_trigger_pipeline_research(item_id: str, marketplace: str = "US"):
    return await trigger_pipeline_research(item_id, marketplace)

@app.get("/api/pipeline/{item_id}/history")
async def api_get_pipeline_history(item_id: str, marketplace: str = "US"):
    detail = await get_pipeline_product_detail(item_id, marketplace)
    if not detail:
        raise HTTPException(status_code=404, detail="Pipeline candidate not found")
    return {"status": "ok", "data": detail.get("trend12m", [])}

# ----------------- Module 4: Opportunity Lab (New Categories) -----------------
@app.get("/api/research")
async def api_get_research():
    return {
        "status": "ok",
        "data": get_all_research_projects()
    }

@app.get("/api/research/{project_id}")
async def api_get_research_by_id(project_id: int):
    p = get_research_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Research project not found")
    return {"status": "ok", "data": p}

@app.post("/api/research")
async def api_conduct_research(req: ResearchRequest):
    return await conduct_new_category_research(req.userQuestion, req.marketplace or "US")

# ----------------- Manual Data Collection Center (V2.5) -----------------
@app.post("/api/collection/asin")
async def api_collection_asin(req: CollectionAsinRequest):
    return await collect_asin_package(req.asin, req.marketplace or "US", req.forceRefresh or False)

@app.post("/api/collection/category")
async def api_collection_category(req: CollectionCategoryRequest):
    return await collect_category_package(req.nodeIdPath, req.marketplace or "US", req.forceRefresh or False)

@app.post("/api/collection/keywords")
async def api_collection_keywords(req: CollectionKeywordsRequest):
    return await collect_keywords_package(req.keywords, req.marketplace or "US")

@app.post("/api/collection/batch-asins")
async def api_collection_batch_asins(req: CollectionBatchAsinsRequest):
    return start_batch_asins_collection(req.asins, req.marketplace or "US")

@app.get("/api/collection/jobs/{job_id}")
async def api_get_collection_job(job_id: int):
    job = db.get_collection_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Collection job not found")
    return {"status": "ok", "data": job}

@app.get("/api/collection/jobs")
async def api_list_collection_jobs(limit: int = 20):
    return {"status": "ok", "data": db.list_collection_jobs(limit=limit)}

@app.get("/api/collection/tools")
async def api_get_collection_tools():
    return {"status": "ok", "data": db.get_mcp_tools()}

@app.post("/api/collection/scan-tools")
async def api_scan_tools():
    return await mcp_client.scan_and_sync_tool_registry()

# ----------------- Local Data Warehouse Assets (V2.5) -----------------
@app.get("/api/assets/stats")
async def api_get_asset_stats():
    return get_warehouse_stats()

@app.get("/api/assets/search")
async def api_search_assets(q: str = Query(..., min_length=1), type: Optional[str] = None, limit: int = 50):
    return search_warehouse_assets(q, asset_type=type, limit=limit)

@app.get("/api/assets/raw/{raw_id}")
async def api_get_raw_asset(raw_id: int):
    raw = get_raw_response_detail(raw_id)
    if raw.get("status") == "error":
        raise HTTPException(status_code=404, detail=raw.get("message"))
    return raw

# ----------------- Data Center & Automation Jobs -----------------
@app.get("/api/data-jobs")
async def api_get_data_jobs():
    return {
        "status": "ok",
        "data": list_data_jobs()
    }

@app.get("/api/data-jobs/status")
async def api_get_automation_status():
    status_data = get_live_scheduler_status()
    return {
        "status": "ok",
        "data": status_data,
        **status_data
    }

@app.post("/api/data-jobs/refresh")
async def api_refresh_data_jobs(marketplace: str = "US"):
    return await trigger_daily_refresh(marketplace)

# ----------------- Phase 2: Replenishment (Experimental) -----------------
@app.post("/api/replenishment/calc")
async def api_calc_replenishment(req: ReplenishRequest):
    return calculate_replenishment(
        stock=req.stock,
        daily_sales=req.dailySales,
        sea_days=req.seaDays,
        batch_size=req.batchSize,
        unit_cost=req.unitCost,
        sea_shipping_rate=req.seaShippingRate,
        air_shipping_rate=req.airShippingRate
    )

# Mount Frontend static files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
