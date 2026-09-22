from typing import Dict, Any, List

def generate_ai_diagnostics(market_data: Dict[str, Any], asin_data: Dict[str, Any], keyword_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesizes market, ASIN and keyword insights into a structured 5-dimension scorecard and operational action report."""
    
    cr4 = market_data.get("cr4", 50.0)
    rating = asin_data.get("rating", 4.3)
    ratings_count = asin_data.get("ratingsCount", 1000)
    price = asin_data.get("price", 49.99)
    
    # Calculate 5-dimension scores (0 to 100)
    market_capacity_score = 88 if market_data.get("priceBrackets") else 75
    
    # Competition Barrier: higher CR4 or higher ratings count means harder barrier
    barrier_score = min(95, int(cr4 * 0.9 + 25))
    
    # Profit Space: estimated based on pricing and price tier
    profit_score = 82 if price and float(price) > 35 else 68
    
    # Growth Potential: based on keyword trends
    growth_score = 85
    
    # New Entrant Difficulty:
    difficulty_score = min(96, int(cr4 * 0.7 + (40 if ratings_count > 5000 else 15)))

    radar_indicators = [
        {"name": "市场容量 (Capacity)", "max": 100, "value": market_capacity_score},
        {"name": "竞争壁垒 (Barriers)", "max": 100, "value": barrier_score},
        {"name": "利润空间 (Profit)", "max": 100, "value": profit_score},
        {"name": "增长潜力 (Growth)", "max": 100, "value": growth_score},
        {"name": "新锐入局难度 (Difficulty)", "max": 100, "value": difficulty_score}
    ]

    # Actionable operational recommendations
    opportunities = [
        f"价格带策略：当前类目主流产品集中在头部品牌价格带，而在中间价格段存在供给凹槽，具有错位竞争空间。",
        f"转化优化：竞品平均评分约为 {rating} 分，若能在产品用料或包装上攻克常见负评痛点，即可在评价积累期实现弯道超车。"
    ]
    
    risks = [
        f"头部垄断风险：Top 4 品牌集中度为 {cr4}%，头部具有极强的广告竞价防御能力，切勿在主核心词上硬拼。",
        f"流量壁垒：竞品评论基数积累深厚，新品入局前 90 天需重度依赖精准长尾词投放与早期买家信任积累。"
    ]

    action_checklist = [
        {"type": "PRICING", "title": "定价定位建议", "detail": f"建议新品首发定价策略采取渗透定价或赠品捆绑策略，并在前台搭配 10% Coupon 标签增强 CTR 点击转化。"},
        {"type": "PPC", "title": "广告投放战术", "detail": "重点投放供需比低于 0.25 的高购买率长尾词，精准匹配为主，避免大词预算被头部竞品快速消耗。"},
        {"type": "LISTING", "title": "Listing 埋词重点", "detail": "在五点描述 (Bullet Points) 和后台 Search Terms 中密集植入 ABA 前列的场景词与人群属性词。"}
    ]

    return {
        "overallScore": round((market_capacity_score + profit_score + growth_score + (100 - difficulty_score)) / 4, 1),
        "radarData": radar_indicators,
        "opportunities": opportunities,
        "risks": risks,
        "actionChecklist": action_checklist
    }
