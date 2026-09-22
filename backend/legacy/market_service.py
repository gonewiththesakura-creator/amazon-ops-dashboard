import logging
from typing import Dict, Any, List
from ..mcp_client import mcp_client

logger = logging.getLogger("market_service")

async def analyze_market(marketplace: str, query: str) -> Dict[str, Any]:
    """Analyzes category market landscape, price brackets, brand concentration and rating distributions."""
    marketplace = marketplace.upper()
    query = query.strip()

    node_id_path = query
    category_name = query

    # If query is not in node format (e.g., '172282:24046923011'), search category node first
    if not (":" in query and query.replace(":", "").isdigit()):
        node_res = await mcp_client.call_tool("product_node", {
            "request": {
                "marketplace": marketplace,
                "keyword": query
            }
        })
        if node_res.get("code") == "OK" and node_res.get("data"):
            first_node = node_res["data"][0]
            node_id_path = first_node.get("nodeIdPath", "")
            category_name = first_node.get("nodeLabelPath", query)
        else:
            # default fallback category path for electronics
            node_id_path = "172282:24046923011:172541"
            category_name = f"Amazon {query} Category"

    # 1. Price Distribution
    price_res = await mcp_client.call_tool("market_price_distribution", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })
    raw_prices = price_res.get("data", []) if price_res.get("code") == "OK" else []

    price_brackets = []
    for item in raw_prices:
        label = item.get("label", "")
        # format label as $X-$Y
        clean_label = label if "$" in label else f"${label}"
        price_brackets.append({
            "bracket": clean_label,
            "products": item.get("products", 0),
            "units": item.get("units", 0),
            "revenue": round(item.get("revenue", 0.0), 2),
            "unitsRatio": round(item.get("unitsRatio", 0.0) * 100, 2)
        })

    # 2. Brand Concentration
    brand_res = await mcp_client.call_tool("market_brand_concentration", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })
    raw_brands = brand_res.get("data", []) if brand_res.get("code") == "OK" else []

    brand_list = []
    top4_units_ratio = 0.0
    for idx, b in enumerate(raw_brands):
        brand_name = b.get("brand", "Unknown")
        ratio = round(b.get("totalUnitsRatio", 0.0) * 100, 2)
        if idx < 4:
            top4_units_ratio += ratio
        brand_list.append({
            "name": brand_name,
            "ranking": b.get("ranking", idx + 1),
            "share": ratio,
            "revenue": round(b.get("totalRevenue", 0.0), 2),
            "units": b.get("totalUnits", 0),
            "avgPrice": b.get("avgPrice", 0.0),
            "rating": b.get("rating", 0.0)
        })

    # CR4 & CR8 calculations
    cr4 = round(top4_units_ratio, 2)
    cr8 = round(sum(b["share"] for b in brand_list[:8]), 2)
    others_share = max(0.0, round(100.0 - sum(b["share"] for b in brand_list[:8]), 2))

    pie_brands = [
        {"name": b["name"], "value": b["share"]} for b in brand_list[:6]
    ]
    if others_share > 0:
        pie_brands.append({"name": "其他品牌 (Others)", "value": others_share})

    # 3. Rating Distribution
    rating_res = await mcp_client.call_tool("market_rating_distribution", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })
    raw_ratings = rating_res.get("data", []) if rating_res.get("code") == "OK" else []
    rating_distribution = [
        {
            "ratingRange": r.get("label", "N/A"),
            "products": r.get("products", 0),
            "units": r.get("units", 0),
            "unitsRatio": round(r.get("unitsRatio", 0.0) * 100, 2)
        }
        for r in raw_ratings
    ]

    # 4. Seller Country Distribution
    country_res = await mcp_client.call_tool("market_seller_country_distribution", {
        "request": {
            "marketplace": marketplace,
            "nodeIdPath": node_id_path
        }
    })
    raw_countries = country_res.get("data", []) if country_res.get("code") == "OK" else []
    country_distribution = [
        {
            "country": c.get("country", "其他"),
            "share": round(c.get("unitsRatio", 0.0) * 100, 2),
            "products": c.get("products", 0),
            "revenue": round(c.get("revenue", 0.0), 2)
        }
        for c in raw_countries
    ]

    return {
        "marketplace": marketplace,
        "query": query,
        "nodeIdPath": node_id_path,
        "categoryName": category_name,
        "cr4": cr4,
        "cr8": cr8,
        "monopolyLevel": "高垄断 (寡头市场)" if cr4 > 65 else ("中度集中" if cr4 > 40 else "充分竞争市场"),
        "priceBrackets": price_brackets,
        "brandSharePie": pie_brands,
        "brandList": brand_list[:10],
        "ratingDistribution": rating_distribution,
        "countryDistribution": country_distribution
    }
