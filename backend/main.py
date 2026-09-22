import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from .config import settings
from .services.core_market_service import get_core_market_overview, get_market_tree
from .services.core_product_service import (
    get_core_products_registry,
    get_core_product_detail,
    get_core_product_competitors,
    get_core_products_comparison
)
from .services.pipeline_service import get_pipeline_products_list, add_pipeline_product
from .services.opportunity_lab_service import (
    conduct_new_category_research,
    get_all_research_projects,
    get_research_project_by_id
)
from .services.rule_diagnostics import get_executive_briefing, generate_rule_diagnostics
from .services.data_job_service import list_data_jobs, trigger_daily_refresh
from .services.replenishment_service import calculate_replenishment

app = FastAPI(title="Amazon AI Opportunity Intelligence API", version="2.0.0")

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
        "version": "2.0.0",
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

# ----------------- Module 2: Core 4 SKUs -----------------
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

# ----------------- Module 3: Pipeline (Memory Foam Supply Chain) -----------------
@app.get("/api/pipeline")
async def api_get_pipeline(marketplace: str = "US"):
    return await get_pipeline_products_list(marketplace)

@app.post("/api/pipeline")
async def api_add_pipeline(req: PipelineAddRequest):
    return add_pipeline_product(req.dict())

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

# ----------------- Data Center & Jobs -----------------
@app.get("/api/data-jobs")
async def api_get_data_jobs():
    return {
        "status": "ok",
        "data": list_data_jobs()
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
