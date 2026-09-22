import os
import sys

# Configure UTF-8 encoding for standard output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
from fastapi.testclient import TestClient

# Ensure scratch project root is on sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from backend.config import settings
from backend.main import app

def run_tests():
    print("=" * 65)
    print("  [*] Running Amazon AI Opportunity Intelligence V2 Test Suite")
    print("=" * 65)

    client = TestClient(app)

    # 1. Security & Config Check
    print("\n[Test 1] Security & Config Sanitization...")
    assert settings.MCP_SECRET, "SELLERSPRITE_MCP_SECRET must not be empty"
    assert "?" not in settings.MCP_URL, f"MCP_URL must not contain query parameters (tokens): {settings.MCP_URL}"
    assert settings.MCP_SECRET not in settings.MCP_URL, "MCP_URL must not leak secret token"
    print("   [PASS] Secret is securely isolated in .env, clean MCP URL:", settings.MCP_URL)

    # 2. Health Check Endpoint
    print("\n[Test 2] Health Endpoint (/api/health)...")
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.1.0"
    print("   [PASS] Health check ok, version:", data["version"])

    # 3. Executive 10-Second Briefing
    print("\n[Test 3] Executive Briefing (/api/dashboard/briefing)...")
    resp = client.get("/api/dashboard/briefing")
    assert resp.status_code == 200
    briefing = resp.json().get("data", {})
    assert "headline" in briefing
    assert "bullets" in briefing
    assert "marketSummary" in briefing
    assert "skusSummary" in briefing
    print(f"   [PASS] Briefing Headline: {briefing['headline']}")
    print(f"   [PASS] Bullets count: {len(briefing.get('bullets', []))}")

    # 4. Module 1: Core Market (Memory Foam Category Tree & Overview)
    print("\n[Test 4] Module 1: Core Market Tree & Overview...")
    tree_resp = client.get("/api/core-market/tree")
    assert tree_resp.status_code == 200
    tree_envelope = tree_resp.json()
    assert tree_envelope["status"] == "ok"
    tree_data = tree_envelope.get("data", {})
    assert "subcategories" in tree_data
    assert len(tree_data["subcategories"]) > 0
    print(f"   [PASS] Market tree subcategories: {len(tree_data['subcategories'])}")

    market_resp = client.get("/api/core-market/overview")
    assert market_resp.status_code == 200
    m_envelope = market_resp.json()
    m_data = m_envelope.get("data", {})
    assert "nodeIdPath" in m_data
    assert "cr4" in m_data
    assert "priceBrackets" in m_data
    assert "executiveOneSentence" in m_data, "executiveOneSentence must be present"
    assert "marketSizeQuestion" in m_data, "marketSizeQuestion must be present"
    assert "concentrationQuestion" in m_data, "concentrationQuestion must be present"
    assert "priceBandQuestion" in m_data, "priceBandQuestion must be present"
    assert "skuImpactQuestion" in m_data, "skuImpactQuestion must be present"
    print(f"   [PASS] Market Overview: CR4={m_data.get('cr4')}%, Price Brackets={len(m_data.get('priceBrackets', []))}")
    print(f"   [PASS] 4 Core Questions answered for Executive: Size, Concentration, Price Band, SKU Impact")

    # 5. Module 2: Core 4 SKU War Room & Zero Fake Fallback Check
    print("\n[Test 5] Module 2: Core Products Registry & Scalar BSR...")
    prods_resp = client.get("/api/core-products")
    assert prods_resp.status_code == 200
    skus = prods_resp.json().get("data", [])
    assert len(skus) == 4, f"Expected strictly 4 core SKUs, found {len(skus)}"
    asin_list = [p["asin"] for p in skus]
    assert "B0GYH8WT22" in asin_list
    assert "B0GY2TDLTZ" in asin_list
    assert "B0GY2WGTDM" in asin_list
    print(f"   [PASS] Registry contains 4 core SKUs: {asin_list}")

    # Test individual ASIN BSR parsing and ensure no string coercion to [object Object]
    detail_resp = client.get("/api/core-products/B0GYH8WT22")
    assert detail_resp.status_code == 200
    prod_env = detail_resp.json()
    assert prod_env["status"] == "ok"
    prod_detail = prod_env.get("data", {})
    assert prod_detail.get("asin") == "B0GYH8WT22"
    bsr_val = prod_detail.get("bsr")
    assert not isinstance(bsr_val, dict), "BSR must be a scalar integer or None, not a raw object"
    assert str(bsr_val) != "[object Object]", "BSR must not be rendered as '[object Object]'"
    assert "plainDiagnosis" in prod_detail, "plainDiagnosis must be present"
    assert "lastPriceChange" in prod_detail, "lastPriceChange must be present"
    assert "priceStepPoints" in prod_detail, "priceStepPoints must be present"
    print(f"   [PASS] ASIN B0GYH8WT22 clean scalar BSR: {bsr_val}, price: {prod_detail.get('price')}")
    print(f"   [PASS] Plain diagnosis: {prod_detail.get('plainDiagnosis')}")

    # Test Competitors endpoint (4 pools)
    comp_resp = client.get("/api/core-products/B0GYH8WT22/competitors")
    assert comp_resp.status_code == 200
    comp_env = comp_resp.json()
    assert comp_env["status"] == "ok"
    comp_data = comp_env.get("data", {})
    assert "directCompetitors" in comp_data
    assert "benchmarkCompetitors" in comp_data
    assert "suggestedCompetitors" in comp_data
    assert "top100Pool" in comp_data
    assert len(comp_data["top100Pool"]) == 100, f"Expected 100 real items in top pool, got {len(comp_data['top100Pool'])}"
    first_item = comp_data["top100Pool"][0]
    assert "gap" in first_item, "Gap analysis must be present for competitor"
    assert "summary" in first_item["gap"]
    assert "insight" in first_item["gap"]
    print(f"   [PASS] Competitor 4 pools: suggested={len(comp_data['suggestedCompetitors'])}, top100={len(comp_data['top100Pool'])}")
    print(f"   [PASS] Competitor gap analysis verified: {first_item['gap']['summary']} | {first_item['gap']['insight']}")

    # Test Manual Competitor CRUD
    add_c_resp = client.post("/api/core-products/B0GYH8WT22/competitors/manual", json={
        "competitorAsin": "B0TESTMANUAL1",
        "notes": "单元测试直接竞品"
    })
    assert add_c_resp.status_code == 200
    print("   [PASS] Added manual direct competitor B0TESTMANUAL1")

    del_c_resp = client.delete("/api/core-products/B0GYH8WT22/competitors/B0TESTMANUAL1")
    assert del_c_resp.status_code == 200
    print("   [PASS] Removed manual direct competitor B0TESTMANUAL1")

    # Test Market Relative Performance
    comp_all = client.get("/api/core-products/comparison")
    assert comp_all.status_code == 200
    comp_all_env = comp_all.json()
    assert comp_all_env["status"] == "ok"
    skus_list = comp_all_env.get("data", {}).get("skus", [])
    assert len(skus_list) == 4
    print(f"   [PASS] SKU Comparison returned {len(skus_list)} items")

    # 6. Module 3: Pipeline (Memory Foam Candidates)
    print("\n[Test 6] Module 3: Supply Chain Extension Pipeline...")
    pipe_resp = client.get("/api/pipeline")
    assert pipe_resp.status_code == 200
    pipe_data = pipe_resp.json().get("data", {})
    pipeline_items = pipe_data.get("candidates", [])
    assert len(pipeline_items) >= 4, f"Expected at least 4 default supply chain candidates, got {len(pipeline_items)}"
    pipe_names = [p["name"] for p in pipeline_items]
    print(f"   [PASS] Pipeline candidates: {pipe_names}")

    # Test POST add to pipeline
    new_candidate = {
        "id": "test_knee_pillow",
        "name": "人体工学记忆棉夹腿枕 (Knee Pillow)",
        "keyword": "knee pillow for side sleepers",
        "categoryLevel": "四类 (需自行调取)",
        "nodeIdPath": "1055398:1063252:1199122:3732111",
        "status": "调研中",
        "decision": "继续观察",
        "rationale": "复用慢回弹记忆棉发泡模具，欧美侧睡人群痛点明确",
        "riskFlag": "需防范拉链及布套起球差评"
    }
    add_resp = client.post("/api/pipeline", json=new_candidate)
    assert add_resp.status_code == 200
    print("   [PASS] Added new candidate to pipeline successfully")

    # 7. Module 4: Opportunity Lab (Natural Language Research)
    print("\n[Test 7] Module 4: Opportunity Lab Research...")
    research_list_resp = client.get("/api/research")
    assert research_list_resp.status_code == 200
    existing_projects = research_list_resp.json().get("data", [])
    print(f"   [PASS] Existing research projects: {len(existing_projects)}")

    # Run research prompt
    research_req = {
        "userQuestion": "我想了解一下儿童防驼背矫正坐垫的市场机会与竞争情况",
        "marketplace": "US"
    }
    research_resp = client.post("/api/research", json=research_req)
    assert research_resp.status_code == 200
    research_env = research_resp.json()
    assert research_env["status"] == "ok"
    research_result = research_env.get("data", {})
    assert "plan" in research_result
    assert "findings" in research_result
    assert "title" in research_result
    print(f"   [PASS] Opportunity Lab completed research: {research_result.get('title')}")
    print(f"   [PASS] Findings conclusion: {research_result['findings'].get('conclusion', '')[:50]}...")

    # 8. Data Jobs & Daily Refresh
    print("\n[Test 8] Data Jobs & Monitoring...")
    jobs_resp = client.get("/api/data-jobs")
    assert jobs_resp.status_code == 200
    jobs = jobs_resp.json().get("data", [])
    print(f"   [PASS] Data jobs logged: {len(jobs)}")

    status_resp = client.get("/api/data-jobs/status")
    assert status_resp.status_code == 200
    st_env = status_resp.json()
    assert st_env["status"] == "ok"
    st_data = st_env.get("data", {})
    assert "cronSchedule" in st_data
    assert "nextRunAt" in st_data
    assert "monitoredTargetsCount" in st_data
    assert st_data["cronSchedule"] == "08:30 CST"
    print(f"   [PASS] Automation status verified: nextRun={st_data['nextRunAt']}, targets={st_data['monitoredTargetsCount']}")

    # 9. Phase 2 Replenishment Model (Kept for continuity)
    print("\n[Test 9] Phase 2: Replenishment Engine...")
    rep_resp = client.post("/api/replenishment/calc", json={
        "stock": 200,
        "dailySales": 50,
        "seaDays": 30,
        "batchSize": 10000,
        "unitCost": 50.0,
        "seaShippingRate": 12.0,
        "airShippingRate": 45.0
    })
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["stockDays"] == 4.0
    assert rep_data["riskLevel"] == "RED"
    print(f"   [PASS] Replenishment math verified: days={rep_data['stockDays']}, risk={rep_data['riskLevel']}")

    # 10. Zero Fake Fallback Check on Non-Existent ASIN
    print("\n[Test 10] Zero Fake Fallback Check on invalid/missing ASIN...")
    missing_resp = client.get("/api/core-products/INVALID_ASIN_99999")
    assert missing_resp.status_code == 200
    missing_env = missing_resp.json()
    missing_data = missing_env.get("data") or {}
    # It must NOT return default $45.99 or 4.2 rating
    assert missing_data.get("price") is None or missing_data.get("price") == 0.0, f"Price must not be fabricated: {missing_data.get('price')}"
    assert missing_data.get("rating") is None or missing_data.get("rating") == 0.0, f"Rating must not be fabricated: {missing_data.get('rating')}"
    print("   [PASS] Zero Fake Data strictly enforced: missing ASIN returns clean null/empty state")

    print("\n" + "=" * 65)
    print("  [SUCCESS] ALL 10 V2 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
