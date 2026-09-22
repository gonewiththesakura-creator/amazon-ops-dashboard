import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from ..mcp_client import mcp_client
from ..database import db

logger = logging.getLogger("opportunity_lab_service")

# Concept & English Keyword Decomposition Engine
INTENT_CONCEPT_MAPPINGS = [
    {
        "keywords": ["防驼背", "矫正", "坐垫", "姿势"],
        "concept": "人体工学姿势支撑与防驼背坐垫 (Ergonomic Posture Support Cushion)",
        "englishKeywords": [
            "posture support cushion",
            "sitting posture corrector seat",
            "ergonomic back support cushion",
            "spine alignment seat pad"
        ],
        "complianceWarning": "涉及姿势支撑与防驼背宣称（Postural Correction），必须做 Amazon FDA / Medical Claims 医疗器械与功能宣称合规排查，切忌直接在 Listing 中使用 treat / cure / correction 等词汇。"
    },
    {
        "keywords": ["开学", "文具", "一年级", "小学"],
        "concept": "小学开学季文具礼包组合 (Elementary School Supplies Bundle)",
        "englishKeywords": [
            "school supplies set",
            "back to school stationery kit",
            "elementary school supplies bundle",
            "kids pencil box bundle"
        ],
        "complianceWarning": "属于典型开学季（7-8月）季节性波段产品，非四季刚需，需注意非旺季断崖式库存滞销风险。"
    },
    {
        "keywords": ["宠物", "慢食", "慢食碗", "防噎"],
        "concept": "宠物防噎慢食益智碗 (Slow Feeder Pet Bowl)",
        "englishKeywords": [
            "slow feeder dog bowl",
            "slow eat cat bowl",
            "anti choke pet bowl",
            "interactive puzzle feeder"
        ],
        "complianceWarning": "需确保采用食品接触级材质（BPA Free，FDA Food Grade）并具备洗碗机耐温安全性认证。"
    },
    {
        "keywords": ["露营", "露营车", "折叠桌", "小桌"],
        "concept": "露营车扩展折叠桌面配件 (Collapsible Wagon Table Top)",
        "englishKeywords": [
            "wagon folding table",
            "camping cart table top",
            "collapsible wagon accessory table"
        ],
        "complianceWarning": "需重点防范不同品牌露营车卡槽尺寸不兼容带来的高退货率与差评风险。"
    },
    {
        "keywords": ["婴儿", "定型", "枕头", "防偏头"],
        "concept": "婴儿定型防偏头护颈枕 (Infant Head Shaping Pillow)",
        "englishKeywords": [
            "baby head shaping pillow",
            "infant flat head support",
            "baby positioning pillow"
        ],
        "complianceWarning": "美国 CPSC 与 Amazon 对婴儿睡眠产品审查极为严苛，严禁涉及预防婴儿猝死 (SIDS) 或医疗重塑头型等绝对宣称。"
    }
]

def parse_research_intent(user_question: str) -> Tuple[str, List[str], str]:
    """Parses natural language query into product concept, candidate English keywords, and compliance flags."""
    user_q = user_question.lower()
    
    for mapping in INTENT_CONCEPT_MAPPINGS:
        if any(kw in user_q for kw in mapping["keywords"]):
            return mapping["concept"], mapping["englishKeywords"], mapping["complianceWarning"]
            
    # Generic extraction fallback
    cleaned = user_question.replace("我想看看", "").replace("有没有机会", "").replace("能不能做", "").replace("做不做", "").replace("调研一下", "").strip("，。？? ")
    if not cleaned:
        cleaned = "ergonomic lifestyle product"
        
    return f"【探索品类】{cleaned}", [cleaned, f"{cleaned} set", f"{cleaned} for home"], "需在立项前确认产品是否涉及特殊认证（FCC/FDA/CPSC/CPC）或专利侵权排查。"

async def conduct_new_category_research(user_question: str, marketplace: str = "US") -> Dict[str, Any]:
    """Autonomous Research Engine for completely new product/market opportunities.
    1. Interprets natural language intent into English keywords
    2. Multi-keyword demand verification via SellerSprite MCP
    3. Categorizes outcome into 4 strictly truthful decision states (🟢/🟡/🔵/🔴)
    4. ZERO fake fallbacks (avgPrice is None if no price data; zero searches NEVER gives 'clear demand')
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    marketplace = marketplace.upper()
    user_question = user_question.strip()

    # 1. Intent & English keyword extraction
    concept_title, candidate_keywords, compliance_warning = parse_research_intent(user_question)

    # 2. Explore category nodes using first primary keyword
    primary_kw = candidate_keywords[0]
    node_env = await mcp_client.call_tool("product_node", {
        "request": {
            "marketplace": marketplace,
            "keyword": primary_kw
        }
    })
    nodes = node_env.get("data") or []
    
    category_levels = []
    best_node_id = None
    if nodes and isinstance(nodes, list) and len(nodes) > 0:
        first = nodes[0]
        best_node_id = first.get("nodeIdPath")
        path_label = first.get("nodeLabelPath") or primary_kw
        category_levels = [seg.strip() for seg in path_label.split(":")]
    else:
        category_levels = ["General Merchandise", concept_title]

    # 3. Multi-keyword verification: Query keyword miner for up to 3 candidate keywords concurrently
    mined_keywords_pool = []
    total_searches = 0
    all_prices = []

    for kw in candidate_keywords[:3]:
        try:
            miner_env = await mcp_client.call_tool("keyword_miner", {
                "request": {
                    "marketplace": marketplace,
                    "keyword": kw,
                    "size": 5
                }
            })
            m_data = miner_env.get("data")
            kw_items = []
            if isinstance(m_data, dict):
                kw_items = m_data.get("items", [])
            elif isinstance(m_data, list):
                kw_items = m_data
            
            for item in kw_items:
                if isinstance(item, dict):
                    k_str = item.get("keyword") or item.get("word")
                    searches = item.get("searches") or 0
                    price_val = item.get("price")
                    mined_keywords_pool.append({
                        "keyword": k_str,
                        "searches": int(searches) if str(searches).isdigit() else 0,
                        "price": float(price_val) if price_val and str(price_val).replace('.', '', 1).isdigit() and float(price_val) > 0 else None,
                        "purchases": item.get("purchases"),
                        "purchaseRate": item.get("purchaseRate")
                    })
                    if searches and str(searches).isdigit():
                        total_searches += int(searches)
                    if price_val and str(price_val).replace('.', '', 1).isdigit() and float(price_val) > 0:
                        all_prices.append(float(price_val))
        except Exception as e:
            logger.warning(f"Failed to mine keyword '{kw}': {e}")

    # Remove duplicate keywords
    unique_mined = []
    seen_words = set()
    for mk in mined_keywords_pool:
        if mk["keyword"] and mk["keyword"] not in seen_words:
            seen_words.add(mk["keyword"])
            unique_mined.append(mk)

    # Calculate real scalar average price - ZERO FAKE FALLBACK (None if unavailable)
    avg_price = round(sum(all_prices) / len(all_prices), 2) if all_prices else None
    price_range_str = f"${min(all_prices):.1f} - ${max(all_prices):.1f}" if all_prices else "暂无有效价格数据"

    # 4. Strictly evaluate one of 4 Truthful Decision States
    # 🟢 值得深入 | 🟡 有信号，但证据不足 | 🔵 数据不足，继续采集 | 🔴 暂不建议
    if total_searches == 0 or len(unique_mined) == 0:
        decision_status = "🔵 数据不足，继续采集"
        status_code = "insufficient_data"
        status_badge = "badge-blue"
        conclusion = "目前核心关键词未获取到有效搜索与购买需求数据，暂时不能判断是否值得做。"
        opportunities = [] # STRICTLY EMPTY WHEN DEMAND IS ZERO!
        
        why = [
            "需求端：测试的英文核心词组未探测到有效月搜索量，暂无消费者明确搜索证据。",
            f"竞争端：已探测到 {len(nodes)} 个可能类目节点，需进一步扩展长尾词或反查头部 ASIN。",
            f"价格端：{price_range_str}，尚不具备统计置信度。",
            f"合规与风险：{compliance_warning}"
        ]
        next_actions = [
            "动作 1：重新使用更通用的 5 个英文核心词扩大查询范围；",
            "动作 2：在亚马逊前台手工找到 5-10 个真实竞品 ASIN，导入系统进行反查与流量词逆向解析。"
        ]
    elif total_searches < 3000:
        decision_status = "🟡 有信号，但证据不足"
        status_code = "weak_signal"
        status_badge = "badge-amber"
        conclusion = f"赛道存在小众长尾搜索（月搜索约 {total_searches:,} 次），但规模偏小，需谨慎验证供应链起订量与毛利空间。"
        opportunities = [
            f"小众长尾需求：核心词月搜索量约 {total_searches:,} 次，存在特定人群痛点。"
        ]
        why = [
            f"需求端：核心词月搜索 {total_searches:,} 次，体量有限，难以支撑大规模备货。",
            f"价格端：{price_range_str}。" if avg_price else "价格端：暂无充分价格样本。",
            f"合规与风险：{compliance_warning}"
        ]
        next_actions = [
            "动作 1：测算工厂首单起订量（MOQ）与单件打样成本；",
            "动作 2：确认该小众客群是否具备高溢价支付意愿以弥补订单频次不足。"
        ]
    else:
        decision_status = "🟢 值得深入"
        status_code = "promising"
        status_badge = "badge-green"
        conclusion = f"赛道具有明确的规模化消费需求（核心词月搜索达 {total_searches:,} 次），建议进一步拆解头部竞品与供应链成本。"
        opportunities = [
            f"需求规模充足：核心关键词月搜索热度达 {total_searches:,} 次，流量池具备支撑力。",
            f"价格空间：主流客单价约 {price_range_str}，具备健康毛利支撑空间。" if avg_price else "价格空间待结合标杆竞品进一步测算。"
        ]
        why = [
            f"需求端：核心词月搜索达 {total_searches:,} 次，消费者主动寻找解决方案意愿强烈。",
            f"价格端：客单均价约 {f'${avg_price}' if avg_price else '待定'}，处于健康消费区间。",
            f"合规与风险：{compliance_warning}"
        ]
        next_actions = [
            "动作 1：挑选 3-5 款热销标杆竞品反查其核心出单关键词与差评退货痛点；",
            "动作 2：核算供应链开模与量产综合成本，评估首批小单测款可行性。"
        ]

    # 5. Formulate structured plan & findings
    plan = {
        "targetMarket": marketplace,
        "productConcept": concept_title,
        "candidateKeywords": candidate_keywords,
        "categoryLevels": category_levels,
        "primaryNodeId": best_node_id,
        "evaluationCriteria": ["搜索容量置信度", "类目竞争壁垒", "价格与毛利空间", "法规与平台合规审查"]
    }

    findings = {
        "conclusion": conclusion,
        "decisionStatus": decision_status,
        "statusCode": status_code,
        "statusBadge": status_badge,
        "totalSearches": total_searches,
        "avgEstimatedPrice": avg_price,
        "priceRange": price_range_str,
        "complianceWarning": compliance_warning,
        "why": why,
        "opportunities": opportunities,
        "nextActions": next_actions,
        "discoveredKeywords": unique_mined[:10],
        "evidenceChain": [
            f"输入想法：{user_question}",
            f"意图解析产品：{concept_title}",
            f"检索核心英文词：{', '.join(candidate_keywords)}",
            f"匹配四级节点：{best_node_id or '未匹配到固定节点'}",
            f"关键词月搜索合计：{total_searches:,} 次",
            f"判定结果：{decision_status}"
        ]
    }

    # 6. Persist to SQLite research_projects
    project_id = None
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO research_projects (title, research_type, status, user_question, plan_json, findings_json)
                VALUES (?, 'new_category', ?, ?, ?, ?)
            """, (concept_title, status_code, user_question, json.dumps(plan, ensure_ascii=False), json.dumps(findings, ensure_ascii=False)))
            conn.commit()
            project_id = cur.lastrowid
    except Exception as e:
        logger.error(f"Failed to persist research project: {e}")

    return {
        "status": "ok",
        "source": "opportunity_lab_v2.3",
        "fetchedAt": now_iso,
        "data": {
            "projectId": project_id,
            "title": concept_title,
            "userQuestion": user_question,
            "decisionStatus": decision_status,
            "statusCode": status_code,
            "statusBadge": status_badge,
            "conclusion": conclusion,
            "why": why,
            "nextActions": next_actions,
            "complianceWarning": compliance_warning,
            "plan": plan,
            "findings": findings
        },
        "error": None
    }

def get_all_research_projects() -> List[Dict[str, Any]]:
    """Lists all historical new category research projects directly from local warehouse."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_projects ORDER BY id DESC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["plan"] = json.loads(d["plan_json"]) if d.get("plan_json") else {}
            except Exception:
                d["plan"] = {}
            try:
                d["findings"] = json.loads(d["findings_json"]) if d.get("findings_json") else {}
            except Exception:
                d["findings"] = {}
            result.append(d)
        return result

def get_research_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single research project by ID from local warehouse."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["plan"] = json.loads(d["plan_json"]) if d.get("plan_json") else {}
        d["findings"] = json.loads(d["findings_json"]) if d.get("findings_json") else {}
        return d
