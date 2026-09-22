from typing import Dict, Any

def calculate_replenishment(
    stock: int = 200,
    daily_sales: int = 50,
    sea_days: int = 30,
    batch_size: int = 10000,
    unit_cost: float = 50.0,
    sea_shipping_rate: float = 12.0,  # 海运单件运费（元）
    air_shipping_rate: float = 45.0   # 空运单件运费（元）
) -> Dict[str, Any]:
    """Calculates stockout warning, replenishment plan, air freight emergency dispatch and cashflow pool.
    Implements the exact logic from the user's meeting architecture chart.
    """
    daily_sales = max(1, daily_sales)
    stock = max(0, stock)

    # 1. 现有可售天数与断货警报
    stock_days = round(stock / daily_sales, 1)
    
    # 风险状态：<= 7天红灯（断货危险），8-15天黄灯（补货预警），>15天绿灯（库存安全）
    if stock_days <= 7:
        risk_level = "RED"
        risk_label = "🚨 极度危险 (亮红灯)：立即断货风险！"
        risk_color = "rose"
    elif stock_days <= 15:
        risk_level = "YELLOW"
        risk_label = "⚠️ 补货预警 (亮黄灯)：进入补货警戒线"
        risk_color = "amber"
    else:
        risk_level = "GREEN"
        risk_label = "✅ 库存安全 (绿灯)"
        risk_color = "emerald"

    # 2. 海运周期内需备量
    sea_required = sea_days * daily_sales

    # 3. 紧急空运补货测算 (填补断货窗口)
    # 比如现有只够卖 4 天，海运需要 30 天，那么中间会有 26 天断货窗口
    stockout_gap_days = max(0, sea_days - int(stock_days))
    air_urgent_units = stockout_gap_days * daily_sales if stockout_gap_days > 0 else 0
    air_shipping_cost = round(air_urgent_units * air_shipping_rate, 2)

    # 4. 批量大货货款与总资金池
    goods_cost = round(batch_size * unit_cost, 2)
    sea_shipping_cost = round((batch_size - air_urgent_units) * sea_shipping_rate, 2) if batch_size > air_urgent_units else round(batch_size * sea_shipping_rate, 2)
    total_shipping_cost = round(sea_shipping_cost + air_shipping_cost, 2)
    total_capital_pool = round(goods_cost + total_shipping_cost, 2)

    return {
        "stock": stock,
        "dailySales": daily_sales,
        "stockDays": stock_days,
        "riskLevel": risk_level,
        "riskLabel": risk_label,
        "riskColor": risk_color,
        "seaDays": sea_days,
        "seaRequired": sea_required,
        "stockoutGapDays": stockout_gap_days,
        "airUrgentUnits": air_urgent_units,
        "airShippingCost": air_shipping_cost,
        "batchSize": batch_size,
        "unitCost": unit_cost,
        "goodsCost": goods_cost,
        "seaShippingCost": sea_shipping_cost,
        "totalShippingCost": total_shipping_cost,
        "totalCapitalPool": total_capital_pool,
        "caseNote": "灰色枕头案例警示：补多少货 ➔ 运费（补少则单位运费高、不划算；补多则需平衡资金占用）"
    }
