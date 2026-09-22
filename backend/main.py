import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from .config import settings
from .services.asin_service import analyze_asin, USER_SKUS
from .services.market_service import analyze_market
from .services.keyword_service import analyze_keyword
from .services.ai_diagnostics import generate_ai_diagnostics
from .services.replenishment_service import calculate_replenishment
from .services.pipeline_products import analyze_pipeline_products

app = FastAPI(title="Amazon Ops Dashboard API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    marketplace: str = "US"
    asin: Optional[str] = "B0GYH8WT22" # Default to user's '刘总枕头'
    keyword: Optional[str] = "cervical pillow"
    nodeIdPath: Optional[str] = "1055398:1063252:1199122:3732111"

class ReplenishRequest(BaseModel):
    stock: int = 200
    dailySales: int = 50
    seaDays: int = 30
    batchSize: int = 10000
    unitCost: float = 50.0
    seaShippingRate: float = 12.0
    airShippingRate: float = 45.0

@app.get("/api/health")
async def health():
    return {"status": "ok", "mcp_url": settings.MCP_URL}

@app.get("/api/skus")
async def get_user_skus():
    """Returns the user's 5 pre-registered ELOVNOVA brand SKUs."""
    return USER_SKUS

@app.post("/api/replenishment/calc")
async def api_calc_replenishment(req: ReplenishRequest):
    """Calculates stockout warning, air freight emergency and cashflow pool."""
    return calculate_replenishment(
        stock=req.stock,
        daily_sales=req.dailySales,
        sea_days=req.seaDays,
        batch_size=req.batchSize,
        unit_cost=req.unitCost,
        sea_shipping_rate=req.seaShippingRate,
        air_shipping_rate=req.airShippingRate
    )

@app.get("/api/pipeline/products")
async def api_get_pipeline_products(marketplace: str = "US"):
    """Returns the market analysis for products to develop (U-pillow, Lumbar, Massage pillow)."""
    return await analyze_pipeline_products(marketplace)

@app.post("/api/analyze/all")
async def api_analyze_all(req: AnalyzeRequest):
    try:
        marketplace = req.marketplace or "US"
        asin = req.asin or "B0GYH8WT22"
        keyword = req.keyword or "cervical pillow"
        node_id = req.nodeIdPath or "1055398:1063252:1199122:3732111"

        asin_result = await analyze_asin(marketplace, asin)
        market_result = await analyze_market(marketplace, node_id)
        keyword_result = await analyze_keyword(marketplace, keyword)
        diagnostics = generate_ai_diagnostics(market_result, asin_result, keyword_result)
        replenishment = calculate_replenishment()
        pipeline_products = await analyze_pipeline_products(marketplace)

        return {
            "marketplace": marketplace,
            "asin": asin_result,
            "market": market_result,
            "keyword": keyword_result,
            "diagnostics": diagnostics,
            "replenishment": replenishment,
            "pipelineProducts": pipeline_products,
            "userSkus": USER_SKUS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount Frontend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
