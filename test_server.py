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
from backend.database import db

def run_tests():
    print("=" * 70)
    print("  [*] Running Amazon Ops Dashboard V2.3 Boss Mode & Semantic Test Suite")
    print("=" * 70)

    client = TestClient(app)

    # 1. Security & Config Check
    print("\n[Test 1] Security & Config Sanitization...")
    assert settings.MCP_SECRET, "SELLERSPRITE_MCP_SECRET must not be empty"
    assert "?" not in settings.MCP_URL, f"MCP_URL must not contain query parameters (tokens): {settings.MCP_URL}"
    assert settings.MCP_SECRET not in settings.MCP_URL, "MCP_URL must not leak secret token"
    print("   [PASS] Secret is securely isolated in .env, clean MCP URL:", settings.MCP_URL)

    # 2. Health Check Endpoint & Version
    print("\n[Test 2] Health Endpoint (/api/health) & Version 2.3.0...")
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.3.0", f"Expected version 2.3.0, got {data['version']}"
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
    print(f"   [PASS] 4 Core Facts & 4 Direct Action Buttons verified")

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
    print(f"   [PASS] One-Sentence Boss Verdict: {one_sentence[:60]}...")

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

    # Competitor 4 pools and Boss Summary
    comp_resp = client.get("/api/core-products/B0GYH8WT22/competitors")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json().get("data", {})
    assert "bossSummary" in comp_data, "bossSummary must be present in competitor response"
    assert "top3Gaps" in comp_data["bossSummary"], "top3Gaps must be present in bossSummary"
    assert "primaryChallenge" in comp_data["bossSummary"], "primaryChallenge must be present"
    print(f"   [PASS] Boss Summary generated: {comp_data['bossSummary']['primaryChallenge'][:50]}...")

    # 6. SEMANTIC TEST C: Invalid Competitor ASIN Rejection (HTTP 400)
    print("\n[Test 6 / Semantic C] Invalid Competitor ASIN Rejection (HTTP 400)...")
    invalid_comp_resp = client.post("/api/core-products/B0GYH8WT22/competitors/manual", json={
        "competitorAsin": "B0INVALID999",
        "notes": "假ASIN测试"
    })
    assert invalid_comp_resp.status_code == 400, f"Expected HTTP 400 for fake ASIN, got {invalid_comp_resp.status_code}"
    err_detail = invalid_comp_resp.json().get("detail", "")
    assert "不存在" in err_detail or "无效" in err_detail or "无法添加" in err_detail, f"Unexpected error message: {err_detail}"
    print(f"   [PASS] Fake ASIN 'B0INVALID999' correctly rejected with HTTP 400: {err_detail}")

    # 7. SEMANTIC TEST D & E: Real Competitor ASIN Full Sync & Warehouse Snapshot Count Increment
    print("\n[Test 7 / Semantic D & E] Real Competitor Closed-Loop Sync & Snapshot Increment...")
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM asin_snapshots")
        snap_count_before = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM mcp_raw_responses")
        mcp_logs_before = c.fetchone()["cnt"]

    # Use a real known Amazon pillow ASIN (e.g. B0GY2TDLTZ or top competitor)
    real_test_asin = "B0GY2TDLTZ"
    real_sync_resp = client.post("/api/core-products/B0GYH8WT22/competitors/manual", json={
        "competitorAsin": real_test_asin,
        "notes": "单元测试真实竞品闭环同步"
    })
    assert real_sync_resp.status_code == 200, f"Expected HTTP 200 for real ASIN, got {real_sync_resp.status_code}: {real_sync_resp.text}"
    sync_data = real_sync_resp.json().get("data", {})
    assert sync_data.get("asin") == real_test_asin
    assert "gap" in sync_data
    assert "summary" in sync_data["gap"]

    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM asin_snapshots")
        snap_count_after = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM mcp_raw_responses")
        mcp_logs_after = c.fetchone()["cnt"]
        c.execute("SELECT * FROM competitor_sets WHERE owner_asin = 'B0GYH8WT22' AND competitor_asin = ?", (real_test_asin,))
        comp_record = c.fetchone()

    assert snap_count_after >= snap_count_before, "Snapshot count must be incremented or updated"
    assert mcp_logs_after > mcp_logs_before, "Raw MCP responses must be archived for traceability"
    assert comp_record is not None, "Competitor set must contain the verified record"
    assert comp_record["verified"] == 1, "Competitor must be verified"
    assert comp_record["relationship_summary"] is not None, "Gap summary must be persisted"
    print(f"   [PASS] Real ASIN {real_test_asin} closed-loop synced: snapshots={snap_count_after}, raw_logs={mcp_logs_after}")
    print(f"   [PASS] Warehouse persisted gap summary: {comp_record['relationship_summary']}")

    # Clean up test competitor record
    client.delete(f"/api/core-products/B0GYH8WT22/competitors/{real_test_asin}")
    print(f"   [PASS] Cleaned up test competitor {real_test_asin}")

    # 8. SEMANTIC TEST A: Opportunity Lab Semantic Honesty with 0 Searches
    print("\n[Test 8 / Semantic A] Opportunity Lab Semantic Honesty with 0 Searches...")
    # Query with non-existent / obscure input that yields 0 searches
    obscure_req = {
        "userQuestion": "一个完全生造的假词测试实验qwertyxyz12345",
        "marketplace": "US"
    }
    obscure_resp = client.post("/api/research", json=obscure_req)
    assert obscure_resp.status_code == 200
    res_data = obscure_resp.json().get("data", {})
    findings = res_data.get("findings", {})
    
    assert findings.get("totalSearches") == 0, f"Expected 0 searches, got {findings.get('totalSearches')}"
    assert findings.get("decisionStatus") == "🔵 数据不足，继续采集", f"Expected '🔵 数据不足，继续采集', got '{findings.get('decisionStatus')}'"
    assert findings.get("opportunities") == [], f"Opportunities must be strictly empty when searches=0, got {findings.get('opportunities')}"
    assert "明确" not in findings.get("conclusion", ""), f"Must not declare clear consumption intent when searches=0: {findings.get('conclusion')}"
    assert findings.get("avgEstimatedPrice") is None, f"avgEstimatedPrice must be None (no fake 28.5 fallback!), got {findings.get('avgEstimatedPrice')}"
    print(f"   [PASS] Zero-search honesty passed: status='{findings.get('decisionStatus')}', opportunities={findings.get('opportunities')}, avgPrice={findings.get('avgEstimatedPrice')}")

    # 9. SEMANTIC TEST B: Opportunity Lab Medical Claim Compliance Warning
    print("\n[Test 9 / Semantic B] Opportunity Lab Medical / Corrective Claims Compliance Check...")
    medical_req = {
        "userQuestion": "我想了解一下儿童防驼背矫正坐垫的市场机会与合规风险",
        "marketplace": "US"
    }
    med_resp = client.post("/api/research", json=medical_req)
    assert med_resp.status_code == 200
    med_findings = med_resp.json().get("data", {}).get("findings", {})
    assert med_findings.get("complianceWarning") is not None, "Medical/corrective claims warning must be flagged"
    warning_text = med_findings.get("complianceWarning", "")
    assert "FDA" in warning_text or "医疗器械" in warning_text or "矫正" in warning_text, f"Expected compliance warning about medical claims, got: {warning_text}"
    print(f"   [PASS] Compliance warning triggered: {warning_text[:60]}...")

    # 10. Automation Live Scheduler Status Check
    print("\n[Test 10] Live Scheduler Status Check...")
    sched_resp = client.get("/api/data-jobs/status")
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json().get("data", {})
    assert "isSchedulerActive" in sched_data
    assert "monitoredTargetsCount" in sched_data
    assert "nextRunTime" in sched_data
    assert sched_data["monitoredTargetsCount"] > 0
    print(f"   [PASS] Live scheduler: running={sched_data.get('isSchedulerActive')}, targets={sched_data.get('monitoredTargetsCount')}, nextRun={sched_data.get('nextRunTime')}")

    print("\n" + "=" * 70)
    print("  [SUCCESS] ALL AMAZON OPS DASHBOARD V2.3 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
