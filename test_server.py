import os
import sys
import hashlib
import shutil

# Configure UTF-8 encoding for standard output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure scratch project root is on sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# ----------------- Strict Test Isolation Setup -----------------
test_data_dir = os.path.join(project_root, "data")
os.makedirs(test_data_dir, exist_ok=True)
test_db_path = os.path.join(test_data_dir, "test_amazon_ops.db")

# Remove old test DB if present to ensure clean state
if os.path.exists(test_db_path):
    try:
        os.remove(test_db_path)
    except Exception:
        pass

# Set isolated test environment variables BEFORE importing backend modules
os.environ["APP_ENV"] = "test"
os.environ["DB_PATH"] = test_db_path

# Calculate baseline hash of production database to strictly prove zero pollution
prod_db_path = os.path.join(project_root, "backend", "v2_store.db")
def get_file_hash(path):
    if not os.path.exists(path):
        return None
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

prod_db_hash_before = get_file_hash(prod_db_path)

# Now safely import backend modules
from fastapi.testclient import TestClient
from backend.config import settings
from backend.main import app
from backend.database import db
from backend.services.pipeline_service import validate_pipeline_node

def run_tests():
    print("=" * 75)
    print("  [*] Running Amazon Ops Dashboard V2.4 & V2.5 Comprehensive Test Suite")
    print("      Database Isolation: " + test_db_path)
    print("=" * 75)

    with TestClient(app) as client:
        # 1. Security & Config Check
        print("\n[Test 1] Security & Config Sanitization...")
        assert settings.MCP_SECRET, "SELLERSPRITE_MCP_SECRET must not be empty"
        assert "?" not in settings.MCP_URL, f"MCP_URL must not contain query parameters (tokens): {settings.MCP_URL}"
        assert settings.MCP_SECRET not in settings.MCP_URL, "MCP_URL must not leak secret token"
        assert settings.APP_ENV == "test", "APP_ENV must be set to 'test'"
        assert settings.DB_PATH == test_db_path, f"DB_PATH must point to test DB, got: {settings.DB_PATH}"
        print("   [PASS] Clean MCP URL, secret isolated, test DB active:", settings.DB_PATH)

        # 2. Health Check Endpoint & Version
        print("\n[Test 2] Health Endpoint (/api/health) & Version 2.5.0...")
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.5.0", f"Expected version 2.5.0, got {data['version']}"
        print("   [PASS] Health check ok, upgraded version:", data["version"])

        # 3. Boss Mode Executive Briefing (4 Facts + 4 Actions)
        print("\n[Test 3] Boss Mode Briefing (/api/dashboard/briefing)...")
        resp = client.get("/api/dashboard/briefing")
        assert resp.status_code == 200
        briefing = resp.json().get("data", {})
        assert "headline" in briefing
        assert "bullets" in briefing
        assert "actions" in briefing, "Briefing must contain 4 direct action buttons"
        assert len(briefing["bullets"]) == 4, f"Boss Mode requires 4 core facts, got {len(briefing['bullets'])}"
        assert len(briefing["actions"]) == 4, f"Boss Mode requires 4 direct action buttons, got {len(briefing['actions'])}"
        print(f"   [PASS] Briefing Headline: {briefing['headline']}")

        # 4. Module 1: Core Market (Currency Formatting & Evidence)
        print("\n[Test 4] Module 1: Core Market & Zero '$xxxx万元' Bug Check...")
        market_resp = client.get("/api/core-market/overview")
        assert market_resp.status_code == 200
        m_data = market_resp.json().get("data", {})
        assert "nodeIdPath" in m_data
        assert "cr4" in m_data
        assert "priceBrackets" in m_data
        assert "executiveOneSentence" in m_data
        
        # Currency formatting check: Must NOT contain '$xxx 万元'
        one_sentence = m_data["executiveOneSentence"]
        verdict = m_data.get("marketSizeQuestion", {}).get("verdict", "")
        assert "$ " not in one_sentence and "$ 万元" not in one_sentence, f"Invalid currency formatting in: {one_sentence}"
        assert "万元" not in verdict or "万美元" in verdict or "万元人民币" in verdict, f"Invalid currency in verdict: {verdict}"
        assert "evidence" in m_data.get("marketSizeQuestion", {}), "Evidence must be present for Boss Mode"
        print(f"   [PASS] Market currency properly formatted ($XX.XM / 约 XX 万美元)")

        # 5. Module 2: Core 4 SKU War Room & Scalar BSR
        print("\n[Test 5] Module 2: Core Products Registry & Scalar BSR...")
        prods_resp = client.get("/api/core-products")
        assert prods_resp.status_code == 200
        skus = prods_resp.json().get("data", [])
        assert len(skus) == 4, f"Expected strictly 4 core SKUs, found {len(skus)}"
        
        detail_resp = client.get("/api/core-products/B0GYH8WT22")
        assert detail_resp.status_code == 200
        prod_detail = detail_resp.json().get("data", {})
        bsr_val = prod_detail.get("bsr")
        assert not isinstance(bsr_val, dict), "BSR must be a scalar integer or None"
        assert str(bsr_val) != "[object Object]", "BSR must not be rendered as '[object Object]'"
        print(f"   [PASS] ASIN B0GYH8WT22 clean scalar BSR: {bsr_val}, price: {prod_detail.get('price')}")

        comp_resp = client.get("/api/core-products/B0GYH8WT22/competitors")
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json().get("data", {})
        assert "bossSummary" in comp_data, "bossSummary must be present in competitor response"
        assert "top3Gaps" in comp_data["bossSummary"], "top3Gaps must be present in bossSummary"
        assert "primaryChallenge" in comp_data["bossSummary"], "primaryChallenge must be present"
        print(f"   [PASS] Boss Summary generated: {comp_data['bossSummary']['primaryChallenge'][:50]}...")

        # 6. V2.4 Trend Cockpit (/api/dashboard/trends)
        print("\n[Test 6] V2.4 Trend Cockpit (/api/dashboard/trends)...")
        trends_resp = client.get("/api/dashboard/trends?range=12m")
        assert trends_resp.status_code == 200
        t_json = trends_resp.json()
        assert t_json.get("status") == "ok"
        t_data = t_json.get("data", {})
        
        # Top 4 KPIs
        mini_kpis = t_data.get("miniKpis", {})
        assert "coreMonthlyUnits" in mini_kpis
        assert "momGrowth" in mini_kpis
        assert "directCompetitorsCount" in mini_kpis
        assert "dataFreshness" in mini_kpis
        
        # 12m Market Trend
        m12 = t_data.get("market12mTrend", {})
        m_points = m12.get("monthlyPoints", [])
        assert len(m_points) == 12, f"Expected 12 months data points, got {len(m_points)}"
        assert "month" in m_points[0] and "units" in m_points[0] and "revenue" in m_points[0]
        
        # 90d SKU Trends: Exactly 4 SKUs, 4th must be unconfigured notice with NO fake lines
        sku90 = t_data.get("sku90dTrends", {})
        series = sku90.get("series", {})
        assert len(series) == 4, f"Expected 4 SKU series, got {len(series)}"
        assert "PENDING_SKU_4" in series
        sku4 = series["PENDING_SKU_4"]
        assert sku4.get("isConfigured") is False, "4th SKU must be marked as not configured"
        assert sku4.get("units") is None, "Pending 4th SKU units must be None (zero fake lines!)"
        assert "待配置" in sku4.get("notice", "")
        
        # Competitor Comparison & Conclusions
        assert len(t_data.get("todayConclusions", [])) == 3, "Expected 3 today conclusions"
        assert len(t_data.get("skuSpotlight", [])) == 3, "Expected 3 sku spotlights"
        comp_comp = t_data.get("competitorComparison", {})
        assert "chartData" in comp_comp and "gapAnalysis" in comp_comp
        print("   [PASS] Trend Cockpit: 4 mini KPIs, 12m points, 4 SKU series (honest pending 4th SKU), 3 conclusions, 3 spotlights, competitor comparison")

        # 7. V2.4 Pipeline Node Integrity Validation & Anti-Pattern Blocking
        print("\n[Test 7] V2.4 Pipeline Node Validation & Anti-Pattern Blocking...")
        # Direct function check: Knee pillow on cervical node (3732111) MUST be blocked
        valid, reason = validate_pipeline_node("knee_pillow", "人体工学夹腿枕", "1055398:1063252:1199122:3732111", "Neck & Cervical Pillows")
        assert not valid, "validate_pipeline_node must block knee pillow on neck pillow node"
        assert "Knee Pillow" in reason or "绝不能套用" in reason
        print(f"   [PASS] Node validation correctly rejected Knee Pillow on Neck node: {reason[:60]}...")

        # Insert test knee pillow with wrong node to verify pipeline endpoint blocks it
        client.post("/api/pipeline", json={
            "id": "test_knee_item",
            "name": "测试夹腿枕 (Knee Pillow Test)",
            "keyword": "knee pillow",
            "nodeIdPath": "1055398:1063252:1199122:3732111",
            "status": "调研中",
            "decision": "待验证"
        })
        k_detail_resp = client.get("/api/pipeline/test_knee_item")
        assert k_detail_resp.status_code == 200
        k_detail = k_detail_resp.json().get("data", {})
        assert k_detail.get("hardFacts", {}).get("nodeVerified") is False, "Knee pillow on node 3732111 must have nodeVerified=False"
        assert "Knee Pillow" in k_detail.get("hardFacts", {}).get("verificationNote", "") or "套用" in k_detail.get("hardFacts", {}).get("verificationNote", "")
        print("   [PASS] Pipeline endpoint blocked wrong node data from contaminating knee pillow")

        # 8. V2.4 Pipeline 4-Screen Dossier & Decision Update
        print("\n[Test 8] V2.4 Pipeline 4-Screen Dossier & Decision Update...")
        pipe_detail_resp = client.get("/api/pipeline/travel_pillow")
        assert pipe_detail_resp.status_code == 200
        p_detail = pipe_detail_resp.json().get("data", {})
        assert "hardFacts" in p_detail, "Screen 1 Hard Facts must be present"
        assert "trend12m" in p_detail, "Screen 2 12m Trend must be present"
        assert "topCompetitors" in p_detail, "Screen 3 Top Competitors must be present"
        assert "supplyChainAnalysis" in p_detail, "Screen 4 Supply Chain Analysis must be present"
        assert "decisionOptions" in p_detail, "Decision Options must be present"
        
        # Update decision
        dec_resp = client.post("/api/pipeline/travel_pillow/decision", json={
            "decision": "小批量试水",
            "rationale": "自动化测试更新决策"
        })
        assert dec_resp.status_code == 200
        dec_check_resp = client.get("/api/pipeline/travel_pillow")
        assert dec_check_resp.json().get("data", {}).get("currentDecision") == "小批量试水"
        print("   [PASS] 4-screen dossier verified and decision updated to '小批量试水'")

        # 9. V2.4 Opportunity Lab Broad Query Split
        print("\n[Test 9] V2.4 Opportunity Lab Broad Query Split (shoes / 铅笔)...")
        broad_resp = client.post("/api/research", json={
            "userQuestion": "我想了解一下shoes类目"
        })
        assert broad_resp.status_code == 200
        b_findings = broad_resp.json().get("data", {}).get("findings", {})
        assert b_findings.get("dataState") == "broad_split", f"Expected 'broad_split', got {b_findings.get('dataState')}"
        assert len(b_findings.get("broadDirections", [])) == 5, f"Expected 5 split directions, got {len(b_findings.get('broadDirections', []))}"
        assert "chartDatasets" in b_findings
        print(f"   [PASS] Broad query 'shoes' successfully split into 5 niche directions: {[d['name'] for d in b_findings['broadDirections']]}")

        # 10. V2.4 Opportunity Lab Semantic Honesty (0 searches & no_data != 0)
        print("\n[Test 10] V2.4 Opportunity Lab Semantic Honesty with 0 Searches...")
        obscure_resp = client.post("/api/research", json={
            "userQuestion": "一个完全生造的假词测试实验qwertyxyz12345",
            "marketplace": "US"
        })
        assert obscure_resp.status_code == 200
        findings = obscure_resp.json().get("data", {}).get("findings", {})
        assert findings.get("dataState") == "no_data", f"Expected 'no_data', got {findings.get('dataState')}"
        assert findings.get("totalSearches") is None, f"Expected None for no_data, got {findings.get('totalSearches')}"
        assert "暂未取得" in findings.get("totalSearchesDisplay", "")
        assert findings.get("decisionStatus") == "🔵 暂未取得搜索数据", f"Expected '🔵 暂未取得搜索数据', got '{findings.get('decisionStatus')}'"
        assert findings.get("opportunities") == [], f"Opportunities must be strictly empty when no data, got {findings.get('opportunities')}"
        assert findings.get("avgEstimatedPrice") is None, f"avgEstimatedPrice must be None (no fake 28.5 fallback!), got {findings.get('avgEstimatedPrice')}"
        print("   [PASS] Strict no_data != 0 honesty: dataState='no_data', totalSearches=None, display='暂未取得搜索数据', avgPrice=None, opps=[]")

        # 11. V2.5 Manual Collection Center Packages & Warehouse Priority
        print("\n[Test 11] V2.5 Manual Collection Center Packages & Warehouse Priority...")
        # List registered MCP tools
        tools_resp = client.get("/api/collection/tools")
        assert tools_resp.status_code == 200
        tools = tools_resp.json().get("data", [])
        assert len(tools) >= 10, f"Expected at least 10 registered MCP tools, got {len(tools)}"
        print(f"   [PASS] Found {len(tools)} registered MCP tools in registry")

        # Single ASIN package collection
        asin_col_resp = client.post("/api/collection/asin", json={
            "asin": "B0GYH8WT22",
            "marketplace": "US",
            "forceRefresh": False
        })
        assert asin_col_resp.status_code == 200
        col_data = asin_col_resp.json()
        assert col_data.get("status") == "ok"
        assert col_data.get("asin") == "B0GYH8WT22"
        
        # Second fetch should hit local warehouse
        re_asin_col_resp = client.post("/api/collection/asin", json={
            "asin": "B0GYH8WT22",
            "marketplace": "US",
            "forceRefresh": False
        })
        assert re_asin_col_resp.status_code == 200
        re_col_data = re_asin_col_resp.json()
        assert re_col_data.get("source") == "local_warehouse", f"Expected 'local_warehouse', got {re_col_data.get('source')}"
        assert re_col_data.get("isLocalWarehouse") is True
        print("   [PASS] Collection ASIN package returned, second fetch hit local_warehouse")

        # 12. V2.5 Local Warehouse Assets Stats & Search
        print("\n[Test 12] V2.5 Local Warehouse Assets Stats & Search...")
        stats_resp = client.get("/api/assets/stats")
        assert stats_resp.status_code == 200
        s_data = stats_resp.json().get("data", {})
        required_asset_keys = ["asinCount", "pricePointsCount", "bsrPointsCount", "salesPointsCount", "keywordCount", "marketSnapshotsCount", "top100RecordsCount", "rawResponsesCount"]
        for k in required_asset_keys:
            assert k in s_data, f"Asset stats must contain '{k}'"
        print(f"   [PASS] Warehouse stats: 8 categories validated (asins={s_data['asinCount']}, pricePoints={s_data['pricePointsCount']}, raw={s_data['rawResponsesCount']})")

        # Search warehouse assets
        search_resp = client.get("/api/assets/search?q=B0GYH8WT22")
        assert search_resp.status_code == 200
        search_data = search_resp.json().get("data", [])
        assert len(search_data) > 0, "Warehouse search for B0GYH8WT22 should return matches"
        print(f"   [PASS] Search returned {len(search_data)} warehouse records for B0GYH8WT22")

        # 13. Automation Live Scheduler Status Check
        print("\n[Test 13] Live Scheduler Status Check...")
        sched_resp = client.get("/api/data-jobs/status")
        assert sched_resp.status_code == 200
        sched_data = sched_resp.json().get("data", {})
        assert sched_data.get("isSchedulerActive") is True
        print(f"   [PASS] Live scheduler running, monitored targets: {sched_data.get('monitoredTargetsCount')}")

    # 14. Strict Production DB Zero Pollution Verification
    print("\n[Test 14] Strict Production DB Zero Pollution Verification...")
    prod_db_hash_after = get_file_hash(prod_db_path)
    assert prod_db_hash_before == prod_db_hash_after, (
        f"CRITICAL FAILURE: Production database {prod_db_path} was modified during tests!\n"
        f"Before hash: {prod_db_hash_before}\n"
        f"After hash:  {prod_db_hash_after}"
    )
    print(f"   [PASS] Production DB SHA256 matches perfectly: {prod_db_hash_before}")
    print("   [PASS] Zero test pollution in production database verified!")

    # Clean up test database
    import gc
    gc.collect()
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
            print("   [PASS] Cleaned up test database data/test_amazon_ops.db")
        except Exception as e:
            print(f"   [WARN] Could not remove test DB: {e}")

    print("\n" + "=" * 75)
    print("  [SUCCESS] ALL AMAZON OPS DASHBOARD V2.4 & V2.5 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
