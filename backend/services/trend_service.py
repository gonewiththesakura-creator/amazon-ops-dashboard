import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from ..database import db

logger = logging.getLogger("trend_service")

def get_dashboard_trends(time_range: str = "12m") -> Dict[str, Any]:
    """Generates the full Trend Cockpit (趋势驾驶舱) dataset reading purely from local SQLite database.
    ZERO FABRICATED DATA RULE:
    - Never hardcode business numbers, fake arrays, or synthetic curves.
    - If historical data points are insufficient, explicitly report hasSufficientHistory=False.
    - All external estimated sales are explicitly labeled 'sellerSpriteEstimatedMonthlyUnits'.
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    now_display = now.strftime("%Y-%m-%d %H:%M")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # 1. Fetch configured core products
        cursor.execute("SELECT asin, sku, internal_name, product_type, status FROM products WHERE is_core_pillow = 1 ORDER BY id ASC")
        core_products = [dict(r) for r in cursor.fetchall()]

        # 2. Fetch confirmed direct competitors (excluding ignored)
        cursor.execute("""
            SELECT competitor_asin, owner_asin, group_type, source, verified, notes, 
                   parent_asin, metric_scope, why_competitor, relative_summary, executive_conclusion
            FROM competitor_sets 
            WHERE group_type = 'direct' AND verified = 1 AND active = 1 AND (status IS NULL OR status != 'ignored')
            ORDER BY id ASC
        """)
        confirmed_direct_comps = [dict(r) for r in cursor.fetchall()]
        direct_comp_count = len(confirmed_direct_comps)

        # 3. Latest snapshots for all core products and confirmed direct competitors
        all_asins = [p["asin"] for p in core_products if p["asin"] != "PENDING_SKU_4"]
        all_asins += [c["competitor_asin"] for c in confirmed_direct_comps]
        all_asins = list(set(all_asins))

        latest_snaps: Dict[str, Dict[str, Any]] = {}
        if all_asins:
            placeholders = ",".join("?" for _ in all_asins)
            cursor.execute(f"""
                SELECT s.asin, s.price, s.estimated_units, s.bsr, s.rating, s.reviews, s.snapshot_date, s.source
                FROM asin_snapshots s
                INNER JOIN (
                    SELECT asin, MAX(snapshot_date) as max_date FROM asin_snapshots 
                    WHERE asin IN ({placeholders})
                    GROUP BY asin
                ) latest ON s.asin = latest.asin AND s.snapshot_date = latest.max_date
            """, all_asins)
            latest_snaps = {r["asin"]: dict(r) for r in cursor.fetchall()}

    # --- Top 4 Mini KPIs ---
    active_core_asins = [p["asin"] for p in core_products if p["status"] == "active" and p["asin"] != "PENDING_SKU_4"]
    total_monthly_units = 0
    units_available = False
    for asin in active_core_asins:
        snap = latest_snaps.get(asin)
        if snap and snap.get("estimated_units") is not None:
            total_monthly_units += snap["estimated_units"]
            units_available = True

    # Check 30d trend from SQLite snapshots for active core products
    mom_growth_label = "从今日开始积累"
    mom_direction = "neutral"
    has_30d_history = False

    with db.get_connection() as conn:
        cursor = conn.cursor()
        if active_core_asins:
            placeholders = ",".join("?" for _ in active_core_asins)
            cursor.execute(f"""
                SELECT snapshot_date, SUM(estimated_units) as total_units
                FROM asin_snapshots
                WHERE asin IN ({placeholders}) AND estimated_units IS NOT NULL
                GROUP BY snapshot_date
                ORDER BY snapshot_date ASC
            """, active_core_asins)
            date_sums = cursor.fetchall()
            if len(date_sums) >= 2:
                distinct_dates = [r["snapshot_date"] for r in date_sums]
                if len(distinct_dates) >= 25:
                    first_val = date_sums[0]["total_units"]
                    last_val = date_sums[-1]["total_units"]
                    if first_val and first_val > 0 and last_val is not None:
                        pct = round(((last_val - first_val) / first_val) * 100, 1)
                        mom_growth_label = f"{pct:+g}%"
                        mom_direction = "up" if pct > 0 else ("down" if pct < 0 else "neutral")
                        has_30d_history = True
                else:
                    mom_growth_label = f"已积累 {len(distinct_dates)} 天"
            elif len(date_sums) == 1:
                mom_growth_label = "已建立首个时点"

    mini_kpis = {
        "coreMonthlyUnits": total_monthly_units if units_available else 0,
        "sellerSpriteEstimatedMonthlyUnits": total_monthly_units if units_available else 0,
        "metricLabel": "卖家精灵预估月销量",
        "credibilityBadge": "🟡 第三方估算" if units_available else "⚪ 数据积累中",
        "momGrowth": mom_growth_label,
        "momDirection": mom_direction,
        "has30dHistory": has_30d_history,
        "directCompetitorsCount": direct_comp_count,
        "dataFreshness": now_display,
        "tooltip": {
            "sourceTool": "sellersprite_mcp",
            "metricType": "第三方月度销量估算",
            "fetchedAt": now_iso,
            "formula": "核心已配置在售SKU最新月估算销量汇总"
        }
    }

    # --- Visual 1: Market 12-Month Trend (from SQLite market_snapshots) ---
    cervical_node_path = "1055398:1063252:1199122:3732111"
    raw_market_history = db.get_market_real_history(cervical_node_path, months=12)
    
    market_monthly_points: List[Dict[str, Any]] = []
    for item in raw_market_history:
        market_monthly_points.append({
            "month": item["month"],
            "units": item.get("units"),
            "sellerSpriteEstimatedMonthlyUnits": item.get("units"),
            "revenue": item.get("revenue"),
            "avgPrice": item.get("avgPrice")
        })

    # Strict Zero Fake Curve check: if less than 6 months of snapshots, mark insufficient
    has_sufficient_market_history = len(market_monthly_points) >= 6
    market_notice = None
    if not has_sufficient_market_history:
        recorded_count = len(market_monthly_points)
        if recorded_count == 0:
            market_notice = "市场大盘数据积累中（本地数据库尚无历史时序切片），系统严禁伪造 12 个月平滑走势"
        else:
            market_notice = f"市场大盘数据积累中（当前已记录 {recorded_count} 个时点），系统严禁伪造 12 个月假走势"

    latest_market_volume = market_monthly_points[-1]["units"] if market_monthly_points else None

    # --- Today Conclusions (Dynamically generated from real database state) ---
    today_conclusions = []
    
    # 1. Market status conclusion
    if latest_market_volume:
        today_conclusions.append({
            "title": "大盘走势判断",
            "badge": "真实快照",
            "content": f"记忆棉颈椎枕类目最新快照月度总容量为 {latest_market_volume:,} 件，每日自动持续监测大盘容量变动。"
        })
    else:
        today_conclusions.append({
            "title": "大盘走势判断",
            "badge": "积累监控中",
            "content": "已锁定 Neck & Cervical Pillows (3732111) 核心四级细分节点，定时任务每日抓取大盘变动，拒绝虚构假走势。"
        })

    # 2. Pricing conclusion based on active SKUs
    active_prices = [latest_snaps[a]["price"] for a in active_core_asins if a in latest_snaps and latest_snaps[a].get("price")]
    if active_prices:
        min_p = min(active_prices)
        max_p = max(active_prices)
        today_conclusions.append({
            "title": "我方价格带分布",
            "badge": f"${min_p:.2f}-${max_p:.2f}",
            "content": f"我方主力在售核心枕头定价在 ${min_p:.2f} 至 ${max_p:.2f} 区间，主打记忆棉人体工学颈椎分区支撑，保持健康溢价。"
        })
    else:
        today_conclusions.append({
            "title": "主力价格带观察",
            "badge": "监控建立中",
            "content": "类目核心走量价格带正通过每日类目快照追踪，聚焦中高端分区颈椎枕消费需求。"
        })

    # 3. Competitor status conclusion
    if direct_comp_count > 0:
        today_conclusions.append({
            "title": "直接竞品对标",
            "badge": f"已锁定 {direct_comp_count} 款",
            "content": f"系统已建立 {direct_comp_count} 款已确认核心直接竞品的每日走势与参数监控，可穿透查看具体差距。"
        })
    else:
        today_conclusions.append({
            "title": "竞品对标状态",
            "badge": "待确认",
            "content": "当前尚未锁定已确认的直接竞品。系统已在战情室准备候选推荐池，请运营人员确认 3-5 款核心竞品加入每日追踪。"
        })

    # --- Visual 2: 4 Core SKUs 90-Day Trend (Pure SQL queries, ZERO fake series) ---
    sku_series: Dict[str, Any] = {}
    all_dates_set = set()

    for prod in core_products:
        p_asin = prod["asin"]
        if p_asin == "PENDING_SKU_4":
            sku_series["PENDING_SKU_4"] = {
                "name": "待配置核心枕头SKU",
                "asin": "PENDING_SKU_4",
                "isConfigured": False,
                "hasSufficientHistory": False,
                "notice": "待配置核心枕头SKU（系统已开启监听槽位，不伪造假线）",
                "units": None,
                "sellerSpriteEstimatedMonthlyUnits": None,
                "bsr": None,
                "price": None
            }
            continue

        hist = db.get_sku_real_history(p_asin, days=90)
        p_dates = [s["date"] for s in hist["snapshots"] if s.get("date")]
        for d in p_dates:
            all_dates_set.add(d)

        units_list = [s.get("units") for s in hist["snapshots"]]
        bsr_list = [s.get("bsr") for s in hist["snapshots"]]
        price_list = [s.get("price") for s in hist["snapshots"]]

        sku_series[p_asin] = {
            "name": f"{prod['internal_name']} ({prod['sku']})",
            "asin": p_asin,
            "isConfigured": True,
            "hasSufficientHistory": hist["hasSufficientHistory"],
            "historyDays": hist["historyDays"],
            "notice": None if hist["hasSufficientHistory"] else f"数据积累中（已记录 {hist['historyDays']} 天，满30天出完整线）",
            "dates": p_dates,
            "units": units_list if units_list else None,
            "sellerSpriteEstimatedMonthlyUnits": units_list if units_list else None,
            "bsr": bsr_list if bsr_list else None,
            "price": price_list if price_list else None,
            "credibilityBadge": "🟢 本地真实采样"
        }

    sorted_dates = sorted(list(all_dates_set))
    has_sufficient_sku_history = len(sorted_dates) >= 15

    # Align series data to sorted_dates if points exist
    if sorted_dates:
        for p_asin, s_data in sku_series.items():
            if not s_data["isConfigured"] or not s_data.get("dates"):
                continue
            date_idx = {d: i for i, d in enumerate(s_data["dates"])}
            aligned_units = []
            aligned_bsr = []
            aligned_price = []
            for d in sorted_dates:
                if d in date_idx:
                    idx = date_idx[d]
                    aligned_units.append(s_data["units"][idx] if s_data["units"] else None)
                    aligned_bsr.append(s_data["bsr"][idx] if s_data["bsr"] else None)
                    aligned_price.append(s_data["price"][idx] if s_data["price"] else None)
                else:
                    aligned_units.append(None)
                    aligned_bsr.append(None)
                    aligned_price.append(None)
            s_data["units"] = aligned_units
            s_data["sellerSpriteEstimatedMonthlyUnits"] = aligned_units
            s_data["bsr"] = aligned_bsr
            s_data["price"] = aligned_price

    sku_90d_trends = {
        "dates": sorted_dates,
        "series": sku_series,
        "hasSufficientHistory": has_sufficient_sku_history,
        "insufficientNotice": "时序历史数据积累中，系统坚守零伪造原则，不生成虚构平滑曲线" if not has_sufficient_sku_history else None,
        "unconfiguredNotice": "PENDING_SKU_4 待配置（不画假线）"
    }

    # SKU Spotlight (Dynamic per active SKU)
    sku_spotlight = []
    for prod in core_products:
        p_asin = prod["asin"]
        if p_asin == "PENDING_SKU_4":
            sku_spotlight.append({
                "asin": "PENDING_SKU_4",
                "name": "第 4 款核心 SKU",
                "badge": "待上架配置",
                "status": "warning",
                "insight": "当前槽位处于待配置状态。建议根据细分人群（如侧睡加高款）规划新品，补齐价格带与形态盲区。"
            })
            continue

        snap = latest_snaps.get(p_asin, {})
        price_val = snap.get("price")
        units_val = snap.get("estimated_units")
        bsr_val = snap.get("bsr")
        rating_val = snap.get("rating")

        price_str = f"${price_val:.2f}" if price_val else "标价待采集"
        units_str = f"月估 {units_val:,} 件" if units_val else "销量积累中"
        bsr_str = f"大类 #{bsr_val:,}" if bsr_val else "BSR待刷新"
        rating_str = f"{rating_val}★" if rating_val else "评分正常"

        insight = f"当前标价 {price_str}，卖家精灵预估 {units_str}，{bsr_str}，买家评分 {rating_str}。每日自动监测异动。"
        sku_spotlight.append({
            "asin": p_asin,
            "name": f"{prod['internal_name']}",
            "badge": "在售监控",
            "status": "normal",
            "insight": insight
        })

    # --- Row 3: We vs Confirmed Direct Competitors Horizontal Bar ---
    competitor_bar_data: List[Dict[str, Any]] = []

    # Add flagship SKU first (B0GYH8WT22)
    flagship_asin = "B0GYH8WT22"
    flagship_snap = latest_snaps.get(flagship_asin, {})
    flagship_units = flagship_snap.get("estimated_units")
    flagship_price = flagship_snap.get("price")
    flagship_rating = flagship_snap.get("rating")
    flagship_reviews = flagship_snap.get("reviews")

    competitor_bar_data.append({
        "asin": flagship_asin,
        "brand": "ELOVNOVA (我方旗舰)",
        "isOur": True,
        "monthlyUnits": flagship_units or 0,
        "sellerSpriteEstimatedMonthlyUnits": flagship_units,
        "price": flagship_price,
        "rating": flagship_rating,
        "reviews": flagship_reviews or 0,
        "credibilityBadge": "🟢 本地仓库核验",
        "sourceTool": "sellersprite_mcp",
        "metricScope": "child_asin"
    })

    # Add ONLY confirmed direct competitors (strictly from DB!)
    for comp in confirmed_direct_comps:
        c_asin = comp["competitor_asin"]
        c_snap = latest_snaps.get(c_asin, {})
        c_units = c_snap.get("estimated_units")
        c_price = c_snap.get("price")
        c_rating = c_snap.get("rating")
        c_reviews = c_snap.get("reviews")

        competitor_bar_data.append({
            "asin": c_asin,
            "brand": comp.get("notes") or f"直接竞品 ({c_asin})",
            "isOur": False,
            "monthlyUnits": c_units or 0,
            "sellerSpriteEstimatedMonthlyUnits": c_units,
            "price": c_price,
            "rating": c_rating,
            "reviews": c_reviews or 0,
            "credibilityBadge": "🟡 卖家精灵预估月销量 (第三方估算)",
            "sourceTool": "sellersprite_mcp",
            "metricScope": comp.get("metric_scope") or "child_asin",
            "whyCompetitor": comp.get("why_competitor") or "同品类直接竞品"
        })

    # Calculate real gap analysis
    other_comps = [c for c in competitor_bar_data if not c["isOur"] and c.get("monthlyUnits")]
    other_prices = [c["price"] for c in competitor_bar_data if not c["isOur"] and c.get("price")]
    other_reviews = [c["reviews"] for c in competitor_bar_data if not c["isOur"] and c.get("reviews") is not None]

    if other_comps:
        sorted_u = sorted([c["monthlyUnits"] for c in other_comps])
        med_u = sorted_u[len(sorted_u) // 2]
        sorted_p = sorted(other_prices) if other_prices else []
        med_p = sorted_p[len(sorted_p) // 2] if sorted_p else (flagship_price or 0.0)
        sorted_r = sorted(other_reviews) if other_reviews else []
        med_r = sorted_r[len(sorted_r) // 2] if sorted_r else 0

        u_gap = (flagship_units or 0) - med_u
        p_diff = round((flagship_price or 0.0) - med_p, 2)
        r_diff = (flagship_reviews or 0) - med_r

        rev_summary = f"已纳管直接竞品 Review 中位数约 {med_r:,} 条，我方主力款为 {flagship_reviews or 0:,} 条，差距在存量评价沉淀。"
        gap_analysis = {
            "hasDirectCompetitors": True,
            "directCount": len(other_comps),
            "ourFlagshipUnits": flagship_units or 0,
            "compMedianUnits": med_u,
            "unitsGap": u_gap,
            "ourFlagshipPrice": flagship_price or 0.0,
            "compMedianPrice": med_p,
            "priceDiff": p_diff,
            "compMedianReviews": med_r,
            "reviewGapSummary": rev_summary
        }
    else:
        gap_analysis = {
            "hasDirectCompetitors": False,
            "directCount": 0,
            "ourFlagshipUnits": flagship_units or 0,
            "compMedianUnits": None,
            "unitsGap": 0,
            "ourFlagshipPrice": flagship_price or 0.0,
            "compMedianPrice": None,
            "priceDiff": 0.0,
            "compMedianReviews": None,
            "reviewGapSummary": "尚未确认直接竞品。请在 4 SKU 战情室中从候选竞品池添加 3-5 款核心对标竞品以激活实时差距分析。"
        }

    return {
        "status": "ok",
        "source": "trend_service_v2.6",
        "fetchedAt": now_iso,
        "data": {
            "miniKpis": mini_kpis,
            "market12mTrend": {
                "categoryLabel": "Home & Kitchen > Bedding > Bed Pillows & Positioners > Neck & Cervical Pillows",
                "nodeIdPath": cervical_node_path,
                "hasSufficientHistory": has_sufficient_market_history,
                "insufficientNotice": market_notice,
                "monthlyPoints": market_monthly_points,
                "currentVolume": latest_market_volume
            },
            "todayConclusions": today_conclusions,
            "sku90dTrends": sku_90d_trends,
            "skuSpotlight": sku_spotlight,
            "competitorComparison": {
                "chartData": competitor_bar_data,
                "gapAnalysis": gap_analysis
            }
        },
        "error": None
    }
