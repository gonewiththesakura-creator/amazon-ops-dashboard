import asyncio
import sys
import os

# Add scratch project root to sys.path
project_root = r"C:\Users\JT\.gemini\antigravity\scratch\amazon_ops_dashboard"
sys.path.insert(0, project_root)

from backend.services.asin_service import analyze_asin
from backend.services.market_service import analyze_market
from backend.services.keyword_service import analyze_keyword
from backend.services.ai_diagnostics import generate_ai_diagnostics

async def test_full_pipeline():
    print("Testing Full Pipeline for Amazon Ops Dashboard...")
    
    # 1. Test ASIN analysis
    print("\n1. Testing analyze_asin...")
    asin_res = await analyze_asin("US", "B0FQFB8FMG")
    assert asin_res["asin"] == "B0FQFB8FMG"
    assert "priceBSRChart" in asin_res
    assert len(asin_res["trafficSources"]) > 0
    print("   ASIN Analysis Passed:", asin_res["title"][:40], "Price:", asin_res["price"])

    # 2. Test Market analysis
    print("\n2. Testing analyze_market...")
    market_res = await analyze_market("US", "wireless earbuds")
    assert "priceBrackets" in market_res
    assert "brandSharePie" in market_res
    assert "cr4" in market_res
    print("   Market Analysis Passed: CR4 =", market_res["cr4"], "Price brackets count =", len(market_res["priceBrackets"]))

    # 3. Test Keyword analysis
    print("\n3. Testing analyze_keyword...")
    kw_res = await analyze_keyword("US", "wireless earbuds")
    assert "timelineChart" in kw_res
    assert len(kw_res["keywords"]) > 0
    print("   Keyword Analysis Passed: Found", len(kw_res["keywords"]), "opportunity keywords")

    # 4. Test AI Diagnostics
    print("\n4. Testing generate_ai_diagnostics...")
    diag = generate_ai_diagnostics(market_res, asin_res, kw_res)
    assert len(diag["radarData"]) == 5
    assert len(diag["opportunities"]) > 0
    assert len(diag["actionChecklist"]) > 0
    print("   AI Diagnostics Passed: Overall Score =", diag["overallScore"])

    print("\n All unit and integration tests PASSED!")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
